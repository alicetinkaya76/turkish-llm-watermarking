# Cevap mektubu şablonu

## Ton kuralları

1. **Her maddeye cevap ver**, atlanan madde editörün gözüne batar.
2. **Yaptığın değişikliği göster**, "we have clarified" deme — hangi cümle, hangi
   bölüm, ne oldu.
3. **Katılmıyorsan katılma.** Bu makalenin gücü savunulabilir sınırlar çizmesi.
   Ama gerekçeyi yaz ve **kanıtı göster** (kod satırı, `audit/` dosyası, DOI).
4. **Kendini savunma anlatısına girme.** Bu makale bir tur boyunca "we say so
   rather than letting…", "the honest reading", "named honestly" gibi cümlelerden
   temizlendi. Cevap mektubunda da aynı şey: olguyu söyle, dürüstlüğünü anlatma.
5. Yeni bir sürüm çıkar ve cevap mektubunda **DOI'sini ver**. Hakem neyin
   değiştiğini kendisi görebilsin.

---

## İskelet

```
[Tarih]

Dear Professor [Editör adı],

Thank you for the reviewers' reports on LRE-D-26-XXXXX, "Watermarking Turkish
LLM Output: Detector Calibration, Scheme Fragility, and a Released Evaluation
Benchmark". The comments identified [N] issues that improved the manuscript, and
I address each below.

The revised manuscript is release v1.9.0-paper, archived at
https://doi.org/10.5281/zenodo.XXXXXXX. A diff against the submitted version is
provided as [Online Resource N / on request], so the reviewers can see every
change without re-reading the article.

[Eğer bir sonuç değiştiyse, BURADA söyle, sonuna saklama:]
One change affects a reported result: [ne, hangi tablo, eski → yeni değer, neden].

Sincerely,
Ali Çetinkaya

---

## Reviewer 1

**Comment 1.1.** [Hakemin yorumunu birebir yapıştır]

*Response.* [Ne yaptın]. Section X, page Y now reads: "[yeni cümle]".

**Comment 1.2.** [...]

*Response.* I have not made this change, and I explain why. [Gerekçe + kanıt].
[Katılmadığında bile bir şey sun: bir ölçüm, bir sınırlılık cümlesi, ya da bir
gelecek-iş maddesi.]
```

---

## Sık gereken cevaplar için kısayol

`02_CEPHANELIK.md` hazır gerekçeleri taşıyor:

| Hakem derse | Cephanelik |
|---|---|
| eşik belirsizliği yayılmıyor | §1.1 |
| Tablo 5 seçim-sonrası | §1.2 (+ `audit/pilot_20260818/`) |
| n çok küçük | §1.3 |
| çok uzun | §1.4 + `03_ACIK_ISLER.md` §3 |
| YZ kullanımı | §1.5 |
| değişebilirlik varsayımı | §1.6 |
| S2 tek kol | §1.7 (+ ~12 USD'ye koşulabilir) |
| dejenere hücrelere test yok | §1.8 |
| Türkçe iddiası ne oldu | §1.9 |

---

## Revizyonu bitirmeden önce

```bash
cd ~/Desktop/MarkLLM/MarkLLM
bash "submission/review gelince bana gel/araclar/kapi_kos.sh"
```

Kapı geçmeden sürüm alma. Sonra:

1. `pilot/make_paper_numbers.py` koştur (sayılar veriden gelsin)
2. `paper/make_docx.js` ile docx üret
3. Sürüm damgasını **altı dosyada** güncelle (kapı zaten denetliyor)
4. Etiket + GitHub release → Zenodo DOI'yi mintler
5. DOI'yi cevap mektubuna yaz
