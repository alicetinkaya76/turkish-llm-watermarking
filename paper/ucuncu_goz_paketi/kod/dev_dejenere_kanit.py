# pilot/dev_dejenere_kanit.py — AUROC = 1.000 hucreleri icin BETIMSEL kanit.
#
# UCUNCU CIKARIMSAL DENEME DE GERI CEKILDI. Bu dosyanin gecmisi, makalede
# raporlanmamasi gereken seyin kaydidir; uretim ciktisina hicbiri girmez:
#
#   (i)   Clopper-Pearson alt siniri (alpha^(1/n) = 0,883). Gecersiz: CP bir
#         Bernoulli oraninin parametresini sinirlar, AUROC ise ikili siralama
#         U-istatistigidir (Bamber ozdesligi). Kume-duzeyi bir olayin
#         olasiligi ile populasyon AUROC'u arasinda genel esitsizlik YOKTUR.
#   (ii)  Istem-ICI etiket degistirilebilirligi permutasyonu (10^-44,3).
#         Gecersiz: EXP'in dort tohumu deterministiktir, degistirilebilirlik
#         savunulamaz.
#   (iii) Istem-duzeyi isaret testi (2^-24). Gecersiz: istem basina 0,5
#         basari olasiligi TASARIMDAN turetilmiyor ve 24 sonucun hepsi AYNI
#         veri-bagimli karsilastiriciyi (havuzlanmis negatiflerin maksimumu)
#         kullandigi icin ortak rastlantisal bilesen tasiyorlar; carpilamazlar.
#         Bagimlilik pozitif oldugundan carpim gercek olasiligi KUCUK gosterir.
#
# URETIMDE KALAN, YALNIZCA BETIMSEL:
#   (1) TAM AYRISMA: her istem kumesinde (ve global olarak) en dusuk
#       filigranli skor, tum temiz negatiflerin maksimumunu asiyor mu?
#   (2) MARJ: bu ayrismanin genisligi, negatif dagilimin standart sapmasi
#       biriminde. "1.000" un ne kadar rahat kazanildigini gosterir ve
#       semalar arasinda DURUSTCE ayrisir (EXP'in marji KGW'ninkinin
#       onlarca kati; ikisini ayni guvenle sunmak yaniltici olurdu).
#
# Gecerli bir test, degistirilebilirligi SAVUNULABILIR bir birimde etiket
# permute etmeli ve karsilastiriciyi her permutasyonda YENIDEN hesaplamalidir.
# Boyle bir test kosulmadi; savunulamayan bir p yerine guclu bir betimleme
# tercih edildi. Ayrinti: paper.md §3.3.
#
# CIKTI: results/dejenere_kanit.json
#   python pilot/dev_dejenere_kanit.py
from __future__ import annotations

import json
import sys
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

    # dejenere hucreler: metrics.py'nin kendi bayragi
    dejenere = det[det["dejenere"].astype(bool)][["scheme", "condition",
                                                  "auroc", "n_kume"]]
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

        satirlar.append({
            "scheme": sema, "condition": kosul,
            "auroc": float(r["auroc"]),
            "n_kume": int(r["n_kume"]),
            "kume_ayrisan": kume_ayrisan, "kume_toplam": kume_toplam,
            "global_tam_ayrisma": global_ayrisma,
            "marj_negatif_sd": marj,
            "poz_min_stat": float(poz["stat"].min()),
            "neg_maks_stat": neg_max, "neg_std": neg_std,
        })

    rap = {
        "_amac": "AUROC=1.000 hucrelerinde raporlanacak BETIMSEL kanit: "
                 "sayilan tam ayrisma + marj. p-degeri ve guven siniri YOK.",
        "_neden_p_yok": (
            "Uc cikarimsal deneme de geri cekildi: (i) Clopper-Pearson alt "
            "siniri -- CP bir Bernoulli oraninin parametresini sinirlar, AUROC "
            "ise ikili siralama U-istatistigidir; (ii) istem-ici "
            "degistirilebilirlik permutasyonu -- EXP'in dort tohumu "
            "deterministik oldugu icin degistirilebilirlik savunulamaz; "
            "(iii) istem-duzeyi isaret testi -- 0,5 null'u tasarimdan "
            "turetilmiyor ve 24 sonuc ayni veri-bagimli karsilastiriciyi "
            "paylastigi icin carpilamaz. Gecerli bir test degistirilebilirligi "
            "savunulabilir bir birimde permute etmeli ve karsilastiriciyi her "
            "permutasyonda yeniden hesaplamalidir; kosulmadi."),
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
          f"{'global':>8s}")
    for s in satirlar:
        print(f"{s['scheme']:9s} {s['condition']:14s} "
              f"{s['kume_ayrisan']:>4d}/{s['kume_toplam']:<4d} "
              f"{s['marj_negatif_sd']:>12.2f} "
              f"{('evet' if s['global_tam_ayrisma'] else 'hayir'):>8s}")
    if satirlar:
        print(f"\nmarj araligi: [{rap['marj_min']:.2f}, {rap['marj_maks']:.2f}] negatif SD")
        print(f"hepsi global ayrisiyor: {rap['hepsi_global_ayrisiyor']}   "
              f"hepsinde TUM kumeler ayrisiyor: {rap['hepsi_tum_kumeler_ayrisiyor']}")
    print(f"\nyazildi -> {yol}")


if __name__ == "__main__":
    main()
