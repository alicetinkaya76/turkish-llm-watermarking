# Pilot Özeti — Türkçe LLM Filigran Sağlamlığı

> ⛔ **KORPUS GEÇERSİZ.** Hiçbir metin istemdeki kelime hedefine ulaşmıyor ve %96'sı cümle ortasında kesik (bkz. *Görev uyumu*). Aşağıdaki bütün sayılar bu korpus üzerinde ölçülmüştür ve ana bulgu olarak kullanılamaz.

## Go / No-Go
- **Öncül (KGW temiz AUROC ≥ 0.9):** GEÇTİ (1.000)
- **TR-saldırılar ΔAUROC (KGW):** dia100=0.015, morph(v0)=0.000, morph_v1=0.000, morph+dia=0.015, rtt=0.084
- **Morfolojik ≠ leksik (morph):** ÖLÇÜLEMEDİ — metin yalnız %0.2 değişti; J=0.999 saldırının leksik korumasını değil, etkisizliğini yansıtıyor
- **Morfolojik ≠ leksik (morph_v1):** ÖLÇÜLEMEDİ — metin yalnız %0.4 değişti; J=0.999 saldırının leksik korumasını değil, etkisizliğini yansıtıyor

## Tespit (pozitifler vs TEMİZ negatifler)
| scheme | condition | n_pos | auroc | ci_lo | ci_hi | tpr_1fpr | pos_stat_mean | attneg_stat_mean |
|---|---|---|---|---|---|---|---|---|
| EXP | clean | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 50.021 | 0.447 |
| EXP | dia100 | 96 | 0.989 | 0.978 | 0.997 | 0.917 | 6.773 | 0.390 |
| EXP | dia50 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 15.080 | 0.379 |
| EXP | morph | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 49.052 | 0.445 |
| EXP | morph+dia | 96 | 0.989 | 0.978 | 0.997 | 0.917 | 6.696 | 0.409 |
| EXP | morph_v1 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 48.052 | 0.437 |
| EXP | morph_v1+dia | 96 | 0.991 | 0.981 | 0.998 | 0.917 | 6.664 | 0.404 |
| EXP | rtt | 96 | 0.917 | 0.873 | 0.954 | 0.625 | 2.443 | 0.505 |
| EXP | para | 96 | 0.970 | 0.941 | 0.990 | 0.896 | 9.686 | 0.421 |
| EXP | launder | 96 | 0.935 | 0.893 | 0.968 | 0.823 | 10.752 | 0.460 |
| EXP | launder_api | 96 | 0.858 | 0.801 | 0.907 | 0.625 | 2.615 | 0.377 |
| KGW | clean | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 8.966 | 0.283 |
| KGW | dia100 | 96 | 0.985 | 0.970 | 0.996 | 0.854 | 4.659 | 0.049 |
| KGW | dia50 | 96 | 0.999 | 0.998 | 1.000 | 0.979 | 6.187 | 0.337 |
| KGW | morph | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 8.936 | 0.297 |
| KGW | morph+dia | 96 | 0.985 | 0.970 | 0.996 | 0.844 | 4.636 | 0.033 |
| KGW | morph_v1 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 8.846 | 0.281 |
| KGW | morph_v1+dia | 96 | 0.985 | 0.969 | 0.996 | 0.844 | 4.622 | 0.040 |
| KGW | rtt | 96 | 0.916 | 0.875 | 0.952 | 0.448 | 2.880 | 0.568 |
| KGW | para | 96 | 0.930 | 0.893 | 0.963 | 0.698 | 4.019 | 0.403 |
| KGW | launder | 96 | 0.969 | 0.947 | 0.989 | 0.719 | 4.938 | 0.609 |
| KGW | launder_api | 96 | 0.906 | 0.864 | 0.942 | 0.396 | 2.857 | 0.352 |
| SynthID | clean | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 0.560 | 0.496 |
| SynthID | dia100 | 96 | 0.972 | 0.946 | 0.991 | 0.792 | 0.514 | 0.496 |
| SynthID | dia50 | 96 | 0.999 | 0.996 | 1.000 | 0.979 | 0.526 | 0.496 |
| SynthID | morph | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 0.559 | 0.496 |
| SynthID | morph+dia | 96 | 0.971 | 0.945 | 0.991 | 0.781 | 0.514 | 0.496 |
| SynthID | morph_v1 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 0.559 | 0.496 |
| SynthID | morph_v1+dia | 96 | 0.967 | 0.941 | 0.988 | 0.771 | 0.513 | 0.496 |
| SynthID | rtt | 96 | 0.835 | 0.776 | 0.886 | 0.365 | 0.504 | 0.497 |
| SynthID | para | 96 | 0.920 | 0.877 | 0.955 | 0.729 | 0.514 | 0.496 |
| SynthID | launder | 96 | 0.893 | 0.844 | 0.936 | 0.698 | 0.517 | 0.496 |
| SynthID | launder_api | 96 | 0.778 | 0.708 | 0.841 | 0.240 | 0.503 | 0.496 |

