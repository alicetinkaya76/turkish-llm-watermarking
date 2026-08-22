# hpc/remote_scripts/drift.py — SÜRÜM KAYMASI ÖLÇÜMÜ. [KONTEYNERDE ÇALIŞIR]
#
# NEDEN VAR: pilot/ kodundaki bazı kararlar YEREL ORTAMDA AMPİRİK ÖLÇÜLMÜŞ davranışlara
# dayanıyor. Hedef ortam farklı sürümlerde. Projenin kuralı ("ölçülmeyeni varsayma")
# gereği bu ölçümler DEVRALINMAZ, burada yeniden yapılır.
#
#   ölçümün yapıldığı sürüm | yerelde şu an | HPC'de
#   ------------------------|---------------|--------
#   transformers 5.10.2     | 5.15.0        | 5.8.0     <- ölçüm HİÇBİR YERDE kurulu değil
#   torch (bilinmiyor)      | 2.13.0        | 2.10.0+cu128
#   python                  | 3.11.9        | 3.12.3
#   cihaz MPS               | MPS           | CUDA sm_75
#
# ÖLÇÜLENLER (her biri pilot/ içinde somut bir karara bağlı):
#   T1 dtype kwarg      -> generate.py:39-41 `torch_dtype=`. v5'te ad `dtype` oldu.
#                          Eski ad sessizce yutulursa model fp32 yüklenir: 14B = 56 GB, OOM.
#   T2 işlemci sırası   -> config.py:50-58 SynthID çift-sıcaklık düzeltmesi. Özel
#                          logits_processor sıcaklık warper'ından ÖNCE mi ÇALIŞIYOR?
#                          Sıra değiştiyse SynthID'nin etkin sıcaklığı yanlış olur ve
#                          şemalar arası karşılaştırma bozulur.
#   T3 top_k varsayılanı-> config.py:16-21. GenerationConfig varsayılanı None ise değer
#                          modelin generation_config.json'undan gelir (Qwen2.5: top_k=20).
#                          Açık top_k=0 gerçekten eziyor mu?
#   T4 determinizm      -> K11. Aynı tohum -> aynı token dizisi mi? (MPS'te 8/8 aynıydı)
#   T5 dtype hızı       -> sm_75'te bf16 EMÜLASYON. is_bf16_supported() True der, yalandır.
#   T6 fp16 sapması     -> fp16 log-olasılıklarının fp32'den sapması. DİKKAT: ilk
#                          sürümde "EXP p-değerini etkiler" yazıyordu ve YANLIŞTI --
#                          üç dedektör de MODELSİZDİR (exp.py:161-180 tokenizer+rng+
#                          gamma.sf, kgw.py:142 karma, synthid.py:371 ngram karma).
#                          Sapma yalnız ÜRETİMİ (örneklenen token dizisini) etkiler.
#
# Çıktı: results_hpc/drift.json (makine) + tablo (insan). Sayılar YALNIZ buradan gelir.
#
#   python hpc/remote_scripts/drift.py --model Qwen/Qwen2.5-0.5B-Instruct
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import warnings
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from transformers.generation.logits_process import LogitsProcessor

SONUC: dict = {"olcumler": {}, "ortam": {}}


def ortam() -> dict:
    d = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "platform": platform.platform(),
        "cuda_var": torch.cuda.is_available(),
    }
    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        d |= {"gpu": p.name, "compute_capability": f"{p.major}.{p.minor}",
              "vram_gb": round(p.total_memory / 1e9, 1),
              "cuda_runtime": torch.version.cuda}
        try:
            d["bf16_native"] = torch.cuda.is_bf16_supported(including_emulation=False)
            d["bf16_emulasyon_dahil"] = torch.cuda.is_bf16_supported()
        except TypeError:
            d["bf16_native"] = "BELIRSIZ (bu torch'ta including_emulation yok)"
    return d


