# pilot/dev_mps_determinism.py — K11'in "MPS'te tam determinizm zayıf"
# sınırlamasını İDDİA olmaktan çıkarıp ÖLÇÜLMÜŞ bir sayıya çevirir.
#
# Yöntem: Faz 1'de saklanmış (prompt_id, seed) çiftlerinin bir alt kümesini
# AYNI tohumlarla yeniden üretir ve saklanan metinle karşılaştırır. Bu, aynı
# süreç içinde tekrar değil, GERÇEK bir yeniden koşudur (ayrı süreç, farklı
# gün), yani tekrarlanabilirlik iddiasının doğru sınavıdır.
#
# Raporlanan: birebir aynı çıkan metin oranı, ilk ayrışma token'ının konumu,
# ve saklanan/yeni metinlerin z-skorları arasındaki fark. Metin birebir
# tutmasa bile |Δz| küçükse SONUÇLAR tekrarlanabilir demektir; asıl önemlisi
# budur.
#
#   python -m pilot.dev_mps_determinism --model Qwen/Qwen2.5-3B-Instruct -n 8
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="MPS determinizm ölçümü")
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("-n", type=int, default=8, help="yeniden üretilecek örnek")
    ap.add_argument("--scheme", default="KGW", choices=C.SCHEMES)
    args = ap.parse_args()

    from pilot.generate import (get_device, load_model_and_tokenizer, load_scheme,
                                make_tcfg, render_prompt, reset_scheme_state,
                                seed_everything, slice_completion, load_prompts)

    device = get_device(args.device)
    model_name = args.model or C.pick_model()[0]

    stored = read_jsonl(C.RESULTS / f"gen_pos_{args.scheme}.jsonl")
    if not stored:
        print(f"gen_pos_{args.scheme}.jsonl yok -> önce Faz 1 koşulmalı.",
              file=sys.stderr)
        sys.exit(2)
    stored = stored[: args.n]
    prompts = load_prompts(C.N_PROMPTS)

    print(f"Model: {model_name} ({device}) | şema: {args.scheme} | "
          f"{len(stored)} örnek yeniden üretiliyor")
    model, tok = load_model_and_tokenizer(model_name, device)
    tcfg = make_tcfg(model, tok, device)
    scheme = load_scheme(args.scheme, tcfg)

    exact = 0
    dzs, first_diff = [], []
    for r in stored:
        pi, seed = r["prompt_id"], r["seed"]
        rendered = render_prompt(tok, prompts[pi])
        seed_everything(seed * 1000 + pi, device)      # Faz 1 ile AYNI tohum
        reset_scheme_state(scheme)
        full = scheme.generate_watermarked_text(rendered)
        new, _ = slice_completion(tok, rendered, full)

        same = new == r["text"]
        exact += same
        z_old = float(scheme.detect_watermark(r["text"])["score"])
        z_new = float(scheme.detect_watermark(new)["score"])
        dzs.append(abs(z_new - z_old))

        a = tok(r["text"], add_special_tokens=False).input_ids
        b = tok(new, add_special_tokens=False).input_ids
        pos = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                   min(len(a), len(b)))
        first_diff.append(len(a) if same else pos)
        print(f"  p{pi:02d}/s{seed}: {'AYNI' if same else 'FARKLI'}  "
              f"z {z_old:6.2f} -> {z_new:6.2f} (|Δ|={abs(z_new-z_old):.2f})  "
              f"ilk ayrışma token #{pos}", flush=True)

    n = len(stored)
    print(f"\nMPS DETERMİNİZMİ ({args.scheme}, n={n}):")
    print(f"  birebir aynı metin : {exact}/{n} (%{100*exact/n:.0f})")
    print(f"  ilk ayrışma (ort.) : token #{statistics.mean(first_diff):.0f}")
    print(f"  |Δz| ort/maks      : {statistics.mean(dzs):.3f} / {max(dzs):.3f}")
    print("  YORUM: metin birebir tutmasa da |Δz| küçükse sonuç düzeyinde "
          "tekrarlanabilirlik korunuyor demektir.")


if __name__ == "__main__":
    main()
