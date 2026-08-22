# pilot/fertility.py — tokenizer bereketi: Türkçe'de kelime başına token.
# Motivasyon (HANDOFF §1): tam-kelime token azlığı <-> filigran kırılganlığı
# bağını mekanistik olarak raporlamak.
from __future__ import annotations

import json

from pilot import config as C
from pilot.jsonl import read_jsonl


def measure(tok, label: str) -> float:
    texts = [r["text"] for r in read_jsonl(C.RESULTS / "gen_neg.jsonl")]
    if not texts:  # negatifler henüz yoksa gömülü örnek paragraf
        texts = [
            "Şehirlerde yaşam hızla değişiyor; insanlar hem işlerini hem de "
            "alışkanlıklarını yeni koşullara göre yeniden düzenlemeye çalışıyor. "
            "Ulaşımdan eğitime kadar pek çok alanda dönüşümün izleri görülüyor."
        ]
    words = toks = 0
    for t in texts:
        ws = t.split()
        words += len(ws)
        toks += len(tok(t, add_special_tokens=False).input_ids)
    fert = toks / max(1, words)

    path = C.RESULTS / "fertility.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    data[label] = fert
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"  bereket[{label}] = {fert:.3f} token/kelime "
          f"({words} kelime, {toks} token)")
    return fert
