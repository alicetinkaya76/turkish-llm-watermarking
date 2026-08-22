# Teslimat — Türkçe LLM Filigran Sağlamlığı Pilotu

**Sürüm 2 (2026-08-16).** Bağımsız üçüncü-göz metodolojik denetimden sonra
revize edildi. Denetim yedi doğrulanabilir kritik bulgu getirdi; **yedisi de bu
veride yeniden üretildi ve hepsi kabul edildi.** Sürüm 1'in geri çekilen
hükümleri §0'da listelidir.

> **Sayıların kaynağı.** Bu belge sayıları TEKRAR ETMEZ; `results/summary.md`
> koddan üretilir ve tek doğru kaynaktır. Sürüm 1'in en can sıkıcı hatası elle
> kopyalanmış bir sayının (`0,019`, gerçeği `0,0247`) bayatlamasıydı — depo
> kuralı "her sayı `data/`den kodla yeniden üretilir" der ve bu ihlal edilmişti.
> Yapıyı buna kapatmak için sayılar artık yalnız üretilen raporda durur.

**Ortam:** torch 2.13.0 · transformers 5.15.0 · Python 3.11.9 · MPS (Apple M4
Max, 48 GB) · MarkLLM `c45ddc40` · üretici **Qwen2.5-3B-Instruct** · K5 MPS
yaması gerekmedi.

---

## 0. Sürüm 1'den geri çekilen / daraltılan hükümler

| sürüm 1 hükmü | durum | gerekçe (`summary.md` bölümü) |
|---|---|---|
| "Manşet metrik TPR@%1FPR olmalı" | **GERİ ÇEKİLDİ** | 96 negatifte %1 eşiği tahmin edilemiyor; saldırılı negatiflerde gerçek FPR %8'e çıkıyor → *D2* |
| "launder_api en yıkıcı saldırı, rtt'yi geçti" | **GERİ ÇEKİLDİ** | eşlenmiş McNemar'da hiçbir şemada anlamlı değil → *D3* |
| "n=96, güven aralıkları" | **DÜZELTİLDİ** | EXP'de dört tohum aynı sonucu veriyor; etkin n=24 → *D1* |
| "Kirlenme sıralamaları değiştirmiyor" | **YANLIŞ, düzeltildi** | `para` ve `launder`'da KGW↔SynthID yer değiştiriyor → *Korpus bütünlüğü* |
| "Ana çalışma ≥7B kullanmalı" | **DARALTILDI** | büyüklük deneyi hiç yapılmadı; hüküm yalnız "Qwen2.5-3B bu ayarlarla uygun değil" |
| "Parçalanma dilin değil seçimin sonucu" | **GERİ ÇEKİLDİ** | İngilizce taban 56 kelime, Türkçe 11.751 (1:209) — TR/EN cezası güvenilmez |
| Yargıç p = 0,0003 / 0,0001 | **DÜZELTİLDİ** | bağımsız birim 30 hüküm değil 15 çift; p = 0,0129 / 0,0034 |
| "Saldırgan hem siliyor hem düzeltiyor" | **GERİ ÇEKİLDİ** | kalite katmanı geçersizken "düzeldi" denemez; Latin-dışı karakterin sıfırlanması kalite ölçüsü değil |

---

## 1. Kabul kriterleri (HANDOFF §5)

Altı kriterin altısı da karşılandı; sayılar `summary.md` başında. Tek nitelendirme:
K11 "tekrarlanabilirlik" iddiası **aynı makine/sürümde KGW için 8 örneklik dar
bir yinelenebilirlik kontrolüdür**, bağımsız reproducibility değildir.

---

## 2. Savunulabilir bulgular

Aşağıdakiler denetimden sonra ayakta kalanlar. Sayılar için `summary.md`.

1. **Üç şema da temiz koşulda bu veri setinde tam ayrım yapıyor.** Bu, nüfus
   genellemesi değil, bu sabit test setine ilişkin ampirik sonuçtur.
2. **API-aklama, yerel aklamadan üç şemada da daha fazla dedektör aşınması
   üretiyor.** Bu dar iddia veriyle destekleniyor. Nedensel etiket "aklayıcı
   modelin gücü" değil, "iki aklama hattı farklı sonuç verdi" olmalıdır.
3. **Morfolojik saldırı ölçülebilir müdahale üretmedi.** Kural kalitesi sorunlu
   değil (%96 zeyrek kabul oranı); kapsam %0,36 (v0) ve %1,08 (v1). Doğru
   hüküm "morfolojik saldırılar etkisizdir" değil, **"bu uygulama bu korpusta
   test edilebilir bir müdahale üretmedi"**dir.
