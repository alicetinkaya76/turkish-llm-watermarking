# `hpc/` — Selçuk TF-HPC ortam katmanı

Bu klasör **ortama ait olan her şeyi** tutar. Bilimsel kod `pilot/` altında kalır ve
**değiştirilmez**: `pilot/metrics.py` iki turluk bağımsız denetimden geçti, fork'lamak
iki kaynak doğruluk yaratır ve tekrarlanabilirliği bitirir. Buradaki dosyalar `pilot/`'u
*içe aktarır*, kopyalamaz.

---

## 1. Ortam envanteri

Aşağıdaki her satır **ölçüldü** (2026-08-19). Hiçbiri tahmin veya belge okuması değil.

| | |
|---|---|
| Erişim | JupyterHub **4.1.6** → kullanıcı başına Docker konteyneri, içinde **root**, `cwd=/workspace` |
| | SSH/SLURM **yok**. `tfhpc.selcuk.edu.tr` → `172.22.202.23` (RFC1918) |
| | Yalnız **üniversite VPN'i** üzerinden. Sertifika **kendinden imzalı** → `verify=False` zorunlu |
| GPU | **Quadro RTX 8000** · Turing **sm_75** · **50,8 GB** VRAM · sürücü 580.159.03 · host'ta tek GPU |
| CPU | Intel Xeon Gold 6226R @ 2.90 GHz — host 24 mantıksal çekirdek, konteynere **12**'si |
| RAM | 125 GB |
| Disk | `/workspace` **ext4 gerçek blok cihaz**, 478 GB boş, **326 MB/s** · `/` overlay |
| | mount seçeneklerinde `usrquota,grpquota` — **kota değeri okunamıyor** (`quota` komutu yok) |
| OS | Ubuntu 24.04.1 LTS · çekirdek 5.15.0-185 · CUDA araç zinciri 12.8 |
| Yığın | Python 3.12.3 · torch **2.10.0+cu128** · transformers **5.8.0** · accelerate 1.13.0 |
| Ağ | huggingface.co / github.com / pypi.org → hepsi 200 |

**Ölçülen dtype hızı** (4096² matmul, 30 yineleme):

| dtype | TFLOPS | |
|---|---:|---|
| **fp16** | **82,1** | tensor çekirdekleri |
| bf16 | 7,3 | **emülasyon** — fp32'den bile yavaş |
| fp32 | 13,4 | |

`torch.cuda.is_bf16_supported()` **`True` döner ve bu yanıltıcıdır**;
`including_emulation=False` ile `False`. `dtype="auto"` çoğu modern modelin
config'inden bf16 seçeceği için **asla kullanılmaz**. → `hpc/config_cuda.py::DTYPE`

**Doğrulandı:** 28 GB'lık tek blok VRAM ayrıldı → 14B fp16 sığar.

---

## 2. Sürüm kayması — bu klasörün asıl varlık sebebi

`pilot/` içindeki bazı kararlar **yerel ortamda ampirik ölçülmüş** davranışlara dayanıyor.
Hedef ortam farklı sürümlerde, üstelik ölçümün yapıldığı sürüm **hiçbir yerde kurulu değil**:

| | ölçümün yapıldığı | yerelde şu an | HPC |
|---|---|---|---|
| transformers | **5.10.2** (`config.py:53`) | 5.15.0 | konteyner 5.8.0 ile geliyor → bootstrap **5.15.0**'a sabitliyor |
| torch | belirtilmemiş | 2.13.0 | 2.10.0+cu128 |
| python | — | 3.11.9 | 3.12.3 |
| cihaz | MPS | MPS | CUDA sm_75 |
| zeyrek | 0.1.3 | 0.1.3 | 0.1.3 (sabitlendi) ⚠ `zeyrek.__version__` "0.1.2" **der ve yalandır**; gerçek sürüm yalnız `importlib.metadata` ile okunur |

Projenin kuralı **"ölçülmeyeni varsayma"** olduğu için bu ölçümler **devralınmaz**.
`hpc/remote_scripts/drift.py` hepsini hedef ortamda yeniden yapar:

