# pilot/dev_s2_fayda.py — S2: saldırıların FAYDA (kullanılabilirlik) ekseni.
#
# ÖN-KAYIT: hpc/README.md "ÖN-KAYIT — S2" (commit cbcb988, koşudan önce).
# Karar kuralı: saldırı "başarılı" = ΔAUROC>0,05 VE yargıç çoğunluğu anlamın
# korunduğunu söylüyor. launder_api için İKİ yargıç da (Opus 5 + gpt-oss-120b,
# farklı aile -- metinleri Opus 5 ürettiği için çıkar çatışması) uyuşmalı.
#
# KÖR KALİBRASYON: özdeş çiftler (tavan; beklenen ESIT + EVET) ve farklı-istem
# çiftleri (zemin; beklenen HAYIR) gerçek çiftlerin arasına karıştırılır.
# Yargıç hangisinin kalibrasyon olduğunu bilmez. Kalibrasyonu geçemeyen
# yargıcın hükümleri o koşul için KULLANILMAZ.
#
#   python -m pilot.dev_s2_fayda --trial 5          # maliyet ölçümü
#   python -m pilot.dev_s2_fayda                    # tam koşu (iki yargıç)
#   python -m pilot.dev_s2_fayda --rapor            # analiz
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import append_jsonl, read_jsonl  # noqa: E402
from pilot.dev_llm_judge import PROMPT  # noqa: E402
from pilot.dev_llm_judge_api import (PAIR_SCHEMA, Usage, ask,  # noqa: E402
                                     make_client)

KOSULLAR = ("rtt", "para", "launder", "launder_api")
KAYNAK = "pos_KGW"
N_CIFT = 40
N_KALIB = 20                     # tür başına (özdeş / farklı-istem)
CIKTI = C.REPO_ROOT / "results_insan" / "s2_fayda.jsonl"
YARGICLAR = {"opus": "claude-opus-5", "gpt-oss": "openai/gpt-oss-120b"}


def groq_client():
    from dotenv import dotenv_values
    from groq import Groq

    key = (dotenv_values(_ROOT / ".env") or {}).get("GROQ_API_KEY")
    if not key:
        raise SystemExit("HATA: .env içinde GROQ_API_KEY yok.")
    print(f"Yargıç-2: gpt-oss-120b | anahtar {key[:4]}… ({len(key)} karakter) | Groq")
    return Groq(api_key=key)


import re as _re

_G_AKICI = _re.compile(r"AKICILIK\s*:?\s*\**\s*(1|2|ESIT|EŞİT)", _re.I)
_G_ANLAM = _re.compile(r"ANLAM\s*:?\s*\**\s*(EVET|KISMEN|HAYIR)", _re.I)


def groq_ask(client, model: str, prompt: str, usage: Usage) -> dict | None:
    """Groq tarafı DÜZ METİN + regex ayrıştırma (yerel yargıçla aynı desen).

    İlk sürüm response_format=json_object kullanıyordu; ÖLÇÜLDÜ: gpt-oss-120b
    akıl yürütme modeli, JSON doğrulaması boş üretimle 400 veriyor
    (json_validate_failed). PROMPT zaten iki satırlık sabit format istiyor;
    ayrıştırma dev_llm_judge'daki regexlerin aynısıyla yapılır. Geçersiz cevap
    None döner ve sayacı raporlanır -- sessizce yutulmaz."""
    for deneme in range(4):
        try:
            r = client.chat.completions.create(
                model=model, max_completion_tokens=2048, temperature=0.0,
                reasoning_effort="low",
                messages=[{"role": "user", "content": prompt}])
        except Exception:
            if deneme == 3:
                raise
            time.sleep(2 ** deneme)
            continue
        usage.calls += 1
        u = r.usage
        usage.inp += getattr(u, "prompt_tokens", 0)
        usage.out += getattr(u, "completion_tokens", 0)
        metin = r.choices[0].message.content or ""
        ma, mn = _G_AKICI.search(metin), _G_ANLAM.search(metin)
        if ma and mn:
            ak = ma.group(1).upper().replace("EŞİT", "ESIT")
            return {"akicilik": ak, "anlam": mn.group(1).upper()}
        return None
    return None


