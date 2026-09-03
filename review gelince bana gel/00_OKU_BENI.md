# Review geldiğinde buradan başla

**Makale:** Watermarking Turkish LLM Output: Detector Calibration, Scheme Fragility,
and a Released Evaluation Benchmark
**Dergi:** Language Resources and Evaluation (Springer, SNAPP portalı)
**Gönderim:** 4 Eylül 2026, Technical Check aşamasında
**Gönderilen sürüm:** `v1.8.1-paper` · commit `250ab6e` · `paper.md` sha256 `70f2253594575ea2`

---

## Claude'a ne söyleyeceksin

Yeni bir oturum aç ve şunu yaz:

> LRE'den karar geldi. `~/Desktop/MarkLLM/MarkLLM/review gelince bana gel/`
> klasörünü oku, sonra hakem raporunu vereceğim.

Claude bu klasörü okuyunca ne gönderildiğini, hangi iddiaların nasıl savunulacağını
ve hangi işlerin hazırda beklediğini bilir. Karar mektubunu ve hakem raporlarını
olduğu gibi yapıştır.

---

## Klasörde ne var

| dosya | ne işe yarar |
|---|---|
| `01_GONDERIM_KUNYESI.md` | Ne gönderildi: sürüm, DOI zinciri, dosyalar, sayılar. Revizyonda "neyi değiştirdim" demek için taban. |
| `02_CEPHANELIK.md` | **En değerli dosya.** Beş denetim turunda çürütülen hakem iddiaları ve bilinçli seçimlerin gerekçeleri. Bir hakem bunlardan birini yazarsa cevap hazır. |
| `03_ACIK_ISLER.md` | Revizyonda yapılabilecekler: S2 uzantısı (~$12, kod hazır), uzunluk kısaltma sırası, Zenodo lisans düzeltmesi. |
| `04_CEVAP_MEKTUBU_SABLONU.md` | Point-by-point cevap formatı + ton kuralları. |
| `05_DERGI_VE_PORTAL.md` | Portal (SNAPP, Editorial Manager DEĞİL), gönderim durumu, dergi künyesi (JIF 2.0, SCIE/Q3), kılavuz kısıtları, editör iletişimi, SNAPP'in üç tuzağı. |
| `gonderilen/` | Gönderilen setin **donmuş kopyası**. Depo ilerlese de bu değişmez. |
| `araclar/` | `revizyon_baslat.sh`, `diff_uret.py`, `kapi_kos.sh` |

---

## Karar tipine göre ilk adım

**Reject.** Cephaneliği aç, red gerekçesini oradaki maddelerle karşılaştır. Gerekçe
zaten çürütülmüş bir iddiaysa (bkz. §2.1, §2.2) o dergiye itiraz etmek yerine
sıradaki dergiye geçmek genellikle daha hızlı. Aday sıralaması `03_ACIK_ISLER.md`
sonunda.

**Major/Minor revision.** `araclar/revizyon_baslat.sh` koştur: yeni dal açar,
sürümü artırır, gönderilen hâli referans olarak sabitler. Sonra madde madde çalış.
Her değişiklikten sonra `araclar/kapi_kos.sh` — tutarlılık kapısı ve sayaçlar.

**Accept.** Prova aşamasında **tek bir şeye dikkat et**: Springer'ın yapısal
"competing interests: none" beyanı, makale gövdesindeki §Competing interests
paragrafının yerine geçerse Claude Opus 5'in çifte rolü (hem `launder_api` üreticisi
hem yargıç) ifşası kaybolur. Provada o paragrafın durduğunu doğrula; yoksa dizgi
editöründen geri koymasını iste.

---

## Değişmez kurallar

1. **Sayı elle yazılmaz.** Her rakam `pilot/make_paper_numbers.py` → `paper/numbers.json`
   üzerinden gelir. Makale tablosuna elle sayı girmek bu projede iki kez gerçek
   hataya yol açtı.
2. **Her düzeltmeden sonra kapıyı koştur.** `pilot/dev_tutarlilik_kapisi.py`
   geri çekilmiş nicelikleri, Tablo 5–6 hücrelerini, sürüm damgasını ve gönderim
   kitini denetler. Negatif kontrolle sınandı.
3. **Metni değiştirdiysen yeni sürüm çıkar.** DOI'li bir sürümü yayımladıktan sonra
   makaleyi düzenlemek, DOI'nin yanlış şeyi göstermesi demek. Kavram DOI'si
   (`10.5281/zenodo.22168552`) hep en sona çözer, kaynakça onu gösteriyor.
4. **Yazım:** İngiliz + Oxford `-ize` (behaviour, analysed, artefact, defence,
   labelled; ama organization, tokenization, realized).
5. **Noktalama:** em dash yok, düzyazıda noktalı virgül yok. Tek istisna APA
   atıflarının içi.

---

## Bilinmesi gereken bağlam

- LRE, 9 Nisan 2026'da Ali'nin başka bir makalesini reddetti ("Automated
  Classification of Ottoman Court Records"). Gerekçe bilinmiyor. Aynı editör
  düşerse bu bir faktör olabilir; bir hakem raporunu okurken akılda tutulmalı ama
  cevap mektubunda **asla anılmaz**.
- Üç paralel gönderim kapak mektubunda beyan edildi: TALLIP-26-0165,
  NLP-2026-0191, IPM (numara istek üzerine). Bir hakem çakışma sorarsa cevap
  kapak mektubunda hazır: ortak korpus, veri, metin veya çözümleme yok.
- Makale 29 sayfa; LRE kılavuzu "tipik 18–25" diyor. Kapak mektubunda gerekçe ve
  **taşıma sırası** yazılı. Editör kısaltma isterse o sırayı izle
  (`03_ACIK_ISLER.md` §3).
