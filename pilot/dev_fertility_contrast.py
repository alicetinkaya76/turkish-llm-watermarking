# pilot/dev_fertility_contrast.py — tokenizer bereketi kontrastı (Faz 3, disksiz).
#
# HANDOFF §1'in mekanistik savı: Türkçe'nin eklemeli morfolojisi tokenizer'da
# parçalanmaya yol açıyor ve bu, filigran kırılganlığının merkezinde. Bu betik
# o savı sayıya çeviriyor: AYNI Türkçe korpus üzerinde farklı tokenizer'ların
# kelime başına token oranı (bereket) ve İngilizce'ye göre cezası.
#
# ÖNEMLİ: yalnızca TOKENIZER dosyaları iner (birkaç MB), model ağırlıkları DEĞİL.
# Türkçe-uyarlı 8B modelin ağırlıkları ~16 GB'dır; bereket için gerekmez.
#
#   python -m pilot.dev_fertility_contrast
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402

# (etiket, HF adı) — hepsi tokenizer-only indirir
# ÖLÇÜLMÜŞ UYARI: ytu-ce-cosmos/Turkish-Llama-8b-v0.1, Llama-3'ün tokenizer'ını
# DEĞİŞTİRMEDEN kullanıyor — iki sözlük yalnız 3 ÖZEL token'da ayrışıyor
# (<|eom_id|>, <|python_tag|>, <|finetune_right_pad_id|> vs yedek yer tutucular),
# gerçek alt-kelime parçalarının %100'ü ortak. Dolayısıyla "TR-uyarlı model ile
# tokenizer kontrastı" bu modelle tanım gereği SIFIR fark verir; anlamlı kontrast
# sözlüğü Türkçe için kurulmuş modellere karşıdır (BERTurk, turkish-gpt2).
TOKENIZERS = [
    ("Qwen2.5 (pilot modeli)", "Qwen/Qwen2.5-3B-Instruct"),
    ("Llama-3.1-8B", "meta-llama/Llama-3.1-8B"),
    ("Turkish-Llama-8b (=Llama-3 tok.)", "ytu-ce-cosmos/Turkish-Llama-8b-v0.1"),
    ("mT5 (çok dilli)", "google/mt5-base"),
    ("XLM-R (çok dilli)", "FacebookAI/xlm-roberta-base"),
    ("BERTurk (TR-özel, 32k)", "dbmdz/bert-base-turkish-cased"),
    ("turkish-gpt2 (TR-özel)", "ytu-ce-cosmos/turkish-gpt2-large"),
]

# İngilizce karşılaştırma metni: aynı içerikli, karşılaştırılabilir uzunlukta.
EN_TEXT = (
    "Life in cities is changing rapidly; people are trying to reorganise both "
    "their work and their habits according to new conditions. Traces of this "
    "transformation can be seen in many areas, from transport to education. "
    "The spread of electric vehicles will reduce noise pollution in city "
    "centres and change the way streets are used by pedestrians."
)


def fertility(tok, texts: list[str]) -> tuple[float, int, int]:
    words = toks = 0
    for t in texts:
        words += len(t.split())
        toks += len(tok(t, add_special_tokens=False).input_ids)
    return toks / max(1, words), words, toks


def main() -> None:
    rows = read_jsonl(C.RESULTS / "gen_neg.jsonl")
    if not rows:
        print("gen_neg.jsonl yok -> önce Faz 1 koşulmalı.", file=sys.stderr)
        sys.exit(2)
    tr_texts = [r["text"] for r in rows]
    print(f"Türkçe korpus: {len(tr_texts)} metin, "
          f"{sum(len(t.split()) for t in tr_texts)} kelime\n")

    from transformers import AutoTokenizer

    out = {}
    print(f"{'tokenizer':32s} {'sözlük':>8s} {'TR bereket':>11s} "
          f"{'EN bereket':>11s} {'TR/EN cezası':>13s}")
    print("-" * 80)
    for label, name in TOKENIZERS:
        try:
            tok = AutoTokenizer.from_pretrained(name)
        except Exception as e:
            msg = str(e).split("\n")[0][:44]
            print(f"{label:32s} {'—':>8s}  ERİŞİLEMEDİ: {msg}")
            out[label] = {"error": msg, "hf_name": name}
            continue
        f_tr, w_tr, t_tr = fertility(tok, tr_texts)
        f_en, _, _ = fertility(tok, [EN_TEXT])
        pen = f_tr / f_en
        vocab = getattr(tok, "vocab_size", 0)
        print(f"{label:32s} {vocab:8d} {f_tr:11.3f} {f_en:11.3f} {pen:12.2f}x")
        out[label] = dict(hf_name=name, vocab_size=int(vocab),
                          tr_fertility=f_tr, en_fertility=f_en,
                          tr_en_penalty=pen, tr_words=w_tr, tr_tokens=t_tr)

    path = C.RESULTS / "fertility_contrast.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n-> {path}")
    print("\nOKUMA: TR bereket = Türkçe'de kelime başına token. TR/EN cezası, "
          "aynı tokenizer'ın Türkçe'yi İngilizce'ye kıyasla kaç kat daha çok "
          "parçaladığı. Yüksek bereket = token başına daha az anlam = filigran "
          "istatistiğinin aynı METİN uzunluğunda daha çok token'a yayılması.")


if __name__ == "__main__":
    main()
