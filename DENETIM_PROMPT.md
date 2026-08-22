# Üçüncü-göz denetim istemi

Aşağıdaki metni bağımsız bir LLM'e (tercihen farklı bir aile: GPT-5.x, Gemini,
DeepSeek) yapıştır ve yanına §"Ekler" listesindeki dosyaları ver.

---

## İSTEM (buradan itibaren kopyala)

Sen bir bilgisayımsal dilbilim / NLP metodoloji hakemisin. Sana bir **pilot
çalışmanın** teslimatı ve ham çıktıları veriliyor. Görevin **düşmanca
metodolojik denetim**: iddiaları doğrulamak değil, **kırmaya çalışmak.**

**Bağlam.** Çalışma, LLM metin filigranlarının Türkçe'deki sağlamlığını ölçüyor
(KGW, EXP, SynthID şemaları; MarkLLM üzerinde). Bu bir *pilot* — amacı ana
çalışmanın güç analizini ve tasarımını bilgilendirmek. Hedef dergi SCI-E.
Yazarlar, önceki bir makalenin "kapsamlı" iddiası ve doğrulanmamış atıflar
yüzünden reddedilmesinden sonra, **abartısızlık ve tekrarlanabilirliği** açık
öncelik yapmış durumda.

**Ne yapmanı istiyorum**

1. Her ana iddiayı veriye karşı sına. İddia verinin taşıyabileceğinden
   fazlasını söylüyorsa göster.
2. İstatistiği denetle: test seçimi, çoklu karşılaştırma, bağımsızlık
   varsayımları, örneklem büyüklüğü, güven aralıkları.
3. Konfoundları ara. Rapor bazılarını kendisi işaretliyor — **onların yeterince
   ele alınıp alınmadığını da denetle**, ve işaretlenmemiş olanları bul.
4. "Geri çekildi" ve "geçerliliğini koruyor" kararlarını sorgula. Yazar kalite
   katmanını geri çekip tespit katmanını korudu. Bu ayrım savunulabilir mi?
5. Tekrarlanabilirlik iddialarını denetle.
6. **Bulgu üretme zorunluluğun yok.** Bir bölüm sağlamsa "sağlam" de. Uydurulmuş
   bulgu, kaçırılmış bulgudan daha zararlı.

**Yazarın kendi zayıf gördüğü noktalar — bunlara özellikle bak**

Bunları sana açıkça veriyorum ki denetim yüzeysel kalmasın. Yazarın bu
konulardaki savunmasını da yetersiz bulabilirsin:

- **TPR@%1FPR yalnız 96 negatifle hesaplanıyor.** %1'lik eşik, 96 noktanın
  ~99. yüzdebirliği — pratikte maksimuma yakın, dolayısıyla eşik tahmini çok
  gürültülü. Makalenin manşet metriği bu. Bu metrik bu örneklemle savunulabilir
  mi? Alternatif ne olmalı?
- **Yargıç deneylerinde n=15 çift**, ve binom testi çift başına 2 yargıyı
  bağımsız sayıyor (rapor bunu not ediyor ama düzeltmiyor). Doğru analiz ne
  olurdu? Sonuç yön değiştirir mi?
- **EXP konfoundu:** EXP hem en dayanıklı hem kaliteyi bozmayan şema. Rapor
  bunun tek mekanizmanın iki sonucu olabileceğini söylüyor ama ayrıştırmıyor.
  Ayrıştırılabilir mi? Ayrıştırılmadan hangi iddialar kurulamaz?
- **Kirlenme–tespit bağımsızlığı:** yazar, metrikleri yalnız kirlenmemiş
  metinlerle yeniden hesaplayıp "sapma AUROC 0,019" diyerek tespit katmanını
  koruyor. Bu test yeterli mi? Kirlenme ile filigran sinyali arasında
  raporlanmamış bir etkileşim olabilir mi (ör. yabancı-yazı token'ları
  yeşil/kırmızı liste istatistiğini nasıl etkiler)?
- **24 prompt × 4 tohum = 96.** Morfolojik saldırının "ölçülemez" ilan edilmesi
  bu örneklemle güvenli mi, yoksa güç yetersizliği mi?
- **Çoklu karşılaştırma bütün çalışma boyunca**: 10 koşul × 3 şema + yargıç
  testleri + kirlenme testleri. Rapor yer yer Bonferroni uyguluyor, yer yer
  uygulamıyor. Tutarlı mı?

**Çıktı biçimi**

Bulguları **önem sırasına göre** ver. Her bulgu için:

```
[ÖNEM: kritik | yüksek | orta | düşük]
İDDİA      : denetlenen cümle/sayı, kaynağıyla (dosya + bölüm)
SORUN      : tam olarak ne yanlış veya desteklenmemiş
KANIT      : neden böyle düşünüyorsun (veriden veya yöntemden)
ETKİ       : bu düzeltilmezse makalede ne çöker
ÖNERİ      : somut düzeltme (yeni analiz, ifade değişikliği, ek deney)
```

Sonunda ayrı üç başlık:

- **SAĞLAM BULDUKLARIM** — hangi iddialar veriyi doğru temsil ediyor
- **VERİ OLMADAN KARAR VEREMEDİKLERİM** — ne görmen gerekirdi
- **HAKEM BUNU SORAR** — bir SCI-E hakeminin soracağını düşündüğün 3-5 soru

Türkçe yanıtla.

## (istem burada bitiyor)

---

## Ekler — denetçiye verilecek dosyalar

**Zorunlu**

| dosya | ne işe yarar |
|---|---|
| `TESLIMAT.md` | ana teslimat: bulgular, geri çekilenler, kararlar |
| `results/summary.md` | koddan üretilmiş tam rapor, bütün tablolar |
| `results/detection_metrics.csv` | AUROC/GA/TPR ham tablo |
| `results/launder_comparison.csv` | yerel vs API aklama karşılaştırması |

**Şiddetle önerilen** (istatistiği kendi yeniden hesaplayabilsin diye)

| dosya | ne işe yarar |
|---|---|
| `results/scores.csv` | 6.336 satır ham skor — her iddia buradan yeniden üretilebilir |
| `results/env.json` | sürümler, tohumlar, üretim ayarları |
| `results/llm_judge_api_wmcost.json` | filigran akıcılık bedeli ham sayıları |
| `results/fertility_contrast.json` | tokenizer bereketi |

**Yöntem sorgulanacaksa**

`pilot/metrics.py` (metrikler + geri çekme kapıları), `pilot/detect.py`
(skorlama), `pilot/attacks.py` (morfolojik saldırılar + zeyrek sağlamlaştırma),
`pilot/config.py` (bütün sabitler).

---

## Uyarı

Bu dosyalar **yayımlanmamış araştırma**. Harici bir servise göndermek onu o
servise açar; bazı sağlayıcılar girdiyi eğitimde kullanabilir veya saklayabilir.
Gönderilecek dosyalarda API anahtarı yok (`.env` eklerde değil), ama karar
yazarlara ait.
