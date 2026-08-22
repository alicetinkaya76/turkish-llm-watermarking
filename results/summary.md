# Pilot Özeti — Türkçe LLM Filigran Sağlamlığı

> Korpus koşudan önce sabitlenen kabul eşiklerini karşılıyor: 384 metnin %97.7'i 300 kelime ölçütünü karşılıyor, %98.3'i sonlandırıcı noktalama ile bitiyor.

## Go / No-Go
- **Öncül (KGW temiz AUROC ≥ 0.9):** GEÇTİ (1.000)
- **TR-saldırılar ΔAUROC (KGW):** dia100=0.006, morph(v0)=0.000, morph_v1=0.000, morph+dia=0.006, rtt=0.046
- **Morfolojik ≠ leksik (morph):** ÖLÇÜLEMEDİ — metin yalnız %0.2 değişti; J=0.998 saldırının leksik korumasını değil, etkisizliğini yansıtıyor
- **Morfolojik ≠ leksik (morph_v1):** ÖLÇÜLEMEDİ — metin yalnız %0.5 değişti; J=0.997 saldırının leksik korumasını değil, etkisizliğini yansıtıyor

## Tespit (pozitifler vs TEMİZ negatifler)
| scheme | condition | n_pos | auroc | ci_lo | ci_hi | tpr_1fpr | pos_stat_mean | attneg_stat_mean |
|---|---|---|---|---|---|---|---|---|
| EXP | clean | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 55.883 | 0.446 |
| EXP | dia100 | 96 | 0.983 | 0.965 | 0.996 | 0.917 | 6.138 | 0.475 |
| EXP | dia50 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 16.088 | 0.419 |
| EXP | morph | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 53.870 | 0.451 |
| EXP | morph+dia | 96 | 0.982 | 0.964 | 0.996 | 0.875 | 5.943 | 0.481 |
| EXP | morph_v1 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 52.301 | 0.432 |
| EXP | morph_v1+dia | 96 | 0.982 | 0.964 | 0.996 | 0.917 | 5.669 | 0.450 |
| EXP | rtt | 96 | 0.956 | 0.920 | 0.981 | 0.792 | 4.522 | 0.430 |
| EXP | para | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 40.425 | 0.446 |
| EXP | launder | 96 | 0.997 | 0.990 | 1.000 | 0.990 | 26.837 | 0.468 |
| EXP | launder_api | 96 | 0.863 | 0.812 | 0.907 | 0.490 | 3.624 | 0.543 |
| KGW | clean | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 10.550 | 0.012 |
| KGW | dia100 | 96 | 0.994 | 0.986 | 1.000 | 0.865 | 6.194 | 0.275 |
| KGW | dia50 | 96 | 0.999 | 0.996 | 1.000 | 0.979 | 7.597 | 0.011 |
| KGW | morph | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 10.498 | 0.015 |
| KGW | morph+dia | 96 | 0.994 | 0.986 | 1.000 | 0.865 | 6.137 | 0.247 |
| KGW | morph_v1 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 10.392 | -0.003 |
| KGW | morph_v1+dia | 96 | 0.993 | 0.985 | 0.999 | 0.844 | 5.992 | 0.123 |
| KGW | rtt | 96 | 0.954 | 0.927 | 0.979 | 0.594 | 3.738 | 0.092 |
| KGW | para | 96 | 0.998 | 0.995 | 1.000 | 0.990 | 8.516 | -0.064 |
| KGW | launder | 96 | 0.999 | 0.996 | 1.000 | 0.938 | 7.016 | 0.016 |
| KGW | launder_api | 96 | 0.917 | 0.877 | 0.952 | 0.427 | 3.171 | -0.141 |
| SynthID | clean | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 0.535 | 0.501 |
| SynthID | dia100 | 96 | 0.929 | 0.896 | 0.961 | 0.677 | 0.509 | 0.501 |
| SynthID | dia50 | 96 | 0.996 | 0.990 | 1.000 | 0.948 | 0.516 | 0.501 |
| SynthID | morph | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 0.535 | 0.501 |
| SynthID | morph+dia | 96 | 0.926 | 0.892 | 0.959 | 0.656 | 0.509 | 0.501 |
| SynthID | morph_v1 | 96 | 1.000 | 1.000 | 1.000 | 1.000 | 0.534 | 0.501 |
| SynthID | morph_v1+dia | 96 | 0.923 | 0.887 | 0.957 | 0.656 | 0.509 | 0.501 |
| SynthID | rtt | 96 | 0.816 | 0.753 | 0.873 | 0.312 | 0.505 | 0.501 |
| SynthID | para | 96 | 0.998 | 0.995 | 1.000 | 0.990 | 0.527 | 0.501 |
| SynthID | launder | 96 | 0.981 | 0.955 | 0.998 | 0.948 | 0.519 | 0.501 |
| SynthID | launder_api | 96 | 0.747 | 0.673 | 0.816 | 0.250 | 0.504 | 0.500 |