# ----------------------------------------------------------------------
# T1: dtype kwarg gerçekten uygulanıyor mu
# ----------------------------------------------------------------------
def t1_dtype_kwarg(name: str) -> dict:
    r: dict = {}
    for kw in ("torch_dtype", "dtype"):
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                m = AutoModelForCausalLM.from_pretrained(name, **{kw: torch.float16})
                got = str(next(m.parameters()).dtype)
                uyari = [str(x.message)[:110] for x in w
                         if "deprecat" in str(x.message).lower() or kw in str(x.message)]
            del m
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            r[kw] = {"kabul": True, "elde_edilen_dtype": got,
                     "fp16_mi": got == "torch.float16", "uyari": uyari[:2]}
        except Exception as e:
            r[kw] = {"kabul": False, "hata": f"{type(e).__name__}: {str(e)[:160]}"}
    calisan = [k for k, v in r.items() if v.get("fp16_mi")]
    r["_karar"] = (f"KULLAN: {calisan[0]}" if calisan
                   else "BLOKE EDİCİ: hiçbir dtype kwarg'ı fp16 üretmedi")
    return r


# ----------------------------------------------------------------------
# T2: özel logits_processor sıcaklıktan ÖNCE mi sonra mı
# ----------------------------------------------------------------------
class _Kaydedici(LogitsProcessor):
    """İlk adımda kendisine GELEN scores'u saklar. Ham logit'e eşitse sıcaklık
    HENÜZ uygulanmamış (biz öncedeyiz); ham/T'ye eşitse sonrayız."""

    def __init__(self) -> None:
        self.ilk: torch.Tensor | None = None

    def __call__(self, input_ids, scores):
        if self.ilk is None:
            self.ilk = scores[0].detach().float().clone()
        return scores


def t2_islemci_sirasi(model, tok, T: float = 0.8) -> dict:
    device = next(model.parameters()).device
    enc = tok("Endülüs tarihi hakkında kısa bir paragraf yaz.", return_tensors="pt").to(device)

    with torch.no_grad():
        ham = model(**enc).logits[0, -1].float().clone()

    kaydedici = _Kaydedici()
    # İç sıralamayı da yakalamayı DENE (tanısal; ampirik oran asıl kanıttır).
    sira: list[str] = []
    try:
        from transformers.generation.utils import GenerationMixin
        orij = GenerationMixin._get_logits_processor

        def casus(self, *a, **k):
            lp = orij(self, *a, **k)
            if not sira:
                sira.extend(type(p).__name__ for p in lp)
            return lp

        GenerationMixin._get_logits_processor = casus
        yamalandi = True
    except Exception:
        yamalandi = False

    try:
        torch.manual_seed(11)
        with torch.no_grad():
            model.generate(**enc, max_new_tokens=1, do_sample=True, temperature=T,
                           top_p=1.0, top_k=0, repetition_penalty=1.0,
                           logits_processor=[kaydedici], pad_token_id=tok.pad_token_id)
    finally:
        if yamalandi:
            from transformers.generation.utils import GenerationMixin
            GenerationMixin._get_logits_processor = orij

    if kaydedici.ilk is None:
        return {"_karar": "BELIRSIZ: işlemci hiç çağrılmadı", "islemci_sirasi": sira}

    # Sıfıra bölmeyi önlemek için yalnız büyüklüğü anlamlı logit'lerde oran al.
    maske = ham.abs() > 1.0
    oran = float((kaydedici.ilk[maske] / ham[maske]).median())
    once = abs(oran - 1.0) < 0.02
    sonra = abs(oran - 1.0 / T) < 0.02
    return {
        "sicaklik_T": T,
        "olculen_oran": round(oran, 4),
        "beklenen_ONCE": 1.0,
        "beklenen_SONRA": round(1.0 / T, 4),
        "islemci_sirasi": sira,
        "_karar": ("ÖNCE (yerel ölçümle AYNI -> SCHEME_GEN_OVERRIDES geçerli)" if once
                   else "SONRA (yerel ölçümden FARKLI -> SCHEME_GEN_OVERRIDES YANLIŞ olur)"
                   if sonra else f"BELIRSIZ: oran {oran:.4f} iki beklentiye de uymuyor"),
    }


