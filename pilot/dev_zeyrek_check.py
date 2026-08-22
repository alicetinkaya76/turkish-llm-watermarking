# pilot/dev_zeyrek_check.py — zeyrek çözümlemelerinin metin sırasından
# BAĞIMSIZ ve DOĞRU olduğunu kanıtlayan denetim.
#
# Neden var: zeyrek.MorphAnalyzer durum taşıyor. Yeterince kelime analiz
# edildikten sonra, daha önce doğru çözümlediği bir kelime için tek bir Unk
# çözümlemesi dönmeye başlıyor (ölçüldü: "etkileyecektir" 750 analizde sağlam,
# 1000'de bozuk, 2525'te bozuk; yeniden kurulum onarıyor). Bu, morph_v0'ı,
# morph_v1'i ve metrics._lemma_set'i (K10 lemma-Jaccard kanıtı) birden metin
# sırasına duyarlı kılar -> K11 ihlali. attacks.py'deki savunma: tek analizör +
# benzersiz kelime başına tek analiz (_PARSE_CACHE) + eşiğin altında yenileme.
#
# Bu betik o savunmayı iki kapıyla sınar:
#   A) DOĞRULUK  — boru hattının kararları, "kelime başına TAZE analizör"
#      referansıyla birebir aynı mı? (referans yavaştır: kelime başına ~4,4 s)
#   B) SIRA BAĞIMSIZLIĞI — metinler düz ve ters sırada işlendiğinde üretilen
#      saldırı metinleri birebir aynı mı?
#
#   python -m pilot.dev_zeyrek_check              # B + A (40 kelimelik örneklem)
#   python -m pilot.dev_zeyrek_check --full       # A'yı tüm adaylarla (yavaş)
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logging.disable(logging.CRITICAL)
import zeyrek  # noqa: E402

from pilot import config as C  # noqa: E402
from pilot import attacks as A  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402


def _corpus_texts() -> list[str]:
    rows = read_jsonl(C.RESULTS / "gen_neg.jsonl")
    if not rows:
        print("gen_neg.jsonl yok -> önce Faz 1 koşulmalı.", file=sys.stderr)
        sys.exit(2)
    return [r["text"] for r in rows]


def _copula_candidates(texts: list[str]) -> list[str]:
    out = set()
    for t in texts:
        for w in t.split(" "):
            core = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", w).lower()
            if core.endswith(A._COP_SUFFIXES):
                out.add(core)
    return sorted(out)


def gate_b_order_independence(texts: list[str]) -> bool:
    """Düz ve ters sırada işlenen metinler birebir aynı mı?"""
    def run(order):
        A._PARSE_CACHE.clear()
        A._ZA = zeyrek.MorphAnalyzer()
        A._ZA_ANALYSES = 0
        A.prewarm_corpus(texts)          # boru hattının sözleşmesi (detect.py)
        res = {}
        for i in order:
            res[i] = (A.morph_attack(texts[i])[0], A.morph_attack_v1(texts[i])[0])
        return res

    fwd = run(range(len(texts)))
    rev = run(reversed(range(len(texts))))
    same = all(fwd[i] == rev[i] for i in fwd)
    h = hashlib.md5(
        "".join(fwd[i][0] + fwd[i][1] for i in sorted(fwd)).encode()
    ).hexdigest()[:12]
    print(f"B) sıra bağımsızlığı: {'GEÇTİ' if same else 'KALDI'}  (metin md5={h})")
    return same


def gate_a_correctness(cands: list[str], sample: int | None) -> bool:
    """Boru hattı kararları, kelime başına taze analizör referansıyla aynı mı?"""
    if sample is not None and sample < len(cands):
        cands = sorted(random.Random(42).sample(cands, sample))
    print(f"A) doğruluk referansı kuruluyor: {len(cands)} kelime "
          f"x taze analizör (~{len(cands) * 4.5 / 60:.1f} dk)…", flush=True)

    ref = {}
    t0 = time.time()
    for i, w in enumerate(cands):
        A._PARSE_CACHE.clear()
        A._ZA = zeyrek.MorphAnalyzer()
        A._ZA_ANALYSES = 0
        ref[w] = A.r3_drop_copula(w)
        if (i + 1) % 20 == 0:
            print(f"   {i + 1}/{len(cands)}  ({time.time() - t0:.0f}s)", flush=True)

    # boru hattı: tek analizör + bellek, tüm korpus ısıtılmış hâlde
    A._PARSE_CACHE.clear()
    A._ZA = zeyrek.MorphAnalyzer()
    A._ZA_ANALYSES = 0
    for t in _corpus_texts():
        A.morph_attack_v1(t)
    bad = [w for w in cands if A.r3_drop_copula(w) != ref[w]]
    n_ok = sum(1 for v in ref.values() if v)
    print(f"A) referans: {n_ok}/{len(ref)} dönüştürülebilir | "
          f"boru hattı sapması: {len(bad)} {bad[:5]}")
    return not bad


def main() -> None:
    ap = argparse.ArgumentParser(description="zeyrek kararlılık denetimi")
    ap.add_argument("--full", action="store_true",
                    help="A kapısını TÜM adaylarla koş (yavaş)")
    ap.add_argument("--sample", type=int, default=40)
    args = ap.parse_args()

    texts = _corpus_texts()
    cands = _copula_candidates(texts)
    print(f"korpus: {len(texts)} metin, {len(cands)} benzersiz kopula adayı\n")

    ok_b = gate_b_order_independence(texts)
    ok_a = gate_a_correctness(cands, None if args.full else args.sample)

    print("\nZEYREK DENETİMİ:", "GEÇTİ ✔" if (ok_a and ok_b) else "KALDI ✘")
    sys.exit(0 if (ok_a and ok_b) else 1)


if __name__ == "__main__":
    main()
