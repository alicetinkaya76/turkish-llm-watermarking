# pilot/dev_launder_api.py — Faz 3: GERÇEK laundering (harici API ile).
#
# Faz 2'nin `launder` saldırısı, metni ÜRETEN modelin (Qwen2.5-3B) kendisine
# yeniden yazdırıyordu — "sıfır-beceri aklama". Gerçek tehdit modeli (Panel-3)
# ise saldırganın GÜÇLÜ bir harici modelden geçirmesidir. Bu betik onu ölçer.
#
# NEDEN KİRLİ KORPUSTA GEÇERLİ: bu deneyin çıktısı tespit düşüşüdür (AUROC/TPR),
# kalite değil. Tespit metriklerinin yabancı-yazı kirlenmesine görece dayanıklı
# olduğu ölçüldü; GÜNCEL sapma değerleri metrics.corpus_integrity tarafından
# KODDAN üretilir (results/summary.md). Buraya sayı YAZMA -- bir önceki sürümde
# elle yazılan sapma değeri launder_api eklenince bayatladı ve denetimde
# yakalandı. Kalite iddiası ÜRETİLMEZ.
#
# Üretilen dosyalar Faz 2'nin şemasına uyar (att_{src}_launder_api.jsonl), böylece
# `python -m pilot.run --phase 2` onları hazır bulup yalnız skorlar.
#
#   python -m pilot.dev_launder_api --trial 4     # ölçülen maliyet
#   python -m pilot.dev_launder_api               # tam koşu
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import append_jsonl, read_jsonl  # noqa: E402
from pilot.dev_llm_judge_api import Usage, make_client  # noqa: E402

# Faz 2'nin yerel `launder` istemiyle AYNI - tek değişken aklayıcı modeldir.
LAUNDER_PROMPT = ("Aşağıdaki Türkçe metindeki bilgiyi eksiksiz koruyarak metni "
                  "baştan, tamamen kendi cümlelerinle yeniden yaz. Açıklama "
                  "ekleme, sadece yeni metni ver:\n\n{t}")


def launder(client, model: str, text: str, usage: Usage) -> str | None:
    for attempt in range(4):
        try:
            r = client.messages.create(
                model=model, max_tokens=4000,
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": LAUNDER_PROMPT.format(t=text)}])
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
            continue
        usage.add(r.usage)
        if r.stop_reason == "refusal":                  # içerik OKUNMADAN önce
            usage.refusals += 1
            return None
        return next((b.text for b in r.content if b.type == "text"), None)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="API ile gerçek laundering")
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--trial", type=int, default=0)
    # n_tokens SABİT Qwen2.5-3B tokenizer'ı ile hesaplanıyordu. Korpus artık
    # Qwen3-14B ile üretiliyor; farklı tokenizer -> n_tokens KARŞILAŞTIRILAMAZ
    # olurdu (uzunluk konfoundu analizi buna dayanıyor).
    ap.add_argument("--gen-model", default="Qwen/Qwen3-14B",
                    help="korpusu ÜRETEN model (n_tokens bunun tokenizer'ıyla)")
    args = ap.parse_args()

    from pilot.generate import get_device, load_model_and_tokenizer

    client = make_client(args.model)
    usage = Usage(args.model)

    sources = [("neg", "gen_neg")] + [(f"pos_{s}", f"gen_pos_{s}") for s in C.SCHEMES]

    if args.trial:
        rows = read_jsonl(C.RESULTS / "gen_pos_KGW.jsonl")[: args.trial]
        print(f"\nDENEME: {len(rows)} metin aklanıyor")
        for r in rows:
            out = launder(client, args.model, r["text"], usage)
            print(f"  p{r['prompt_id']:02d}/s{r['seed']}: "
                  f"{len(r['text'])} -> {len(out) if out else 0} karakter")
        c = usage.cost()
        if c is None:
            print(f"\n  {usage.report()}")
            print("  Maliyet hesaplanamadı; tam koşu tahmini üretilmiyor.")
            return
        per = c / max(1, usage.calls)
        n_full = sum(len(read_jsonl(C.RESULTS / f"{f}.jsonl")) for _, f in sources)
        print(f"\n  {usage.report()}")
        print(f"  metin başına ${per:.4f}")
        print(f"  TAM KOŞU: {n_full} metin -> ~${per * n_full:.2f}")
        return

    # tokenizer yalnız n_tokens için; model yüklenmez
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.gen_model)

    for src_tag, gen_file in sources:
        rows = read_jsonl(C.RESULTS / f"{gen_file}.jsonl")
        path = C.RESULTS / f"att_{src_tag}_launder_api.jsonl"
        done = {(r["prompt_id"], r["seed"]) for r in read_jsonl(path)}
        todo = [r for r in rows if (r["prompt_id"], r["seed"]) not in done]
        print(f"\n{src_tag}: {len(rows)} taban, {len(done)} hazır, {len(todo)} yapılacak")
        for i, r in enumerate(todo):
            out = launder(client, args.model, r["text"], usage)
            if out is None:
                print(f"  UYARI: red/boş - p{r['prompt_id']}/s{r['seed']} atlandı")
                continue
            append_jsonl(path, {
                **{k: r[k] for k in ("prompt_id", "seed", "wm")},
                "text": out.strip(),
                "n_tokens": len(tok(out, add_special_tokens=False).input_ids),
                "edits": -1, "rejected": 0})
            if (i + 1) % 20 == 0:
                print(f"  [{src_tag}] {i + 1}/{len(todo)} | {usage.report()}",
                      flush=True)
    print(f"\nTAMAM. {usage.report()}")
    print(f"Skorlamak için:  python -m pilot.run --phase 2 --config cuda "
          f"--model {args.gen_model}")


if __name__ == "__main__":
    main()