# ----------------------------------------------------------------------
# T3: top_k / repetition_penalty varsayılanları nereden geliyor
# ----------------------------------------------------------------------
def t3_topk_varsayilani(model, tok, name: str) -> dict:
    device = next(model.parameters()).device
    enc = tok("Bir cümle yaz.", return_tensors="pt").to(device)
    bos = GenerationConfig()
    mdl = GenerationConfig.from_pretrained(name)

    def sonlu_sayisi(**gk) -> int:
        torch.manual_seed(11)
        with torch.no_grad():
            o = model.generate(**enc, max_new_tokens=1, do_sample=True, temperature=0.8,
                               output_scores=True, return_dict_in_generate=True,
                               pad_token_id=tok.pad_token_id, **gk)
        return int(torch.isfinite(o.scores[0][0]).sum())

    try:
        varsayilan = sonlu_sayisi()                       # hiçbir şey verilmez
        acik_0 = sonlu_sayisi(top_k=0, repetition_penalty=1.0)
        acik_20 = sonlu_sayisi(top_k=20, repetition_penalty=1.0)
    except Exception as e:
        return {"_karar": f"BELIRSIZ: {type(e).__name__}: {str(e)[:140]}"}

    return {
        "GenerationConfig_bos": {"top_k": bos.top_k, "repetition_penalty": bos.repetition_penalty},
        "model_generation_config": {"top_k": mdl.top_k, "repetition_penalty": mdl.repetition_penalty},
        "sonlu_logit_sayisi": {"hicbir_sey_verilmedi": varsayilan,
                               "acik_top_k=0": acik_0, "acik_top_k=20": acik_20},
        "_karar": ("AÇIK DEĞER EZİYOR (config.py:16-21 varsayımı geçerli)"
                   if acik_0 > acik_20 and acik_20 <= 20
                   else "DİKKAT: açık top_k beklendiği gibi ezmiyor -- config.py:16-21 yeniden incelenmeli"),
    }


# ----------------------------------------------------------------------
# T4: determinizm (K11)
# ----------------------------------------------------------------------
def t4_determinizm(model, tok, tekrar: int = 6) -> dict:
    device = next(model.parameters()).device
    enc = tok("Endülüs'te bilim hayatını anlat.", return_tensors="pt").to(device)
    diziler = []
    for _ in range(tekrar):
        torch.manual_seed(11000)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(11000)
        with torch.no_grad():
            o = model.generate(**enc, max_new_tokens=48, do_sample=True, temperature=0.8,
                               top_p=0.95, top_k=0, repetition_penalty=1.0,
                               pad_token_id=tok.pad_token_id)
        diziler.append(o[0].tolist())
    ayni = sum(d == diziler[0] for d in diziler)
    return {"tekrar": tekrar, "ilkine_ozdes": ayni,
            "_karar": ("TAM DETERMİNİSTİK" if ayni == tekrar
                       else f"DETERMİNİSTİK DEĞİL: {tekrar - ayni}/{tekrar} sapma -- K11 riski")}


# ----------------------------------------------------------------------
# T5: dtype hızı (sm_75'te bf16 emülasyon)
# ----------------------------------------------------------------------
def t5_dtype_hizi(n: int = 4096, it: int = 30) -> dict:
    if not torch.cuda.is_available():
        return {"_karar": "ATLANDI: CUDA yok"}
    r = {}
    for dt, nm in ((torch.float16, "fp16"), (torch.bfloat16, "bf16"), (torch.float32, "fp32")):
        try:
            a = torch.randn(n, n, device="cuda", dtype=dt)
            b = torch.randn(n, n, device="cuda", dtype=dt)
            for _ in range(5):
                a @ b
            torch.cuda.synchronize()
            t0 = time.time()
            for _ in range(it):
                a @ b
            torch.cuda.synchronize()
            r[nm] = round(2 * n ** 3 * it / (time.time() - t0) / 1e12, 1)
            del a, b
            torch.cuda.empty_cache()
        except Exception as e:
            r[nm] = f"HATA {type(e).__name__}"
    ok = all(isinstance(r.get(k), float) for k in ("fp16", "bf16"))
    r["_karar"] = (f"fp16 ZORUNLU (bf16'nın {r['fp16'] / r['bf16']:.1f} katı hızlı)"
                   if ok and r["bf16"] and r["fp16"] > r["bf16"] else "BELIRSIZ")
    return r