## Morfolojik-leksik ayrışma (pos_KGW alt-örneklemi)
| attack | n | lemma_jaccard | char_ratio |
|---|---|---|---|
| launder | 40 | 0.551 | 0.367 |
| morph | 40 | 0.999 | 0.998 |
| morph_v1 | 40 | 0.999 | 0.996 |
| para | 40 | 0.543 | 0.343 |
| rtt | 40 | 0.496 | 0.129 |

## Kalite (e5 kosinüs) — ⚠️ GERİ ÇEKİLDİ

> Aşağıdaki tablo YALNIZCA tekrarlanabilirlik için bırakılmıştır; **bulgu olarak kullanılamaz.** Korpusun %36'sı Latin-dışı yazı sistemi içeriyor (bkz. *Korpus bütünlüğü*), dolayısıyla 'anlam korunuyor' okuması bulamacın korunduğunu ölçer. Gerekçe ve ölçüm o bölümde.

| src | condition | n | e5_cos_mean | e5_cos_p05 |
|---|---|---|---|---|
| neg | dia100 | 96 | 0.960 | 0.937 |
| neg | dia50 | 96 | 0.978 | 0.962 |
| neg | morph | 96 | 1.000 | 0.999 |
| neg | morph+dia | 96 | 0.960 | 0.937 |
| neg | morph_v1 | 96 | 1.000 | 0.999 |
| neg | morph_v1+dia | 96 | 0.960 | 0.938 |
| neg | rtt | 96 | 0.972 | 0.939 |
| neg | para | 96 | 0.971 | 0.920 |
| neg | launder | 96 | 0.968 | 0.925 |
| neg | launder_api | 96 | 0.975 | 0.943 |
| pos_KGW | dia100 | 96 | 0.959 | 0.933 |
| pos_KGW | dia50 | 96 | 0.977 | 0.962 |
| pos_KGW | morph | 96 | 1.000 | 1.000 |
| pos_KGW | morph+dia | 96 | 0.959 | 0.934 |
| pos_KGW | morph_v1 | 96 | 1.000 | 0.999 |
| pos_KGW | morph_v1+dia | 96 | 0.959 | 0.934 |
| pos_KGW | rtt | 96 | 0.970 | 0.947 |
| pos_KGW | para | 96 | 0.970 | 0.934 |
| pos_KGW | launder | 96 | 0.968 | 0.927 |
| pos_KGW | launder_api | 96 | 0.975 | 0.949 |
| pos_EXP | dia100 | 96 | 0.956 | 0.931 |
| pos_EXP | dia50 | 96 | 0.974 | 0.958 |
| pos_EXP | morph | 96 | 1.000 | 0.999 |
| pos_EXP | morph+dia | 96 | 0.956 | 0.931 |
| pos_EXP | morph_v1 | 96 | 1.000 | 0.999 |
| pos_EXP | morph_v1+dia | 96 | 0.956 | 0.933 |
| pos_EXP | rtt | 96 | 0.979 | 0.970 |
| pos_EXP | para | 96 | 0.973 | 0.937 |
| pos_EXP | launder | 96 | 0.964 | 0.930 |
| pos_EXP | launder_api | 96 | 0.979 | 0.965 |
| pos_SynthID | dia100 | 96 | 0.959 | 0.940 |
| pos_SynthID | dia50 | 96 | 0.978 | 0.965 |
| pos_SynthID | morph | 96 | 1.000 | 0.999 |
| pos_SynthID | morph+dia | 96 | 0.959 | 0.940 |
| pos_SynthID | morph_v1 | 96 | 1.000 | 0.999 |
| pos_SynthID | morph_v1+dia | 96 | 0.959 | 0.940 |
| pos_SynthID | rtt | 96 | 0.972 | 0.951 |
| pos_SynthID | para | 96 | 0.968 | 0.933 |
| pos_SynthID | launder | 96 | 0.965 | 0.921 |
| pos_SynthID | launder_api | 96 | 0.975 | 0.951 |

