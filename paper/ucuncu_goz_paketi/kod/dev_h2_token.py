# pilot/dev_h2_token.py — D10: H2'nin token-uzunluk konfoundunu ölç.
#
# SORUN. S1 pencereleri KELİME ile eşlendi (dev_insan_fpr.py:43 PENCERE_KELIME=365).
# Türkçe'nin alt-sözcük bereketi İngilizce'den yüksek olduğu için aynı kelime
# sayısı çok farklı TOKEN sayısına karşılık geliyor. KGW'nin z'si
#   z = (yesil - gamma*T) / sqrt(T*gamma*(1-gamma))
# ve null'un ASIL varyansı ardışık göstergelerin bagimsiz olmamasindan geliyor;
# bagimlilik uzun dizide birikir. Dolayisiyla "TR null EN'den genis" bulgusu
# DIL etkisiyle UZUNLUK etkisini ayirt etmiyor. H2 bu ayrimi yapmadan
# "sisme dili izliyor" diyorsa, iddia tasarimin tasiyabileceginden guclu.
#
# YONTEM. Kirpma TOKEN duzeyinde ve BIREBIR yapilir: metin bir kez tokenlenir,
# ilk T token alinir ve dedektorun kendi score_sequence(input_ids) yolu
# dogrudan cagrilir. Boylece coz-yeniden-tokenle sapmasi YOKTUR (detect_watermark
# metinden gider; biz token dizisinden gidiyoruz — ayni fonksiyon, kgw.py:243).
#
# CIKTI: results_insan/h2_token_rapor.json + skor_h2_token.jsonl
#
#   python pilot/dev_h2_token.py --T 300 400 500 --n 1500
#
# NOT: Bu bir ONARIM olcumudur, yeni bir hipotez testi degil. Sonuc H2'yi
# dogrulasa da yanlislasa da OLDUGU GIBI raporlanir; kosullu hukum verilir.
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import levene, binomtest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import append_jsonl, read_jsonl  # noqa: E402

VERI = C.REPO_ROOT / "results_insan"
KORPUSLAR = [("tr", "", "Turkish (Wikipedia)"),
             ("en", "", "English (Wikipedia)"),
             ("tr", "_wikisource", "Turkish (Wikisource)")]


def _detektor():
    """Kosunun kendi tokenizer'i ve KGW yapilandirmasi (env.json rejim kapisi)."""
    from transformers import AutoTokenizer
    from utils.transformers_config import TransformersConfig
    from watermark.auto_watermark import AutoWatermark

    env = json.loads((C.RESULTS / "env.json").read_text())
    model_adi = env["model"]
    tok = AutoTokenizer.from_pretrained(model_adi)
    tcfg = TransformersConfig(model=None, tokenizer=tok, device="cpu")
    tcfg.temperature = C.TEMPERATURE
    tcfg.top_k = -1
    w = AutoWatermark.load("KGW", algorithm_config=C.SCHEME_CONFIGS["KGW"],
                           transformers_config=tcfg)
    return tok, w, model_adi


def olc(T_listesi: list[int], n_sinir: int | None) -> dict:
    tok, w, model_adi = _detektor()
    cikti = VERI / "skor_h2_token.jsonl"
    hazir = {(r["pageid"], r["korpus"], r["T"]) for r in read_jsonl(cikti)}

    ham: dict[str, dict[int, list[float]]] = {}
    token_uzunluk: dict[str, list[int]] = {}

    for dil, ek, etiket in KORPUSLAR:
        kaynak = VERI / f"insan_{dil}{ek}.jsonl"
        if not kaynak.exists():
            print(f"  {etiket}: veri yok, ATLANDI"); continue
        korpus = f"{dil}{ek}"
        rows = read_jsonl(kaynak)
        if n_sinir:
            rows = rows[:n_sinir]
        ham[korpus] = {T: [] for T in T_listesi}
        token_uzunluk[korpus] = []
        print(f"{etiket}: {len(rows)} pencere", flush=True)
        t0 = time.time()
        for i, r in enumerate(rows):
            ids = tok(r["text"], return_tensors="pt",
                      add_special_tokens=False)["input_ids"][0]
            token_uzunluk[korpus].append(int(len(ids)))
            for T in T_listesi:
                if len(ids) < T:
                    continue          # kirpilamayan pencere sessizce DUSMEZ:
                                      # asagida her T icin gecerli n raporlanir
                anahtar = (r["pageid"], korpus, T)
                if anahtar in hazir:
                    continue
                z, _ = w.utils.score_sequence(ids[:T])
                append_jsonl(cikti, {"pageid": r["pageid"], "korpus": korpus,
                                     "T": T, "score": float(z),
                                     "detektor_tokenizer": model_adi})
            if (i + 1) % 200 == 0:
                print(f"  {i+1}/{len(rows)}  "
                      f"({(time.time()-t0)/(i+1):.2f} s/pencere)", flush=True)

    # skorlari dosyadan topla (yeniden kosumda da tam olsun)
    for r in read_jsonl(cikti):
        k, T = r["korpus"], r["T"]
        if k in ham and T in ham[k]:
            ham[k][T].append(r["score"])

    return _rapor(ham, token_uzunluk, T_listesi)


