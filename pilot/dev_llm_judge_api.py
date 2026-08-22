# pilot/dev_llm_judge_api.py — BAĞIMSIZ LLM-yargıç (Faz 3).
#
# dev_llm_judge.py'nin aile-içi 3B yargıcı ölçüm aleti olarak kalibre DEĞİL:
# ikili protokolde konum dönmesi %84 (metne değil sıraya bakıyor), tekli
# protokolde dokuz kıyastan hiçbiri Bonferroni'den sonra anlamlı değil.
# Bu betik aynı örneklemi, aynı iki protokolle, BAĞIMSIZ bir yargıca sorar.
# Karşılaştırma ("aile-içi yapamıyor, bağımsız yapıyor") kendisi bir bulgudur.
#
# API SÖZLEŞMESİ (claude-api referansından, hafızadan değil):
#   * Opus 5'te temperature/top_p/top_k KALDIRILDI -> gönderilirse 400. Yani
#     yerel yargıçtaki do_sample=False determinizmi burada kurulamaz; koşular
#     arası küçük oynama beklenir ve raporlanır.
#   * Düşünme Opus 5'te VARSAYILAN OLARAK AÇIK. Kapatmıyoruz: kapalı düşünmede
#     modelin yanıta <thinking> etiketi sızdırdığı belgeli, bu da ayrıştırmayı
#     bozardı. effort="low" ile derinlik sınırlanıyor.
#   * output_config.format (JSON şeması) ile biçim garanti altına alınıyor ->
#     "ayrıştırılamayan cevap" kategorisi ortadan kalkıyor.
#   * stop_reason == "refusal" içerik OKUNMADAN önce denetlenmeli.
#   * ANTHROPIC_BASE_URL ortam değişkeni YOK SAYILIR; adres kodda sabit, anahtar
#     .env'den. Böylece kullanıcının Claude Code oturumuyla karışmaz.
#
#   python -m pilot.dev_llm_judge_api --trial 5      # önce maliyeti ölç
#   python -m pilot.dev_llm_judge_api -n 15          # ikili protokol
#   python -m pilot.dev_llm_judge_api -n 15 --pointwise
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402
from pilot.dev_llm_judge import PROMPT, POINT_PROMPT  # aynı sorular  # noqa: E402

API_BASE = "https://api.anthropic.com"          # ortam değişkeni bilerek yok sayılıyor
DEFAULT_MODEL = "claude-opus-5"
# $/MTok (giriş, çıkış) — claude-api referansı, 2026-06-24 önbelleği
PRICES = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),           # 2026-08-31'e dek tanıtım: 2.00/10.00
    "claude-haiku-4-5": (1.00, 5.00),
}

# --- Filigranın KENDİ kalite bedeli -------------------------------------
# Şu ana dek hiç ölçülmedi: e5 kosinüsü yalnız saldırılı-vs-orijinal bakıyor,
# filigransız-vs-filigranlı bakmıyor. Burada aynı prompt ve AYNI TOHUMLA
# üretilmiş filigransız/filigranlı çiftler karşılaştırılır. İki metin aynı
# soruya verilmiş BAĞIMSIZ yanıtlar olduğu için "aynı bilgiyi mi aktarıyor"
# sorusu anlamsızdır; yalnız akıcılık sorulur.
WM_PROMPT = """Aşağıda aynı soruya verilmiş iki Türkçe yanıt var.

[METİN 1]
{a}

[METİN 2]
{b}

Hangisi daha akıcı ve dilbilgisel olarak doğru Türkçe? İçeriğin ne anlattığına
değil, yalnız dil kalitesine bak. Açıklama yazma."""

WM_SCHEMA = {
    "type": "object",
    "properties": {"akicilik": {"type": "string", "enum": ["1", "2", "ESIT"]}},
    "required": ["akicilik"],
    "additionalProperties": False,
}

PAIR_SCHEMA = {
    "type": "object",
    "properties": {
        "akicilik": {"type": "string", "enum": ["1", "2", "ESIT"]},
        "anlam": {"type": "string", "enum": ["EVET", "KISMEN", "HAYIR"]},
    },
    "required": ["akicilik", "anlam"],
    "additionalProperties": False,
}
POINT_SCHEMA = {
    "type": "object",
    "properties": {"puan": {"type": "integer", "enum": [1, 2, 3, 4, 5]}},
    "required": ["puan"],
    "additionalProperties": False,
}


