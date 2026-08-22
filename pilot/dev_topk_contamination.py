# pilot/dev_topk_contamination.py — S3 düzeltmesi yabancı-yazı kirlenmesine
# sebep oldu mu? Kontrollü karşılaştırma.
#
# BULGU: üretilen 384 metnin %36'sı CJK/Hangul/Kiril/İbranice/Arapça karakter
# içeriyor (gen_neg %40, KGW %43, SynthID %46, EXP %17).
#
# ŞÜPHELİ: S3 düzeltmem Qwen'in generation_config'indeki top_k=20'yi kapatıp
# top_k=0 yaptı (gerekçe: şemalar arası örneklemeyi eşitlemek). top_k=0,
# 151.643 kelimelik sözlüğün TAMAMINI örneklemeye açar ve o sözlüğün kuyruğu
# CJK/Hangul token'larıyla doludur. top_p=0.95 bu kuyruğu kesmeye yetmemiş
# olabilir.
#
# Bu betik aynı prompt+tohumlarla iki ayarı karşılaştırır. Fark büyükse sebep
# benim düzeltmemdir ve Faz 1/2 yeniden üretilmelidir; fark yoksa sebep modelin
# kendisidir (3B Türkçe için yetersiz) ve 7B'ye çıkmak gerekir.
#
#   python -m pilot.dev_topk_contamination
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch  # noqa: E402

from pilot.generate import (get_device, load_model_and_tokenizer, load_prompts,  # noqa: E402
                            render_prompt, seed_everything, slice_completion)

FOREIGN = re.compile(r"[一-鿿぀-ヿ가-힯ᄀ-ᇿ"
                     r"Ѐ-ӿ֐-׿؀-ۿ]")

CONFIGS = {
    "A: top_k=0  rep=1.00  (S3 düzeltmem)": dict(top_k=0, repetition_penalty=1.0),
    "B: top_k=20 rep=1.05  (Qwen varsayılanı)": dict(top_k=20, repetition_penalty=1.05),
    "C: top_k=50 rep=1.00  (ara nokta)": dict(top_k=50, repetition_penalty=1.0),
}


def main() -> None:
    model_name = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-3B-Instruct"
    device = get_device()   # sabit "mps" degildi -> CUDA/CPU makinede de kosar
    print(f"Model: {model_name} ({device})")
    model, tok = load_model_and_tokenizer(model_name, device)
    prompts = load_prompts(8)
    seeds = (11, 12, 13)

    print(f"\n{'ayar':42s} {'n':>3s} {'kirli metin':>14s} {'yabancı kar.':>13s}")
    print("-" * 76)
    for label, extra in CONFIGS.items():
        hit = chars = n = 0
        for pi, p in enumerate(prompts):
            rendered = render_prompt(tok, p)
            enc = tok(rendered, return_tensors="pt").to(device)
            for seed in seeds:
                seed_everything(seed * 1000 + pi, device)   # Faz 1 ile aynı tohum
                with torch.no_grad():
                    out = model.generate(
                        **enc, max_new_tokens=320, min_new_tokens=200,
                        do_sample=True, temperature=0.8, top_p=0.95,
                        pad_token_id=tok.pad_token_id, **extra)
                txt, _ = slice_completion(
                    tok, rendered, tok.batch_decode(out, skip_special_tokens=True)[0])
                found = FOREIGN.findall(txt)
                n += 1
                hit += bool(found)
                chars += len(found)
        print(f"{label:42s} {n:3d} {hit:7d} (%{100 * hit / n:3.0f}) {chars:11d}",
              flush=True)

    print("\nOKUMA: A ile B arasında büyük fark varsa kirlenmenin sebebi S3'tür "
          "(top_k=0) ve Faz 1/2 yeniden üretilmelidir. Fark yoksa sebep modeldir "
          "(3B) ve 7B'ye çıkmak gerekir.")


if __name__ == "__main__":
    main()
