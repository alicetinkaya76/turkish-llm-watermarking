# pilot/dev_llm_judge.py — LLM-yargıç kalite değerlendirmesi (Faz 3, disksiz).
#
# e5 kosinüsü anlam korunumunu vektör uzayında ölçüyor; bu betik aynı soruyu
# bir dil modeline sorar: saldırılı metin akıcı Türkçe mi, anlamı koruyor mu?
#
# SINIRLAMA (raporda AÇIKÇA yazılmalı): yargıç, metinleri üreten modelin TA
# KENDİSİ (Qwen2.5-3B-Instruct). Bu "aile-içi yargıç"tır ve kendi çıktısını
# kayırma konfoundu taşır. Bağımsız yargıç için harici API gerekir (Faz 3'ün
# ayrı bir ayağı, kullanıcı onayına bağlı).
#
# YARGICIN DENETİMİ: her çift İKİ SIRADA sorulur (orijinal önce / saldırılı
# önce). Karar sıraya göre dönüyorsa yargıç konum yanlısıdır. Dönme oranı
# raporlanır; yüksekse akıcılık sayıları BULGU SAYILMAZ.
#
#   python -m pilot.dev_llm_judge --model Qwen/Qwen2.5-3B-Instruct -n 15
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402

PROMPT = """Aşağıda iki Türkçe metin var.

[METİN 1]
{a}

[METİN 2]
{b}

İki soruyu yanıtla. Açıklama yazma, yalnızca aşağıdaki iki satırı ver:
AKICILIK: <1 veya 2 veya ESIT>   (hangisi daha akıcı ve dilbilgisel olarak doğru Türkçe)
ANLAM: <EVET veya KISMEN veya HAYIR>   (iki metin aynı bilgiyi mi aktarıyor)"""

_AKICI = re.compile(r"AKICILIK\s*:\s*\*{0,2}\s*(1|2|ESIT|EŞİT)", re.I)
_ANLAM = re.compile(r"ANLAM\s*:\s*\*{0,2}\s*(EVET|KISMEN|HAYIR)", re.I)

# --- Tekli (pointwise) protokol -----------------------------------------
# İkili protokolde ölçülen %84 konum dönmesi, "yargıç metni okumuyor" ile
# "ikili biçim konum yanlılığı üretiyor" arasını AYIRMIYOR. Tekli puanlamada
# konum diye bir şey yok; yargıç yine ayırt edemiyorsa sorun modeldedir.
POINT_PROMPT = """Aşağıdaki Türkçe metni dil kalitesi açısından değerlendir.

[METİN]
{t}

Yalnızca tek bir satır yaz, açıklama ekleme:
PUAN: <1-5 arası tam sayı>   (1 = bozuk/anlaşılmaz Türkçe, 5 = kusursuz akıcı Türkçe)"""

_PUAN = re.compile(r"PUAN\s*:\s*\*{0,2}\s*([1-5])")


def judge_point(model, tokz, device, text: str) -> int | None:
    import torch
    from pilot.generate import render_prompt, slice_completion

    rendered = render_prompt(tokz, POINT_PROMPT.format(t=text))
    enc = tokz(rendered, return_tensors="pt", add_special_tokens=True).to(device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=12, do_sample=False,
                             temperature=None, top_p=None, top_k=None,
                             pad_token_id=tokz.pad_token_id)
    comp, _ = slice_completion(
        tokz, rendered, tokz.batch_decode(out, skip_special_tokens=True)[0])
    m = _PUAN.search(comp)
    return int(m.group(1)) if m else None


def _norm_fluency(tok: str) -> str:
    t = tok.upper().replace("EŞİT", "ESIT")
    return t if t in {"1", "2", "ESIT"} else "?"


def judge_once(model, tokz, device, a: str, b: str) -> tuple[str, str]:
    import torch
    from pilot.generate import render_prompt, slice_completion

    rendered = render_prompt(tokz, PROMPT.format(a=a, b=b))
    enc = tokz(rendered, return_tensors="pt", add_special_tokens=True).to(device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=24, do_sample=False,
                             temperature=None, top_p=None, top_k=None,
                             pad_token_id=tokz.pad_token_id)
    full = tokz.batch_decode(out, skip_special_tokens=True)[0]
    comp, _ = slice_completion(tokz, rendered, full)
    mf, mm = _AKICI.search(comp), _ANLAM.search(comp)
    return (_norm_fluency(mf.group(1)) if mf else "?",
            mm.group(1).upper() if mm else "?")