class Usage:
    """Token muhasebesi. Maliyet ÖLÇÜLÜR, tahmin edilmez."""

    def __init__(self, model: str):
        self.model = model
        self.calls = self.inp = self.out = self.cache_r = self.cache_w = 0
        self.refusals = 0

    def add(self, u) -> None:
        self.calls += 1
        self.inp += u.input_tokens
        self.out += u.output_tokens
        self.cache_r += getattr(u, "cache_read_input_tokens", 0) or 0
        self.cache_w += getattr(u, "cache_creation_input_tokens", 0) or 0

    def cost(self) -> float | None:
        """Bilinmeyen model için None döner — SESSİZCE 0 DÖNMEZ.

        Eskiden `PRICES.get(model, (0.0, 0.0))` idi: fiyatı bilinmeyen bir
        modelle koşulduğunda maliyet sessizce $0,00 çıkıyor ve rapora 'ÖLÇÜLEN
        MALİYET' diye giriyordu. Gerçekte on dolarlarca harcanmışken raporun
        sıfır demesi, bu deponun 'sayı uydurma' yasağının en kötü hâli.
        """
        pr = PRICES.get(self.model)
        if pr is None:
            return None
        return (self.inp / 1e6) * pr[0] + (self.out / 1e6) * pr[1]

    def cost_str(self) -> str:
        c = self.cost()
        if c is None:
            return (f"HESAPLANAMADI (model '{self.model}' PRICES'ta yok — "
                    f"fiyatı ekleyin: {sorted(PRICES)})")
        return f"${c:.3f}"

    def report(self) -> str:
        return (f"{self.calls} çağrı | giriş {self.inp:,} tok | çıkış {self.out:,} tok"
                f" | önbellek okuma {self.cache_r:,} | red {self.refusals}"
                f" | ÖLÇÜLEN MALİYET {self.cost_str()}")


def make_client(model: str):
    from dotenv import dotenv_values
    import anthropic

    key = (dotenv_values(_ROOT / ".env") or {}).get("ANTHROPIC_API_KEY")
    if not key:
        print("HATA: .env içinde ANTHROPIC_API_KEY yok.", file=sys.stderr)
        sys.exit(2)
    # anahtar değeri hiçbir yere basılmaz; yalnız ön ek/uzunluk teyidi
    print(f"Yargıç: {model} | anahtar {key[:7]}… ({len(key)} karakter) | {API_BASE}")
    return anthropic.Anthropic(api_key=key, base_url=API_BASE)


