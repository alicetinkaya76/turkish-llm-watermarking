# Gönderim künyesi

Bu dosya, LRE'ye 4 Eylül 2026'da gönderilen hâlin kaydıdır. Revizyonda "ne
değişti" sorusunun tabanı budur. Depo ilerlese de bu dosya değişmez.

## Kimlik

| | |
|---|---|
| Git etiketi | `v1.8.1-paper` |
| Commit | `250ab6e` (dal `turkce-filigran-faz2`) |
| `paper.md` sha256 | `70f2253594575ea2…` |
| `paper.docx` sha256 | `f8df293af54a233b…` |
| Depo | https://github.com/alicetinkaya76/turkish-llm-watermarking |
| Kavram DOI | 10.5281/zenodo.22168552 (kaynakça bunu gösterir, hep en sona çözer) |
| Sürüm DOI | 10.5281/zenodo.22287518 |

## Gönderilen dosyalar (SNAPP)

| Slot | Dosya |
|---|---|
| Manuscript | `paper.docx` — 29 sayfa, Times New Roman 10 pt, otomatik sayfa numarası |
| Figures | `Fig1.png`, `Fig2.png`, `Fig3.png` (makale numaralarıyla eşleşir) |
| Supplementary | `ESM_1.pdf` — Online Resource 1, Tablo S1 (33 hücrelik gerçekleşen FPR tablosu) |
| Cover letter | `cover_letter.docx` |

Donmuş kopyaları: `gonderilen/`

## Makalenin ölçüleri

| | |
|---|---|
| Sayfa | 29 (LRE kılavuzu "tipik 18–25") |
| Özet | 249 kelime (sınır 150–250) |
| Anahtar sözcük | 6 (sınır 4–6) |
| Kaynak | 43, hepsi atıflı, iki yönde de yetim yok |
| Tablo | 10 (gövdede) + Tablo S1 (Online Resource 1) |
| Şekil | 3 |
| Başlık derinliği | ≤3 düzey, ondalık |
| Em dash | 0 · Düzyazı noktalı virgül | 1 (APA iç içe parantez, meşru) |

## SNAPP formuna girilen beyanlar

Springer **yalnızca arayüzden gireni** yayımlıyor. Girilenler:

- **Publishing policy:** kabul edildi (hibrit; rota kabulde seçilecek, fon yok)
- **Competing interests:** "No" (çıplak). ⚠️ Serbest metin kutusu çıkmadı —
  üç şeffaflık maddesi yalnızca makale gövdesinde. Bkz. `00_OKU_BENI.md` "Accept".
- **Dual publication:** No
- **Third party material:** No (üç şekil de kendi üretimimiz; Wikimedia metinleri
  veri kümesinde, makale gövdesinde alıntı yok)
- **Data availability:** Yes + üç paragraflık tam beyan (erişim, içerik+ön-kayıt,
  lisans tekdüze değil)
- **Acknowledgements:** üç paragraf (HPC tesisi, MarkLLM geliştiricileri,
  Wikimedia katkıcıları — sonuncusu CC BY-SA atfının parçası)
- **Research funding:** No
- **Preprint (Research Square):** No — öncelik zaten Zenodo depoziti ile kurulu,
  ve CC-BY dondurulmuş bir kopya senkron riski
- **Peer review:** Single anonymous

## Sürüm zinciri

Onu superseded, biri güncel. Hiçbiri silinmedi: bir DOI sessizce başka bir şeyi
göstermemeli.

| Sürüm | DOI | Tarih |
|---|---|---|
| **1.8.1** | **22287518** | **3 Eyl — GÖNDERİLEN** |
| 1.8.0 | 22283192 | 3 Eyl |
| 1.7.2 | 22275847 | 3 Eyl |
| 1.7.1 | 22273963 | 3 Eyl |
| 1.7.0 | 22271924 | 3 Eyl |
| 1.6.0 | 22255372 | 2 Eyl |
| 1.5.0 | 22249519 | 2 Eyl |
| 1.4.0 | 22231200 | 1 Eyl |
| 1.3.0 | 22230948 | 1 Eyl |
| 1.2.0 | 22212071 | 31 Ağu |
| 1.1.0 | 22168553 | 30 Ağu |

Makalenin Veri Erişilebilirliği bölümü onunu da adıyla anıyor ve neyin
değiştiğini söylüyor.

## Üç manşet bulgu

1. **Kalibrasyon hatası.** KGW'nin null standart sapması insan Türkçesinde 1.479
   (teorik 1); sevk edilen z = 4 eşiği 1.500 pencerede 3 aşım veriyor, nominalin
   ~63 katı (kesin aralık 13×–184×). Sekiz anahtarda da şişme var, kuyruk sayısı
   değişiyor (3–143), yani manşet en muhafazakâr okuma.
2. **En az yanlış-pozitif veren dedektör en kırılgan.** SynthID kendi eşiğinde
   1.500 insan penceresinin hiçbirini işaretlemiyor (KGW 3, EXP 13) ama saldırı
   altında en çok AUROC kaybediyor. Üç şemayla bu gözlenen bir örüntü, ödünleşim
   değil.
3. **Harici LLM ile aklama**, üç şemada da tespiti düşüren ve yargıçların anlamı
   korunmuş bulduğu tek saldırı. Ölçülen üretim maliyeti 17,704 USD.

**Negatif sonuç dürüstçe raporlandı:** planlanan morfolojik saldırı ateşlemedi
(metin başına 1,1 düzenleme, metinlerin %60,4'ü değişmemiş, ΔAUROC 0,000). Ve
ön-kayıtlı H2 (şişmenin Türkçeye özgü olduğu) sonradan eklenen uzunluk kontrolünü
**geçemedi** — makale bunu geri çekiyor, gizlemiyor.
