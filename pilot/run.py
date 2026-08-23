# pilot/run.py — faz orkestratörü.
#
#   python -m pilot.run --phase 0          # duman testi (küçük model, 2 prompt)
#   python -m pilot.run --phase 1          # temiz üretim + öncül AUROC + bereket
#   python -m pilot.run --phase 2          # saldırılar + tüm metrikler + summary.md
#   python -m pilot.run --phase all        # 1 + 2
#
# Seçenekler: --model <hf_adı>  --ram <GB>  --device mps|cpu  --no-quality
# MarkLLM repo kökünden çalıştırılmalı. PYTORCH_ENABLE_MPS_FALLBACK=1 önerilir.
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# repo kökünü sys.path'e garanti et (watermark/, utils/ importları için)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402


def write_env(device: str, model_name: str, ram: float,
              model_source: str = "ram-tier", config_adi: str = "pilot") -> None:
    import hashlib
    import torch
    import transformers

    def _git(*a) -> str:
        try:
            return subprocess.check_output(["git", *a], cwd=_ROOT, text=True,
                                           stderr=subprocess.DEVNULL).strip()
        except Exception:
            return "unknown"

    commit = _git("rev-parse", "HEAD")

    # ⛔ GIT PROVENANSI HPC'DE ISE YARAMAZ. deploy.py pilot/ ve hpc/ dizinlerini
    # DOSYA olarak kopyalar, git gecmisini DEGIL; HPC'deki MarkLLM klonu
    # upstream c45ddc40'ta duruyor. Yani orada `git rev-parse HEAD` DAIMA
    # upstream commit'ini verir ve bu kodun hangi halinin kostugu KAYDEDILMEZ.
    # Cozum: kaynak dosyalarin ICERIK OZETI -- git'ten bagimsiz, her iki
    # ortamda AYNI degeri verir ve iki tarafin ayni kodu kostugunu KANITLAR.
    def _kaynak_ozeti() -> dict:
        h = hashlib.sha256()
        dosyalar = []
        for d in ("pilot", "hpc"):
            kok = _ROOT / d
            if not kok.exists():
                continue
            for f in sorted(kok.rglob("*")):
                if (f.is_file() and f.suffix in (".py", ".json", ".sh")
                        and "__pycache__" not in str(f)):
                    rel = str(f.relative_to(_ROOT))
                    b = f.read_bytes()
                    h.update(rel.encode() + b)
                    dosyalar.append(rel)
        return {"kaynak_sha256": h.hexdigest()[:16], "n_dosya": len(dosyalar)}

    kaynak = _kaynak_ozeti()
    # PILOT KODUNUN SÜRÜMÜ. Önceki sürüm YALNIZ upstream MarkLLM commit'ini
    # kaydediyordu (repo ayrık HEAD'de c45ddc4'teydi) -> bu kodun hangi hâliyle
    # üretildiği HİÇ kayıtlı değildi.
    pilot_kirli = bool(_git("status", "--porcelain", "pilot", "hpc"))
    kgw_src = (_ROOT / "watermark/kgw/kgw.py").read_text(encoding="utf-8")
    env = dict(
        torch=torch.__version__,
        transformers=transformers.__version__,
        python=sys.version.split()[0],
        # DIKKAT: HPC'de bu DAIMA upstream commit'idir (klon oradan yapiliyor),
        # pilot kodunun surumu DEGILDIR. Onun icin kaynak_sha256'ya bak.
        markllm_commit=commit,
        **kaynak,
        # Çalışma dalı + kirlilik. Kirli ağaçtan üretilen çıktı TAM olarak
        # yeniden üretilemez; bunu gizlemek yerine kayda geçiriyoruz.
        dal=_git("rev-parse", "--abbrev-ref", "HEAD"),
        pilot_kirli=pilot_kirli,
        pilot_kirliyse_uyari=("çalışma ağacı KİRLİ -- bu çıktı tam olarak "
                              "yeniden üretilemez" if pilot_kirli else ""),
        mps_patch_applied=("MPS uyumu" in kgw_src),
        device=device,
        model=model_name,
        # "ram-tier" = K6 kademesinden otomatik; "cli-override" = --model ile elle
        # seçildi (kademe başka bir model derdi -> sapma burada görünür kalsın).
        model_source=model_source,
        ram_tier_model=C.pick_model(ram)[0],
        ram_gb=round(ram, 1),
        seeds=C.SEEDS,
        gen_kwargs=C.GEN_KWARGS,
        # EXP EOS'ta durmaz; uzunlugunu YALNIZ bu deger belirler. env.json'da HIC
        # yoktu -> koşunun EXP uzunlugu provenansta gorunmuyordu.
        exp_sequence_length=C.EXP_SEQUENCE_LENGTH,
        # Hangi config seti yururlukteydi ("pilot" | "cuda"). Ezmeler sessizce
        # devreye girmesin/girmemis olmasin diye ACIKCA kaydediliyor.
        config_adi=config_adi,
        # Istemler korpusun tanimidir; kelime hedefi degistiginde (300 -> 500)
        # eski kosularla karistirilmamasi icin icerik ozeti kayda giriyor.
        prompts_sha256=hashlib.sha256(
            Path(C.PROMPTS_PATH).read_bytes()).hexdigest(),
        n_prompts=C.N_PROMPTS,
        scheme_gen_overrides=C.SCHEME_GEN_OVERRIDES,
        # MarkLLM çekirdeğine dokunmadan pilot tarafında uygulanan düzeltmeler
        # (gerekçeleri config.py / generate.py yorumlarında):
        pilot_fixes=[
            # SABIT METIN DEGIL: gercek degerlerden uretiliyor. Onceki surumde
            # "top_k=0 ... verildi" yaziyordu; cuda config'inde top_k=20 oldugu
            # icin env.json KENDI ICINDE CELISIYORDU.
            f"S3: top_k={C.GEN_KWARGS.get('top_k')} + repetition_penalty="
            f"{C.GEN_KWARGS.get('repetition_penalty')} açıkça verildi "
            "(modelin generation_config.json'undaki değerler ezildi)",
            "S4: SynthID üretiminde gen temperature=1.0 -> çift sıcaklık giderildi",
            "S5: SynthID logits_processor.state her üretimden önce sıfırlanıyor",
        ],
        mps_fallback_env=os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK", ""),
    )
    C.RESULTS.mkdir(parents=True, exist_ok=True)
    (C.RESULTS / "env.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2)
    )
    print("env.json:", json.dumps(env, ensure_ascii=False))