def _ozet(x: list[float]) -> dict:
    a = np.asarray(x, dtype=float)
    k = int((a > 4.0).sum())
    ci = binomtest(k, len(a)).proportion_ci(confidence_level=0.95, method="exact")
    return {"n": int(a.size), "mean": float(a.mean()), "std": float(a.std(ddof=1)),
            "z_max": float(a.max()), "n_z4": k,
            "fpr": k / a.size,
            "fpr_ci": [float(ci.low), float(ci.high)]}


def _rapor(ham, token_uzunluk, T_listesi) -> dict:
    rap: dict = {"T_listesi": T_listesi, "korpus": {}, "karsilastirma": {},
                 "token_uzunluk": {}}

    for k, uz in token_uzunluk.items():
        a = np.asarray(uz, dtype=float)
        rap["token_uzunluk"][k] = {
            "n": int(a.size), "medyan": float(np.median(a)),
            "ort": float(a.mean()), "p10": float(np.percentile(a, 10)),
            "p90": float(np.percentile(a, 90))}

    for k, per_T in ham.items():
        rap["korpus"][k] = {str(T): _ozet(v) for T, v in per_T.items() if v}

    # TR vs EN, HER T'de ayni kesim: yalnizca o T'ye kirpilabilen pencereler
    for T in T_listesi:
        tr = ham.get("tr", {}).get(T, [])
        en = ham.get("en", {}).get(T, [])
        if len(tr) < 30 or len(en) < 30:
            continue
        lev = levene(tr, en, center="median")
        s_tr, s_en = float(np.std(tr, ddof=1)), float(np.std(en, ddof=1))
        rap["karsilastirma"][str(T)] = {
            "n_tr": len(tr), "n_en": len(en),
            "std_tr": s_tr, "std_en": s_en, "oran": s_tr / s_en,
            "levene_p": float(lev.pvalue),
            "yon": "TR>EN" if s_tr > s_en else "EN>=TR",
            # HUKUM KOSULLU: veriden turetilir, elle yazilmaz
            "H2_ayakta": bool(s_tr > s_en and lev.pvalue < 0.05)}
    return rap


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--T", type=int, nargs="+", default=[300, 400, 500])
    ap.add_argument("--n", type=int, default=None,
                    help="korpus basina pencere siniri (deneme icin)")
    a = ap.parse_args()

    rap = olc(sorted(a.T), a.n)
    yol = VERI / "h2_token_rapor.json"
    yol.write_text(json.dumps(rap, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== TOKEN UZUNLUKLARI (kelime-eslemeli pencerelerin gercek T'si) ===")
    for k, v in rap["token_uzunluk"].items():
        print(f"  {k:16s} medyan {v['medyan']:7.1f}  ort {v['ort']:7.1f}  "
              f"[p10 {v['p10']:.0f}, p90 {v['p90']:.0f}]  n={v['n']}")

    print("\n=== T SABITKEN TR vs EN (H2'nin gercek sinavi) ===")
    for T, v in sorted(rap["karsilastirma"].items(), key=lambda x: int(x[0])):
        print(f"  T={T:>4}  std TR {v['std_tr']:.4f}  EN {v['std_en']:.4f}  "
              f"oran {v['oran']:.3f}  Levene p={v['levene_p']:.4f}  "
              f"{v['yon']}  H2 ayakta: {v['H2_ayakta']}"
              f"   (n {v['n_tr']}/{v['n_en']})")

    print("\n=== DOZ-YANIT: std, T ile nasil degisiyor ===")
    for k, per_T in rap["korpus"].items():
        satir = "  ".join(f"T={T}: {d['std']:.3f}"
                          for T, d in sorted(per_T.items(), key=lambda x: int(x[0])))
        print(f"  {k:16s} {satir}")
    print(f"\nyazildi -> {yol}")


if __name__ == "__main__":
    main()