## KGW mekanistik okuma
- `morph`: düzenleme başına Δz eğimi **0.076** (r=0.37, n=18, ort. edit=1.4)
- `morph_v1`: düzenleme başına Δz eğimi **0.091** (r=0.43, n=64, ort. edit=1.8)

## Tokenizer bereketi (token/kelime)
- Qwen/Qwen2.5-3B-Instruct: 2.585

## Yöntem notları
- Üretim ayarları (tüm şemalar, EXP hariç): `{'max_new_tokens': 320, 'min_new_tokens': 200, 'do_sample': True, 'temperature': 0.8, 'top_p': 0.95, 'top_k': 0, 'repetition_penalty': 1.0}`
- Şema-özel ezmeler: SynthID: {'temperature': 1.0} (SynthID kendi logits işlemcisinde sıcaklığı uyguladığı için HF'in ikinci uygulaması kapatıldı; etkin T üç şemada da eşit)
- EXP `max_new_tokens`'ı yok sayar: uzunluğu `pilot/exp_pilot.json` içindeki `sequence_length` belirler ve EOS'ta durmaz -> EXP pozitifleri sabit uzunlukta, negatifler değil. Uzunluk konfoundu için `n_tokens` her satırda loglanır.
- SynthID'nin logits işlemcisi durumu her üretimden önce sıfırlanır (MarkLLM'de sıfırlanmıyor; örnekler arası bağlam sızıntısı sonucu üretim sırasına bağımlı kılıyordu).
- **Tekrarlanabilirlik ÖLÇÜLDÜ** (`pilot.dev_mps_determinism`): saklanan Faz 1 çıktılarının 8 örneği, iki gün sonra ayrı bir süreçte aynı tohumlarla yeniden üretildiğinde **8/8 birebir aynı** metni verdi, |Δz| ort/maks = 0.000/0.000. K11'in varsaydığı 'MPS'te tam determinizm zayıf' kaydı bu kurulumda gözlenmedi. Kapsam: KGW, tek makine, sabit torch/transformers/model sürümleri (bkz. env.json) — makineler veya sürümler arası taşınabilirlik iddiası DEĞİLDİR.

## ⛔ GÖREV UYUMU — KORPUS İSTEMİ YERİNE GETİRMİYOR

24/24 istem **en az 300 kelime** istiyor. Üretim bütçesi `max_new_tokens=320`.

Ölçülen bereket (2.585 token/kelime) ile 300 kelime yaklaşık **776 token** gerektirir — bütçe gerekenin **%41**'i. Görev yapısal olarak yerine getirilemez.

| kaynak | n | ort_kelime | min_kelime | maks_kelime | hedefi_gecen | sonlandirilmis | token_tavaninda |
|---|---|---|---|---|---|---|---|
| filigransız | 96 | 122.400 | 1 | 271 | 0 | 4 | 87 |
| KGW | 96 | 123.400 | 6 | 271 | 0 | 9 | 84 |
| EXP | 96 | 118.400 | 89 | 135 | 0 | 0 | 0 |
| SynthID | 96 | 125.500 | 11 | 273 | 0 | 3 | 81 |

**0/384 metin hedefe ulaşıyor. 368/384 (%95.8) sonlandırıcı noktalama olmadan bitiyor** — yani cümle ortasında kesik.