def ask(client, model: str, prompt: str, schema: dict, usage: Usage) -> dict | None:
    """Bir yargı. Şema dayatıldığı için ayrıştırma hatası olamaz."""
    for attempt in range(4):
        try:
            r = client.messages.create(
                model=model,
                max_tokens=2000,                       # düşünme + yanıt birlikte
                output_config={"effort": "low", "format": {
                    "type": "json_schema", "schema": schema}},
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:                          # 429/5xx: SDK zaten yeniden dener
            if attempt == 3:
                raise
            print(f"    (yeniden deneme {attempt + 1}: {type(e).__name__})", flush=True)
            time.sleep(2 ** attempt)
            continue
        usage.add(r.usage)
        if r.stop_reason == "refusal":                  # içerik OKUNMADAN önce
            usage.refusals += 1
            return None
        txt = next((b.text for b in r.content if b.type == "text"), None)
        return json.loads(txt) if txt else None
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Bağımsız LLM-yargıç (API)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("-n", type=int, default=15, help="saldırı başına çift")
    ap.add_argument("--src", default="pos_KGW")
    ap.add_argument("--pointwise", action="store_true")
    ap.add_argument("--trial", type=int, default=0,
                    help="yalnız N çift koş ve ÖLÇÜLEN maliyeti bildir")
    ap.add_argument("--wm-cost", action="store_true",
                    help="filigranın kendi akıcılık bedeli (filigransız vs filigranlı)")
    args = ap.parse_args()

    base = {(r["prompt_id"], r["seed"]): r["text"]
            for r in read_jsonl(C.RESULTS / f"gen_{args.src}.jsonl")}
    if not base:
        print(f"gen_{args.src}.jsonl yok -> önce Faz 1/2 koşulmalı.", file=sys.stderr)
        sys.exit(2)

    client = make_client(args.model)
    usage = Usage(args.model)
    rnd = random.Random(11)                             # yerel yargıçla AYNI örneklem
    results, t0 = {}, time.time()

    if args.trial:
        rows = [r for r in read_jsonl(C.RESULTS / f"att_{args.src}_rtt.jsonl")
                if (r["prompt_id"], r["seed"]) in base][: args.trial]
        print(f"\nDENEME: {len(rows)} çift (rtt), iki sıra = {2 * len(rows)} çağrı")
        for r in rows:
            o, a = base[(r["prompt_id"], r["seed"])], r["text"]
            for x, y in ((o, a), (a, o)):
                ask(client, args.model, PROMPT.format(a=x, b=y), PAIR_SCHEMA, usage)
        per_call = usage.cost() / max(1, usage.calls)
        print(f"  {usage.report()}")
        print(f"  çağrı başına ${per_call:.5f}")
        print(f"\nTAM KOŞU TAHMİNİ (ölçülen çağrı maliyetinden):")
        print(f"  ikili  9x{args.n}x2 = {9 * args.n * 2:4d} çağrı -> "
              f"${per_call * 9 * args.n * 2:.2f}")
        print(f"  tekli  (9+1)x{args.n} = {10 * args.n:4d} çağrı -> "
              f"~${per_call * 10 * args.n * 0.55:.2f} (istem yarı uzunlukta)")
        return

    if args.wm_cost:
        import statistics
        from scipy.stats import mannwhitneyu

        neg = {(r["prompt_id"], r["seed"]): r["text"]
               for r in read_jsonl(C.RESULTS / "gen_neg.jsonl")}
        keys = sorted(rnd.sample(sorted(neg), min(args.n, len(neg))))

        # (a) İKİLİ: aynı prompt+tohum, filigransız vs filigranlı, iki sırada
        print("\n(a) İKİLİ akıcılık — filigransız vs filigranlı (aynı prompt+tohum)")
        for s in C.SCHEMES:
            pos = {(r["prompt_id"], r["seed"]): r["text"]
                   for r in read_jsonl(C.RESULTS / f"gen_pos_{s}.jsonl")}
            cnt, flip, n = Counter(), 0, 0
            for k in keys:
                if k not in pos:
                    continue
                da = ask(client, args.model, WM_PROMPT.format(a=neg[k], b=pos[k]),
                         WM_SCHEMA, usage)
                db = ask(client, args.model, WM_PROMPT.format(a=pos[k], b=neg[k]),
                         WM_SCHEMA, usage)
                if not da or not db:
                    continue
                n += 1
                fb = {"1": "2", "2": "1", "ESIT": "ESIT"}[db["akicilik"]]
                flip += da["akicilik"] != fb
                cnt[da["akicilik"]] += 1
                cnt[fb] += 1
            if not n:
                continue
            results[f"pair_{s}"] = dict(
                n=n, filigranli_daha_akici=cnt["2"] / (2 * n),
                esit=cnt["ESIT"] / (2 * n), filigransiz_daha_akici=cnt["1"] / (2 * n),
                konum_donmesi=flip / n)
            v = results[f"pair_{s}"]
            print(f"  {s:8s} n={n:2d}  filigranlı daha akıcı %{100*v['filigranli_daha_akici']:3.0f}"
                  f" | eşit %{100*v['esit']:3.0f}"
                  f" | filigransız daha akıcı %{100*v['filigransiz_daha_akici']:3.0f}"
                  f" | dönme %{100*v['konum_donmesi']:3.0f}", flush=True)

        # (b) TEKLİ: her metne bağımsız puan; konum diye bir şey yok
        print("\n(b) TEKLİ puan (1-5) — konumsuz, Mann-Whitney ile filigransıza karşı")
        scores = {}
        for label, src in [("filigransız", neg)] + [
                (s, {(r["prompt_id"], r["seed"]): r["text"]
                     for r in read_jsonl(C.RESULTS / f"gen_pos_{s}.jsonl")})
                for s in C.SCHEMES]:
            sc = [d["puan"] for k in keys if k in src
                  and (d := ask(client, args.model, POINT_PROMPT.format(t=src[k]),
                                POINT_SCHEMA, usage))]
            scores[label] = sc
            line = f"  {label:12s} n={len(sc):2d} ort={statistics.mean(sc):.2f}"
            if label != "filigransız" and scores["filigransız"]:
                _, p = mannwhitneyu(sc, scores["filigransız"], alternative="two-sided")
                d = statistics.mean(sc) - statistics.mean(scores["filigransız"])
                line += (f"  Δ={d:+.2f}  p={p:.3f}"
                         f"  Bonferroni(×3) {'ANLAMLI' if p * 3 < 0.05 else '—'}")
            results[f"point_{label}"] = dict(n=len(sc), mean=statistics.mean(sc),
                                             dist=dict(Counter(sc)))
            print(line, flush=True)
        out = C.RESULTS / "llm_judge_api_wmcost.json"

    elif args.pointwise:
        import statistics
        rows0 = rnd.sample(sorted(base.items()), min(args.n, len(base)))
        sc = [d["puan"] for _, t in rows0
              if (d := ask(client, args.model, POINT_PROMPT.format(t=t),
                           POINT_SCHEMA, usage))]
        results["_orijinal"] = dict(n=len(sc), mean=statistics.mean(sc),
                                    dist=dict(Counter(sc)))
        print(f"  {'ORİJİNAL (saldırısız)':22s} n={len(sc):2d} "
              f"ort={statistics.mean(sc):.2f}")
        for attack in C.ATTACKS:
            rows = [r for r in read_jsonl(C.RESULTS / f"att_{args.src}_{attack}.jsonl")
                    if (r["prompt_id"], r["seed"]) in base]
            if not rows:
                continue
            sc = [d["puan"] for r in rnd.sample(rows, min(args.n, len(rows)))
                  if (d := ask(client, args.model, POINT_PROMPT.format(t=r["text"]),
                               POINT_SCHEMA, usage))]
            if not sc:
                continue
            m = statistics.mean(sc)
            results[attack] = dict(n=len(sc), mean=m, dist=dict(Counter(sc)))
            print(f"  {attack:22s} n={len(sc):2d} ort={m:.2f}  "
                  f"Δ={m - results['_orijinal']['mean']:+.2f}  "
                  f"dağılım={dict(sorted(Counter(sc).items()))}", flush=True)
        means = [v["mean"] for v in results.values()]
        print(f"\nPUAN aralığı: {min(means):.2f} – {max(means):.2f} "
              f"(yayılım {max(means) - min(means):.2f})")
        out = C.RESULTS / "llm_judge_api_pointwise.json"
    else:
        for attack in C.ATTACKS:
            rows = [r for r in read_jsonl(C.RESULTS / f"att_{args.src}_{attack}.jsonl")
                    if (r["prompt_id"], r["seed"]) in base]
            if not rows:
                continue
            sample = rnd.sample(rows, min(args.n, len(rows)))
            fluent, meaning, flip, lost = Counter(), Counter(), 0, 0
            for r in sample:
                o, a = base[(r["prompt_id"], r["seed"])], r["text"]
                da = ask(client, args.model, PROMPT.format(a=o, b=a), PAIR_SCHEMA, usage)
                db = ask(client, args.model, PROMPT.format(a=a, b=o), PAIR_SCHEMA, usage)
                if not da or not db:
                    lost += 1
                    continue
                fb = {"1": "2", "2": "1", "ESIT": "ESIT"}[db["akicilik"]]
                flip += da["akicilik"] != fb
                fluent[da["akicilik"]] += 1
                fluent[fb] += 1
                meaning[da["anlam"]] += 1
                meaning[db["anlam"]] += 1
            n = len(sample) - lost
            if n <= 0:
                continue
            results[attack] = dict(
                n_pairs=n, att_daha_akici=fluent["2"] / (2 * n),
                esit=fluent["ESIT"] / (2 * n), orij_daha_akici=fluent["1"] / (2 * n),
                anlam_evet=meaning["EVET"] / (2 * n),
                anlam_kismen=meaning["KISMEN"] / (2 * n),
                anlam_hayir=meaning["HAYIR"] / (2 * n),
                konum_donmesi=flip / n, kayip=lost)
            v = results[attack]
            print(f"  {attack:14s} n={n:2d}  EVET %{100*v['anlam_evet']:3.0f} "
                  f"KISMEN %{100*v['anlam_kismen']:3.0f} HAYIR %{100*v['anlam_hayir']:3.0f} "
                  f"| saldırılı daha akıcı %{100*v['att_daha_akici']:3.0f} "
                  f"| konum dönmesi %{100*v['konum_donmesi']:3.0f}"
                  f"{'  <-- GÜVENİLMEZ' if v['konum_donmesi'] > 0.30 else ''}", flush=True)
        flips = [v["konum_donmesi"] for v in results.values()]
        if flips:
            print(f"\nort. konum dönmesi: %{100*sum(flips)/len(flips):.0f}")
        out = C.RESULTS / "llm_judge_api.json"

    out.write_text(json.dumps({
        "judge_model": args.model, "judge_type": "BAĞIMSIZ (üreten modelden farklı)",
        "protocol": "pointwise" if args.pointwise else "pairwise",
        "structured_output": True, "sampling_params": "yok (Opus 5'te kaldırıldı)",
        "src": args.src, "usage": {
            "calls": usage.calls, "input_tokens": usage.inp,
            "output_tokens": usage.out, "refusals": usage.refusals,
            "measured_cost_usd": (round(usage.cost(), 4)
                                  if usage.cost() is not None else None),
            "price_table_hit": usage.model in PRICES},
        "results": results}, ensure_ascii=False, indent=2))
    print(f"\n{usage.report()}  ({time.time() - t0:.0f} s)\n-> {out}")


if __name__ == "__main__":
    main()