def cift_kur() -> list[dict]:
    """Gerçek + kalibrasyon çiftleri; karıştırılmış, etiketler gizli."""
    rnd = random.Random(11)
    base = {(r["prompt_id"], r["seed"]): r["text"]
            for r in read_jsonl(C.RESULTS / f"gen_{KAYNAK}.jsonl")}
    ciftler = []
    for kosul in KOSULLAR:
        att = [r for r in read_jsonl(C.RESULTS / f"att_{KAYNAK}_{kosul}.jsonl")
               if (r["prompt_id"], r["seed"]) in base]
        for r in rnd.sample(att, min(N_CIFT, len(att))):
            k = (r["prompt_id"], r["seed"])
            ciftler.append(dict(tur="gercek", kosul=kosul,
                                prompt_id=k[0], seed=k[1],
                                a=base[k], b=r["text"]))
    # kalibrasyon: ozdes (tavan) -- gen_neg'den, EXP'ten ASLA (tohumlar ozdes)
    # UZANTI (2026-09-03): kalibrasyon ciftleri yargic guvenilirligini olcer ve
    # KGW kolunda olculdu; EXP/SynthID uzantisinda tekrarlanmaz (kol-bagimsiz).
    if KAYNAK != "pos_KGW":
        return ciftler
    neg = read_jsonl(C.RESULTS / "gen_neg.jsonl")
    for r in rnd.sample(neg, N_KALIB):
        ciftler.append(dict(tur="kalib_ozdes", kosul="kalib",
                            prompt_id=r["prompt_id"], seed=r["seed"],
                            a=r["text"], b=r["text"]))
    # kalibrasyon: farkli istem (zemin) -- anlam HAYIR beklenir
    idx = rnd.sample(range(len(neg)), N_KALIB * 2)
    for i in range(N_KALIB):
        r1, r2 = neg[idx[2 * i]], neg[idx[2 * i + 1]]
        if r1["prompt_id"] == r2["prompt_id"]:
            continue
        ciftler.append(dict(tur="kalib_farkli", kosul="kalib",
                            prompt_id=r1["prompt_id"], seed=r1["seed"],
                            a=r1["text"], b=r2["text"]))
    rnd.shuffle(ciftler)
    return ciftler


def kos(trial: int) -> None:
    ciftler = cift_kur()
    if trial:
        ciftler = ciftler[:trial]
    hazir = {(r["yargic"], r["tur"], r["kosul"], r["prompt_id"], r["seed"], r["sira"])
             for r in read_jsonl(CIKTI)}
    istemciler = {"opus": (make_client(YARGICLAR["opus"]), None)}
    gq = groq_client()
    istemciler["gpt-oss"] = (gq, YARGICLAR["gpt-oss"])
    kullanim = {ad: Usage(YARGICLAR[ad]) for ad in istemciler}
    gecersiz = {ad: 0 for ad in istemciler}

    n_toplam = len(ciftler) * 2 * len(istemciler)
    print(f"{len(ciftler)} çift x 2 sıra x {len(istemciler)} yargıç = {n_toplam} çağrı")
    t0 = time.time()
    yapilan = 0
    for ci, c in enumerate(ciftler):
        for sira, (x, y) in enumerate(((c["a"], c["b"]), (c["b"], c["a"]))):
            p = PROMPT.format(a=x, b=y)
            for ad, (cl, mdl) in istemciler.items():
                anahtar = (ad, c["tur"], c["kosul"], c["prompt_id"], c["seed"], sira)
                if anahtar in hazir:
                    continue
                if ad == "opus":
                    d = ask(cl, YARGICLAR["opus"], p, PAIR_SCHEMA, kullanim[ad])
                else:
                    d = groq_ask(cl, mdl, p, kullanim[ad])
                if d is None:
                    gecersiz[ad] += 1
                    continue
                append_jsonl(CIKTI, {
                    "yargic": ad, "tur": c["tur"], "kosul": c["kosul"],
                    "prompt_id": c["prompt_id"], "seed": c["seed"], "sira": sira,
                    "akicilik": d["akicilik"], "anlam": d["anlam"],
                })
                yapilan += 1
        if (ci + 1) % 20 == 0:
            print(f"  {ci+1}/{len(ciftler)} çift | "
                  + " | ".join(f"{a}: {k.report()}" for a, k in kullanim.items()),
                  flush=True)
    for ad in istemciler:
        print(f"\n{ad}: {kullanim[ad].report()} | geçersiz cevap: {gecersiz[ad]}")
    if trial:
        for ad, k in kullanim.items():
            cst = k.cost()
            if cst:
                tam = cst / max(1, k.calls) * len(cift_kur()) * 2
                print(f"  {ad}: TAM KOŞU TAHMİNİ ~${tam:.2f}")


