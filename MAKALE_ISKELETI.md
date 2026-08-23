# Makale İskeleti — Türkçe LLM Filigran Sağlamlığı ve Kalibrasyonu

> **Kural:** Bu iskelet SAYI İÇERMEZ. Her iddia, sayısını üreten dosyaya işaret
> eder; yazım sırasında sayılar YALNIZ o dosyalardan alınır (elle kopyalanmaz,
> mümkünse tablolar koddan üretilir). Selefi makale doğrulanamayan sayılar
> yüzünden reddedildi — bu disiplinin sebebi o.

---

## Başlık adayı

*"Watermarking Turkish LLM Output: Calibration Failure, Scheme Fragility, and
the Laundering Attack"* — üç bulgunun üçünü de taşıyor; "comprehensive" gibi
savunulamayacak sıfatlar YOK.

## 1. Giriş

- Problem: LLM filigranları İngilizce-merkezli geliştirildi; sondan eklemeli
  bir dilde davranışları ölçülmemiş.
- Katkılar (üçü de ölçülmüş, ikisi ön-kayıtlı):
  1. **Kalibrasyon bulgusu:** KGW'nin null dağılımı Türkçede teorik varsayımdan
     sapıyor; varsayılan eşik insan metninde nominalin ~63 katı yanlış pozitif
     üretiyor. → kanıt: `results_insan/insan_fpr_rapor.json` (ön-kayıt 8f8df72)
  2. **Şema kırılganlık sıralaması:** SynthID saldırı altında diğer iki şemadan
     anlamlı kırılgan; ama insan metninde en temiz null. Sağlamlık–kalibrasyon
     ödünleşimi. → kanıt: `results/summary.md` "Şemalar arası" + S1 tablosu
  3. **Aklama saldırısı:** güçlü harici modelden geçirme, anlamı koruyarak üç
     şemanın tespitini de düşüren TEK saldırı. → kanıt:
     `results/detection_metrics.csv` + `results_insan/s2_rapor.json`
     (ön-kayıt cbcb988)
- NEGATİF SONUÇ (gizlenmez, bölüm 6'da): planlanan morfolojik saldırı bu
  korpusta ateşlemedi (kapsam ~%0,3-0,6). → kanıt: `results/summary.md`
  "Morfolojik-leksik ayrışma" + `results/dz_saglamlik.json`

## 2. İlgili çalışmalar

- KGW (Kirchenbauer+), EXP (Aaronson/Kuditipudi), SynthID-Text (DeepMind) —
  MarkLLM gerçeklemeleri (commit `c45ddc40`, sabit).
- Çok dilli filigran çalışmaları; Türkçe NLP'de token bereketi literatürü.
- DİKKAT: her atıf DOI ile doğrulanacak; sürüklenen atıf selefi makalenin
  ret gerekçesiydi.

## 3. Yöntem

### 3.1 Korpus
- 24 istem × 4 tohum × {filigransız, KGW, EXP, SynthID} = 384 metin;
  Qwen3-14B, fp16, ayarlar → `results/env.json` (rejim kapısıyla mühürlü).
- İstem kalibrasyonu ŞEFFAF anlatılır: istemler 500 kelime ister çünkü model
  istenenin %72-80'ini teslim ediyor (ölçüm: `results_hpc/istem_provenans.json`);
  kabul ölçütü 300'de sabit (ön-kayıt: `hpc/README.md`).
- Kabul eşikleri ve sonuçları: `results/summary.md` manşet + "Görev uyumu".
- EXP'in sabit uzunluğu (EOS'ta durmaz) ve muafiyeti açıkça anlatılır.

### 3.2 Saldırılar
- 10 tür; launder_api = Opus 5 ile gerçek aklama (maliyet ölçülü).
- Uzunluk konfoundu savunması: saldırı/kaynak token oranları her satırda
  (`tavan`, `uzunluk_orani` alanları); para 0,997 / rtt 0,894 → "kısaltma
  artefaktı" itirazı veriyle kapalı.

