# Üçüncü-göz denetim — TUR 2

Bu paket, birinci tur denetimden **sonra** revize edilmiş hâldir. Aşağıdaki
istemi bağımsız bir LLM'e yapıştır ve paketin tamamını ek olarak ver.

---

## İSTEM (buradan itibaren kopyala)

Sen bir bilgisayımsal dilbilim / NLP metodoloji hakemisin. Bu, aynı pilot
çalışmanın **ikinci tur denetimi**. Birinci turda yedi kritik bulgu getirildi;
yazar hepsini kendi verisinde doğruladı ve kabul etti. Şimdi **düzeltmelerin
gerçekten yapılıp yapılmadığını** ve **yeni sorunları** denetliyorsun.

**Bağlam.** Çalışma, LLM metin filigranlarının (KGW, EXP, SynthID; MarkLLM
üzerinde) Türkçe'deki sağlamlığını ölçen bir *pilot*. Hedef SCI-E. Yazarların
açık önceliği abartısızlık ve tekrarlanabilirlik.

### Bu turda pakette YENİ olan

Birinci tur "paket deneyi yeniden üretmiyor, yalnız nokta metriklerini
hesaplatıyor" demişti. Bu tur şunlar eklendi:

- `kod/` — bütün `pilot/*.py`, promptlar (`prompts_tr.json`), şema config'i,
  çözümlenmiş bağımlılık listesi
- `ham_metin/` — 384 üretim + 3.840 saldırılı metnin **tamamı** (JSONL)
- `veri/row_flags.csv` — **satır düzeyinde** kirlenme bayrakları (4.224 satır),
  uzunluk, edit/rejected sayaçları
- `veri/llm_judge*.json` — yargıç koşularının ham çıktıları
- `denetim_v1/` — birinci tur raporu ve yeniden hesaplamaların
- `MANIFEST.sha256` — bütün dosyaların özetleri

### Birinci turda kabul edilen ve düzeltildiği iddia edilen bulgular

Her birinin **gerçekten düzeltildiğini doğrula**; düzeltme yetersizse söyle.

1. **§1/§2 düşük-FPR**: "TPR@%1FPR manşet metrik" geri çekildi; `summary.md`'ye
   *D2* bölümü eklendi ve her koşul için saldırılı-negatif gerçek FPR üretiliyor.
2. **§3 tohum bağımsızlığı**: *D1* bölümü tohum dejenerasyonunu koddan sayıyor;
   EXP için etkin n=24 ilan edildi.
3. **§4 saldırı geçerliliği**: "saldırgan hem siliyor hem düzeltiyor" geri
   çekildi. **Ham metinler artık pakette** — semantik koruma iddiasının
   gerçekten kurulamayacağını (veya kurulabileceğini) sen değerlendir.
4. **§6 sıralama**: `corpus_integrity()` artık sıralama değişimini iddia etmek
   yerine **sayıyor**; maksimum sapma koddan geliyor.
5. **§7 yargıç birimi**: p-değerleri çift düzeyine indirildi (15 çift).
6. **§8 tehdit sıralaması**: *D3* bölümü eşlenmiş McNemar üretiyor; "en yıkıcı"
   manşeti geri çekildi.
7. **§9 ≥7B**: hüküm "Qwen2.5-3B bu ayarlarla uygun değil"e daraltıldı.
8. **§10 tokenizer**: TR/EN cezası ve "parçalanma dilin değil seçimin sonucu"
   iddiası geri çekildi.
9. **§12 çoklu karşılaştırma**: pilot keşifsel ilan edildi.

### Bu turda özellikle bakmanı istediğim yerler

- **Düzeltmeler yeterli mi, yoksa kozmetik mi?** Geri çekilen bir iddia başka
  bir yerde ima yoluyla duruyor olabilir.
- **Ham metinlerle §4'ü karara bağla:** RTT / paraphrase / laundering çıktıları
  anlamı koruyor mu? Kaynak metinlerin ne kadarı zaten anlamsız? Kirli kaynakla
  yapılan saldırı ölçümü kurtarılabilir mi, yoksa korpus baştan mı üretilmeli?
- **Kodla §3'ü karara bağla:** EXP'nin tohum davranışı algoritma tasarımı mı,
  uygulama hatası mı? `pilot/generate.py`, `pilot/run.py` ve MarkLLM'in EXP
  uygulaması buna izin veriyor mu?
- **Kodda başka hata var mı?** Özellikle `metrics.py` (metrik hesapları, geri
  çekme kapıları), `detect.py` (skorlama), `attacks.py` (morfolojik kurallar +
  zeyrek sağlamlaştırma).
- **`row_flags.csv` ile kirlenme–filigran etkileşimini test et.** Yazar bunu
  yalnız "temiz altküme vs tam korpus" karşılaştırmasıyla yaptı; sen satır
  düzeyinde modelleyebilirsin.
- **Yeni eklenen D1/D2/D3 bölümleri kendi içinde doğru mu?**

### Kurallar

- İddiaları veriye ve koda karşı sına; **otoriteye güvenme**.
- **Bulgu üretme zorunluluğun yok.** Bir bölüm sağlamsa "sağlam" de. Uydurulmuş
  bulgu, kaçırılmış bulgudan daha zararlı.
- Birinci turda getirilip bu turda düzeltilen bir maddeyi tekrar bulgu olarak
  yazma; yalnız **yetersiz düzeltmeleri** ve **yeni sorunları** raporla.

### Çıktı biçimi

```
[DURUM: düzeltildi | yetersiz | düzeltilmemiş]  — birinci tur maddeleri için
[ÖNEM: kritik | yüksek | orta | düşük]          — yeni bulgular için
İDDİA      : denetlenen cümle/sayı, kaynağıyla (dosya + bölüm)
SORUN      : tam olarak ne yanlış veya desteklenmemiş
KANIT      : veriden/koddan gerekçe
ETKİ       : düzeltilmezse makalede ne çöker
ÖNERİ      : somut düzeltme
```

Sonunda üç başlık: **ARTIK SAĞLAM**, **HÂLÂ AÇIK**, **HAKEM BUNU SORAR**.

Türkçe yanıtla.

## (istem burada bitiyor)

---

## Paket içeriği

```
rapor/      TESLIMAT.md (v2), summary.md (koddan üretilmiş, tek doğru kaynak)
veri/       scores.csv (6.336), row_flags.csv (4.224), detection_metrics.csv,
            launder_comparison.csv, env.json, yargıç JSON'ları, fertility
ham_metin/  gen_*.jsonl (384) + att_*.jsonl (3.840) — bütün metinler
kod/        pilot/*.py, prompts_tr.json, exp_pilot.json, requirements_resolved
denetim_v1/ birinci tur raporu + yeniden hesaplamalar
MANIFEST.sha256
```

**Uyarı:** yayımlanmamış araştırma. Harici servise göndermek onu o servise açar.
API anahtarı pakette yok (`.env` dâhil edilmedi).
