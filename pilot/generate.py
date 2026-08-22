# pilot/generate.py — model + şema yükleme ve JSONL cache'li üretim döngüsü.
# MarkLLM repo kökünden çalıştırılmalı (watermark/, utils/, config/ importları).
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import torch

from pilot import config as C


# ----------------------------------------------------------------------
# Cihaz / model
# ----------------------------------------------------------------------
def get_device(prefer: str | None = None) -> str:
    if prefer:
        return prefer
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def seed_everything(seed: int, device: str) -> None:
    torch.manual_seed(seed)
    if device == "mps" and hasattr(torch, "mps"):
        try:
            torch.mps.manual_seed(seed)
        except Exception:
            pass


def load_model_and_tokenizer(name: str, device: str, dtype: str = "float16"):
    """Model + tokenizer yukle.

    VRAM ON-KONTROLU: onceki surumde YOKTU -- yer yoksa from_pretrained saatlerce
    surmus bir kosunun ortasinda CUDA OOM ile patliyordu. GPU PAYLASIMLI oldugu icin
    (baska oturum ayni kartta 36,7 GB tutmustu, olculdu) bu gercek bir senaryo.
    Yuklemeden ONCE bos VRAM okunur ve yetmiyorsa ANLASILIR mesajla durulur.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if device == "cuda" and torch.cuda.is_available():
        bos, toplam = torch.cuda.mem_get_info()
        print(f"  VRAM: {bos/1e9:.1f} GB bos / {toplam/1e9:.1f} GB toplam", flush=True)
        if bos < 8e9:
            raise SystemExit(
                f"\n⛔ VRAM YETERSIZ: yalniz {bos/1e9:.1f} GB bos.\n"
                f"   GPU paylasimli; baska bir surec kart uzerinde olabilir.\n"
                f"   Kontrol:  python -m hpc.remote sh 'nvidia-smi'\n"
                f"   Yer acilana kadar BEKLE; yarim kosu baslatma.")

    torch_dtype = getattr(torch, dtype) if device != "cpu" else torch.float32
    tok = AutoTokenizer.from_pretrained(name)
    # attn_implementation ACIKCA veriliyor: config_cuda.py "sdpa" tanimliyordu ama
    # HICBIR YERE gecmiyordu; transformers varsayilaninin sdpa'ya dusmesi BEKLENIR,
    # ancak beklenti provenans degildir. FlashAttention-2 Turing'de YOK (olculdu).
    _attn = getattr(C, "ATTN_IMPLEMENTATION", None)
    _ek = {"attn_implementation": _attn} if _attn else {}
    model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch_dtype, **_ek)
    model = model.to(device).eval()
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    return model, tok


def make_tcfg(model, tok, device: str, **gen_overrides):
    """TransformersConfig kur. K7b: EXP sıcaklığı kwargs'tan DEĞİL
    attribute'tan okur; burada elle atanır."""
    from utils.transformers_config import TransformersConfig

    gen = dict(C.GEN_KWARGS)
    gen.update(gen_overrides)
    gen.setdefault("pad_token_id", tok.pad_token_id)
    tcfg = TransformersConfig(model=model, tokenizer=tok, device=device, **gen)
    tcfg.temperature = gen.get("temperature", C.TEMPERATURE)  # K7b
    tcfg.top_k = -1
    return tcfg


class MpsGeneratorError(RuntimeError):
    """torch.Generator(device='mps') desteklenmiyor -> yama gerekli (K5)."""