> **Sonuç:** `short` (150 token) ve `clean_cut` kapıları GÖREV UYUMUNU sınamaz; ikisi de geçtiği için korpus geçerli sanıldı. Bu korpusta ölçülen her şey — tespit dahil — **kesik ve göreve uymayan metin** üzerinde ölçülmüştür. Saldırı deneyleri tamamlanmamış metinlerin yeniden yazımını ölçmektedir.

> Ana çalışma korpusu YENİDEN ÜRETİLMELİDİR: hedef kelime sayısına yetecek token bütçesi (güvenli payla ~900-1000), şemalar arası eşlenmiş EOS/uzunluk politikası ve üretim sonrası zorunlu ön-kapı (kelime sayısı, sonlandırılmış cümle, dil saflığı, görev uyumu). Kapıyı geçemeyen üretim saldırı aşamasına TAŞINMAMALIDIR.

## Denetim düzeltmeleri (üçüncü-göz, 2026-08-16)

Bağımsız metodolojik denetim yedi kritik bulgu getirdi; hepsi bu veride doğrulandı. Aşağıdakiler koddan üretilir.

### D1 — Tohumlar bağımsız tekrar değil (KRİTİK)

| sema | ozdes_hucre | toplam_hucre | oran | etkin_n |
|---|---|---|---|---|
| EXP | 168 | 264 | 0.636 | 24 (tohum etkisiz) |
| KGW | 0 | 264 | 0.000 | 96 |
| SynthID | 0 | 264 | 0.000 | 96 |

**EXP için dört tohum aynı sonucu veriyor.** Sebep: EXP'nin `seed_rng`'i prompt'un son `prefix_length` token'ından türer, torch RNG'sini kullanmaz — algoritma prompt+anahtar verildiğinde deterministiktir. Özdeşlik tam olarak DETERMİNİSTİK koşullarda (clean, dia100, morph×4, rtt) görülür, stokastik olanlarda (dia50, para, launder, launder_api) kaybolur.

> **Sonuç:** bu şema için etkin bağımsız kaynak sayısı 96 değil **24 prompt**'tur. Raporun bütün güven aralıkları o şema için DAR; satır-düzeyi bootstrap yerine prompt-kümeli bootstrap gerekir. Bu, pilot tasarımının kusurudur: dört tohum EXP için tekrar üretmiyor.

### D2 — 'TPR@%1FPR' saldırılı veride %1 FPR DEĞİL (KRİTİK)

Eşik temiz negatiflerden kuruluyor; saldırılı negatiflerde o eşiğin gerçek yanlış-pozitif oranı ölçülmemişti. En kötü altı hücre:

| sema | kosul | tpr | gercek_fpr |
|---|---|---|---|
| EXP | rtt | 0.625 | 0.083 |
| EXP | launder | 0.823 | 0.073 |
| EXP | morph_v1+dia | 0.917 | 0.042 |
| EXP | dia100 | 0.917 | 0.031 |
| EXP | morph+dia | 0.917 | 0.031 |
| KGW | dia50 | 0.979 | 0.031 |

**En yüksek gerçek FPR %8.3** — yani bazı hücrelerde 'yüksek TPR' etiketinin bedeli %1 değil %8.3'e kadar yanlış pozitif (13 hücrede eşiğin iki katından fazla). Metrik operasyonel olarak yanlış adlandırılmıştı. Ana çalışmada her koşul için (i) temiz eşikte TPR, (ii) aynı eşikte saldırılı-negatif FPR, (iii) saldırılı pozitif–saldırılı negatif AUROC birlikte verilmelidir.

### D3 — 'launder_api en yıkıcı saldırı' iddiası GERİ ÇEKİLDİ

| sema | tpr_rtt | tpr_launder_api | fark | mcnemar_p | bonferroni |
|---|---|---|---|---|---|
| EXP | 0.625 | 0.625 | 0.000 | 1.000 | — |
| KGW | 0.448 | 0.396 | -0.052 | 0.522 | — |
| SynthID | 0.365 | 0.240 | -0.125 | 0.050 | — |

Eşlenmiş McNemar testinde hiçbir şemada fark Bonferroni'yi geçmiyor. Önceki manşet, seçilmiş minimum nokta tahminine ve kazananın-laneti etkisine dayanıyordu.

