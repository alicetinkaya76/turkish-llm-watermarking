# pilot/dev_dejenere_kanit.py — C1/C2/C5: AUROC = 1.000 hucreleri icin
# Clopper-Pearson'in YERINE gececek kanit.
#
# NEDEN. Makale su an dejenere hucrelerde "sifir basarisizlik 24 kumede
# AUROC'u 0.883'te sinirlar" diyor (metrics.py:82-92, alpha**(1/n)).
# Bu turetim gecersiz: CP sinirir bir Bernoulli oraninin alt siniridir;
# AUROC ise ikili siralama U-istatistigidir. Kume duzeyinde bir "basari"
# olayinin olasiligi ile populasyon AUROC'u arasinda genel bir esitsizlik
# YOKTUR. Sayinin buyuklugu degil, ilan edilen turetim yanlis.
#
# YERINE NE KONACAK. Dejenere hucrede gozlenen sey aslinda CP'den daha
# guclu ve dogrudan raporlanabilir:
#   (1) TAM AYRISMA: her istem kumesinde (ve global olarak) en dusuk
#       filigranli skor, tum temiz negatiflerin maksimumunu asiyor mu?
#   (2) MARJ: bu ayrismanin genisligi, negatif dagilimin standart sapmasi
#       biriminde. Bu, "1.000" un ne kadar rahat kazanildigini gosterir ve
#       semalar arasinda DURUSTCE ayrisir (EXP'in marji KGW'ninkinin
#       onlarca kati; ikisini ayni guvenle sunmak yaniltici olurdu).
#   (3) TAM PERMUTASYON p: dagilimdan bagimsiz, varsayimsiz. Istem icinde
#       filigranli/temiz etiketleri degistirilebilir kabul edilirse
#       tek yanli tam p = (1/C(m+k, m))^(istem sayisi).
#       Ayrica daha zayif varsayimli isaret-cevirme surumu de verilir.
#
# CIKTI: results/dejenere_kanit.json
#   python pilot/dev_dejenere_kanit.py
from __future__ import annotations

import json
import sys
from math import comb, log10
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402


