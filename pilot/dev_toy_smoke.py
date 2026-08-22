# pilot/dev_toy_smoke.py — İNDİRMESİZ uçtan uca doğrulama.
#
# Rastgele ağırlıklı mini bir GPT-2 + sıfırdan kurulan kelime-düzeyi Türkçe
# tokenizer ile KGW/EXP/SynthID'nin üret->dilimle->tespit hattını CPU'da test
# eder. Filigran örnekleme yanlılığı model kalitesinden bağımsız olduğu için
# rastgele modelde bile z ayrımı görülmelidir. Bu betik hem geliştirici
# sandbox'ında hem kullanıcının Mac'inde (HF indirmesi yapmadan, saniyeler
# içinde) boru hattının bütünlüğünü kanıtlar.
#
#   python -m pilot.dev_toy_smoke            # cpu
#   python -m pilot.dev_toy_smoke --device mps
from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch  # noqa: E402

_CORPUS = (
    "şehir hayatı hızla değişiyor insanlar yeni alışkanlıklar ediniyor "
    "ulaşım eğitim sağlık alanlarında dönüşüm sürüyor teknoloji günlük "
    "yaşamın parçası haline geliyor kitap okumak zihni besliyor deniz "
    "kenarında yürüyüş yapmak iyi geliyor çocuklar parkta oyun oynuyor "
    "kahve içmek sabahları güzel bir başlangıç sunuyor müzik ruhu "
    "dinlendiriyor yağmur sonrası toprak kokusu yayılıyor akşam üzeri "
    "gökyüzü turuncuya dönüyor komşular selamlaşıyor pazar yerinde taze "
    "sebzeler satılıyor öğrenciler kütüphanede ders çalışıyor sanat "
    "insanı düşündürüyor doğa yürüyüşleri bedeni canlandırıyor aile "
    "sofrada bir araya geliyor eski fotoğraflar anıları tazeliyor ."
)


def build_toy_tokenizer():
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from tokenizers.trainers import WordLevelTrainer
    from transformers import PreTrainedTokenizerFast

    tk = Tokenizer(WordLevel(unk_token="[UNK]"))
    tk.pre_tokenizer = Whitespace()
    trainer = WordLevelTrainer(special_tokens=["[UNK]", "[PAD]", "[EOS]"])
    tk.train_from_iterator([_CORPUS], trainer)
    tok = PreTrainedTokenizerFast(
        tokenizer_object=tk, unk_token="[UNK]",
        pad_token="[PAD]", eos_token="[EOS]",
    )
    return tok


def build_toy_model(vocab_size: int, device: str):
    from transformers import GPT2Config, GPT2LMHeadModel

    cfg = GPT2Config(vocab_size=vocab_size, n_positions=512,
                     n_embd=64, n_layer=2, n_head=2,
                     bos_token_id=None, eos_token_id=None)
    torch.manual_seed(0)
    return GPT2LMHeadModel(cfg).to(device).eval()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    args = ap.parse_args()
    device = args.device
    if device == "mps" and not torch.backends.mps.is_available():
        print("MPS yok, cpu'ya düşüldü"); device = "cpu"

    from pilot import config as C
    from pilot.generate import (MpsGeneratorError, generate_records,
                                load_scheme, make_tcfg)

    tok = build_toy_tokenizer()
    model = build_toy_model(len(tok), device)
    print(f"oyuncak: vocab={len(tok)}, device={device}, "
          f"torch={torch.__version__}")

    tcfg = make_tcfg(model, tok, device,
                     max_new_tokens=120, min_new_tokens=60)

    # EXP için kısa sequence_length'li geçici config (repo/paket config'ine dokunma)
    tmp_exp = Path(tempfile.mkstemp(suffix=".json")[1])
    tmp_exp.write_text(json.dumps({
        "algorithm_name": "EXP", "prefix_length": 4,
        "hash_key": 15485863, "threshold": 1e-4, "sequence_length": 80,
    }))
    C.SCHEME_CONFIGS = dict(C.SCHEME_CONFIGS, EXP=str(tmp_exp))

    prompts = ["şehir hayatı", "kitap okumak", "deniz kenarında",
               "çocuklar parkta", "müzik ruhu", "pazar yerinde"]

    try:
        kgw = load_scheme("KGW", tcfg)
    except MpsGeneratorError as e:
        print(f"HATA — {e}"); sys.exit(2)

    import pilot.generate as G
    with tempfile.TemporaryDirectory() as td:
        neg = generate_records(kgw, "KGW", False, tok, device,
                               Path(td) / "n.jsonl", prompts, [1])
        pos = generate_records(kgw, "KGW", True, tok, device,
                               Path(td) / "p.jsonl", prompts, [1])
    zn = [kgw.detect_watermark(r["text"])["score"] for r in neg]
    zp = [kgw.detect_watermark(r["text"])["score"] for r in pos]
    print(f"KGW  z(no-wm)={statistics.mean(zn):+.2f}  "
          f"z(wm)={statistics.mean(zp):+.2f}")

    # EXP'nin seed_rng'i prompt'un son prefix_length (=4) tokenına bakar; oyuncak
    # tokenizer kelime düzeyinde olduğu için buradaki prompt EN AZ 4 KELİME olmalı,
    # yoksa IndexError. Gerçek koşuda prompt sohbet şablonuyla zaten çok daha uzun.
    exp = load_scheme("EXP", tcfg)
    t = exp.generate_watermarked_text("şehir hayatı hızla değişiyor insanlar")
    d = exp.detect_watermark(t)
    print(f"EXP  p={d['score']:.3g}  is_wm={d['is_watermarked']}")

    sid = load_scheme("SynthID", tcfg)   # ngram_len=5 -> aynı gerekçeyle uzun prompt
    t = sid.generate_watermarked_text("kitap okumak zihni besliyor deniz")
    d = sid.detect_watermark(t)
    print(f"SynthID  mean={d['score']:.4f}  is_wm={d['is_watermarked']}")

    ok = statistics.mean(zp) - statistics.mean(zn) > 2.0
    print("OYUNCAK DUMAN:", "GEÇTİ ✔" if ok else "ŞÜPHELİ")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