4. **KGW ve SynthID akıcılığı bozuyor, EXP bozmuyor** (çift düzeyinde işaret
   testi, Bonferroni sonrası ayakta). İki bağımsız ölçüt aynı yönde: yargıç ve
   Latin-dışı kirlenme oranı.
5. **Aynı Türkçe korpusta tokenizer'lar arasında bereket belirgin farklılaşıyor**
   ve sözlük büyüklüğü belirleyici değil. (TR/EN cezası iddiası geri çekildi.)
6. **`ytu-ce-cosmos/Turkish-Llama-8b-v0.1` Llama-3'ün tokenizer'ını
   değiştirmeden kullanıyor** — sözlükler yalnız 3 özel token'da ayrışıyor.
   HANDOFF §7'nin planladığı "TR-uyarlı tokenizer kontrastı" tanım gereği sıfır
   fark verirdi.
7. **Aile-içi 3B yargıç ölçüm aleti olarak kalibre değil** (konum dönmesi %84),
   bağımsız yargıç kalibre (%6). Sorun ikili protokolde değil, yargıcın
   kapasitesindeydi. *Yargıcın saldırı-içerik okumaları raporlanmıyor* — kirli
   korpusta verildiler.

---

## 3. Geri çekilen katman: kalite

Üretilen 384 metnin **%36'sı** Latin-dışı yazı sistemi içeriyor. Sebep ölçüldü,
varsayılmadı: `top_k` 0/20/50 karşılaştırmasında kirlenme oranı sabit kalıyor →
sebep örnekleme ayarı değil, model. S3 düzeltmesi yalnız şiddeti artırıyor.

Tespit katmanı geri çekilmedi; bu da ölçüldü (temiz altküme vs tam korpus).
**Ama** iki nitelendirmeyle: maksimum AUROC sapması `0,0247`'dir (sürüm 1'de
`0,019` yazıyordu) ve **bazı alt sıralamalar değişiyor**. Sapmanın küçük olması
kirlenme–filigran bağımsızlığını kanıtlamaz; seçici filtre yanlılığı taşıyabilir.

---

## 4. Ana çalışma için yapılacaklar (revize)

1. **Ölçüm noktası.** %1 FPR'yi 96 negatifle kullanmayın. Pilot ölçeğinde
   TPR@%5FPR ve FPR≤%10 kısmi-AUROC raporlayın. Ana çalışmada eşik için ayrı
   kalibrasyon seti, FPR doğrulaması için ayrı test negatifleri ve **≥1.000
   negatif** kullanın.
2. **Saldırılı negatifleri analize dahil edin.** Her koşul için üç sayı:
   temiz eşikte TPR, aynı eşikte saldırılı-negatif FPR, saldırılı
   pozitif–saldırılı negatif AUROC.
3. **Analiz birimi prompt olsun.** Prompt-kümeli bootstrap veya prompt rastgele
   kesişli karma model. EXP'de tohum tekrar üretmiyor — ya şemaya özgü
   anahtar/nonce ile bağımsızlık sağlayın ya da `n=24` raporlayın.
4. **Saldırı geçerliliği kapısı.** Filigran sağlamlığı saldırısının geçerli
   sayılması için dönüşüm anlamı/işlevi korumalı. Önce kaynak metin için dil ve
   akıcılık kapısı, sonra çıktı için semantik eşdeğerlik ve uzunluk sapması
   kapısı; ana analiz yalnız kapıyı geçen eşlenmiş çiftlerde.
5. **Şemaları eşleyin.** Aynı temiz TPR/FPR bütçesi, eşlenmiş uzunluk/EOS ve
   örnekleme entropisi olmadan "EXP daha sağlam" nedensel sonucu kurulamaz.
   Filigransız ama yoğunlaştırılmış örnekleyici kontrolü ekleyin.
6. **Üretici seçimi boyut kuralıyla değil ön-kapıyla.** Dil saflığı, akıcılık,
   görev uyumu ve tekrar oranı eşiklerini geçen herhangi bir model. En az iki
   aile ve iki boyutta küçük preflight koşun.
7. **Tokenizer karşılaştırması** alan ve uzunlukça eşlenmiş paralel TR–EN
   korpusla; encoder ve causal-decoder tabloları ayrı.