def load_scheme(name: str, tcfg, seq_len: int | None = None):
    from watermark.auto_watermark import AutoWatermark

    # EXP EOS'ta durmaz; uzunluğu sequence_length sabitler. Token bütçesi
    # (GEN_KWARGS["max_new_tokens"]) değiştiğinde bunun onunla birlikte değişmesi
    # gerekir, yoksa EXP metinleri diğer şemalardan farklı uzunlukta olur ve
    # şemalar arası karşılaştırma bozulur. JSON'a değil buraya bağlandı.
    extra = {}
    if name == "EXP":
        extra["sequence_length"] = C.EXP_SEQUENCE_LENGTH if seq_len is None else seq_len

    try:
        obj = AutoWatermark.load(
            name, algorithm_config=C.SCHEME_CONFIGS[name], transformers_config=tcfg,
            **extra
        )
    except RuntimeError as e:
        msg = str(e).lower()
        if "generator" in msg and ("mps" in msg or "device" in msg):
            raise MpsGeneratorError(
                f"{name}: torch.Generator MPS'te kurulamadı. Çözüm (K5):\n"
                "    git apply patches/mps_generator.patch\n"
                "sonra komutu yeniden çalıştır."
            ) from e
        raise

    # Şema-özel gen_kwargs ezmesi (C.SCHEME_GEN_OVERRIDES; SynthID çift sıcaklık).
    # YENİ bir sözlük atanır: tcfg.gen_kwargs tüm şemaların paylaştığı tek nesnedir,
    # yerinde değiştirilirse diğer şemalara da sızar.
    # DİKKAT: ezilmiş bir nesneyle generate_unwatermarked_text çağrılırsa negatifler
    # de ezilmiş ayarla üretilir; bu yüzden negatifler daima KGW nesnesiyle üretilir
    # (run.phase1, dev_toy_smoke).
    if name in C.SCHEME_GEN_OVERRIDES:
        obj.config.gen_kwargs = dict(tcfg.gen_kwargs, **C.SCHEME_GEN_OVERRIDES[name])
    return obj


def reset_scheme_state(scheme_obj) -> None:
    """Filigran işlemcisinin üretimler-arası durumunu sıfırlar.

    MarkLLM'de SynthIDLogitsProcessor.state yalnız ilk çağrıda kuruluyor ve
    generate_watermarked_text çağrıları arasında SIFIRLANMIYOR. Sonuçları:
    (i) her yeni üretimin ilk ngram_len-1 adımı bir ÖNCEKİ metnin son
    tokenlarını bağlam sanıyor; (ii) 1024'lük context_history örnekler arasında
    taşınıyor, yanlış 'tekrar eden bağlam' tespiti bazı adımlarda filigranı hiç
    uygulatmıyor; (iii) skorlar üretim SIRASINA bağımlı hâle geliyor -> K11
    (tekrarlanabilirlik) ihlali. Çekirdeğe dokunmadan her üretimden önce
    sıfırlıyoruz. KGW/EXP'de böyle bir durum yok; çağrı no-op.
    """
    lp = getattr(scheme_obj, "logits_processor", None)
    if lp is not None and hasattr(lp, "state"):
        lp.state = None


# ----------------------------------------------------------------------
# Prompt hazırlama + completion dilimleme (K8)
# ----------------------------------------------------------------------
def render_prompt(tok, user_text: str, enable_thinking: bool | None = None) -> str:
    """Sohbet şablonunu uygula.

    DÜŞÜNME KİPİ: Qwen3 ve sonrası şablonlarda `enable_thinking` var ve VARSAYILANI
    AÇIK; model cevaptan önce <think>...</think> akıl yürütmesi üretiyor (ölçüldü:
    Qwen3-14B, <think> id 151667, results_hpc/tokenizer_facts.json).

    Burada VARSAYILAN OLARAK KAPATILIYOR, üç sebeple:
      1. Görev 300 kelimelik Türkçe kompozisyon; akıl yürütme token bütçesini yer ve
         ön-kapıyı (kelime sayısı, sonlandırılmışlık) SAHTE biçimde düşürür.
      2. EXP'in uzunluğu sequence_length ile sabit; bütçenin akıl yürütmeye gitmesi
         EXP metinlerini diğer şemalardan farklı etkiler -> karşılaştırma bozulur.
      3. Pilot Qwen2.5 ile koşuldu; orada düşünme kipi YOKTU. Kapatmak iki koşuyu
         aynı üretim rejiminde tutar.

    Şablonda anahtar yoksa (Qwen2.5 vb.) HİÇBİR ŞEY geçilmez -> eski davranış birebir.
    """
    tmpl = getattr(tok, "chat_template", None)
    if not tmpl:
        return user_text
    kw = {}
    if "enable_thinking" in tmpl:
        kw["enable_thinking"] = False if enable_thinking is None else enable_thinking
    return tok.apply_chat_template(
        [{"role": "user", "content": user_text}],
        tokenize=False,
        add_generation_prompt=True,
        **kw,
    )


