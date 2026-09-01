# pilot/dev_tutarlilik_kapisi.py — GERI CEKILMIS NICELIKLER GERI SIZMASIN.
#
# NEDEN VAR. Bu makalede uc ayri cikarimsal islem geri cekildi
# (Clopper-Pearson siniri, istem-ici degistirilebilirlik permutasyonu, istem
# duzeyi isaret testi). Her turda bir onceki turun kalintisi baska bir dosyada
# hayatta kaldi: bir tur metinde duzeltildi ama numbers.json'da kaldi, bir
# baska tur §3.3'te geri cekildi ama bes yerde hala "exact permutation p-value"
# vaat ediliyordu. Insan gozu bu sizintiyi yakalayamiyor; kapi yakalar.
#
# CIKIS KODU 1 => surum alma. make_paper_numbers ve make_figures'dan SONRA kos.
#   python pilot/dev_tutarlilik_kapisi.py
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

# (desen, aciklama) — uretim ciktilarinda ve makale metninde YASAK.
YASAK_ALAN = [
    (r"\bci_lo_cp\b", "geri cekilen Clopper-Pearson AUROC alt siniri"),
    (r"\bcp_geri_cekilen\b", "geri cekilen CP siniri (eski alan adi)"),
    (r"log10_p_tam_permutasyon", "geri cekilen tam permutasyon p"),
    (r"log10_p_isaret_cevirme", "geri cekilen isaret-cevirme p"),
]
# Makale metninde YASAK ifadeler: geri cekilmis bir seyi VAAT eden cumleler.
# Geri cekmeyi ANLATAN cumleler serbest -- bu yuzden desenler dar.
YASAK_METIN = [
    (r"(?<!withdrawn )exact permutation p-value(?! rather| that| we| is withdrawn)",
     "Tablo 3 p-degeri vermiyor; metin vaat ediyor"),
    (r"and an exact p-value", "Tablo 3 p-degeri vermiyor"),
    (r"2⁻²⁴|2\^-24", "geri cekilen isaret testi degeri"),
]
# Geri cekmeyi ANLATAN baglam. Bir yasak ifade bu isaretlerden birinin
# yakininda geciyorsa mesru: makale kendi hatasini anlatiyor demektir.
# Bu liste olmadan §3.3'un durustluk paragrafi kapiyi kirar.
MESRU_BAGLAM = [
    "withdraw", "we attach no p-value", "but that is arithmetic",
    "cannot be multiplied", "earlier version", "an earlier",
    "no longer", "we do not report",
]
PENCERE = 700  # karakter


def main() -> int:
    hata = []

    # 1) uretim ciktilarinda geri cekilmis ALANLAR
    hedefler = [_ROOT / "paper" / "numbers.json",
                _ROOT / "results" / "detection_metrics.csv",
                _ROOT / "results" / "dejenere_kanit.json"]
    for yol in hedefler:
        if not yol.exists():
            continue
        g = yol.read_text(encoding="utf-8", errors="replace")
        for desen, ne in YASAK_ALAN:
            if re.search(desen, g):
                hata.append(f"{yol.relative_to(_ROOT)}: {ne} ({desen})")

    # 2) makale metninde geri cekilmis seyi VAAT eden ifadeler
    pm = _ROOT / "paper" / "paper.md"
    if pm.exists():
        g = pm.read_text(encoding="utf-8")
        dg = g.lower()
        for desen, ne in YASAK_METIN:
            for m in re.finditer(desen, g):
                yakin = dg[max(0, m.start() - PENCERE): m.end() + PENCERE]
                if any(b in yakin for b in MESRU_BAGLAM):
                    continue          # geri cekmeyi anlatiyor, mesru
                sat = g[:m.start()].count("\n") + 1
                hata.append(f"paper.md:{sat}: {ne} -> {m.group(0)!r}")

    # 3) D3: makaledeki p'ler numbers.json ile ayni mi?
    nj = _ROOT / "paper" / "numbers.json"
    if nj.exists() and pm.exists():
        n = json.loads(nj.read_text(encoding="utf-8"))
        d3 = n.get("d3_istem_duzeyi", {})
        metin = pm.read_text(encoding="utf-8")
        for sema, r in d3.items():
            p = f"{r['p_permutasyon']:.3f}"
            if p not in metin:
                hata.append(f"D3 {sema}: permutasyon p={p} makalede GECMIYOR "
                            "(numbers.json ile metin ayrismis olabilir)")
        # estimand kontrolu: ham stat uzerinde kosulmadigini dogrula
        if "ort_oran_farki" not in str(d3):
            hata.append("D3 ciktisinda 'ort_oran_farki' yok -- test tespit "
                        "orani yerine ham stat uzerinde kosuyor olabilir")

    if hata:
        print("TUTARLILIK KAPISI: BASARISIZ\n")
        for h in hata:
            print("  ✗", h)
        print(f"\n{len(hata)} sorun. Surum ALMAYIN.")
        return 1
    print("TUTARLILIK KAPISI: gecti "
          "(geri cekilmis nicelik yok, D3 p'leri metinle uyusuyor).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