def main() -> None:
    sc = pd.read_csv(C.RESULTS / "scores.csv")
    det = pd.read_csv(C.RESULTS / "detection_metrics.csv")

    # dejenere hucreler: metrics.py'nin kendi bayragi (ci_lo_cp dolu olanlar)
    dejenere = det[det["ci_lo_cp"].notna()][["scheme", "condition", "auroc",
                                             "ci_lo_cp", "n_kume"]]
    satirlar = []
    for _, r in dejenere.iterrows():
        sema, kosul = r["scheme"], r["condition"]
        # pozitifler: bu kosulun filigranli kolu; negatifler: TEMIZ filigransiz
        poz = sc[(sc.scheme == sema) & (sc.condition == kosul) & (sc.wm == 1)]
        neg = sc[(sc.scheme == sema) & (sc.condition == "clean") & (sc.wm == 0)]
        if poz.empty or neg.empty:
            continue
        neg_stat = neg["stat"].to_numpy(dtype=float)
        neg_max, neg_std = float(neg_stat.max()), float(neg_stat.std(ddof=1))

        # (1) global tam ayrisma
        global_ayrisma = bool(poz["stat"].min() > neg_max)

        # (2) istem-duzeyi tam ayrisma sayimi — VARSAYILMAZ, SAYILIR
        kume_ayrisan = 0
        kume_toplam = 0
        for pid, g in poz.groupby("prompt_id"):
            kume_toplam += 1
            if float(g["stat"].min()) > neg_max:
                kume_ayrisan += 1

        # (3) marj: en dusuk pozitif ile en yuksek negatif arasi, negatif SD birimi
        marj = (float(poz["stat"].min()) - neg_max) / neg_std if neg_std > 0 else float("nan")

        # (4) tam permutasyon p — istem ICINDE etiket degistirilebilirligi
        #     her istemde m pozitif + k negatif; en uc siralamanin olasiligi
        m = int(poz.groupby("prompt_id").size().median())
        k = int(neg.groupby("prompt_id").size().median())
        p_istem = 1.0 / comb(m + k, m) if (m + k) <= 60 else float("nan")
        log10_p_tam = kume_ayrisan * log10(p_istem) if p_istem == p_istem else float("nan")
        # isaret-cevirme (daha zayif varsayim: istem basina tek ikili sonuc)
        log10_p_isaret = kume_ayrisan * log10(0.5)

        satirlar.append({
            "scheme": sema, "condition": kosul,
            "auroc": float(r["auroc"]),
            "cp_geri_cekilen": float(r["ci_lo_cp"]),
            "n_kume": int(r["n_kume"]),
            "kume_ayrisan": kume_ayrisan, "kume_toplam": kume_toplam,
            "global_tam_ayrisma": global_ayrisma,
            "marj_negatif_sd": marj,
            "poz_min_stat": float(poz["stat"].min()),
            "neg_maks_stat": neg_max, "neg_std": neg_std,
            "m_poz_per_istem": m, "k_neg_per_istem": k,
            "log10_p_tam_permutasyon": log10_p_tam,
            "log10_p_isaret_cevirme": log10_p_isaret,
        })

    rap = {
        "_amac": "AUROC=1.000 hucrelerinde Clopper-Pearson yerine raporlanacak "
                 "dogrudan kanit: sayilan tam ayrisma + marj + tam permutasyon p.",
        "_cp_neden_geri_cekildi": (
            "CP sinirir bir Bernoulli oraninin alt sinirir; AUROC ikili siralama "
            "U-istatistigidir. Kume-duzeyi bir olayin olasiligi ile populasyon "
            "AUROC'u arasinda genel bir esitsizlik yoktur, dolayisiyla "
            "'zero failures in 24 clusters bounds AUROC at 0.883' turetimi "
            "gecersizdir. Ayrica 24 olay ortak negatif havuzunu paylastigi icin "
            "bagimsiz Bernoulli denemeleri de degildir."),
        "n_dejenere_hucre": len(satirlar),
        "hucreler": satirlar,
    }
    if satirlar:
        marjlar = [s["marj_negatif_sd"] for s in satirlar]
        rap["marj_min"] = float(np.min(marjlar))
        rap["marj_maks"] = float(np.max(marjlar))
        rap["hepsi_global_ayrisiyor"] = bool(all(s["global_tam_ayrisma"] for s in satirlar))
        rap["hepsi_tum_kumeler_ayrisiyor"] = bool(
            all(s["kume_ayrisan"] == s["kume_toplam"] for s in satirlar))

    yol = C.RESULTS / "dejenere_kanit.json"
    yol.write_text(json.dumps(rap, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(satirlar)} dejenere hucre\n")
    print(f"{'sema':9s} {'kosul':14s} {'ayrisan':>9s} {'marj(negSD)':>12s} "
          f"{'log10 p_tam':>12s}  CP(geri cekilen)")
    for s in satirlar:
        print(f"{s['scheme']:9s} {s['condition']:14s} "
              f"{s['kume_ayrisan']:>4d}/{s['kume_toplam']:<4d} "
              f"{s['marj_negatif_sd']:>12.2f} {s['log10_p_tam_permutasyon']:>12.1f}"
              f"  {s['cp_geri_cekilen']:.3f}")
    if satirlar:
        print(f"\nmarj araligi: [{rap['marj_min']:.2f}, {rap['marj_maks']:.2f}] negatif SD")
        print(f"hepsi global ayrisiyor: {rap['hepsi_global_ayrisiyor']}   "
              f"hepsinde TUM kumeler ayrisiyor: {rap['hepsi_tum_kumeler_ayrisiyor']}")
    print(f"\nyazildi -> {yol}")


if __name__ == "__main__":
    main()
