# pilot/dev_insan_fpr.py — S1: filigransız İNSAN metninde yanlış pozitif oranı.
#
# ÖN-KAYIT: hpc/README.md "ÖN-KAYIT — S1" (commit 8f8df72, veri toplanmadan önce).
# H1: insan Türkçesinde KGW null std > 1 (şişme model metnine özgü değil)
# H2: eşlenmiş İngilizcede şişme Türkçeden küçük
# H3: EXP ve SynthID null'larında anlamlı şişme yok
#
# NEDEN MODELSİZ: üç dedektör de yalnız tokenizer + karma/RNG kullanıyor
# (exp.py:161-180, kgw.py:142, synthid.py:371; model=None ile ölçülerek
# doğrulandı). Bu yüzden S1 tamamen CPU işidir, GPU/VPN gerektirmez.
#
# VERİ: Vikipedi rastgele maddeleri (action API, explaintext). Her maddenin
# pageid/revid/timestamp'i kayda girer -- örneklem yeniden çekilebilir.
# Pencereleme: korpusun uzunluk dağılımına eşlenir (medyan ~365 kelime TR),
# cümle ortasından kesmez.
#
#   python -m pilot.dev_insan_fpr topla --dil tr --hedef 1000
#   python -m pilot.dev_insan_fpr topla --dil en --hedef 1000
#   python -m pilot.dev_insan_fpr skorla
#   python -m pilot.dev_insan_fpr rapor
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import append_jsonl, read_jsonl  # noqa: E402

VERI = C.REPO_ROOT / "results_insan"
API = {"tr": "https://tr.wikipedia.org/w/api.php",
       "en": "https://en.wikipedia.org/w/api.php"}
# Korpusla eşlenen pencere hedefi (kelime): gen_* medyanı ~365 (TR).
# EN'de kelimeler daha uzun bilgi taşır; eşleme TÜR ve UZUNLUK (kelime) üzerinden.
PENCERE_KELIME = 365
MIN_MADDE_KELIME = 250          # bundan kısa maddeler atlanır
TERMINAL = (".", "!", "?", "…")


def _pencere(text: str, hedef: int, rng: random.Random) -> str | None:
    """Cümle sınırlarına saygılı, hedef uzunluğa yakın bitişik pencere."""
    # kaba cümle bölme; kısaltma hataları pencere seçimini bozmaz
    cumleler = [c.strip() for c in re.split(r"(?<=[.!?…])\s+", text) if c.strip()]
    if not cumleler:
        return None
    # rastgele başlangıç, hedefe ulaşana dek cümle ekle
    bas = rng.randrange(len(cumleler))
    parca, n = [], 0
    for c in cumleler[bas:]:
        parca.append(c)
        n += len(c.split())
        if n >= hedef:
            break
    if n < MIN_MADDE_KELIME:
        return None
    metin = " ".join(parca)
    return metin if metin.rstrip().endswith(TERMINAL) else None


DUMP_SURUM = "20231101"     # provenans: wikimedia/wikipedia HF dump'i


def topla(dil: str, hedef: int) -> None:
    """Vikipedi DUMP'indan akisla toplar (tam indirme yok).

    Ilk surum action API kullaniyordu; olculdu: prop=extracts coklu sayfada
    yalniz ILK sayfanin tam metnini donduruyor (bilinen API kisiti) -> ~1
    belge/2dk. Dump akisi ise saniyede onlarca madde tarar ve provenans daha
    guclu: sabit dump surumu, herkes ayni kaynagi yeniden cekebilir.
    KAYDIRMA YOK: akis sirasi dump sirasidir; ornekleme "ilk N uygun madde"
    olarak ON-KAYITLIDIR (rastgele degil ama deterministik ve tekrarlanabilir;
    stub oraninin yuksekligi nedeniyle uygunluk filtresi zaten seyreltiyor).
    """
    from datasets import load_dataset

    VERI.mkdir(exist_ok=True)
    yol = VERI / f"insan_{dil}.jsonl"
    var = read_jsonl(yol)
    gorulen = {r["pageid"] for r in var}
    rng = random.Random(42)
    ds = load_dataset("wikimedia/wikipedia", f"{DUMP_SURUM}.{dil}",
                      split="train", streaming=True)
    print(f"{dil}: {len(var)} hazır, hedef {hedef} (dump {DUMP_SURUM})")
    t0, taranan = time.time(), 0
    for madde in ds:
        if len(gorulen) >= hedef:
            break
        taranan += 1
        pid = int(madde["id"])
        if pid in gorulen:
            continue
        metin = madde.get("text") or ""
        if len(metin.split()) < MIN_MADDE_KELIME:
            continue
        pencere = _pencere(metin, PENCERE_KELIME, rng)
        if pencere is None:
            continue
        append_jsonl(yol, {
            "pageid": pid, "title": madde.get("title"),
            "dump": f"{DUMP_SURUM}.{dil}",
            "dil": dil, "n_kelime": len(pencere.split()),
            "text": pencere,
        })
        gorulen.add(pid)
        if len(gorulen) % 100 == 0:
            print(f"  {len(gorulen)}/{hedef}  (taranan {taranan}, "
                  f"{(time.time()-t0):.0f} sn)", flush=True)
    print(f"TAMAM: {len(gorulen)} belge ({taranan} tarandı) -> {yol}")