def rapor() -> None:
    import numpy as np
    import pandas as pd

    d = pd.DataFrame(read_jsonl(CIKTI))
    if not len(d):
        raise SystemExit("veri yok")
    print("=" * 66)
    print("S2 RAPOR — fayda ekseni (ön-kayıt: cbcb988)")
    print("=" * 66)

    # 1) KALİBRASYON: yargıç güvenilir mi?
    print("\nKALİBRASYON (yargıç kör; geçemeyen yargıcın hükümleri kullanılmaz)")
    kalib_gecti = {}
    for ad in d.yargic.unique():
        oz = d[(d.yargic == ad) & (d.tur == "kalib_ozdes")]
        fk = d[(d.yargic == ad) & (d.tur == "kalib_farkli")]
        oz_ok = (oz.anlam == "EVET").mean() if len(oz) else float("nan")
        fk_ok = (fk.anlam == "HAYIR").mean() if len(fk) else float("nan")
        gecti = oz_ok >= 0.9 and fk_ok >= 0.9
        kalib_gecti[ad] = gecti
        print(f"  {ad:8s} özdeş->EVET {oz_ok:.2f} (n={len(oz)}) | "
              f"farklı->HAYIR {fk_ok:.2f} (n={len(fk)}) | "
              f"{'GEÇTİ' if gecti else 'KALDI'}")

    # 2) konum dönmesi + hükümler
    print(f"\n{'koşul':12s} {'yargıç':8s} {'n':>3s} {'ANLAM korunmuş':>15s} "
          f"{'orij. daha akıcı':>17s} {'konum dönme':>12s}")
    ozet = {}
    for kosul in KOSULLAR:
        for ad in sorted(d.yargic.unique()):
            g = d[(d.yargic == ad) & (d.kosul == kosul) & (d.tur == "gercek")]
            if not len(g):
                continue
            piv = g.pivot_table(index=["prompt_id", "seed"], columns="sira",
                                values="akicilik", aggfunc="first")
            if 0 in piv and 1 in piv:
                tam = piv.dropna()
                # sıra 0'da a=ORİJİNAL; sıra 1'de a=SALDIRILI. Tutarlı hüküm =
                # iki sırada da AYNI METNİ seçmek:
                #   (s0="1", s1="2") -> ikisinde de orijinal
                #   (s0="2", s1="1") -> ikisinde de saldırılı
                #   (s0=ESIT, s1=ESIT) -> ikisinde de eşit
                # İLK SÜRÜM HATALIYDI: pandas'ta `|` karşılaştırmadan önce
                # bağlanır; `A != B | C` ifadesi `A != (B|C)` olarak ayrıştı ve
                # dönme oranları anlamsızdı. Parantezli açık tanıma geçildi.
                tutarli = (((tam[0] == "1") & (tam[1] == "2"))
                           | ((tam[0] == "2") & (tam[1] == "1"))
                           | ((tam[0] == "ESIT") & (tam[1] == "ESIT")))
                donme = float((~tutarli).mean())
            else:
                donme = float("nan")
            anlam_ok = float(g.anlam.isin(["EVET", "KISMEN"]).mean())
            orij = float(((g.sira == 0) & (g.akicilik == "1")
                          | (g.sira == 1) & (g.akicilik == "2")).mean())
            ozet[(kosul, ad)] = dict(n=len(g), anlam=anlam_ok, orij=orij,
                                     donme=donme, guvenilir=kalib_gecti.get(ad))
            print(f"  {kosul:12s} {ad:8s} {len(g):3d} {anlam_ok:15.2f} "
                  f"{orij:17.2f} {donme:12.2f}")

    # 3) ön-kayıtlı karar kuralı
    print("\nKARAR (ön-kayıt: başarılı = ΔAUROC>0,05 VE anlam korunuyor; "
          "launder_api'de iki yargıç da)")
    # ŞEFFAFLIK: ön-kayıt ΔAUROC'un hangi ŞEMADA ölçüleceğini belirtmemişti.
    # Tek şema seçmek (hele sonucu gördükten sonra) post-hoc olur; üç şema da
    # ayrı satırda değerlendirilir ve bu belirsizlik raporda açıkça yazılır.
    det = pd.read_csv(C.RESULTS / "detection_metrics.csv")
    print("  (ön-kayıt şema belirtmemişti -> üçü de raporlanır, seçim yapılmaz)")
    for kosul in KOSULLAR:
        hukumler = {ad: ozet.get((kosul, ad), {}).get("anlam", float("nan"))
                    for ad in sorted(d.yargic.unique())}
        gecerli = [ad for ad, v in hukumler.items()
                   if kalib_gecti.get(ad) and v == v]
        if kosul == "launder_api":
            anlam_ok = all(hukumler[ad] >= 0.5 for ad in gecerli) and len(gecerli) >= 2
        else:
            anlam_ok = any(hukumler[ad] >= 0.5 for ad in gecerli)
        parcalar = []
        for sema in C.SCHEMES:
            dk = det[(det.scheme == sema) & (det.condition == kosul)]
            dc = det[(det.scheme == sema) & (det.condition == "clean")]
            if not len(dk):
                continue
            da = float(dc.auroc.iloc[0] - dk.auroc.iloc[0])
            parcalar.append(f"{sema}{'✓' if (da > 0.05 and anlam_ok) else '·'}{da:+.3f}")
        print(f"  {kosul:12s} anlam {'OK' if anlam_ok else 'YOK'} | ΔAUROC: "
              + "  ".join(parcalar)
              + "   (✓ = o şemada ön-kayıt kuralı sağlandı)")

    yol = C.REPO_ROOT / "results_insan" / ("s2_rapor.json" if KAYNAK == "pos_KGW" else f"s2_rapor_{KAYNAK}.json")
    # numpy bool/float JSON'a çevrilemiyor; saf Python tiplerine indir.
    def _saf(v):
        return {kk: (bool(x) if isinstance(x, (bool, np.bool_)) else
                     float(x) if isinstance(x, (int, float, np.floating)) else x)
                for kk, x in v.items()}
    yol.write_text(json.dumps(
        {f"{k}|{a}": _saf(v) for (k, a), v in ozet.items()},
        ensure_ascii=False, indent=2))
    print(f"\nyazıldı: {yol}")


def main() -> None:
    ap = argparse.ArgumentParser(description="S2: fayda ekseni")
    ap.add_argument("--trial", type=int, default=0)
    ap.add_argument("--rapor", action="store_true")
    ap.add_argument("--kaynak", default="pos_KGW",
                    choices=["pos_KGW", "pos_EXP", "pos_SynthID"],
                    help="Yargilanacak kaynak kol. On-kayit KGW; EXP/SynthID = kayit-sonrasi UZANTI, ayri dosyaya yazar.")
    a = ap.parse_args()
    global KAYNAK, CIKTI
    KAYNAK = a.kaynak
    if KAYNAK != "pos_KGW":
        CIKTI = C.REPO_ROOT / "results_insan" / f"s2_fayda_{KAYNAK}.jsonl"
        CIKTI.touch()
    if a.rapor:
        rapor()
    else:
        kos(a.trial)


if __name__ == "__main__":
    main()
