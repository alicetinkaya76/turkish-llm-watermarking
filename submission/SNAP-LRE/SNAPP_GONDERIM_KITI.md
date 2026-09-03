# SNAPP gönderim kiti — LRE

Portal: **submission.springernature.com** (Springer Nature SNAPP).
Editorial Manager DEĞİL — LRE SNAPP'e taşınmış.
Sekmeler: **Files → Details → Authors → Declarations → Review**

Kaynak: `paper/paper.md` (v1.7.2-paper, sha256 791af135). Gönderim paketi: `submission/SNAP-LRE/`.

---

## 1. Files sekmesi

**Upload manuscript → `submission/SNAP-LRE/paper.docx`**

SNAPP "tek düzenlenebilir dosya, şekiller ve tablolar metnin içinde" istiyor.
`paper.docx` tam olarak bu: 30 sayfa, 11 tablo gerçek Word tablosu, 3 şekil
gövdeye gömülü. Ek işlem gerekmiyor.

**Figures and tables (optional) → ATLA.**
Ekranda "ilk gönderimde ayrı yüklemek zorunda değilsiniz" yazıyor. Kabul
edilirse yüksek çözünürlüklü asılları isteyecekler. Şekil dosya adları makale
numaralarıyla eşleşmiyor, o yüzden **o aşamaya gelince** şu eşlemeyi kullan:

| Makalede | Dosya (LRE adlandırması, `submission/SNAP-LRE/figures/`) | Kaynak |
|---|---|---|
| Figure 1 | `Fig1.png` | `paper/figs/fig2_auroc_attacks.png` |
| Figure 2 | `Fig2.png` | `paper/figs/fig3_tradeoff.png` |
| Figure 3 | `Fig3.png` | `paper/figs/fig1_null_distributions.png` |

**Supplementary material (optional) → ATLA.**
Her şey zaten Zenodo'da ve makale onu adres gösteriyor. Aynı malzemeyi
buraya da yüklemek iki ayrı "kayıt" yaratır ve hangisinin yetkili olduğu
belirsizleşir — bu turda tam olarak bu hatayı temizledik.

**Title page ayrı slot YOK.** SNAPP yazar bilgisini *Authors* sekmesinden
alıyor ve `paper.docx` zaten sorumlu yazar bloğunu taşıyor (LRE tek-kör, yazar
adı metinde kalabilir). `title_page.docx` elinin altında dursun ama muhtemelen
gerekmeyecek.

---

## 2. Details sekmesi

⚠️ **SNAPP başlığı ve özeti .docx'ten OTOMATİK ÇIKARIYOR** ("We'll try to fill
in or update some form fields by extracting the information"). Otomatik
çıkarım özeti kırpabilir, başlığa altbilgi karıştırabilir.
**Her alanı aşağıdakiyle KARŞILAŞTIR, farklıysa üzerine yaz.**

**Title**
```
Watermarking Turkish LLM Output: Detector Calibration, Scheme Fragility, and a Released Evaluation Benchmark
```

**Article type:** Original Paper / Research Article

**Abstract** (249 kelime, LRE sınırı 150–250)
```
Statistical watermarks for large language model (LLM) output are evaluated predominantly on English. We measure three schemes (KGW, EXP, SynthID) on Turkish with MarkLLM and Qwen3-14B: 384 generated texts under ten removal attacks, a pre-registered false-positive study on 4,000 windows of human-written encyclopedic and older literary prose, and a two-judge meaning-preservation study. First, KGW's detector is miscalibrated on that human text: its null standard deviation is 1.479 against a theoretical 1, and the shipped z = 4 threshold gives 3 exceedances in 1,500 windows, about 63 times nominal (exact interval 13 to 184). The inflation holds across eight keys though the tail count does not (3 to 143), and it is not Turkish-specific: English shows the same tail count, and at matched token length we detect no difference. Turkish increases exposure to the same failure. Its subword fertility doubles the tokens a given reading length becomes, and inflation grows with tokens scored. Second, the detector flagging the fewest human windows is the most fragile: at its shipped threshold SynthID flags none of 1,500 against KGW's 3 and EXP's 13, yet loses the most area under the receiver operating characteristic curve (AUROC) under attack. With three schemes this is an observed pattern, not a trade-off. Third, laundering through an external LLM is the only attack degrading detection for all three schemes while LLM judges rated meaning preserved, though only KGW-arm pairs were judged. A planned morphological attack did not fire. We report its coverage and release corpus, scores and annotations.
```