### 3.3 Ölçüm
- AUROC (istem-kümeli bootstrap GA; dejenere hücrelerde Clopper-Pearson alt
  sınırı), temiz-eşikte TPR (GA'lı; adlandırma dürüstlüğü), saldırılı-negatif
  FPR (33 hücre tam tablo), aynı-dönüşüm AUROC (sağlamlık kontrolü).
- Neden istem-kümeli: EXP'in tohumları deterministik koşullarda özdeş (D1);
  çıkarım hedefi yeni istemlere genelleme.
- İnsan FPR protokolü (S1): Vikipedi dump penceresi, model=None dedektörler,
  TR + eşlenmiş EN.
- Fayda protokolü (S2): ikili yargıç, kör kalibrasyon, çıkar çatışması kırma
  (farklı aile), koşudan önce ilan edilmiş karar kuralı.

## 4. Bulgular

### 4.1 Temiz metinde tespit (tablo: detection_metrics.csv'den üretilir)
- Üç şema da temiz metinde tavana yakın; dejenere GA'lar CP alt sınırıyla.

### 4.2 Saldırı sıralaması
- launder_api > rtt > diakritik > (para, launder, morph ≈ 0).
- İstem düzeyi eşlenmiş testler: launder_api > rtt yalnız KGW'de kurulabiliyor
  (D3); şemalar arası fark: SynthID 4/6 testte anlamlı kırılgan.

### 4.3 Kalibrasyon (S1) — MANŞET
- KGW null std TR insan 1,479 / EN 1,321 / teorik 1; z=4'ün gerçek FPR'ı.
- Mekanizma önerisi: prefix_length=1 + ek alt-token tekrarı → ardışık kararlar
  bağımsız değil. (Öneri olarak sunulur; nedensel kanıt İDDİA EDİLMEZ.)
- Keşifsel (etiketli): EN null ortalaması sıfırdan kayık; EXP'in TR kuyruğu.

### 4.4 Fayda (S2)
- Hiçbir saldırı anlamı bozmuyor; launder_api üç şemada da kuralı sağlıyor.
- Akıcılık: çıkar çatışması nedeniyle yalnız bağımsız yargıç; "düşürmüyor"
  denebilir, "yükseltiyor" denemez.

## 5. Tartışma

- Pratik sonuç: varsayılan eşikler dile göre KALİBRE EDİLMELİ; Türkçe
  dağıtımda z=4 kullanılamaz.
- Sağlamlık–kalibrasyon ödünleşimi: SynthID ↔ KGW/EXP.
- Tehdit modeli: aklama ucuz ($/metin ölçülü) ve etkili; savunma açık soru.

## 6. Sınırlamalar (tam liste — kısaltılmaz)

1. TEK üretici model (Qwen3-14B); model ailesi genellemesi YOK.
2. TEK makine/GPU; tekrarlanabilirlik tek ortamda ölçüldü (drift T4).
3. Morfolojik saldırı ateşlemedi — kapsam ölçümüyle negatif sonuç; resmî
   yazım dili üreten LLM'lerde -Iyor kaydı yok. Gayriresmî korpusta açık soru.
4. EXP yapısal olarak farklı: sabit uzunluk, gen_kwargs tüketmez; şemalar
   arası KALİTE karşılaştırması bu farkla konfoundlu.
5. S1 tek register (ansiklopedi); n=1500 → %1 FPR GA ~±0,5 puan, %0,1
   iddiası İÇİN YETERSİZ (yalnız büyüklük sırası).
6. launder_api kapalı modelle (Opus 5) yapıldı; sürüm değişebilir. Ham
   çıktılar depoda → aynı metinler yeniden skorlanabilir; aynı saldırı
   yeniden üretilemeyebilir.
7. Kabul eşiklerinden 0,90/0,05 dışsal gerekçesiz (veri öncesi sabit ama
   duyarlılık analizi yok).
8. KGW etkin gamma sapması −0,000882 (len(tok) ≠ vocab_size).
9. 2/96 KGW ve 2/96 SynthID metni 1800 tavanına dayandı (kesik).
10. attn_implementation ilk koşuda transformers varsayılanına düştü (fiilen
    sdpa; seçim bizim değildi — provenans notu `hpc/config_cuda.py`).
11. Kirlenme-şema ilişkisi (KGW/SynthID ~4× vs EXP 0) POST-HOC; tekrarlama
    hipotezi olarak kayıtlı, bulgu değil.

## 7. Tekrarlanabilirlik beyanı

- Kod + korpus + skorlar tek depoda; her rapor sayısı `pilot/metrics.py`
  tarafından veriden üretilir; rejim kapısı yanlış config'le rapor üretimini
  engeller; kaynak içerik özeti iki ortamın aynı kodu koştuğunu kanıtlar.
- İnsan korpusu pageid + dump sürümüyle yeniden çekilebilir.
- Ön-kayıtlar commit'lerle mühürlü: eşikler (Faz 1 öncesi), S1 (8f8df72),
  S2 (cbcb988).

---

## Yazım sırası önerisi

1. Bulgular 4.3 (S1) — en güçlü, en yeni katkı
2. 4.2 + 4.4 birlikte (saldırı + fayda tek hikâye)
3. Yöntem (zaten belgelenmiş, özetlenecek)
4. Sınırlamalar (listeden düzyazıya)
5. Giriş/ilgili çalışmalar en son (atıf doğrulama turuyla birlikte)