**Savunulabilir dar iddia:** *bu pilotta API-aklama, yerel aklamadan üç şemada da daha fazla dedektör aşınması üretti; RTT'ye göre üstünlüğü şemaya bağlı ve kesin değildir.*


## Korpus bütünlüğü — KALİTE KATMANI GERİ ÇEKİLDİ

Üretilen 384 metnin **139'i (%36)** Latin-dışı yazı sistemi (CJK / Hangul / Kiril / İbranice / Arapça) içeriyor. Sebep ölçüldü: aynı prompt+tohumlarla `top_k` 0/20/50 karşılaştırıldığında kirlenme oranı %50-58 aralığında sabit kalıyor (bkz. `pilot.dev_topk_contamination`), yani örnekleme ayarı değil **modelin kendisi** (Qwen2.5-3B) kaynak. Ayar yalnız şiddeti etkiliyor (`top_k=0` yabancı karakter sayısını ~3 katına çıkarıyor).

| kaynak | n | kirli | oran | yabanci_karakter |
|---|---|---|---|---|
| gen_neg | 96 | 38 | 0.396 | 1683 |
| gen_pos_KGW | 96 | 41 | 0.427 | 1535 |
| gen_pos_EXP | 96 | 16 | 0.167 | 268 |
| gen_pos_SynthID | 96 | 44 | 0.458 | 1851 |

**Sonuç:** bu korpus üzerinde e5 kosinüsü ve LLM-yargıç kalite ölçümleri ANLAMLI DEĞİL — %36'sı çok-yazılı bulamaç olan metinlerde 'anlam korunuyor' demek, bulamacın korunduğunu ölçmektir. Kalite bölümü geri çekilmiştir. **DARALTILDI (denetim §9):** önceki teslimat 'ana çalışma >=7B kullanmalı' diyordu; bu bir BÜYÜKLÜK DENEYİ ile test edilmedi (7B ayağı disk nedeniyle hiç koşulmadı). Veriden çıkan hüküm yalnız: **Qwen2.5-3B bu promptlar ve üretim ayarlarıyla ana çalışma için uygun değildir.** Boyut eşiği yerine model-agnostik ön-kapı önerilir: dil saflığı, akıcılık, görev uyumu ve tekrar oranı eşiklerini geçen herhangi bir üretici.

### Tespit katmanı kirlenmeden etkileniyor mu? (ÖLÇÜLDÜ)

Metrikler yalnız kirlenmemiş metinlerle yeniden hesaplandı ve tam korpusla karşılaştırıldı. **En büyük sapma: AUROC 0.0247 (SynthID/launder_api), TPR 0.076.**

> ⚠️ **DÜZELTME (denetim §6):** önceki teslimatta 'sıralama değişmiyor' yazıyordu — **yanlış.** Şema sıralaması 3 koşulda değişiyor: `dia50` (tam EXP>KGW>SynthID → temiz EXP>SynthID>KGW); `para` (tam EXP>SynthID>KGW → temiz EXP>KGW>SynthID); `launder` (tam EXP>KGW>SynthID → temiz EXP>SynthID>KGW). Ayrıca sapmanın altkümede küçük kalması kirlenme–filigran bağımsızlığını KANITLAMAZ; seçici filtre yanlılığı taşıyabilir.

**Daraltılmış iddia:** *büyük yönler (rtt/launder_api en yıkıcı, morph etkisiz, clean tavan) korunuyor; bazı alt sıralamalar değişiyor.*