def _load_stack(model_name: str, device: str):
    from pilot.generate import (MpsGeneratorError, load_model_and_tokenizer,
                                load_scheme, make_tcfg)

    print(f"Model yükleniyor: {model_name} ({device}, {C.__dict__.get('DTYPE','float16')})")
    model, tok = load_model_and_tokenizer(model_name, device)
    tcfg = make_tcfg(model, tok, device)
    schemes = {}
    for s in C.SCHEMES:
        try:
            schemes[s] = load_scheme(s, tcfg)
        except MpsGeneratorError as e:
            print(f"\nHATA — {e}", file=sys.stderr)
            sys.exit(2)
    return model, tok, tcfg, schemes


# ----------------------------------------------------------------------
def phase0(device: str, model_name: str | None = None,
           n_prompts: int | None = None, seeds: list[int] | None = None,
           out_dir=None) -> None:
    """Duman testi: KGW wm/no-wm ayrımı + EXP ve SynthID'nin ayağa kalktığı.

    MODEL ARTIK PARAMETRE. Önceki sürüm C.SMOKE_MODEL'i SABİT yüklüyordu, yani
    --model yok sayılıyordu. Sonuç: ön-kapı yalnız FİLİGRANSIZ yolu ölçmüştü
    (dev_preflight düz model.generate çağırır) ve üç filigranlı kol ÜRETİM
    MODELİYLE hiç sınanmamıştı. Oysa filigran tam da örnekleme dağılımını
    değiştirir; kapının filigransız sonucu diğer kollara devredilemez.
    Varsayılanlar korundu -> mevcut `--phase 0` komutu birebir aynı davranır.
    """
    from pilot.generate import generate_records, load_prompts

    model, tok, tcfg, schemes = _load_stack(model_name or C.SMOKE_MODEL, device)
    prompts = load_prompts(n_prompts or C.SMOKE_PROMPTS)
    seeds = seeds or C.SMOKE_SEEDS
    smoke_dir = out_dir or (C.RESULTS / "smoke")

    neg = generate_records(schemes["KGW"], "KGW", False, tok, device,
                           smoke_dir / "neg.jsonl", prompts, seeds)
    pos = generate_records(schemes["KGW"], "KGW", True, tok, device,
                           smoke_dir / "pos_KGW.jsonl", prompts, seeds)
    zs_n = [schemes["KGW"].detect_watermark(r["text"])["score"] for r in neg]
    zs_p = [schemes["KGW"].detect_watermark(r["text"])["score"] for r in pos]
    mn, mp = sum(zs_n) / len(zs_n), sum(zs_p) / len(zs_p)
    print(f"\nKGW duman: z(no-wm)={mn:.2f}  z(wm)={mp:.2f}  fark={mp-mn:.2f}")

    for s in ("EXP", "SynthID"):
        r = generate_records(schemes[s], s, True, tok, device,
                             smoke_dir / f"pos_{s}.jsonl", prompts[:1],
                             C.SMOKE_SEEDS)
        det = schemes[s].detect_watermark(r[0]["text"])
        print(f"{s} duman: score={det['score']:.4g} "
              f"is_watermarked={det['is_watermarked']}")

    ok = (mp - mn) > 2.0
    print("\nFAZ 0:", "GEÇTİ ✔" if ok else
          "ŞÜPHELİ — z ayrımı zayıf; kabul kriterine bak", flush=True)
    sys.exit(0 if ok else 1)


