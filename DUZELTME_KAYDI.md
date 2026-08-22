# Düzeltme kaydı — tur 1 denetiminden sonra ne değişti

Bu dosya, birinci tur denetiminden sonra yapılan değişikliklerin tam listesidir.
Denetçinin "düzeltildi mi, kozmetik mi" sorusunu doğrulayabilmesi için her madde
**hangi dosyada ve hangi fonksiyonda** karşılığı olduğunu söyler.

## A. Denetim bulgularına yanıt (7 madde, hepsi kabul edildi)

| denetim | ne yapıldı | nerede |
|---|---|---|
| §1, §2 düşük-FPR | "TPR@%1FPR manşet metrik" geri çekildi; her koşul için saldırılı-negatif GERÇEK FPR koddan üretiliyor | `metrics.audit_corrections()` → D2 |
| §3 tohum bağımsızlığı | tohum dejenerasyonu koddan sayılıyor; etkin n ilan ediliyor | `metrics.audit_corrections()` → D1 |
| §4 saldırı geçerliliği | "saldırgan hem siliyor hem düzeltiyor" geri çekildi; ham metinler pakete eklendi | `TESLIMAT.md` §0, `ham_metin/` |
| §6 sıralama | sıralama değişimi iddia edilmiyor, **sayılıyor**; maksimum sapma koddan | `metrics.corpus_integrity()` |
| §7 yargıç birimi | p-değerleri çift düzeyine indirildi | `metrics._phase3_sections()` |
| §8 tehdit sıralaması | eşlenmiş McNemar üretiliyor; "en yıkıcı" manşeti geri çekildi | `metrics.audit_corrections()` → D3 |
| §9 ≥7B | hüküm daraltıldı | `metrics.corpus_integrity()`, `TESLIMAT.md` §4.6 |
| §10 tokenizer | TR/EN cezası ve nedensellik iddiası geri çekildi | `metrics._phase3_sections()` |
| §11 tekrarlanabilirlik | kod, promptlar, ham metinler, satır bayrakları, manifest eklendi | bu paket |
| §12 çoklu karşılaştırma | pilot keşifsel ilan edildi | `TESLIMAT.md` §4.8 |

## B. Öz-inceleme: denetim yanıtı kodunda bulunan 4 hata

Denetim §11 "kod hiç bağımsız gözden geçirilmedi" diyordu. Kod incelemesi
yapıldı ve **denetime yanıt olarak yazılan kodda** dört hata bulundu:

1. **`Usage.cost()` bilinmeyen modelde sessizce `0.0` dönüyordu**
   (`kod/dev_llm_judge_api.py`). `PRICES` tablosunda olmayan bir modelle
   koşulunca "ÖLÇÜLEN MALİYET $0,00" raporlanıyordu — canlı doğrulandı
   (1M+1M token → $0.00). Artık `None` döner ve "HESAPLANAMADI" basılır;
   JSON'a `price_table_hit` bayrağı yazılır. *Bu oturumdaki bütün maliyet
   rakamları doğrudur (hep `claude-opus-5` kullanıldı), ama koruma yoktu.*

2. **Yargıç çift aritmetiği ESIT hükümlerini "filigranlı kazandı" sayıyordu**
   (`kod/metrics.py`, `_phase3_sections`). İki sırada da "eşit" denen çiftler
   `dec`'te kalıp `filigranli` sütununa yazılıyordu. Bu koşuda `esit=0` olduğu
   için tetiklenmedi, ama şema ESIT'e izin veriyor. Artık berabere çiftler
   testten çıkarılıyor; `berabere` sütunu ve `muhasebe_tutarli` denetimi var.

3. **D1 tohum sayımı tek satırlı hücreyi "özdeş" sayıyordu**
   (`kod/metrics.py`, `audit_corrections`). `nunique()==1` tek elemanlı grupta
   daima doğrudur; kısmi üretim (kesilen resume, red alıp atlanan satır,
   `--attacks` alt kümesi) sayacı şişirip **uydurma bir KRİTİK bulgu**
   üretebilirdi. `len(sub) < 2` artık atlanıyor.

4. **Üretilen rapor metnine gömülü beş sabit sayı** (`kod/metrics.py`).
   Denetimin yakaladığı `0,019` bayatlamasının aynı sınıfı: tablo veriden
   gelirken açıklama cümlesi sabitti. Hepsi f-string ile hesaplanıyor ya da
   ilgili tabloya devrediliyor.

**Kök neden (3 ve 4 ortak):** ölçülen şeyi anlatırken sayıyı elle yazmak.
Denetim bunu bir kez yakaladı; düzeltme yazılırken beş kez tekrarlandı.

## C. Değişmeyenler

Ham veri (`veri/scores.csv`, `ham_metin/`) **değişmedi** — hiçbir deney yeniden
koşulmadı. Değişen yalnız analiz kodu ve rapor metnidir. Nokta metrikler
(AUROC/TPR) aynıdır; yargıç p-değerleri düzeltilmiş birimle yeniden hesaplandı
(`0,0003 → 0,0129` ve `0,0001 → 0,0034`; yön korunuyor).