| kosul | sema | auroc_temiz | tpr_temiz | auroc_tam | tpr_tam |
|---|---|---|---|---|---|
| clean | KGW | 1.000 | 1.000 | 1.000 | 1.000 |
| clean | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| clean | SynthID | 1.000 | 1.000 | 1.000 | 1.000 |
| dia100 | KGW | 0.992 | 0.873 | 0.985 | 0.854 |
| dia100 | EXP | 0.988 | 0.900 | 0.989 | 0.917 |
| dia100 | SynthID | 0.955 | 0.788 | 0.972 | 0.792 |
| dia50 | KGW | 0.999 | 0.964 | 0.999 | 0.979 |
| dia50 | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| dia50 | SynthID | 0.998 | 0.981 | 0.999 | 0.979 |
| morph | KGW | 1.000 | 1.000 | 1.000 | 1.000 |
| morph | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| morph | SynthID | 1.000 | 1.000 | 1.000 | 1.000 |
| morph+dia | KGW | 0.991 | 0.873 | 0.985 | 0.844 |
| morph+dia | EXP | 0.988 | 0.900 | 0.989 | 0.917 |
| morph+dia | SynthID | 0.954 | 0.769 | 0.971 | 0.781 |
| morph_v1 | KGW | 1.000 | 1.000 | 1.000 | 1.000 |
| morph_v1 | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| morph_v1 | SynthID | 1.000 | 1.000 | 1.000 | 1.000 |
| morph_v1+dia | KGW | 0.991 | 0.855 | 0.985 | 0.844 |
| morph_v1+dia | EXP | 0.991 | 0.900 | 0.991 | 0.917 |
| morph_v1+dia | SynthID | 0.953 | 0.712 | 0.967 | 0.771 |
| rtt | KGW | 0.935 | 0.436 | 0.916 | 0.448 |
| rtt | EXP | 0.926 | 0.700 | 0.917 | 0.625 |
| rtt | SynthID | 0.839 | 0.288 | 0.835 | 0.365 |
| para | KGW | 0.933 | 0.709 | 0.930 | 0.698 |
| para | EXP | 0.983 | 0.912 | 0.970 | 0.896 |
| para | SynthID | 0.908 | 0.673 | 0.920 | 0.729 |
| launder | KGW | 0.973 | 0.691 | 0.969 | 0.719 |
| launder | EXP | 0.945 | 0.812 | 0.935 | 0.823 |
| launder | SynthID | 0.900 | 0.712 | 0.893 | 0.698 |
| launder_api | KGW | 0.898 | 0.364 | 0.906 | 0.396 |
| launder_api | EXP | 0.861 | 0.588 | 0.858 | 0.625 |
| launder_api | SynthID | 0.754 | 0.192 | 0.778 | 0.240 |

## Tokenizer bereketi kontrastı (Faz 3)
| tokenizer | sozluk | tr_bereket | en_bereket | tr_en_cezasi |
|---|---|---|---|---|
| Qwen2.5 (pilot modeli) | 151643 | 2.585 | 1.143 | 2.262 |
| Llama-3.1-8B | 128000 | 2.216 | 1.143 | 1.939 |
| Turkish-Llama-8b (=Llama-3 tok.) | 128000 | 2.216 | 1.143 | 1.939 |
| mT5 (çok dilli) | 250100 | 2.165 | 1.446 | 1.497 |
| turkish-gpt2 (TR-özel) | 50257 | 1.867 | 1.839 | 1.015 |
| XLM-R (çok dilli) | 250002 | 1.798 | 1.250 | 1.438 |
| BERTurk (TR-özel, 32k) | 32000 | 1.598 | 2.054 | 0.778 |

**Geçerli okuma:** aynı 11.751 kelimelik Türkçe korpusta tokenizer'lar arasında TR bereketi belirgin farklılaşıyor (Qwen2.5 2,585 -> BERTurk 1,598) ve sözlük büyüklüğü belirleyici değil (BERTurk 32k ile en iyi, mT5 250k ile kötü). **GERİ ÇEKİLDİ (denetim §10): tr_en_cezasi sütunu ve 'parçalanma dilin değil seçimin sonucu' iddiası** — İngilizce taban yalnız 56 kelimelik elle yazılmış tek paragraf, Türkçe taraf 11.751 kelime (1:209); eşlenmemiş korpusla hesaplanan oran güvenilir değil. Encoder ile üretici decoder tokenizerları da aynı nedensel tabloda yorumlanamaz.