# ----------------------------------------------------------------------
def phase1(model_name: str, device: str) -> None:
    from pilot import fertility
    from pilot.generate import generate_records, load_prompts
    from pilot.detect import run_detection
    from pilot.metrics import auroc, detection_table
    import pandas as pd

    model, tok, tcfg, schemes = _load_stack(model_name, device)
    prompts = load_prompts(C.N_PROMPTS)

    # Negatifler BİR kez (K9): üç dedektör de aynı metinleri skorlar.
    generate_records(schemes["KGW"], "none", False, tok, device,
                     C.RESULTS / "gen_neg.jsonl", prompts, C.SEEDS)
    for s in C.SCHEMES:
        generate_records(schemes[s], s, True, tok, device,
                         C.RESULTS / f"gen_pos_{s}.jsonl", prompts, C.SEEDS)

    fertility.measure(tok, model_name)

    csv_path = C.RESULTS / "scores.csv"
    if csv_path.exists():
        csv_path.unlink()  # temiz fazda skorlar sıfırdan
    for s in C.SCHEMES:
        run_detection(schemes[s], s, attacks=[], csv_path=csv_path)

    scores = pd.read_csv(csv_path)
    det = detection_table(scores)
    print("\nTemiz AUROC'lar:")
    print(det[det.condition == "clean"][
        ["scheme", "auroc", "ci_lo", "ci_hi", "tpr_1fpr"]
    ].to_string(index=False))
    kgw = det[(det.scheme == "KGW") & (det.condition == "clean")]["auroc"]
    if len(kgw) and float(kgw.iloc[0]) < C.SANITY_AUROC:
        print(f"\nÖNCÜL KALDI: KGW temiz AUROC {float(kgw.iloc[0]):.3f} < "
              f"{C.SANITY_AUROC}. HANDOFF §4/Faz-1 gereği DUR ve kullanıcıya "
              "danış (anlatı değişir).")
        sys.exit(3)
    print("\nFAZ 1: öncül GEÇTİ ✔")