**Keywords** (6 — her biri ayrı kutuya)
```
LLM watermarking
Turkish
detector calibration
false-positive rate
subword fertility
evaluation benchmark
```

**Cover letter** kutusu burada ya da Declarations'ta çıkar →
`submission/SNAP-LRE/cover_letter.md` içeriğini yapıştır. Üç paralel gönderimi
(TALLIP-26-0165, NLP-2026-0191, IPM) ve uzunluk gerekçesini beyan ediyor,
**silme.**

---

## 3. Authors sekmesi

Tek yazar, corresponding author = sen. Ortak yazar EKLEME.

| Alan | Değer |
|---|---|
| First name | Ali |
| Last name | Çetinkaya |
| E-mail | ali.cetinkaya@selcuk.edu.tr |
| ORCID | 0000-0002-7747-6854 |
| Institution | Selçuk University |
| Department | Department of Computer Engineering, Faculty of Technology |
| Address | Alaeddin Keykubat Campus, 42075 Selçuklu, Konya, Türkiye |
| Country | Türkiye |
| Phone | +90 332 241 11 02 |

---

## 4. Declarations sekmesi

**Springer yalnızca ARAYÜZDEN gireni yayımlıyor** — makaledeki metin tek
başına saymıyor. Hepsini buraya da gir.

**Funding** — fon YOK. Funder Registry açılırsa "no funding received" seç.
```
No funds, grants, or other support were received during the preparation of this manuscript.
```
⚠️ Bölüm/kurum kaynağı YAZMA — makale "fon alınmadı" diyor, çelişir. HPC
erişimi Acknowledgments'ta teşekkür, fon değil.

**Competing interests**
```
The author has no competing interests to declare. Three transparency items are set out in full in the manuscript: purchased API services, a declared and mitigated structural conflict inside the S2 judging design, and the fork relationship to the evaluated toolkit.
```

**Ethics approval**
```
Not required. The study involves no human participants, no animals and no personal data. The LLM judges are measurement instruments, not participants.
```

**Consent to participate / Consent to publish**
```
Not applicable.
```

**Data availability**
```
Openly available at https://github.com/alicetinkaya76/turkish-llm-watermarking, release tag v1.7.2-paper, archived at Zenodo under the concept DOI 10.5281/zenodo.22168552, which resolves to the most recent archived version. Licensing is not uniform across components; see DATA_LICENSE.md.
```

**Author contributions**
```
Ali Çetinkaya is the sole author and performed all aspects of the work: conceptualization, methodology, software, validation, formal analysis, investigation, resources, data curation, writing (original draft and review/editing), visualization and project administration.
```

**Generative AI use** (sorarsa)
```
Generative AI was used in three distinct roles: as the attack instrument under study, as the two judges of Study S2 (both documented in Methods), and as a coding and drafting assistant. No AI system is an author. The author takes sole responsibility for the content.
```

---

## 5. Review sekmesi

Oluşan PDF'i **aç ve gözden geçir**, sonra gönder. Özellikle bak:

- Otomatik çıkarılan özet tam mı, kırpılmış mı
- Tablo 5 ve Tablo 6 bozulmadan geçmiş mi (bu turda ikisini de düzelttik)
- Türkçe karakterler (Çetinkaya, Selçuk, Türkiye) doğru mu
- Şekiller gövdede yerinde mi

Gönderdikten sonra bir manuscript numarası gelmeli.

---

## Son kontrol

- [ ] `paper.docx` yüklendi (tek dosya, şekiller gömülü)
- [ ] Details'teki otomatik çıkarım kontrol edildi, gerekirse üzerine yazıldı
- [ ] Declarations'ın hepsi arayüzden girildi
- [ ] Funding = "no funding" (kurum kaynağı YAZILMADI)
- [ ] Kapak mektubu yapıştırıldı, paralel gönderimler beyanı duruyor
- [ ] **Zenodo access_token döndürüldü** (oturum dökümüne sızmıştı)
- [ ] Depo herkese açık, `v1.7.2-paper` etiketi ve sürüm DOI'si 10.5281/zenodo.22275847 görünüyor