## Morfolojik-leksik ayrışma (pos_KGW alt-örneklemi)
| attack | n | lemma_jaccard | char_ratio |
|---|---|---|---|
| launder | 40 | 0.832 | 0.891 |
| morph | 40 | 0.998 | 0.998 |
| morph_v1 | 40 | 0.997 | 0.995 |
| para | 40 | 0.881 | 0.941 |
| rtt | 40 | 0.598 | 0.751 |

## Kalite (e5 kosinüs)

> Korpus kirlenme oranı %4.9 (eşik %5) — kalite ölçümü GEÇERLİ. Değerler orijinal ve saldırılmış metin arasındaki çok dilli e5 kosinüs benzerliğidir; **1'e yakın = anlam korunmuş**. Saldırının 'başarılı' sayılması için hem tespiti düşürmesi hem metni kullanılabilir bırakması gerekir.

| src | condition | n | e5_cos_mean | e5_cos_p05 |
|---|---|---|---|---|
| neg | dia100 | 96 | 0.961 | 0.947 |
| neg | dia50 | 96 | 0.976 | 0.965 |
| neg | morph | 96 | 1.000 | 0.999 |
| neg | morph+dia | 96 | 0.961 | 0.947 |
| neg | morph_v1 | 96 | 0.999 | 0.998 |
| neg | morph_v1+dia | 96 | 0.961 | 0.947 |
| neg | rtt | 96 | 0.984 | 0.971 |
| neg | para | 96 | 0.998 | 0.994 |
| neg | launder | 96 | 0.996 | 0.989 |
| neg | launder_api | 96 | 0.985 | 0.977 |
| pos_KGW | dia100 | 96 | 0.962 | 0.944 |
| pos_KGW | dia50 | 96 | 0.976 | 0.964 |
| pos_KGW | morph | 96 | 1.000 | 1.000 |
| pos_KGW | morph+dia | 96 | 0.961 | 0.944 |
| pos_KGW | morph_v1 | 96 | 0.999 | 0.998 |
| pos_KGW | morph_v1+dia | 96 | 0.962 | 0.945 |
| pos_KGW | rtt | 96 | 0.983 | 0.973 |
| pos_KGW | para | 96 | 0.996 | 0.992 |
| pos_KGW | launder | 96 | 0.994 | 0.986 |
| pos_KGW | launder_api | 96 | 0.985 | 0.974 |
| pos_EXP | dia100 | 96 | 0.960 | 0.945 |
| pos_EXP | dia50 | 96 | 0.975 | 0.964 |
| pos_EXP | morph | 96 | 1.000 | 0.999 |
| pos_EXP | morph+dia | 96 | 0.960 | 0.943 |
| pos_EXP | morph_v1 | 96 | 0.999 | 0.998 |
| pos_EXP | morph_v1+dia | 96 | 0.960 | 0.947 |
| pos_EXP | rtt | 96 | 0.984 | 0.975 |
| pos_EXP | para | 96 | 0.996 | 0.986 |
| pos_EXP | launder | 96 | 0.992 | 0.979 |
| pos_EXP | launder_api | 96 | 0.984 | 0.976 |
| pos_SynthID | dia100 | 96 | 0.962 | 0.950 |
| pos_SynthID | dia50 | 96 | 0.977 | 0.968 |
| pos_SynthID | morph | 96 | 1.000 | 0.999 |
| pos_SynthID | morph+dia | 96 | 0.962 | 0.950 |
| pos_SynthID | morph_v1 | 96 | 0.999 | 0.997 |
| pos_SynthID | morph_v1+dia | 96 | 0.962 | 0.949 |
| pos_SynthID | rtt | 96 | 0.983 | 0.969 |
| pos_SynthID | para | 96 | 0.996 | 0.990 |
| pos_SynthID | launder | 96 | 0.993 | 0.987 |
| pos_SynthID | launder_api | 96 | 0.985 | 0.975 |