# ----------------------------------------------------------------------
def phase2(model_name: str, device: str, with_quality: bool,
           attacks: list[str] | None = None) -> None:
    """attacks=None ise C.ATTACKS (yedi saldırının tamamı). Alt küme verildiğinde
    yalnız o saldırılar üretilip skorlanır; saldırılı metinler JSONL'de cache'li
    olduğu için sonradan tam kümeyle yeniden koşmak eksikleri tamamlar."""
    from pilot.detect import build_attacked_texts, run_detection
    from pilot.generate import read_jsonl
    from pilot.heavy_attacks import RoundTripTranslator
    from pilot.metrics import write_summary

    attacks = list(C.ATTACKS) if attacks is None else attacks
    if attacks != list(C.ATTACKS):
        print(f"KISMİ FAZ 2 — yalnız {attacks}; atlananlar: "
              f"{[a for a in C.ATTACKS if a not in attacks]}")
    model, tok, tcfg, schemes = _load_stack(model_name, device)

    neg = read_jsonl(C.RESULTS / "gen_neg.jsonl")
    if not neg:
        print("Önce Faz 1 koşulmalı (gen_neg.jsonl yok)."); sys.exit(4)

    rtt = None
    if "rtt" in attacks:
        print("RTT çevirmeni yükleniyor (NLLB-600M)…")
        rtt = RoundTripTranslator(device)
    sources = [("neg", neg)] + [
        (f"pos_{s}", read_jsonl(C.RESULTS / f"gen_pos_{s}.jsonl"))
        for s in C.SCHEMES
    ]
    for tag, rows in sources:
        print(f"Saldırılı metinler: {tag} ({len(rows)} taban)")
        build_attacked_texts(tag, rows, attacks, tok, device,
                             model=model, rtt=rtt)
    if rtt is not None:
        rtt.close()

    csv_path = C.RESULTS / "scores.csv"
    if csv_path.exists():
        csv_path.unlink()  # tam tabloyu tutarlı tek geçişte yeniden yaz
    for s in C.SCHEMES:
        run_detection(schemes[s], s, attacks=attacks, csv_path=csv_path)

    write_summary(device, with_quality=with_quality)
    print("\nFAZ 2 tamam ✔  ->  results/summary.md")


# ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Türkçe filigran pilotu")
    ap.add_argument("--phase", required=True, choices=["0", "1", "2", "all"])
    ap.add_argument("--model", default=None, help="HF model adı (kademe yerine)")
    ap.add_argument("--ram", type=float, default=None, help="GB (otomatik yerine)")
    ap.add_argument("--device", default=None, choices=["mps", "cuda", "cpu"])
    ap.add_argument("--no-quality", action="store_true",
                    help="e5 kalite metriğini atla")
    ap.add_argument("--attacks", default=None,
                    help="Faz 2 için virgülle ayrılmış saldırı alt kümesi "
                         f"(varsayılan hepsi: {','.join(C.ATTACKS)})")
    # ⛔ BU BAYRAK OLMADAN hpc/config_cuda.py'deki ÖLÇÜME DAYALI EZMELER KOŞUYA
    # HİÇ GİRMİYORDU. Denetimde bulundu: config_cuda'yı hiçbir modül import
    # etmiyordu -> yürürlükteki değerler max_new_tokens=320, top_k=0,
    # EXP_SEQUENCE_LENGTH=300 kalıyordu; yani korpus, GEÇERSİZ İLAN EDİLEN
    # rejimin ta kendisiyle üretilirdi ve koşu hatasız biterdi.
    #
    # Sadece `import hpc.config_cuda` YETMEZ: o dosya `from pilot.config import *`
    # ile isimleri KENDİ ad alanına kopyalıyor. Bu yüzden pilot.config MODÜL
    # NİTELİKLERİ yamalanıyor -- generate/detect/metrics hepsi `C.X` diye
    # ÇAĞRI ANINDA okuduğu için yama hepsine birden ulaşır.
    ap.add_argument("--smoke-prompts", type=int, default=None,
                    help="faz 0: istem sayısı (varsayılan C.SMOKE_PROMPTS)")
    ap.add_argument("--smoke-seeds", type=int, default=None,
                    help="faz 0: tohum sayısı (varsayılan C.SMOKE_SEEDS)")
    ap.add_argument("--smoke-out", default=None,
                    help="faz 0: çıktı dizini (results/smoke yerine). Ana korpus "
                         "dosyalarına YAZMAMAK için kullan -- resume sızdırır.")
    ap.add_argument("--config", choices=["pilot", "cuda"], default="pilot",
                    help="'cuda': hpc/config_cuda.py ezmelerini uygula (TF-HPC). "
                         "Varsayılan 'pilot' -- mevcut komutlar aynen çalışsın.")
    args = ap.parse_args()

    if args.config == "cuda":
        import pilot.config as _pc
        from hpc import config_cuda as _H
        # Ezilecek adlar config_cuda'da TANIMLI ve config.py'de VAR olan tum
        # buyuk harfli sabitlerden turetilir. Elle liste tutmak delik birakti:
        # ATTN_IMPLEMENTATION listede yoktu -> config_cuda'daki "sdpa" kosuya
        # hic girmedi (generate.py None gorup transformers varsayilanina dustu).
        _EZILEN = tuple(sorted(
            ad for ad in dir(_H)
            if ad.isupper() and not ad.startswith("_")
            and hasattr(_pc, ad)
            and getattr(_H, ad) != getattr(_pc, ad)))
        for _ad in _EZILEN:
            _eski, _yeni = getattr(_pc, _ad), getattr(_H, _ad)
            setattr(_pc, _ad, _yeni)
            print(f"  config ezildi: {_ad} = {_yeni}   (pilot: {_eski})")
        # Sessiz kayma olmasın: yamanın gerçekten tuttuğunu KANITLA.
        assert C.GEN_KWARGS is _H.GEN_KWARGS, "config ezmesi tutmadı"
        print(f"  ETKİN: max_new_tokens={C.GEN_KWARGS['max_new_tokens']} "
              f"top_k={C.GEN_KWARGS['top_k']} EXP={C.EXP_SEQUENCE_LENGTH}")

    attacks = None
    if args.attacks:
        attacks = [a.strip() for a in args.attacks.split(",") if a.strip()]
        bad = [a for a in attacks if a not in C.ATTACKS]
        if bad:
            ap.error(f"bilinmeyen saldırı: {bad}; geçerli: {C.ATTACKS}")

    from pilot.generate import get_device

    device = get_device(args.device)
    # ⛔ --model VERILMEZSE C.pick_model() KADEMEYE duser. Olculdu
    # (results/preflight_sweep.json): o kademenin sectigi Qwen2.5-7B on-kapiyi
    # 3/16 ile GECEMEDI, latin_temiz 4/16. Yani bayrak unutulunca kosu sessizce
    # ELENMIS bir modelle saatlerce calisirdi. Bilimsel fazlarda ARTIK ZORUNLU.
    if args.phase in ("1", "2", "all") and not args.model:
        ap.error(
            "--model zorunlu (faz 1/2/all).\n"
            "  Varsayilan kademe Qwen2.5-7B secer; o model on-kapiyi GECEMEDI "
            "(3/16, latin 4/16).\n"
            "  On-kapiyi gecen: --model Qwen/Qwen3-14B  (14/16, latin 16/16)")
    model_name, ram = ((args.model, C.detect_ram_gb()) if args.model
                       else C.pick_model(args.ram))
    print(f"Cihaz: {device} | RAM: {ram:.0f} GB | Model: {model_name}")
    if 24 <= ram < 32 and "7B" in model_name:
        print("NOT: 24 GB'ta 7B fp16 sınırdadır; bellek baskısında "
              "'--model Qwen/Qwen2.5-3B-Instruct' ile yeniden başlat.")
    if device == "mps" and os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") != "1":
        print("NOT: PYTORCH_ENABLE_MPS_FALLBACK=1 ayarlı değil; desteklenmeyen "
              "bir op çıkarsa hata yerine CPU'ya düşmesi için ayarlanması önerilir.")

    # ETKİN model kaydedilir. Eski koşul faz 0'da DAİMA C.SMOKE_MODEL yazıyordu;
    # phase0 artık --model'e saygı duyduğu için bu, env.json'un YANLIŞ MODELİ
    # kaydetmesi demekti (ölçüldü: Qwen3-14B koşarken env.json Qwen2.5-1.5B yazdı).
    # Provenansın yanlış olması, olmamasından kötüdür.
    etkin_model = (args.model or C.SMOKE_MODEL) if args.phase == "0" else model_name
    write_env(device, etkin_model, ram,
              model_source="cli-override" if args.model else "ram-tier",
              config_adi=args.config)

    if args.phase == "0":
        phase0(device, model_name=args.model, n_prompts=args.smoke_prompts,
               seeds=list(range(11, 11 + args.smoke_seeds)) if args.smoke_seeds else None,
               out_dir=(C.REPO_ROOT / args.smoke_out) if args.smoke_out else None)
    elif args.phase == "1":
        phase1(model_name, device)
    elif args.phase == "2":
        phase2(model_name, device, with_quality=not args.no_quality,
               attacks=attacks)
    else:
        phase1(model_name, device)
        phase2(model_name, device, with_quality=not args.no_quality,
               attacks=attacks)


if __name__ == "__main__":
    main()