| test | neye bağlı | yanlışsa sonucu |
|---|---|---|
| **T1** dtype kwarg | `generate.py:39-41` `torch_dtype=` | v5'te ad `dtype` oldu; eski ad yutulursa model **fp32** yüklenir → 14B = 56 GB → **OOM** |
| **T2** işlemci sırası | `config.py:50-58` SynthID çift-sıcaklık | sıra değiştiyse SynthID'nin etkin sıcaklığı yanlış → **şemalar arası karşılaştırma bozulur** |
| **T3** top_k varsayılanı | `config.py:16-21` | açık değer ezmiyorsa örneklem entropisi, dolayısıyla **ölçülen filigran gücü** kayar |
| **T4** determinizm | K11 | aynı tohum farklı çıktı → **tekrarlanabilirlik ihlali** |
| **T5** dtype hızı | — | bf16'ya düşülürse koşu **11 kat** yavaşlar |
| **T6** fp16 sapması | üretimde örneklenen token dizisi | fp16 farklı token seçtirebilir. ~~Tespiti etkiler~~ **ETKİLEMEZ** — üç dedektör de modelsiz (exp.py:161-180, kgw.py:142, synthid.py:371) |

Ölçüm bitmeden ana koşu başlatılmaz. `drift.py` bloke edici bulguda **çıkış kodu 2** verir.

### Ölçüm sonuçları (2026-08-19, `results_hpc/drift.json`)

Ortam: python 3.12.3 · torch 2.10.0+cu128 · transformers **5.15.0** (yerele sabitlendi) ·
Quadro RTX 8000 sm_7.5 · `bf16_native=False`, `bf16_emülasyon_dahil=True`