## KGW mekanistik okuma

> Eğim SAĞLAMLIK TESTİNDEN geçirilir: bootstrap %95 GA sıfırı dışlamalı, Spearman p<0.05 olmalı, ve en yüksek 3 kaldıraç noktası atılınca işaret korunmalı. Üçünden biri düşerse eğim GERİ ÇEKİLİR -- OLS eğimi birkaç uç gözlemden gelebilir.
- `morph`: düzenleme başına Δz eğimi **+0.052** (%95 GA [+0.022, +0.071], Theil-Sen +0.051, Spearman ρ=+0.58 p=0.000, n=38, ort. edit=2.9)
  - Pratik büyüklük: ort. 2.9 edit × 0.052 ≈ Δz 0.15; KGW temiz z ≈ 10.6 üzerinden sinyalin ~%1.4'i. AUROC etkisi ölçülen: 0.000.
- `morph_v1`: **GERİ ÇEKİLDİ** — eğim sıfırdan ayırt edilemiyor. OLS +0.026 ama %95 GA [-0.005, +0.034] sıfırı içeriyor, Theil-Sen +0.005 (OLS'ten farklı → kaldıraç), Spearman ρ=+0.09 (p=0.390), en yüksek 3 nokta atılınca eğim -0.003.

## Tokenizer bereketi (token/kelime)
- Qwen/Qwen3-14B: 2.545

## Yöntem notları
- Üretim ayarları (tüm şemalar, EXP hariç): `{'max_new_tokens': 1800, 'min_new_tokens': 400, 'do_sample': True, 'temperature': 0.8, 'top_p': 0.95, 'top_k': 20, 'repetition_penalty': 1.0}`
- Şema-özel ezmeler: SynthID: {'temperature': 1.0} (SynthID kendi logits işlemcisinde sıcaklığı uyguladığı için HF'in ikinci uygulaması kapatıldı; etkin T üç şemada da eşit)
- EXP `max_new_tokens`'ı yok sayar: uzunluğu `pilot/exp_pilot.json` içindeki `sequence_length` belirler ve EOS'ta durmaz -> EXP pozitifleri sabit uzunlukta, negatifler değil. Uzunluk konfoundu için `n_tokens` her satırda loglanır.
- SynthID'nin logits işlemcisi durumu her üretimden önce sıfırlanır (MarkLLM'de sıfırlanmıyor; örnekler arası bağlam sızıntısı sonucu üretim sırasına bağımlı kılıyordu).
- **Tekrarlanabilirlik OLCULDU** (CUDA, `hpc/remote_scripts/drift.py::T4`): 6/6 yineleme birebir ayni token dizisini verdi. Kapsam: tek GPU, sabit surumler -- tasinabilirlik iddiasi DEGILDIR.

## Görev uyumu

24/24 istem **en az 500 kelime** istiyor; kabul ölçütü **300 kelime** (model istenenin bir kısmını teslim ettiği için istem kalibre edildi — ölçüm: results_hpc/istem_provenans.json). Üretim bütçesi `max_new_tokens=1800`.

Ölçülen bereket (2.545 token/kelime) ile 300 kelime yaklaşık **764 token** gerektirir — bütçe gerekenin **%236**'i.

| kaynak | n | ort_kelime | min_kelime | maks_kelime | hedefi_gecen | sonlandirilmis | token_tavaninda |
|---|---|---|---|---|---|---|---|
| filigransız | 96 | 370.400 | 281 | 581 | 94 | 95 | 0 |
| KGW | 96 | 392.500 | 292 | 678 | 92 | 94 | 2 |
| EXP | 96 | 381.600 | 348 | 439 | 96 | -1 | 0 |
| SynthID | 96 | 394.200 | 290 | 1637 | 93 | 94 | 2 |

**375/384 (%97.7) metin 300 kelime olcutunu karsiliyor. 5/288 (%1.7) sonlandirici noktalama olmadan bitiyor** (sonlandirma paydasi 288: EXP in 96 metni yapisal olarak muaf).

> Korpus, koşudan önce sabitlenen eşikleri karşılıyor (uyum ≥ %75, sonlandırma ≥ %90).

## Denetim düzeltmeleri (üçüncü-göz, 2026-08-16)

Bağımsız metodolojik denetim yedi kritik bulgu getirdi; hepsi bu veride doğrulandı. Aşağıdakiler koddan üretilir.

### D1 — Tohumlar bağımsız tekrar değil (KRİTİK)

| sema | ozdes_hucre | toplam_hucre | oran | etkin_n |
|---|---|---|---|---|
| EXP | 175 | 264 | 0.663 | 24 (tohum etkisiz) |
| KGW | 0 | 264 | 0.000 | 96 |
| SynthID | 0 | 264 | 0.000 | 96 |

**EXP için dört tohum aynı sonucu veriyor.** Sebep: EXP'nin `seed_rng`'i prompt'un son `prefix_length` token'ından türer, torch RNG'sini kullanmaz — algoritma prompt+anahtar verildiğinde deterministiktir. Özdeşlik tam olarak DETERMİNİSTİK koşullarda (clean, dia100, morph×4, rtt) görülür, stokastik olanlarda (dia50, para, launder, launder_api) kaybolur.

> **Sonuç:** bu şema için etkin bağımsız kaynak sayısı 96 değil **24 prompt**'tur. Raporun bütün güven aralıkları o şema için DAR; satır-düzeyi bootstrap yerine prompt-kümeli bootstrap gerekir. Bu, pilot tasarımının kusurudur: dört tohum EXP için tekrar üretmiyor.

### D2 — 'TPR@%1FPR' saldırılı veride %1 FPR DEĞİL (KRİTİK)

Eşik temiz negatiflerden kuruluyor; saldırılı negatiflerde o eşiğin gerçek yanlış-pozitif oranı ölçülmemişti. En kötü altı hücre:

| sema | kosul | tpr | gercek_fpr |
|---|---|---|---|
| EXP | launder_api | 0.490 | 0.062 |
| SynthID | morph_v1+dia | 0.656 | 0.062 |
| EXP | dia100 | 0.917 | 0.042 |
| EXP | morph+dia | 0.875 | 0.042 |
| SynthID | rtt | 0.312 | 0.042 |
| EXP | dia50 | 1.000 | 0.031 |

**En yüksek gerçek FPR %6.2** — yani bazı hücrelerde 'yüksek TPR' etiketinin bedeli %1 değil %6.2'e kadar yanlış pozitif (16 hücrede eşiğin iki katından fazla). Metrik operasyonel olarak yanlış adlandırılmıştı. Ana çalışmada her koşul için (i) temiz eşikte TPR, (ii) aynı eşikte saldırılı-negatif FPR, (iii) saldırılı pozitif–saldırılı negatif AUROC birlikte verilmelidir.

### D3 — launder_api, rtt'den daha yıkıcı (2/3 şemada ANLAMLI)

| sema | tpr_rtt | tpr_launder_api | fark | mcnemar_p | bonferroni |
|---|---|---|---|---|---|
| EXP | 0.792 | 0.490 | -0.302 | 0.000 | ANLAMLI |
| KGW | 0.594 | 0.427 | -0.167 | 0.002 | ANLAMLI |
| SynthID | 0.312 | 0.250 | -0.062 | 0.392 | — |

Eşleşmiş McNemar testinde EXP, KGW şemasında fark Bonferroni düzeltmesini geçiyor. Ortalama TPR farkı -0.177 (negatif = launder_api daha yıkıcı).

**Kapsam:** bu karşılaştırma yalnız rtt ile launder_api arasındadır; tüm saldırıların sıralaması için *Tespit* tablosuna bakınız.


## Korpus bütünlüğü

Üretilen 384 metnin **19'i (%4.9)** Latin-dışı yazı sistemi (CJK / Hangul / Kiril / İbranice / Arapça) içeriyor. Etkin üretici: `Qwen/Qwen3-14B`.

| kaynak | n | kirli | oran | yabanci_karakter |
|---|---|---|---|---|
| gen_neg | 96 | 2 | 0.021 | 5 |
| gen_pos_KGW | 96 | 8 | 0.083 | 22 |
| gen_pos_EXP | 96 | 0 | 0.000 | 0 |
| gen_pos_SynthID | 96 | 9 | 0.094 | 28 |

**Sonuç:** kirlenme oranı %4.9 ≤ eşik %5; kalite katmanı geçerli sayılır.

### Tespit katmanı kirlenmeden etkileniyor mu? (ÖLÇÜLDÜ)

Metrikler yalnız kirlenmemiş metinlerle yeniden hesaplandı ve tam korpusla karşılaştırıldı. **En büyük sapma: AUROC 0.0121 (SynthID/rtt), TPR 0.024.**

Bu veride sıralama değişimi saptanmadı.

| kosul | sema | auroc_temiz | tpr_temiz | auroc_tam | tpr_tam |
|---|---|---|---|---|---|
| clean | KGW | 1.000 | 1.000 | 1.000 | 1.000 |
| clean | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| clean | SynthID | 1.000 | 1.000 | 1.000 | 1.000 |
| dia100 | KGW | 0.994 | 0.864 | 0.994 | 0.865 |
| dia100 | EXP | 0.982 | 0.917 | 0.983 | 0.917 |
| dia100 | SynthID | 0.937 | 0.701 | 0.929 | 0.677 |
| dia50 | KGW | 0.999 | 0.977 | 0.999 | 0.979 |
| dia50 | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| dia50 | SynthID | 0.995 | 0.943 | 0.996 | 0.948 |
| morph | KGW | 1.000 | 1.000 | 1.000 | 1.000 |
| morph | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| morph | SynthID | 1.000 | 1.000 | 1.000 | 1.000 |
| morph+dia | KGW | 0.994 | 0.864 | 0.994 | 0.865 |
| morph+dia | EXP | 0.981 | 0.875 | 0.982 | 0.875 |
| morph+dia | SynthID | 0.934 | 0.678 | 0.926 | 0.656 |
| morph_v1 | KGW | 1.000 | 1.000 | 1.000 | 1.000 |
| morph_v1 | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| morph_v1 | SynthID | 1.000 | 1.000 | 1.000 | 1.000 |
| morph_v1+dia | KGW | 0.993 | 0.841 | 0.993 | 0.844 |
| morph_v1+dia | EXP | 0.982 | 0.917 | 0.982 | 0.917 |
| morph_v1+dia | SynthID | 0.929 | 0.678 | 0.923 | 0.656 |
| rtt | KGW | 0.952 | 0.591 | 0.954 | 0.594 |
| rtt | EXP | 0.955 | 0.792 | 0.956 | 0.792 |
| rtt | SynthID | 0.804 | 0.299 | 0.816 | 0.312 |
| para | KGW | 0.998 | 0.989 | 0.998 | 0.990 |
| para | EXP | 1.000 | 1.000 | 1.000 | 1.000 |
| para | SynthID | 0.998 | 0.989 | 0.998 | 0.990 |
| launder | KGW | 0.998 | 0.932 | 0.999 | 0.938 |
| launder | EXP | 0.997 | 0.990 | 0.997 | 0.990 |
| launder | SynthID | 0.979 | 0.943 | 0.981 | 0.948 |
| launder_api | KGW | 0.913 | 0.420 | 0.917 | 0.427 |
| launder_api | EXP | 0.862 | 0.490 | 0.863 | 0.490 |
| launder_api | SynthID | 0.751 | 0.241 | 0.747 | 0.250 |

_Figürler: results/figs/ — Ham skorlar: results/scores.csv_