> **Plan düzeltmesi (ölçüldü):** HANDOFF §7'nin Faz-3 adayı `ytu-ce-cosmos/Turkish-Llama-8b-v0.1`, Llama-3'ün tokenizer'ını DEĞİŞTİRMEDEN kullanıyor — iki sözlük yalnız 3 ÖZEL token'da ayrışıyor, gerçek alt-kelime parçalarının %100'ü ortak. O modelle 'TR-uyarlı tokenizer kontrastı' tanım gereği sıfır fark verirdi.

## API ile GERÇEK laundering (Faz 3)

Faz 2'nin `launder` saldırısı metni ÜRETEN modele (Qwen2.5-3B) yeniden yazdırıyordu; `launder_api` harici bir modele (Opus 5) yazdırır. İstem metni aynıdır, ancak **üretim prosedürü eşlenmiş DEĞİLDİR** (yerel: max 480 token, T=0.7, top_p=0.95, satır başına tohum YOK; API: max 4000 token, effort=low, örnekleme denetimi yok). Bu yüzden 'tek değişken model' denemez — iki FARKLI AKLAMA HATTI karşılaştırılmaktadır (denetim tur-2 §10).

| kosul | EXP | KGW | SynthID |
|---|---|---|---|
| clean | 1.000 | 1.000 | 1.000 |
| dia100 | 0.917 | 0.854 | 0.792 |
| launder | 0.823 | 0.719 | 0.698 |
| launder_api | 0.625 | 0.396 | 0.240 |
| para | 0.896 | 0.698 | 0.729 |
| rtt | 0.625 | 0.448 | 0.365 |

**Betimsel gözlem:** yerel hat TPR KGW 0.719, EXP 0.823, SynthID 0.698; API hattı KGW 0.396, EXP 0.625, SynthID 0.240. API hattı üç şemada da daha düşük TPR veriyor. NEDENSEL etiket ('model gücü') KURULMADI: hatlar çıktı bütçesi ve decoding rejimi bakımından eşlenmemiştir.

**Nokta TPR değerleri (KGW, artan):** `launder_api` 0.396 -> `rtt` 0.448 -> `para` 0.698 -> `launder` 0.719 -> `dia100` 0.854

> ⚠️ Bu bir TEHDİT SIRALAMASI DEĞİLDİR. Eşlenmiş McNemar (D3) hiçbir şemada anlamlı fark bulmuyor; denetim tur-2 ayrıca saldırılı-pozitif vs saldırılı-negatif AUROC ile sıralamanın iki şemada TERSİNE döndüğünü gösterdi. Sıralama okuması yapılmamalıdır.

## Filigranın kendi akıcılık bedeli (Faz 3)

Bağımsız yargıç (Opus 5), AYNI prompt ve AYNI tohumla üretilmiş filigransız/filigranlı çiftleri iki sırada karşılaştırdı. İki metin aynı soruya bağımsız yanıtlar olduğu için yalnız akıcılık soruldu. **DÜZELTME (denetim §7):** p-değerleri artık ÇİFT düzeyinde (15 çift), 30 hüküm üzerinden değil — sıra tersleme bağımsız örnek değil yanlılık kontrolüdür; önceki 0,0003/0,0001 değerleri ~30 kat iyimserdi. Ayrıca 'konfound iki kolda simetrik' savunması YANLIŞ: kirlenme taban %39,6 · KGW %42,7 · SynthID %45,8 · EXP %16,7. Birincil analiz iki tarafı da temiz çiftlerle yapılmalıydı; bu pakette yapılmadı.

| sema | n_cift | kararli_cift | filigransiz | filigranli | berabere | sira_uyumsuz | isaret_testi_p | bonferroni | muhasebe_tutarli |
|---|---|---|---|---|---|---|---|---|---|
| KGW | 15 | 14 | 12 | 2 | 0 | 1 | 0.013 | ANLAMLI: filigran BOZUYOR | True |
| EXP | 15 | 13 | 5 | 8 | 0 | 2 | 0.581 | fark yok | True |
| SynthID | 15 | 13 | 12 | 1 | 0 | 2 | 0.003 | ANLAMLI: filigran BOZUYOR | True |

**Bozan şemalar yukarıdaki tabloda ANLAMLI olarak işaretlidir.** Bu bulgu, *Korpus bütünlüğü* bölümündeki kirlenme oranlarıyla aynı yönde — iki bağımsız ölçüt aynı sıralamayı veriyor (sayılar orada, koddan üretilir).