# ----------------------------------------------------------------------
# T6: fp16 vs fp32 logit sapması (dedektör hassasiyeti)
# ----------------------------------------------------------------------
def t6_fp16_sapmasi(name: str, tok) -> dict:
    if not torch.cuda.is_available():
        return {"_karar": "ATLANDI: CUDA yok"}
    metin = "Endülüs'te kurulan kütüphaneler dönemin ilim hayatını derinden etkilemiştir."
    enc = tok(metin, return_tensors="pt").to("cuda")
    cikti = {}
    for dt, nm in ((torch.float32, "fp32"), (torch.float16, "fp16")):
        m = AutoModelForCausalLM.from_pretrained(name, dtype=dt).to("cuda").eval()
        with torch.no_grad():
            lp = torch.log_softmax(m(**enc).logits[0].float(), dim=-1)
        cikti[nm] = lp[:-1].gather(1, enc.input_ids[0, 1:, None]).squeeze(1).cpu()
        del m
        torch.cuda.empty_cache()
    fark = (cikti["fp16"] - cikti["fp32"]).abs()
    return {
        "token_sayisi": int(fark.numel()),
        "ortalama_mutlak_log_olasilik_farki": round(float(fark.mean()), 5),
        "azami_fark": round(float(fark.max()), 5),
        # DÜZELTME: ilk sürüm "EXP p-değeri etkilenir" diyordu ve YANLIŞTI.
        # Kaynak okundu: ÜÇ DEDEKTÖR DE MODELSİZDİR --
        #   exp.py:161-180  tokenizer + torch.rand(generator=rng) + gamma.sf
        #   kgw.py:142      get_greenlist_ids (karma tabanlı)
        #   synthid.py:371  ngram unfold + karma
        # fp16 yalnız ÜRETİMİ (hangi tokenin örneklendiğini) etkiler, TESPİTİ etkilemez.
        "_karar": (f"ÜRETİMİ etkiler, TESPİTİ ETKİLEMEZ (dedektörler modelsiz). "
                   f"Azami sapma {float(fark.max()):.4f} nat; sonuç: örneklenen "
                   f"token dizisi fp32'den farklı olabilir, ama aynı metin üzerinde "
                   f"tespit istatistiği dtype'tan BAĞIMSIZDIR."),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="sürüm kayması ölçümü")
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct",
                    help="küçük olsun; ölçülen davranış model-bağımsız")
    ap.add_argument("--out", default="results_hpc/drift.json")
    args = ap.parse_args()

    SONUC["ortam"] = ortam()
    SONUC["ortam"]["olculen_model"] = args.model
    print("ORTAM")
    for k, v in SONUC["ortam"].items():
        print(f"  {k:26s} {v}")

    print("\nT1  dtype kwarg (generate.py:39-41)", flush=True)
    SONUC["olcumler"]["T1_dtype_kwarg"] = t1_dtype_kwarg(args.model)
    print(f"  -> {SONUC['olcumler']['T1_dtype_kwarg']['_karar']}")

    kw = "dtype" if SONUC["olcumler"]["T1_dtype_kwarg"].get("dtype", {}).get("fp16_mi") else "torch_dtype"
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(
        args.model, **{kw: torch.float16 if dev == "cuda" else torch.float32}).to(dev).eval()

    for etiket, fn in (
        ("T2_islemci_sirasi", lambda: t2_islemci_sirasi(model, tok)),
        ("T3_topk_varsayilani", lambda: t3_topk_varsayilani(model, tok, args.model)),
        ("T4_determinizm", lambda: t4_determinizm(model, tok)),
        ("T5_dtype_hizi", t5_dtype_hizi),
    ):
        print(f"\n{etiket.replace('_', '  ', 1)}", flush=True)
        try:
            SONUC["olcumler"][etiket] = fn()
        except Exception as e:
            SONUC["olcumler"][etiket] = {"_karar": f"HATA {type(e).__name__}: {str(e)[:180]}"}
        print(f"  -> {SONUC['olcumler'][etiket]['_karar']}")

    del model
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    print("\nT6  fp16 dedektör sapması", flush=True)
    try:
        SONUC["olcumler"]["T6_fp16_sapmasi"] = t6_fp16_sapmasi(args.model, tok)
    except Exception as e:
        SONUC["olcumler"]["T6_fp16_sapmasi"] = {"_karar": f"HATA {type(e).__name__}: {str(e)[:180]}"}
    print(f"  -> {SONUC['olcumler']['T6_fp16_sapmasi']['_karar']}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(SONUC, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print("KARARLAR")
    for k, v in SONUC["olcumler"].items():
        print(f"  {k:22s} {v.get('_karar', '?')}")
    blokeli = [k for k, v in SONUC["olcumler"].items()
               if "BLOKE" in str(v.get("_karar", "")) or "FARKLI" in str(v.get("_karar", ""))]
    print("=" * 72)
    print(f"yazıldı: {out}")
    if blokeli:
        print(f"\n⛔ TAŞIMA ÖNCESİ ÇÖZÜLMELİ: {', '.join(blokeli)}")
        sys.exit(2)


if __name__ == "__main__":
    main()
