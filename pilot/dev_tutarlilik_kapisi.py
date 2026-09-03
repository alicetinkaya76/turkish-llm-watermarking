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
    # results/summary.md LISTEDE OLMALI: tur 5 denetimi onu ATLAMISTI ve dosya
    # dokuz gun boyunca GERI CEKILEN ham-stat D3 sonucunu ("Bonferroni-3
    # sonrasi anlamli: KGW") yayimlamaya devam etti -- makale EXP diyordu.
    # Depoda izlenen, surumle birlikte dagitilan bir dosyanin makaleyle
    # celismesi tam da bu kapinin var olma nedeni.
    hedefler = [_ROOT / "paper" / "numbers.json",
                _ROOT / "results" / "detection_metrics.csv",
                _ROOT / "results" / "dejenere_kanit.json",
                _ROOT / "results" / "summary.md"]
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
    # NOT: bu kontrol SATIR ICINDE arar, cunku bir p degeri makalenin baska bir
    # yerinde (baska tablo, sayfa numarasi, GA ucu) tesadufen gecebilir. Onceki
    # surum 116 KB'lik metinde ciplak alt-dizi ariyordu; uc haneli bir sayi
    # icin bu neredeyse garanti gecisti.
    nj = _ROOT / "paper" / "numbers.json"
    if nj.exists() and pm.exists():
        n = json.loads(nj.read_text(encoding="utf-8"))
        d3 = n.get("d3_istem_duzeyi", {})
        metin = pm.read_text(encoding="utf-8")
        t5 = [s for s in metin.splitlines()
              if s.startswith("| KGW |") or s.startswith("| EXP |")
              or s.startswith("| SynthID |")]
        for sema, r in d3.items():
            p = f"{r['p_permutasyon']:.3f}"
            sat = [s for s in t5 if s.startswith(f"| {sema} |")]
            if not sat:
                hata.append(f"D3 {sema}: Tablo 5 satiri BULUNAMADI")
            elif not any(p in s for s in sat):
                hata.append(f"D3 {sema}: permutasyon p={p} Tablo 5'in {sema} "
                            f"SATIRINDA gecmiyor -> {sat[0][:90]!r}")
        # estimand kontrolu: ham stat uzerinde kosulmadigini dogrula
        if "ort_oran_farki" not in str(d3):
            hata.append("D3 ciktisinda 'ort_oran_farki' yok -- test tespit "
                        "orani yerine ham stat uzerinde kosuyor olabilir")

        # 3b) TABLO 6: makaledeki satirlar numbers.json ile birebir mi?
        # Tur 5 denetimi burada gercek bir SAYI HATASI buldu: makale ilk iki
        # satira da p=0.001 basiyordu; gercek degerler 0.0003 ve 0.0012, yani
        # gercek bir siralama 3 ondalikta cokmustu. Deger sabit dosyadan
        # (results/summary.md, 9 gun bayat) elle kopyalanmisti. Kapi Tablo 6'yi
        # HIC denetlemiyordu; artik satir satir denetliyor.
        # DIKKAT: bu alan bazen satir listesi, bazen TEK bir cok-satirli metin.
        # Ilk yazimda satir listesi varsayilmisti ve kontrol SESSIZCE hicbir
        # satir bulamiyordu -- kapinin yakalamak icin yazildigi hatanin ta
        # kendisi. Once duzlestir, sonra ayikla.
        _ham = n.get("sema_karsilastirma_md", [])
        if isinstance(_ham, str):
            _ham = [_ham]
        t6md = [satir for blok in _ham for satir in str(blok).splitlines()]
        t6veri = [s for s in t6md if s.startswith("| ")
                  and not s.startswith("| kosul") and "---" not in s]
        if not t6veri:
            hata.append("Tablo 6 kontrolu: numbers.json'dan HIC veri satiri "
                        "ayiklanamadi -- kontrol sessizce bos kosuyor")
        for s in t6veri:
            h = [c.strip() for c in s.strip("|").split("|")]
            kosul, cift, ofark, _n, p, hesik = h[0], h[1], h[2], h[3], h[4], h[5]
            aday = [r for r in metin.splitlines()
                    if r.startswith(f"| {kosul} | {cift} |")]
            if not aday:
                hata.append(f"Tablo 6: '{kosul} | {cift}' satiri makalede YOK")
                continue
            r = aday[0]
            for ad, deg in (("p", p), ("holm_esik", hesik),
                            ("ort_fark", ofark.lstrip("-"))):
                if deg not in r:
                    hata.append(
                        f"Tablo 6 [{kosul} | {cift}]: {ad}={deg} makale "
                        f"satirinda gecmiyor -> {r[:100]!r}")

    # 3c) GONDERIM KITI: yukleme sirasinda okunan belge bayat sayi tasimasin.
    # Kit, paper.md'nin sha256 onekini ve sayfa/tablo sayisini yaziyor; bunlar
    # v1.7.2'de sessizce bayatladi (791af135 / "30 sayfa, 11 tablo" derken gercek
    # a4a7d26a / 29 sayfa, 10 tabloydu). Ali yuklerken bu belgeye bakiyor.
    kit = _ROOT / "paper" / "SNAPP_GONDERIM_KITI.md"
    if kit.exists() and pm.exists():
        import hashlib
        kt = kit.read_text(encoding="utf-8")
        gercek = hashlib.sha256(pm.read_bytes()).hexdigest()[:8]
        m = re.search(r"sha256 ([0-9a-f]{8})\)", kt)
        if not m:
            hata.append("kit: sha256 damgasi bulunamadi")
        elif m.group(1) != gercek:
            hata.append(f"kit: sha256 {m.group(1)} != paper.md {gercek} (kit bayat)")
        n_tbl = len(re.findall(r"^\*\*Table \d+\.\*\*", pm.read_text(encoding="utf-8"), re.M))
        m2 = re.search(r"(\d+) tablo gercek Word tablosu|(\d+) tablo gerçek Word tablosu", kt)
        if m2:
            iddia = int(m2.group(1) or m2.group(2))
            if iddia != n_tbl:
                hata.append(f"kit: '{iddia} tablo' != makaledeki {n_tbl} tablo")

    # 4) SURUM DAMGASI: gonderim dosyalari ayni surumu mu gosteriyor?
    # Tur 5 denetiminin ikinci blocker'i tam olarak buydu: paper.md v1.5.0,
    # cover_letter.md v1.4.0, title_page.md v1.2.0 diyordu. Editor hangi
    # arsivlenmis nesnenin yetkili oldugunu cikaramaz. Kapinin surum kontrolu
    # HIC yoktu; bu yuzden uc dosyada uc farkli etiket dokuz gun yasadi.
    surum_dosya = {
        "paper/paper.md": r"v(\d+\.\d+\.\d+)-paper",
        "paper/cover_letter.md": r"v(\d+\.\d+\.\d+)-paper",
        "paper/title_page.md": r"v(\d+\.\d+\.\d+)-paper",
        "paper/citation_verification.json": r"v(\d+\.\d+\.\d+)-paper",
        "CITATION.cff": r"v?(\d+\.\d+\.\d+)(?:-paper)?",
        ".zenodo.json": r"v?(\d+\.\d+\.\d+)(?:-paper)?",
    }
    bulunan: dict[str, set[str]] = {}
    for rel, desen in surum_dosya.items():
        yol = _ROOT / rel
        if not yol.exists():
            continue
        g = yol.read_text(encoding="utf-8", errors="replace")
        # gecmis surumleri ANLATAN satirlar haric (superseded listesi, denetim
        # notu): yalnizca "release tag"/"version" baglamindakiler sayilir.
        s = {m.group(1) for m in re.finditer(desen, g)}
        if s:
            bulunan[rel] = s
    if bulunan:
        # her dosyanin EN YUKSEK surumu, o dosyanin iddia ettigi surumdur
        iddia = {rel: max(s, key=lambda v: [int(x) for x in v.split(".")])
                 for rel, s in bulunan.items()}
        if len(set(iddia.values())) > 1:
            hata.append("SURUM UYUSMAZLIGI: " + ", ".join(
                f"{rel}={v}" for rel, v in sorted(iddia.items())))

    if hata:
        print("TUTARLILIK KAPISI: BASARISIZ\n")
        for h in hata:
            print("  ✗", h)
        print(f"\n{len(hata)} sorun. Surum ALMAYIN.")
        return 1
    print("TUTARLILIK KAPISI: gecti (geri cekilmis nicelik yok; Tablo 5 ve "
          "Tablo 6 satirlari numbers.json ile uyusuyor; surum damgasi tek).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