def main() -> None:
    ap = argparse.ArgumentParser(description="LLM-yargıç (aile-içi)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("-n", type=int, default=15, help="saldırı başına çift")
    ap.add_argument("--src", default="pos_KGW")
    ap.add_argument("--pointwise", action="store_true",
                    help="konumsuz tekli puanlama (konum yanlılığı imkânsız)")
    args = ap.parse_args()

    from pilot.generate import get_device, load_model_and_tokenizer

    device = get_device(args.device)
    model_name = args.model or C.pick_model()[0]

    base = {(r["prompt_id"], r["seed"]): r["text"]
            for r in read_jsonl(C.RESULTS / f"gen_{args.src}.jsonl")}
    if not base:
        print(f"gen_{args.src}.jsonl yok -> önce Faz 1/2 koşulmalı.", file=sys.stderr)
        sys.exit(2)

    print(f"Yargıç: {model_name} ({device}) — AİLE-İÇİ (üreten modelle aynı)")
    model, tokz = load_model_and_tokenizer(model_name, device)

    rnd = random.Random(11)
    results, t0 = {}, time.time()

    if args.pointwise:
        import statistics
        rows0 = rnd.sample(sorted(base.items()), min(args.n, len(base)))
        orig_scores = [s for _, t in rows0
                       if (s := judge_point(model, tokz, device, t)) is not None]
        print(f"  {'ORİJİNAL (saldırısız)':22s} n={len(orig_scores):2d} "
              f"ort={statistics.mean(orig_scores):.2f}")
        results["_orijinal"] = dict(n=len(orig_scores),
                                    mean=statistics.mean(orig_scores),
                                    dist=dict(Counter(orig_scores)))
        for attack in C.ATTACKS:
            rows = [r for r in read_jsonl(C.RESULTS / f"att_{args.src}_{attack}.jsonl")
                    if (r["prompt_id"], r["seed"]) in base]
            if not rows:
                continue
            sc = [s for r in rnd.sample(rows, min(args.n, len(rows)))
                  if (s := judge_point(model, tokz, device, r["text"])) is not None]
            if not sc:
                continue
            m = statistics.mean(sc)
            results[attack] = dict(n=len(sc), mean=m, dist=dict(Counter(sc)))
            print(f"  {attack:22s} n={len(sc):2d} ort={m:.2f}  "
                  f"Δ={m - results['_orijinal']['mean']:+.2f}  "
                  f"dağılım={dict(sorted(Counter(sc).items()))}", flush=True)
        means = [v["mean"] for k, v in results.items()]
        path = C.RESULTS / "llm_judge_pointwise.json"
        path.write_text(json.dumps(
            {"judge_model": model_name, "protocol": "pointwise (konumsuz)",
             "results": results}, ensure_ascii=False, indent=2))
        print(f"\nPUAN aralığı: {min(means):.2f} – {max(means):.2f} "
              f"(yayılım {max(means)-min(means):.2f} puan / 4 puanlık ölçek)")
        print("YORUM: yayılım ~0 ise yargıç konumdan bağımsız olarak da metni "
              "okumuyor demektir; sorun ikili biçimde değil modeldedir.")
        print(f"-> {path}")
        return

    for attack in C.ATTACKS:
        rows = [r for r in read_jsonl(C.RESULTS / f"att_{args.src}_{attack}.jsonl")
                if (r["prompt_id"], r["seed"]) in base]
        if not rows:
            print(f"  {attack}: veri yok, atlandı")
            continue
        sample = rnd.sample(rows, min(args.n, len(rows)))
        fluent, meaning, flip = Counter(), Counter(), 0
        for r in sample:
            orig, att = base[(r["prompt_id"], r["seed"])], r["text"]
            # sıra A: orijinal 1. / sıra B: saldırılı 1.
            fa, ma = judge_once(model, tokz, device, orig, att)
            fb, mb = judge_once(model, tokz, device, att, orig)
            # sıra B'de etiketleri çevir ki ikisi de "saldırılı kazandı mı"ya baksın
            fb_al = {"1": "2", "2": "1", "ESIT": "ESIT", "?": "?"}[fb]
            if fa != fb_al:
                flip += 1
            fluent[fa] += 1
            fluent[fb_al] += 1
            meaning[ma] += 1
            meaning[mb] += 1
        n2 = 2 * len(sample)
        results[attack] = dict(
            n_pairs=len(sample),
            att_daha_akici=fluent["2"] / n2,
            esit=fluent["ESIT"] / n2,
            orij_daha_akici=fluent["1"] / n2,
            anlam_evet=meaning["EVET"] / n2,
            anlam_kismen=meaning["KISMEN"] / n2,
            anlam_hayir=meaning["HAYIR"] / n2,
            ayristirilamayan=(fluent["?"] + meaning["?"]) / (2 * n2),
            konum_donmesi=flip / len(sample),
        )
        r = results[attack]
        print(f"  {attack:14s} n={r['n_pairs']:2d}  anlam EVET %{100*r['anlam_evet']:3.0f} "
              f"| saldırılı daha akıcı %{100*r['att_daha_akici']:3.0f} "
              f"| konum dönmesi %{100*r['konum_donmesi']:3.0f}"
              f"{'  <-- YARGIÇ GÜVENİLMEZ' if r['konum_donmesi'] > 0.30 else ''}",
              flush=True)

    path = C.RESULTS / "llm_judge.json"
    path.write_text(json.dumps(
        {"judge_model": model_name, "judge_type": "aile-içi (üreten model = yargıç)",
         "src": args.src, "results": results}, ensure_ascii=False, indent=2))
    flips = [v["konum_donmesi"] for v in results.values()]
    mean_flip = sum(flips) / max(1, len(flips))
    print(f"\nort. konum dönmesi: %{100*mean_flip:.0f}  ({time.time()-t0:.0f} s)")
    print("YORUM: dönme oranı %30'u aşan koşullarda akıcılık kararı BULGU "
          "SAYILMAZ; yargıç metni değil sırayı okuyor demektir.")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