def slice_completion(tok, rendered_prompt: str, full_text: str) -> tuple[str, bool]:
    """MarkLLM üretimleri prompt DAHİL döner (doğrulandı). Tespit/saldırı
    yalnız completion'da koşmalı. Döner: (completion, temiz_dilimlendi_mi)."""
    ids = tok(rendered_prompt, add_special_tokens=True).input_ids
    p_str = tok.decode(ids, skip_special_tokens=True)
    if full_text.startswith(p_str):
        return full_text[len(p_str):].lstrip("\n"), True
    # nadir yol: ortak önekten kes, son boşlukta hizala
    i = 0
    for a, b in zip(full_text, p_str):
        if a != b:
            break
        i += 1
    cut = full_text.rfind(" ", 0, i)
    return full_text[(cut + 1 if cut > 0 else i):].lstrip("\n"), False


def count_tokens(tok, text: str) -> int:
    return len(tok(text, add_special_tokens=False).input_ids)


# ----------------------------------------------------------------------
# JSONL cache yardımcıları (pilot.jsonl'den; geri uyum için re-export)
# ----------------------------------------------------------------------
from pilot.jsonl import append_jsonl, read_jsonl  # noqa: E402,F401


# ----------------------------------------------------------------------
# Üretim döngüsü
# ----------------------------------------------------------------------
def load_prompts(n: int, path: str | Path | None = None) -> list[str]:
    prompts = json.loads(Path(path or C.PROMPTS_PATH).read_text(encoding="utf-8"))
    return prompts[:n]


# ----------------------------------------------------------------------
# Ön-kapı ölçütleri — TEK KAYNAK
# ----------------------------------------------------------------------
# Tanım dev_preflight.py'deydi ve YALNIZ orada koşuyordu; üretim yolunda hiç
# çalışmıyordu. Oysa dev_preflight.py:18 ve rapor metni "kapıyı geçemeyen üretim
# ana korpusa ALINMAZ" diyordu -> yazılı yükümlülük uygulanmıyordu.
#
# ⚠ KAPI ELEME DEĞİL, RAPORLAMA ALANIDIR. Gerekçe ÖLÇÜLDÜ: EXP sabit uzunlukta
# üretir ve EOS'ta durmaz (exp.py:127) -> pilot verisinde EXP metinlerinin
# 0/96'sı noktalama ile bitiyor (KGW 9/96, SynthID 3/96, negatif 4/96).
# "sonlandırılmış" ölçütü eleme olarak uygulansaydı TÜM EXP korpusu silinir ve
# şema karşılaştırması tamamen yanlılanırdı. Bu yüzden her metin korpusta KALIR,
# bayrakları satırına YAZILIR, eleme YAPILMAZ; rapor oranları bu bayraklardan üretir.
FOREIGN_RE = re.compile(r"[一-鿿぀-ヿ가-힯ᄀ-ᇿЀ-ӿ֐-׿؀-ۿ]")
TERMINAL_CHARS = (".", "!", "?", "…")


def kapi_olcutleri(text: str, hedef: int | None = None,
                   scheme: str | None = None) -> dict:
    """Dört ön-kapı ölçütü. Döner: bayraklar + ham sayımlar.

    scheme="EXP" verilirse `sonlandirilmis` None olur: EXP'in EOS'ta durmaması
    yapısaldır, kusur değildir; onu kusur saymak EXP'i haksız yere cezalandırır.
    """
    hedef = C.KAPI_HEDEF_KELIME if hedef is None else hedef
    w = text.split()
    uniq = len({x.lower() for x in w}) / max(1, len(w))
    son = None if scheme == "EXP" else text.rstrip().endswith(TERMINAL_CHARS)
    return {
        "kapi_kelime": len(w) >= hedef,
        "kapi_sonlandirilmis": son,
        "kapi_latin": not FOREIGN_RE.search(text),
        "kapi_tekrar": uniq >= 0.35,
        "n_kelime": len(w),
        "benzersiz_oran": round(uniq, 4),
        "yabanci_kar": len(FOREIGN_RE.findall(text)),
    }