def skorla() -> None:
    from transformers import AutoTokenizer
    from utils.transformers_config import TransformersConfig
    from watermark.auto_watermark import AutoWatermark

    env = json.loads((C.RESULTS / "env.json").read_text())
    model_adi = env["model"]
    tok = AutoTokenizer.from_pretrained(model_adi)
    tcfg = TransformersConfig(model=None, tokenizer=tok, device="cpu")
    tcfg.temperature = C.TEMPERATURE
    tcfg.top_k = -1
    semalar = {}
    for ad in C.SCHEMES:
        extra = ({"sequence_length": env.get("exp_sequence_length", 950)}
                 if ad == "EXP" else {})
        semalar[ad] = AutoWatermark.load(
            ad, algorithm_config=C.SCHEME_CONFIGS[ad],
            transformers_config=tcfg, **extra)

    for dil in ("tr", "en"):
        kaynak = VERI / f"insan_{dil}.jsonl"
        if not kaynak.exists():
            print(f"  {dil}: veri yok, atlandı"); continue
        cikti = VERI / f"skor_{dil}.jsonl"
        hazir = {(r["pageid"], r["scheme"]) for r in read_jsonl(cikti)}
        rows = read_jsonl(kaynak)
        print(f"{dil}: {len(rows)} belge x {len(semalar)} şema "
              f"({len(hazir)} hazır)")
        t0 = time.time()
        for i, r in enumerate(rows):
            for ad, w in semalar.items():
                if (r["pageid"], ad) in hazir:
                    continue
                res = w.detect_watermark(r["text"])
                append_jsonl(cikti, {
                    "pageid": r["pageid"], "dil": dil, "scheme": ad,
                    "score": float(res["score"]),
                    "is_watermarked_config_esigi": bool(res["is_watermarked"]),
                    "n_kelime": r["n_kelime"],
                    "detektor_tokenizer": model_adi,
                })
            if (i + 1) % 200 == 0:
                print(f"  {i+1}/{len(rows)}  ({(time.time()-t0)/(i+1):.2f} s/belge)",
                      flush=True)
        print(f"  bitti -> {cikti}")


def rapor() -> None:
    import numpy as np

    cikti = {"olcum_tarihi": "2026-08-23", "on_kayit": "hpc/README.md S1 (8f8df72)"}
    # model-negatiflerinden kalibre eşik (karşılaştırma için)
    import pandas as pd
    sc = pd.read_csv(C.RESULTS / "scores.csv")
    for dil in ("tr", "en"):
        yol = VERI / f"skor_{dil}.jsonl"
        if not yol.exists():
            continue
        d = pd.DataFrame(read_jsonl(yol))
        cikti[dil] = {}
        for ad in C.SCHEMES:
            x = d[d.scheme == ad]["score"].to_numpy()
            if not len(x):
                continue
            neg = sc[(sc.scheme == ad) & (sc.condition == "clean")
                     & (sc.wm == 0)]["stat"].to_numpy()
            # yön düzeltmesi: stat uzayına çevir
            yon = C.SCORE_DIRECTION[ad]
            xs = x * yon if ad != "EXP" else -np.log10(np.clip(x, 1e-300, 1))
            kalibre = float(np.quantile(neg, 1 - C.TPR_AT_FPR))
            blok = {
                "n": int(len(x)),
                "null_ort": float(np.mean(xs)), "null_std": float(np.std(xs, ddof=1)),
                "fpr_config_esigi": float(d[d.scheme == ad]
                                          ["is_watermarked_config_esigi"].mean()),
                "fpr_model_kalibre_esik": float((xs > kalibre).mean()),
                "esik_model_kalibre": kalibre,
            }
            if ad == "KGW":
                from scipy.stats import norm
                blok["z4_nominal_fpr"] = float(norm.sf(4.0))
                blok["z4_gozlenen_dagilimda"] = float(
                    norm.sf(4.0, loc=blok["null_ort"], scale=blok["null_std"]))
            cikti[dil][ad] = blok
    yol = VERI / "insan_fpr_rapor.json"
    yol.write_text(json.dumps(cikti, ensure_ascii=False, indent=2))
    print(json.dumps(cikti, ensure_ascii=False, indent=2))
    print(f"\nyazıldı: {yol}")


def main() -> None:
    ap = argparse.ArgumentParser(description="S1: insan metninde FPR")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("topla"); t.add_argument("--dil", choices=("tr", "en"), required=True)
    t.add_argument("--hedef", type=int, default=1000)
    sub.add_parser("skorla"); sub.add_parser("rapor")
    a = ap.parse_args()
    if a.cmd == "topla":
        topla(a.dil, a.hedef)
    elif a.cmd == "skorla":
        skorla()
    else:
        rapor()


if __name__ == "__main__":
    main()
