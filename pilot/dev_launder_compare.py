# pilot/dev_launder_compare.py — "sıfır-beceri aklama" vs GERÇEK aklama.
#
# Faz 2'nin `launder` saldırısı metni üreten modelin (Qwen2.5-3B) kendisine
# yeniden yazdırıyordu. `launder_api` ise güçlü harici bir modeli (Opus 5)
# kullanıyor — Panel-3 tehdit modelinin gerçek hâli. Tek değişken aklayıcı
# model; istem birebir aynı.
#
# Bu betik ikisini yan yana koyar. DİKKAT (denetim §8): nokta TPR sıralaması
# tehdit sıralaması DEĞİLDİR -- eşlenmiş McNemar testinde launder_api ile rtt
# arasındaki fark hiçbir şemada anlamlı çıkmadı. Bu betiğin 'SIRALAMA' çıktısı
# betimleyicidir; çıkarımsal iddia için metrics.audit_corrections (D3) kullan.
#
#   python -m pilot.dev_launder_compare
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd  # noqa: E402

from pilot import config as C  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402
from pilot.metrics import auroc, auroc_ci, tpr_at_fpr  # noqa: E402

FOREIGN = re.compile(r"[一-鿿぀-ヿ가-힯ᄀ-ᇿЀ-ӿ֐-׿؀-ۿ]")
FOCUS = ["clean", "dia100", "rtt", "para", "launder", "launder_api"]


def main() -> None:
    scores = pd.read_csv(C.RESULTS / "scores.csv")
    if "launder_api" not in set(scores.condition):
        print("launder_api scores.csv'de yok -> önce skorlama koşmalı.",
              file=sys.stderr)
        sys.exit(2)

    print("=== TESPİT: TPR@%1FPR (parantezde AUROC) ===")
    print(f"{'koşul':14s} " + "".join(f"{s:>20s}" for s in C.SCHEMES))
    rows = []
    for cond in FOCUS:
        cells = []
        for s in C.SCHEMES:
            d = scores[scores.scheme == s]
            neg = d[(d.condition == "clean") & (d.wm == 0)]["stat"].to_numpy()
            pos = d[(d.condition == cond) & (d.wm == 1)]["stat"].to_numpy()
            if len(pos) == 0:
                cells.append("—")
                continue
            a, t = auroc(pos, neg), tpr_at_fpr(pos, neg)
            lo, hi = auroc_ci(pos, neg)
            cells.append(f"{t:.3f} ({a:.3f})")
            rows.append(dict(kosul=cond, sema=s, tpr=t, auroc=a,
                             ci_lo=lo, ci_hi=hi, n_pos=len(pos)))
        print(f"{cond:14s} " + "".join(f"{c:>20s}" for c in cells))

    df = pd.DataFrame(rows)
    print("\n=== ΔTPR (temiz - koşul): saldırının şiddeti ===")
    piv = df.pivot(index="kosul", columns="sema", values="tpr")
    print((piv.loc["clean"] - piv).drop("clean").reindex(
        [c for c in FOCUS if c != "clean"]).round(3).to_string())

    print("\n=== SIRALAMA: en yıkıcı saldırı hangisi? (KGW üzerinden) ===")
    kg = df[df.sema == "KGW"].set_index("kosul")["tpr"].drop("clean").sort_values()
    for i, (cond, t) in enumerate(kg.items(), 1):
        print(f"  {i}. {cond:14s} TPR {t:.3f}")

    # aklama korpusu temizliyor mu? (tehdit modeli açısından: bedava iyileşme)
    print("\n=== YAN ETKİ: aklama korpusu temizliyor mu? ===")
    for src in ["neg"] + [f"pos_{s}" for s in C.SCHEMES]:
        base = read_jsonl(C.RESULTS / (
            "gen_neg.jsonl" if src == "neg" else f"gen_{src}.jsonl"))
        out = []
        for att in ("launder", "launder_api"):
            rows_a = read_jsonl(C.RESULTS / f"att_{src}_{att}.jsonl")
            if rows_a:
                h = sum(bool(FOREIGN.search(r["text"])) for r in rows_a)
                out.append(f"{att} %{100 * h / len(rows_a):.0f}")
        b = sum(bool(FOREIGN.search(r["text"])) for r in base)
        print(f"  {src:14s} orijinal %{100 * b / len(base):3.0f}  ->  "
              + "  ".join(out))

    df.round(4).to_csv(C.RESULTS / "launder_comparison.csv", index=False)
    print(f"\n-> {C.RESULTS / 'launder_comparison.csv'}")


if __name__ == "__main__":
    main()