# ----------------------------------------------------------------------
# Koşu parmak izi (K11)
# ----------------------------------------------------------------------
def run_fingerprint(model_name: str) -> str:
    """Üretim rejimini tek bir özete indirger.

    NEDEN: resume yalnız (prompt_id, seed) çiftine bakıyordu. Ayarlar değişince
    -- max_new_tokens 320 -> 1800, istem "300 kelime" -> "500 kelime", EXP uzunluğu
    300 -> 950 -- ESKİ satırlar da "hazır" sayılıyor, hiçbir uyarı basılmıyor ve
    ortaya İKİ REJİMİN KARIŞIMI bir korpus çıkıyordu. Üstelik env.json yeni model
    adıyla üstüne yazıldığı için provenans aktif olarak YALAN söylüyordu.

    Özete giren her şey metni fiilen değiştirir: model, üretim ayarları, istemlerin
    kendisi, EXP'in sabit uzunluğu. Şema adı GİRMEZ -- her şema kendi dosyasında.
    """
    ozet = json.dumps({
        "model": model_name,
        "gen_kwargs": {k: C.GEN_KWARGS[k] for k in sorted(C.GEN_KWARGS)},
        "exp_sequence_length": C.EXP_SEQUENCE_LENGTH,
        "prompts_sha256": hashlib.sha256(
            Path(C.PROMPTS_PATH).read_bytes()).hexdigest(),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(ozet.encode("utf-8")).hexdigest()[:16]


def fingerprint_dogrula(path: Path, fp: str) -> None:
    """Var olan dosya BAŞKA bir rejimde üretilmişse DUR. Dosyayı SİLME -- kanıttır
    ve silme kararı insana aittir."""
    eskiler = {r.get("fp") for r in read_jsonl(path)}
    eskiler.discard(fp)
    if eskiler:
        raise SystemExit(
            f"\n⛔ REJİM UYUŞMAZLIĞI: {path}\n"
            f"   dosyadaki parmak izi : {sorted(x for x in eskiler if x) or ['(yok - eski sürüm)']}\n"
            f"   şu anki parmak izi   : {fp}\n"
            f"   Bu dosya BAŞKA ayarlarla üretilmiş. Devam edilirse iki rejim karışır.\n"
            f"   Dosyayı SİLMİYORUM. Seçenekler:\n"
            f"     mv {path.parent} {path.parent}_arsiv_<tarih>   (arşivle, yeniden üret)\n"
            f"   veya eski ayarlara dönüp koşuyu tamamla.")


def generate_records(
    scheme_obj,
    scheme_name: str,
    watermarked: bool,
    tok,
    device: str,
    out_path: Path,
    prompts: list[str],
    seeds: list[int],
) -> list[dict]:
    """Her (prompt, seed) için bir completion üretir; out_path'e satır satır
    yazar (kesinti güvenli). Var olan id'ler atlanır (resume)."""
    fp = run_fingerprint(getattr(tok, "name_or_path", "?"))
    fingerprint_dogrula(out_path, fp)
    done = {(r["prompt_id"], r["seed"]) for r in read_jsonl(out_path)}
    total = len(prompts) * len(seeds)
    made = 0
    t0 = time.time()
    for pi, ptext in enumerate(prompts):
        rendered = render_prompt(tok, ptext)
        for seed in seeds:
            if (pi, seed) in done:
                continue
            seed_everything(seed * 1000 + pi, device)
            reset_scheme_state(scheme_obj)
            if watermarked:
                full = scheme_obj.generate_watermarked_text(rendered)
            else:
                full = scheme_obj.generate_unwatermarked_text(rendered)
            comp, clean_cut = slice_completion(tok, rendered, full)
            n_tok = count_tokens(tok, comp)
            row = dict(
                prompt_id=pi,
                seed=seed,
                scheme=scheme_name,
                wm=int(watermarked),
                text=comp,
                n_tokens=n_tok,
                short=int(n_tok < C.MIN_COMPLETION_TOKENS),
                clean_cut=int(clean_cut),
                fp=fp,          # koşu parmak izi (K11) -- bkz. run_fingerprint
                # Ön-kapı bayrakları: ELEME DEĞİL, raporlama (bkz. kapi_olcutleri)
                **kapi_olcutleri(comp, scheme=scheme_name),
            )
            append_jsonl(out_path, row)
            made += 1
            el = time.time() - t0
            print(
                f"  [{scheme_name} wm={int(watermarked)}] "
                f"{len(done) + made}/{total}  ({n_tok} tok, {el / made:.1f} s/örnek)",
                flush=True,
            )
    return read_jsonl(out_path)
