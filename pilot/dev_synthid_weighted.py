# pilot/dev_synthid_weighted.py — G1: SynthID'yi weighted_mean dedektörüyle
# YENİDEN skorla (üretim yok; dedektör modelsiz).
#
# NEDEN: ana sonuçlar SynthID'nin varsayılan 'mean' dedektörüyle. Hakem sorusu:
# "daha iyi dedektörünü denediniz mi?" weighted_mean, MarkLLM'de eğitimsiz
# ikinci seçenek. POST-HOC/KEŞİFSEL: ön-kayıtlı manşet 'mean' KALIR; bu ayrı
# CSV'ye yazılır, kilitli scores.csv'ye DOKUNULMAZ.
#
# ÖN KAPI (denetim şartı): önce mevcut 'mean' skorları birebir yeniden üretilir
# (|Δ|>1e-6 tek satırda bile varsa DUR) -- boru hattının aynı olduğu kanıtlanır,
# ancak ondan sonra weighted_mean koşulur.
#
#   python -m pilot.dev_synthid_weighted
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402

OUT = C.RESULTS / "scores_synthid_weighted.csv"


def main() -> None:
    import pandas as pd
    from transformers import AutoTokenizer
    from utils.transformers_config import TransformersConfig
    from watermark.auto_watermark import AutoWatermark

    env = json.loads((C.RESULTS / "env.json").read_text())
    tok = AutoTokenizer.from_pretrained(env["model"])
    # CIHAZ SINIFI ZORUNLU OLARAK URETICIYLE AYNI. Olculdu: CPU'da g-degeri
    # anahtari FARKLI RNG dizisinden turuyor -> filigranli metin sansa cokuyor
    # (0,498 vs CUDA 0,529); CUDA'da mean skorlari scores.csv ile BIREBIR
    # (maks |D| = 0). Bu betik bu yuzden yalniz CUDA'da anlamli.
    import torch
    if not torch.cuda.is_available():
        raise SystemExit("⛔ CUDA yok. SynthID anahtari cihaz-sinifi bagimli "
                         "(olculdu); bu betik uretim cihazinda (CUDA) kosulmali.")
    tcfg = TransformersConfig(model=None, tokenizer=tok, device="cuda")
    tcfg.temperature = C.TEMPERATURE
    tcfg.top_k = -1

    mean_det = AutoWatermark.load("SynthID", algorithm_config=C.SCHEME_CONFIGS["SynthID"],
                                  transformers_config=tcfg)
    w_det = AutoWatermark.load("SynthID", algorithm_config=C.SCHEME_CONFIGS["SynthID"],
                               transformers_config=tcfg, detector_type="weighted_mean")

    eski = pd.read_csv(C.RESULTS / "scores.csv")
    eski = eski[eski.scheme == "SynthID"]

    # ---- ÖN KAPI: mean birebir yeniden üretiliyor mu? (örneklem: her koşuldan 8)
    print("ÖN KAPI: mevcut 'mean' skorlarının birebir yeniden üretimi")
    n_test = maks_fark = 0
    for (cond, wm), grup in eski.groupby(["condition", "wm"]):
        for _, row in grup.head(4).iterrows():
            kaynak = ("gen_neg" if (wm == 0 and cond == "clean") else
                      f"gen_pos_SynthID" if cond == "clean" else
                      f"att_{'neg' if wm == 0 else 'pos_SynthID'}_{cond}")
            recs = {(r["prompt_id"], r["seed"]): r["text"]
                    for r in read_jsonl(C.RESULTS / f"{kaynak}.jsonl")}
            t = recs.get((row["prompt_id"], row["seed"]))
            if t is None:
                continue
            yeni = float(mean_det.detect_watermark(t)["score"])
            fark = abs(yeni - row["score"])
            maks_fark = max(maks_fark, fark)
            n_test += 1
    print(f"  {n_test} satır test edildi, maks |Δ| = {maks_fark:.2e}")
    if maks_fark > 1e-6:
        raise SystemExit("⛔ mean skorları birebir üretilemedi -- boru hattı "
                         "farklı, weighted_mean koşulmayacak.")
    print("  GEÇTİ -- boru hattı aynı.\n")

    # ---- weighted_mean tam skorlama
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scheme", "condition", "wm",
                                          "prompt_id", "seed", "score_weighted"])
        w.writeheader()
        for cond in ["clean"] + C.ATTACKS:
            for wm, kaynak in ((0, "neg"), (1, "pos_SynthID")):
                dosya = (f"gen_{kaynak}" if cond == "clean"
                         else f"att_{kaynak}_{cond}")
                yol = C.RESULTS / f"{dosya}.jsonl"
                if not yol.exists():
                    continue
                for r in read_jsonl(yol):
                    s = float(w_det.detect_watermark(r["text"])["score"])
                    w.writerow(dict(scheme="SynthID", condition=cond, wm=wm,
                                    prompt_id=r["prompt_id"], seed=r["seed"],
                                    score_weighted=s))
            print(f"  {cond} tamam", flush=True)

    # ---- karşılaştırmalı AUROC (mean vs weighted_mean)
    import numpy as np
    from pilot.metrics import auroc
    yeni = pd.read_csv(OUT)
    print(f"\n{'koşul':14s} {'mean AUROC':>11s} {'weighted AUROC':>15s} {'Δ':>7s}")
    rapor = {}
    for cond in ["clean"] + C.ATTACKS:
        e_neg = eski[(eski.condition == "clean") & (eski.wm == 0)]["stat"].to_numpy()
        e_pos = eski[(eski.condition == cond) & (eski.wm == 1)]["stat"].to_numpy()
        y_neg = yeni[(yeni.condition == "clean") & (yeni.wm == 0)]["score_weighted"].to_numpy()
        y_pos = yeni[(yeni.condition == cond) & (yeni.wm == 1)]["score_weighted"].to_numpy()
        if not len(e_pos) or not len(y_pos):
            continue
        a1, a2 = auroc(e_pos, e_neg), auroc(y_pos, y_neg)
        rapor[cond] = {"mean": a1, "weighted_mean": a2}
        print(f"{cond:14s} {a1:11.3f} {a2:15.3f} {a2-a1:+7.3f}")
    (C.RESULTS / "synthid_weighted_karsilastirma.json").write_text(
        json.dumps(rapor, indent=2))
    print(f"\nyazıldı: {OUT} ve synthid_weighted_karsilastirma.json")


if __name__ == "__main__":
    main()