8. **Çoklu karşılaştırma.** Pilot bütünüyle keşifsel ilan edilmeli. Ana çalışma
   için birincil şema, birincil saldırı kontrastı ve birincil işletim noktası
   önceden kaydedilmeli; doğrulayıcı ailede Holm, keşifsel ailede FDR.
9. **LLM-yargıç kullanılacaksa** bağımsız ve güçlü olmalı, konum dönmesi her
   koşulda raporlanmalı, birim çift olmalı.

---

## 5. Kodda yapılanlar

`pilot/` — 21 dosya, paket kopyasıyla senkron.

**Üretim düzeltmeleri:** S3 `top_k`/`repetition_penalty` açıkça verildi ·
S4 SynthID çift sıcaklık · S5 SynthID logits-işlemci durum sızıntısı.

**zeyrek kararlılığı (K11):** analizör çok sayıda analizden sonra aynı kelime
için farklı sonuç veriyordu → `morph`, `morph_v1` ve `_lemma_set` metin sırasına
duyarlıydı. Çözüm: kanonik sıralı ısıtma + benzersiz kelime başına tek analiz.
`dev_zeyrek_check` iki kapıyla denetliyor, ikisi de geçiyor. **Kök sebep
bulunamadı**; bulunan `lru_cache` mutable-set hatası gerçek ama tek başına
gidermiyor — kodda böyle yazılı.

**Denetim yanıtı:** `metrics.audit_corrections()` D1/D2/D3 düzeltmelerini
**koddan** üretir (tohum dejenerasyonu, saldırılı-negatif FPR, eşlenmiş McNemar).
`corpus_integrity()` artık sıralama değişimlerini iddia etmek yerine sayar.

**Öz-inceleme (denetim §11'in "kod hiç gözden geçirilmedi" uyarısı üzerine).**
Denetim yanıtı olarak yazılan kod kendi kanıt standardını karşılamıyordu; dört
hata bulundu ve düzeltildi:

| hata | belirti | düzeltme |
|---|---|---|
| `Usage.cost()` bilinmeyen modelde sessizce `0.0` | fiyatı tabloda olmayan bir modelle koşulunca "ÖLÇÜLEN MALİYET $0,00" raporlanır; gerçekte on dolarlar harcanmış olabilir | `None` döner, `cost_str()` "HESAPLANAMADI" basar, JSON'a `price_table_hit` yazılır |
| Yargıç çift aritmetiği ESIT'i kayıp sayıyor | iki sırada da "eşit" denen çiftler "filigranlı kazandı" sütununa giriyordu, işaret testi p'si bozuluyordu | berabere çiftler `dec`'ten çıkarıldı, `berabere` sütunu ve `muhasebe_tutarli` denetimi eklendi |
| D1 tohum sayımı tek satırlı hücreyi "özdeş" sayıyor | `nunique()==1` tek elemanlı grupta daima doğru → kısmi üretim UYDURMA bir "tohum etkisiz" bulgusu üretebilir | `len(sub) < 2` atlanıyor |
| Üretilen metne gömülü beş sabit sayı | tablo veriden gelirken açıklama cümlesi sabit → aynı `0,019` bayatlaması sınıfı | hepsi f-string ile hesaplanıyor ya da ilgili tabloya devrediliyor |

Üçünün kök nedeni aynı: **ölçülen şeyi anlatırken sayıyı elle yazmak.** Denetim
bunu bir kez yakaladı, düzeltme yazılırken beş kez tekrarlandı. Artık rapor
metnine giren her sayı ya hesaplanır ya tabloya devredilir.

**Maliyet:** ~1.020 API çağrısı, ölçülen ~$11,00, 0 red.

---

## 6. Açık kalanlar

- **Depo commit edilmedi.** `pilot/` yukarı akış MarkLLM klonunun içinde.
- **Tekrarlanabilirlik paketi eksik** (denetim §11): kod, promptlar, ham
  metinler, satır-düzeyi kirlenme bayrakları, yargıcın ham kararları ve SHA256
  manifesti pakette yok. Denetçi bu yüzden EXP tohum davranışının tasarım mı
  hata mı olduğunu ayıramadı.
- **Gemma-2-9b** tokenizer tablosunda yok (kapılı depo).
- **7B ayağı koşulmadı**; disk 14 GiB, 7B fp16 15,2 GB.
- `results/summary_STALE_morph.md` — hatalı zeyrek davranışıyla üretilmiş eski
  özet, karşılaştırma için bırakıldı.