> **Konfound uyarısı:** EXP hem en dayanıklı hem kaliteyi bozmayan şema. Bu iki bağımsız üstünlük DEĞİL, tek mekanizmanın iki sonucu olabilir: EXP olasılık kütlesini yüksek olasılıklı token'lara yoğunlaştırır — bu hem çok dilli kuyruğu bastırır (temiz metin) hem filigran sinyalini güçlendirir (yüksek tespit payı). Makalede 'EXP iki eksende iyi' değil, 'EXP'nin örnekleme yoğunlaştırması iki eksende birden fayda üretiyor' biçiminde yazılmalıdır.

## LLM-yargıç (Faz 3) — NEGATİF SONUÇ
- **İkili protokol kullanılamaz.** Konum dönmesi %53–%100 (ort. %84): çift ters çevrilince yargıç kararını değiştiriyor, yani metne değil sıraya bakıyor. `morph` koşulunda dönme %100 — iki metin neredeyse aynıyken bile 'eşit' diyemiyor (karakter oranı için *Morfolojik-leksik ayrışma* tablosuna bak).
- **Evet-yanlılığı.** ANLAM=EVET aralığı %87–%100; HAYIR hiç kullanılmadı. Neredeyse özdeş `morph` ile büyük ölçüde değişmiş `rtt` aynı cevabı alıyor -> ayırt etme gücü yok.
- **Tekli protokol konum yanlılığını kaldırıyor ama karar veremiyor.** Sıralama doğru yönde (`dia100` 2.40 en düşük, `launder` 3.27 en yüksek; orijinal 2.47), fakat hiçbir kıyas Bonferroni düzeltmesinden sonra anlamlı değil. Ölçek kullanılmıyor: yargıç 1 ve 5 puanlarını hiç vermedi, bütün ortalamalar 2.40–3.27 aralığına sıkıştı (gürültü > sinyal).
- **Sonuç:** aile-içi 3B yargıç (üreten modelin kendisi) kalite ölçüm aleti olarak KALİBRE DEĞİL.

### Bağımsız yargıç (claude-opus-5) — sorun protokolde değil, yargıçtaydı

Aynı örneklem, aynı iki protokol, aynı sorular. **Ortalama konum dönmesi %84 -> %6**; ANLAM sütununun yayılımı 13 puandan 97 puana çıktı. Yani ikili protokol sağlamdı; aile-içi 3B onu kullanacak kapasitede değildi.

| kosul | donme_3B | donme_bagimsiz | EVET_3B | EVET_bagimsiz |
|---|---|---|---|---|
| dia100 | 0.867 | 0.000 | 1.000 | 1.000 |
| dia50 | 0.867 | 0.000 | 1.000 | 1.000 |
| morph | 1.000 | 0.067 | 1.000 | 1.000 |
| morph+dia | 0.867 | 0.000 | 0.967 | 1.000 |
| morph_v1 | 1.000 | 0.067 | 1.000 | 1.000 |
| morph_v1+dia | 0.733 | 0.000 | 1.000 | 1.000 |
| rtt | 0.933 | 0.067 | 1.000 | 0.167 |
| para | 0.800 | 0.133 | 1.000 | 0.033 |
| launder | 0.533 | 0.200 | 0.867 | 0.067 |

Yapısal çıktı (JSON şeması) kullanıldığı için ayrıştırılamayan cevap kategorisi ortadan kalktı; biçim uyumu ile yargı kalitesi ayrıştı. Opus 5'te sampling parametreleri kaldırıldığı için yerel yargıçtaki `do_sample=False` determinizmi API tarafında kurulamaz — koşular arası küçük oynama beklenir.

> **İçerik okumaları raporlanmıyor:** bağımsız yargıcın saldırılar hakkındaki *anlam/akıcılık* kararları kirli korpus üzerinde verildi. Raporlanan bulgu yargıçlar arasındaki KALİBRASYON farkıdır; saldırıların kalite etkisi değil.

_Figürler: results/figs/ — Ham skorlar: results/scores.csv_