| test | sonuç | sonuç ne demek |
|---|---|---|
| **T1** | `torch_dtype` **kabul ediliyor** (kullanımdan kaldırma uyarısıyla); `dtype` de çalışıyor | fp32'ye sessiz düşme **yok**. `generate.py:39-41` olduğu gibi çalışır; yeni ada geçmek ayrı bir temizlik işi |
| **T2** | **ÖNCE** — yerel ölçümle **aynı** | `SCHEME_GEN_OVERRIDES` (SynthID çift-sıcaklık düzeltmesi) **geçerli kalıyor**, değişiklik gerekmiyor |
| **T3** | açık değer eziyor | `config.py:16-21` varsayımı geçerli |
| **T4** | **6/6 özdeş** | CUDA'da tam deterministik, K11 sağlanıyor |
| **T5** | fp16 **12,6×** bf16 | `DTYPE="float16"` doğrulandı |
| **T6** | ortalama 0,0093 nat, azami 0,0401 nat (23 token, **Qwen2.5-0.5B**'de ölçüldü) | ⚠ İLK OKUMAM YANLIŞTI. Kaynak okundu: üç dedektör de MODELSİZ (`exp.py:161-180` tokenizer+rng+gamma.sf, `kgw.py:142` karma, `synthid.py:371` ngram karma). fp16 **üretimi** etkiler, **tespiti etkilemez**. Kalan gerçek etki: `exp.py:130` softmax fp16'da çok küçük olasılıkları sıfırlar (örtük kuyruk kesmesi). Açık kalem DEĞİL |

**Sonuç:** taşımanın bloke edici sürprizi çıkmadı. T6 açık kalem sanılmıştı, kaynak okunca kapandı.

---

## 3. Kullanım

```bash
# tek seferlik: .env'e TFHPC_TOKEN + TFHPC_USER (parola DEĞİL, token)
python -m hpc.deploy --drift        # gönder + kur + sürüm kaymasını ölç

python -m hpc.remote probe          # hızlı envanter
python -m hpc.remote sh "nvidia-smi" --venv
python -m hpc.remote push pilot     # yalnız kodu tazele
python -m hpc.remote log /workspace/logs/kosu.log -n 60
python -m hpc.remote get /workspace/MarkLLM/results/scores.csv ./scores.csv
```

| dosya | nerede çalışır | ne yapar |
|---|---|---|
| `remote.py` | **yerel** | JupyterHub REST + websocket istemcisi (token ile) |
| `deploy.py` | **yerel** | gönder → bootstrap → drift ölçümü |
| `config_cuda.py` | her ikisi | `pilot/config.py` ezmeleri, VRAM hesabı, ortam doğrulaması |
| `remote_scripts/bootstrap.sh` | **konteyner** | dizinler, venv, paketler, MarkLLM klonu |
| `remote_scripts/drift.py` | **konteyner** | T1–T6 sürüm kayması ölçümleri |

---

## 4. Kurulumun tasarım kararları

1. **Her şey `/workspace` altında.** Konteynerin kökü *overlay*'dir; JupyterHub
   idle-culler sunucuyu durdurunca yazılabilir katman gider. Varsayılan HF önbelleği
   `~/.cache/huggingface` overlay'de olurdu → 30 GB'lık model her yeniden başlatmada
   uçardı. `HF_HOME=/workspace/hf` bu yüzden **zorunlu**.
2. **`venv --system-site-packages`.** torch 2.10.0+cu128 sistemde kurulu ve bu
   sürücüyle eşleşiyor. Temiz venv 3 GB'lık torch'u yeniden indirir ve CUDA eşleşmesini
   bozma riski taşır. **torch asla yükseltilmez** — bootstrap bunu koşu sonunda
   doğrular ve değişmişse hata verir.
3. **transformers yerel sürüme sabitlenir** (`5.15.0`). İki ortam farklı sürümdeyse
   sonuçlar karşılaştırılamaz. `--system-transformers` ile HPC'deki 5.8.0 korunabilir.
   Hangisi seçilirse seçilsin **`drift.py` yine çalıştırılır.**
4. **zeyrek 0.1.3'e sabitlenir.** TUZAK: `zeyrek.__version__` **"0.1.2" der ve yanlıştır**
   — 0.1.3 tekerleğinin içindeki sabit güncellenmemiş. Gerçek sürüm yalnız
   `importlib.metadata.version("zeyrek")` ile okunur; yerelde ölçüldü: **0.1.3**
   (`requirements_resolved.txt:61` ile tutarlı). Bootstrap ilk sürümde `__version__`'a
   bakıp yanlışlıkla 0.1.2 pinliyordu; kurulum sonrası artık metadata ile doğruluyor.
5. **MarkLLM upstream'den sabit commit ile klonlanır**
   (`c45ddc40f7b761beabe55a1b8dc4690e531d1c6d`). Yerel klonda izlenen dosyalarda
   değişiklik olmadığı doğrulandı, bu yüzden klon birebir aynı çekirdeği verir ve
   5,8 MB'lık `results/` taşınmaz.

---

## 5. Açık kararlar ve bilinmeyenler

**Model seçimi.** `config_cuda.py`'de **varsayılan model yok**; açıkça verilmezse hata
verir, sessizce yanlış modelle koşu başlamasın.

- Qwen2.5-3B ve 7B ön-kapıyı **5 konfigürasyonda geçemedi** (%36 Latin-dışı kirlenme).
- Groq duman testi görevin **yapılabilir** ve kapının **doğru kalibre** olduğunu kanıtladı
  (8/9 geçti, sıfır kirlenme).
- Nicemleme **K4 ile yasak**, bu sınır aşılamaz.

Adaylar, checkpoint `model.safetensors.index.json`'undan **ölçülen** boyutlarla
(tahmin değil; boş VRAM 50,6 GB):

| model | ölçülen boyut | KV'ye kalan | karar |
|---|---:|---:|---|
| `Qwen/Qwen3.8-27B` | **55,6 GB** (27,8B) | **−5,0 GB** | ⛔ **sığmaz** — ağırlıklar tek başına VRAM'i aşıyor |
| `Qwen/Qwen3.5-9B` | **19,3 GB** (9,7B) | 31,3 GB | ✅ rahat sığar |
| `Qwen/Qwen3.5-4B` | 9,3 GB (4,7B) | 41,3 GB | ✅ sığar (yedek) |

Bu ailenin basamakları 0,8 / 2 / 4 / 9 / 27B — **14B yok**, yani sığan en büyük yoğun
model 9B'dir.

**`qwen3_5` mimarisine dair, ana koşudan önce sınanacaklar** (config'ten okundu):

- Sınıf `Qwen3_5ForConditionalGeneration`, `image_token_id` var, `language_model_only:
  False` → **çok kipli**. MarkLLM `AutoModelForCausalLM` bekliyor; transformers'ta
  `Qwen3_5ForCausalLM` de mevcut ama checkpoint'in hangisiyle yükleneceği **sınanmalı**.
- `full_attention_interval: 4`, `linear_conv_kernel_dim`, `mamba_ssm_dtype: float32`
  → **hibrit doğrusal-dikkat / SSM**. Katmanların yalnız dörtte biri tam dikkat.
  Filigran logit düzeyinde çalıştığı için kavramsal engel yok, ama fp16'ya çevirmenin
  SSM özyinelemesine etkisi **ölçülmeli** (T6 ile aynı aile risk).
- Checkpoint `bfloat16`; bu GPU'da bf16 emülasyon olduğu için fp16'ya çevrilecek.

**Ölçülmemiş, iddia edilmiyor:**

| bilinmeyen | nasıl ölçülecek |
|---|---|
| `/workspace` gerçekten kalıcı mı | `/workspace/.kalicilik_testi` ve `/root/.kalicilik_testi` işaretçileri bırakıldı; konteyner yeniden başladıktan sonra hangisinin sağ kaldığına bakılacak |
| disk kotasının değeri | `quota` komutu yok; gerçek tüketim izlenerek ölçülecek |
| T6'nın tespit metriklerine etkisi | aynı metinler üzerinde fp16 ve fp32 tespit istatistikleri karşılaştırılacak |
| `qwen3_5` + MarkLLM uyumu | model yüklenip ön-kapı ve filigran yolu fiilen koşturulacak |

### ÖN-KAYIT — S2: fayda ekseni (yazım anı: 2026-08-23, KOŞUDAN ÖNCE)

**Soru:** "en yıkıcı saldırı" dediğimiz launder_api, metni KULLANILABİLİR
bırakıyor mu? Tespiti düşüren ama metni imha eden şey saldırı değil imhadır;
e5 kosinüsü bu ayrımı yapamıyor (dia100'ü 0,962 ile zeminden ayıramıyor).

**Protokol:**
- Yalnız İKİLİ karşılaştırma (orijinal vs saldırılı, iki sırada). Pointwise
  KOŞULMAZ: eski koşuda ölçek tabanda kilitliydi (orijinaller dahil her şey 1/5).
- Koşullar: rtt, para, launder, launder_api. Kaynak: pos_KGW (e5 tablosu
  faydanın kaynağa değişmez olduğunu gösteriyor). Saldırı başına 40 çift.
- KÖR kalibrasyon: 20 özdeş çift (tavan; beklenen hüküm ESIT) + 20 farklı-istem
  çifti (zemin; beklenen ANLAM=HAYIR), gerçek çiftlerle karıştırılır.
  gen_pos_EXP'ten ASLA (tohumlar %66 özdeş).
- **Çıkar çatışması:** launder_api metinlerini Opus 5 üretti. İKİ yargıç koşulur:
  Opus 5 (Anthropic) + gpt-oss-120b (Groq, farklı aile). launder_api hükmü
  yalnız iki yargıç UYUŞURSA kullanılır; uyuşmazlık raporlanır.
- Analiz birimi ÇİFT (n=40/koşul); istem-kümeli bootstrap; konum dönme oranı
  her koşulda raporlanır (kabul: <%30).

**Karar kuralı (koşudan önce):** bir saldırı "başarılı" sayılır ancak
(i) ΔAUROC > 0,05 VE (ii) yargıç çoğunluğu ANLAM=EVET/KISMEN verirse.
launder_api için (ii) iki yargıçta da sağlanmalı.

### ÖN-KAYIT — S1: insan metninde yanlış pozitif oranı (yazım anı: 2026-08-23, VERİ TOPLANMADAN ÖNCE)

**Soru:** dedektörler filigransız İNSAN Türkçesini filigranlı sanıyor mu, ve bu
Türkçeye özgü mü?

**Motivasyon (model-negatiflerinden ölçüldü, n=96):** KGW null dağılımı N(0,1)
olmalıyken ort +0,013, **std 1,313** (varyans şişmesi 1,72×); `config/KGW.json`
`z_threshold=4.0` bu dağılımda yalnız 3,04σ uzakta → nominal FPR 3,2e-5 iken
gözlenen dağılım altında ~1,2e-3 (**~38×**). Öne sürülen mekanizma:
`prefix_length=1` + sondan eklemeli dilde tekrarlanan ek alt-tokenleri →
ardışık yeşil-liste kararları bağımsız değil.

**Hipotezler (veri görülmeden):**
- H1: İnsan Türkçesinde KGW null std > 1 (varyans şişmesi model metniyle sınırlı değil).
- H2: Tür ve uzunlukça eşlenmiş İngilizce kümede şişme Türkçeden KÜÇÜK.
- H3: EXP ve SynthID null'larında anlamlı şişme YOK (EXP ~Uniform; SynthID std≈0,003).

**Protokol:** TR Vikipedi + eşlenmiş EN Vikipedi rastgele maddeleri; belge başına
korpus uzunluk dağılımına eşlenmiş bitişik pencere (cümle ortasından kesmeden);
hedef ≥1000 belge/dil, ulaşılan n raporlanır. Üç dedektör `model=None` ile
(doğrulandı: üçü de modelsiz çalışıyor). Çıktı: şema×dil null ort/std,
`z_threshold=4.0`'ta gözlenen FPR, model-negatiflerinden kalibre eşikte FPR.
Kesinlik: n=1000'de %1 FPR'nin GA'sı ~±0,6 puan; %0,1 iddiası İÇİN YETERSİZ —
yalnız büyüklük sırası raporlanır.

**Sınır:** tek register (ansiklopedi). Gazete/deneme registerı toplanamadıysa
"Vikipedi registerında" diye daraltılarak yazılır.

**EK — ikinci register (yazım anı: 2026-08-25, VERİ TOPLANMADAN ÖNCE):**
TR Vikikaynak (wikimedia/wikisource 20231201 dump) — eski resmî/edebî düzyazı.
Aynı pencereleme, aynı dedektörler, aynı eşikler. Hipotez: H1 bu registerde de
tutar (KGW null std > 1). Register farkı KEŞİFSEL olarak raporlanır; ansiklopedi
sonuçlarıyla havuzlanmaz. n hedefi >=750 (Vikikaynak TR küçük; ulaşılan n yazılır).

### ÖN-KAYIT — korpus kabul eşikleri

Bu üç eşik `pilot/config.py`'de tanımlı ve **Faz 1 başlamadan önce**, denetimin
bulduğu bloke edici kusurlar giderilirken sabitlendi — yani korpus verisi
görülmeden. Raporun "korpus geçerli mi", "kalite ölçülebilir mi" hükümlerini
bunlar belirler.

| sabit | değer | ne bağlar | gerekçe |
|---|---|---|---|
| `KAPI_HEDEF_KELIME` | **300** | kabul ölçütü | İstemler 500 ister (model istenenin %72-80'ini teslim ediyor, ölçüldü). Kalibre edilen istemdir, eşik değil. |
| `KORPUS_UYUM_ESIGI` | **0,75** | hedefe ulaşan metin oranı | Ön-kapıdaki `KAPI ≥ 12/16` ile aynı oran. |
| `KORPUS_SONLANDIRMA_ESIGI` | **0,90** | düzgün biten metin oranı | Pilotun düştüğü yer (%4,2). EXP muaf: EOS'ta durmaz, paydadan düşer. |
| `KORPUS_KIRLENME_ESIGI` | **0,05** | kalite katmanının geçerliliği | Üstündeyse e5/LLM-yargıç ölçümleri geri çekilir — kirli metinde "anlam korunuyor" demek bulamacın korunduğunu ölçer. |

**Dürüstlük notu:** 0,75 ön-kapı ölçütünden türetildi; 0,90 ve 0,05 bu çalışmaya
özgü ve literatürden gelmiyor. İkisi de veri görülmeden sabitlendi ama
**dışsal olarak gerekçelendirilmiş değildir**; farklı bir eşik farklı hüküm
verebilirdi. Duyarlılık analizi yapılmadı.

### ÖN-KAPI KOŞU KAYDI

**Koşu 1 — ön-kayıtlı, KALDI.** İstemler "en az 300 kelime". Qwen3-14B:
`latin 15/16` (16 gerekiyordu), `KAPI 0/16` (≥12 gerekiyordu), medyan 244 kelime.
Eşik gevşetilmedi. Veri: `results_hpc/onkapi_Qwen3-14B.jsonl`

**Teşhis — kapı DEĞİL.** İstem 500 kelime istedi, ölçüt 300'de kaldı. 16/16 metnin
hepsi uzadı (ortalama +117), medyan 364, `latin 16/16`, `KAPI 13/16`. Sonuç:
model uzunluk talimatına duyarlı, **istenenin %72-80'ini** teslim ediyor.
Kesilen 2 metin tam 1024 token'da → bütçe bağlayıcıydı.
Veri: `results_hpc/onkapi_14b_istem500.jsonl`

**Koşu 2 — resmî, ön-kaydı aşağıda.** İki değişiklik yapıldı ve ikisi de ölçüme dayanıyor:
1. İstemler `300 kelime` → `500 kelime` (24/24; `results_hpc/istem_provenans.json`,
   sha256 öncesi/sonrası kayıtlı, geri alınabilir). **Kalibre edilen istemdir, eşik değil.**
2. `max_new_tokens` 1024 → **1400** (ölçülen bereket 2,623 tok/kelime; 500 kelime =
   1312 token; 1024'te 2/16 metin kesiliyordu).

`KAPI ≥ 300 kelime` ölçütü **değişmedi**. 300 zaten bilimsel gereklilik değil:
tespit `MIN_COMPLETION_TOKENS=150` istiyor, ölçülen medyan 926 token.

### ÖN-KAYIT — koşu 2 ölçütü (yazıldığı an: 2026-08-20, koşudan ÖNCE)

Model seçimi bu ölçütle kapanır. Eşik **koşu sonrası değiştirilmeyecektir**; sonradan
ayarlanan eşik ölçüm değil, gerekçelendirmedir.

```
komut: python -m pilot.dev_preflight --device cuda --model Qwen/Qwen3-14B \
         --budgets 1400 --prompts 8 --seeds 2 --top-k 20 --rep 1.0 --temp 0.8
istem: pilot/prompts_tr.json, "en az 500 kelime"
       sha256 8fcbe4074b46965c8f7b639a45666f90...
n    : 16 üretim (8 istem × 2 tohum)

GEÇME ÖLÇÜTÜ (ikisi birden):
  1. latin  = 16/16   ZORUNLU  (Latin-dışı kirlenme sıfır olmalı; pilotun düştüğü yer buydu)
  2. KAPI  >= 12/16            (dört ölçütü birden geçen üretim)
```

`--top-k 20` bir tercih değil, ölçüm sonucu: `top_k=0` ölçülerek zararlı bulundu
(drift T3'te sonlu logit 36 vs 9; sweep'te 7B'de kapı 0 vs 3).

**Aday sırası** — ikisi aynı anda yüklenmez (29,54 + 19,3 GB kapıyı aşar), arada
`del model; torch.cuda.empty_cache()`:

1. `Qwen/Qwen3-14B` — 29,54 GB ölçüldü, `Qwen3ForCausalLM`, **çok kipli değil, hibrit değil**
2. `Qwen/Qwen3.5-9B` — 19,3 GB ölçüldü, ama `Qwen3_5ForConditionalGeneration` + hibrit
   SSM/doğrusal-dikkat → EXP'in standart KV-cache varsayan ham forward döngüsüyle riskli

Her ikisi de düşerse **ana koşu başlatılmaz**, sonuç olduğu gibi raporlanır.

**⚠ GPU TEK VE PAYLAŞILIYOR.** Paralel bir oturum `Qwen3.8-27B` test ediyor; ölçüldüğünde
**36,7 GB VRAM** tutuyor ve %34-37 kullanımdaydı; geriye 12,2 GB kalıyor, bu 9B için
(19,3 GB) **yetmez**. Koşu öncesi `nvidia-smi` kontrolü zorunlu, iki oturumun aynı anda
model yüklememesi için sıra gözetilmeli. HF önbelleği (`/workspace/hf`) bilinçli olarak
**paylaşılıyor** — aynı model iki kez indirilmesin diye.

---

## 6. Kurulumda çıkan ve düzeltilen tuzaklar

Hepsi ölçülerek bulundu; kod içinde yorumlarla işaretli.

| tuzak | belirti | düzeltme |
|---|---|---|
| jupyter contents API gizli dosyaları reddediyor | `.push_pilot.tar.gz` → **400 Bad Request** (`allow_hidden` varsayılan False) | geçici ad nokta ile başlamıyor (`_push_…`) |
| contents API yolları **sunucu köküne** göre | `/workspace/MarkLLM/…` mutlak verilince 404 — `drift.json` sessizce inmedi | `HPC._rel()` `/workspace/` önekini kırpıyor |
| konteynerde `ensurepip` yok | `python3 -m venv` başarısız | bootstrap gerekirse `python3-venv`'i apt ile kuruyor |
| kırık venv sağlam sanıldı | `bin/python` vardı ama `pip` yoktu | varlık değil **kullanılabilirlik** sınanıyor (`pip --version`) |
| bash komut yolu önbelleği | venv silindikten sonra `python3` eski yolda aranıp **rc=127** | mutlak `SYSPY=/usr/bin/python3` + `hash -r` |
| HF önbellek yolu uyuşmazlığı | `HF_HUB_CACHE=$HF_HOME/hub` ama modeller doğrudan `/workspace/hf` altında | `env.sh` tek kaynak doğruluk; `remote.py` artık yol sabit yazmıyor, `env.sh`'ı source ediyor |

**Operasyon notu:** VPN düşerse *istemci* bağlantısı kopar, konteynerdeki iş kopmaz —
uzun koşular `remote.nohup()` ile `setsid nohup` altında başlatılır ve log dosyasından
izlenir. Çekirdek hücresinde uzun iş çalıştırmak tercih edilmez: websocket kopunca
çekirdek öldürülebilir.
