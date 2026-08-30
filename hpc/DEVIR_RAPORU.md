# TF-HPC devir raporu

Bu dosya **başka bir oturuma aktarmak için** yazıldı. Selçuk Teknoloji Fakültesi
HPC'sine nasıl bağlanıldığını, neyin ölçülmüş neyin varsayım olduğunu ve hangi
tuzakların sessizce yanlış sonuç ürettiğini anlatır. Tam envanter `hpc/README.md`
içinde; burası bağlanma katmanının özeti.

Her sayı **ölçüldü** (2026-08-19 / 2026-08-25). Hiçbiri belge okuması veya tahmin
değil. Ölçülmemiş olanlar §6'da ayrıca listelendi.

---

## 1. Ortamın şekli — beklediğin HPC değil

| | |
|---|---|
| Erişim | **JupyterHub 4.1.6** → kullanıcı başına bir **Docker konteyneri**, içinde **root**, `cwd=/workspace` |
| **SSH yok, SLURM yok** | Kuyruk sistemi yoktur. İş göndermezsin; konteynerde doğrudan koşarsın. |
| Adres | `tfhpc.selcuk.edu.tr` → `172.22.202.23` (RFC1918) — **yalnız üniversite VPN'i üzerinden** |
| Sertifika | **Kendinden imzalı** → `verify=False` zorunlu |
| GPU | **Quadro RTX 8000** · Turing **sm_75** · 50,8 GB VRAM · sürücü 580.159.03 · host'ta tek GPU |
| CPU / RAM | Xeon Gold 6226R; konteynere **12** mantıksal çekirdek · 125 GB RAM |
| Disk | `/workspace` **gerçek ext4 blok cihaz**, 478 GB boş, 326 MB/s. `/` **overlay** |
| Yığın | Python 3.12.3 · torch **2.10.0+cu128** · transformers 5.8.0 (koşuda 5.15.0'a sabitlenir) |
| Ağ | huggingface.co / github.com / pypi.org → hepsi 200 |

Bunun pratik sonucu: **uzun işi bir kabuk oturumuna bağlayamazsın.** VPN kopunca
websocket de kopar. Çözüm §3'te (`nohup`).

---

## 2. Kimlik doğrulama — token, parola değil

Kimlik doğrulama **JupyterHub API token'ı** ile yapılır. İki değişken `.env`
içinde durur (mod 600, `.gitignore:135`):

```
TFHPC_TOKEN=<JupyterHub API token>
TFHPC_USER=<JupyterHub kullanıcı adı>
```

`hpc/remote.py` bunları `dotenv_values` ile okur. Değerler hiçbir yere
yazdırılmaz, loglanmaz, `env.json`/`summary.md` içine girmez, commit edilmez.

**Token neden parola değil:** token iptal edilebilir ve kapsamı sınırlıdır.
Parola öyle değildir.

### Bu projede geçerli üç güvenlik kuralı

1. **HPC parolası kullanılmaz.** Parola bir kez WhatsApp üzerinden paylaşıldı ve
   ekran görüntüsünde göründü. Asistan onu hiçbir yere yazmadı, kullanmadı ve
   tekrarlamadı. **Bu parolanın değiştirilmesi hâlâ açık bir iş.** Kimlik
   doğrulama token ile yapılır ve token gerektiğinde iptal edilebilir.
2. **API anahtarları HPC'ye KOPYALANMAZ.** `ANTHROPIC_API_KEY` ve `GROQ_API_KEY`
   yalnız yerelde durur. HPC paylaşımlı bir makinedir. Bu yüzden `launder_api`
   saldırısı ve S2 yargıç koşusu **yerelde** çalıştırıldı, HPC'de değil.
3. **Anahtar terminale yazdırılmaz.** `echo`/`export` ile bir anahtarı kabuğa
   yazmak onu shell geçmişine düşürür. `.env` bir editörle açılır:
   `open -e .env`. Doğrulama gerekiyorsa yalnız önek + uzunluk gösterilir.

### `verify=False` neden güvenli tutuluyor

Sertifika kendinden imzalı olduğu için doğrulama kapatılmak zorunda. Sessizce
her hedefe güvensiz istek atmayalım diye `remote.py` bir **beyaz liste** tutar:

```python
ALLOWED_HOST = "tfhpc.selcuk.edu.tr"   # remote.py:43
```

Hedef başka bir hosta kayarsa istemci bağlanmaz, `SystemExit` verir. Kopyalayıp
başka bir sunucuya çevirirken bu satırı atlamayın.

---

## 3. Protokol — ne konuşuluyor

`hpc/remote.py` iki katman kullanır:

| katman | ne için |
|---|---|
| **REST** (`requests`) | `/hub/api/users/<user>` sunucu durumu, `POST .../server` sunucuyu uyandırma, `POST /user/<user>/api/kernels` çekirdek açma |
| **WebSocket** (`wss://.../api/kernels/<id>/channels`) | kod yürütme |

**Neden websocket:** Jupyter'in HTTP arayüzünde çıktının nerede bittiği belirsiz.
Çekirdek protokolü ise `status: idle` mesajıyla bitişi açıkça bildirir, o yüzden
`execute()` websocket üzerinden konuşur ve idle'ı bekler.

**Akış:** `ensure_server()` konteyner uykudaysa uyandırır ve 180 sn'ye kadar
bekler → `start_kernel()` → `execute()` → `close()` çekirdeği siler.

### Komutlar

```bash
python -m hpc.deploy --drift              # gönder + kur + sürüm kaymasını ölç
python -m hpc.remote probe                # hızlı envanter
python -m hpc.remote sh "nvidia-smi" --venv
python -m hpc.remote push pilot           # yalnız kodu tazele
python -m hpc.remote log /workspace/logs/kosu.log -n 60
python -m hpc.remote get /workspace/MarkLLM/results/scores.csv ./scores.csv
```

| dosya | nerede koşar | ne yapar |
|---|---|---|
| `hpc/remote.py` | **yerel** | JupyterHub REST + websocket istemcisi |
| `hpc/deploy.py` | **yerel** | gönder → bootstrap → drift ölçümü |
| `hpc/config_cuda.py` | ikisi | `pilot/config.py` ezmeleri, VRAM hesabı, ortam doğrulaması |
| `hpc/remote_scripts/bootstrap.sh` | **konteyner** | dizinler, venv, paketler, MarkLLM klonu |
| `hpc/remote_scripts/drift.py` | **konteyner** | T1–T6 sürüm kayması ölçümleri |

### Uzun işler: `nohup`, kabuk hücresi değil

```python
h.nohup("python -m pilot.kosu ...", log="/workspace/logs/kosu.log")
```

VPN veya websocket koparsa iş konteynerde **devam eder**. Bu iki kez fiilen
kanıtlandı. Uzun işi `sh()` ile çalıştırma; bağlantı kopunca işi kaybedersin.

`push_dir` bayat dosyaları **siler** — hedefte kalan eski bir dosyanın sessizce
koşuya girmesini önlemek için. Kod eşitliği kaynak-sha ile kanıtlanır.

---

## 4. Sessizce yanlış sonuç üreten tuzaklar

Bunların hepsi **ölçüldü**. Her biri sessizdir: hata vermez, yanlış sayı üretir.

### bf16 bu GPU'da emülasyondur

```
fp16   82,1 TFLOPS   ← tensor çekirdekleri
bf16    7,3 TFLOPS   ← EMÜLASYON, fp32'den bile yavaş
fp32   13,4 TFLOPS
```

`torch.cuda.is_bf16_supported()` **`True` döner ve bu yanıltıcıdır**;
`including_emulation=False` verilince `False` olur.

**`dtype="auto"` ASLA kullanılmaz** — çoğu modern modelin config'i bf16 der,
`auto` ona uyar, koşu **12,6 kat** yavaşlar. `hpc/config_cuda.py::DTYPE` fp16'ya
sabitlenmiştir.

### `HF_HOME` overlay'de olamaz

Konteynerin kökü overlay'dir. JupyterHub idle-culler sunucuyu durdurunca yazılabilir
katman gider. Varsayılan `~/.cache/huggingface` overlay'de olur → 30 GB'lık model
her yeniden başlatmada **uçar**. `HF_HOME=/workspace/hf` zorunludur.

### torch asla yükseltilmez

venv `--system-site-packages` ile kurulur. torch 2.10.0+cu128 sistemde kuruludur ve
sürücüyle eşleşir. Temiz venv 3 GB'lık torch'u yeniden indirir ve CUDA eşleşmesini
bozma riski taşır. Bootstrap koşu sonunda torch sürümünü **doğrular**, değişmişse
hata verir.

### `zeyrek.__version__` yalan söyler

`"0.1.2"` der; gerçek sürüm **0.1.3**'tür (tekerleğin içindeki sabit
güncellenmemiş). Gerçek sürüm yalnız `importlib.metadata.version("zeyrek")` ile
okunur. Bootstrap ilk sürümde `__version__`'a bakıp yanlış sürüm pinliyordu.

### `--config cuda` bayrağı olmadan ezmeler koşuya GİRMEZ

`hpc/config_cuda.py` ezmeleri `pilot.config` modül nitelikleri yamalanarak
uygulanır. Bayrağı unutursan koşu yerel ayarlarla çalışır ve **hata vermez**.

### Dedektör üreticiyle aynı cihaz sınıfında koşmalı

SynthID'nin g-değeri anahtarı cihaz sınıfına bağlıdır. CPU'da skorlanan filigranlı
metin şansa çöker (ortalama g 0,498 vs CUDA 0,529); doğru cihazda skorlama
gönderilen skorları bit düzeyinde tekrar üretir (azami fark 5,55 × 10⁻¹⁷).

**İstisna:** S1 (insan metni null ölçümü) etkilenmez — filigran yok, null dağılımı
anahtar-değişmez, SynthID null std iki cihazda da 0,003.

### EXP EOS'ta durmaz

`sequence_length` sabittir, `gen_kwargs` tüketilmez, aynı istem+anahtar
deterministik olarak aynı diziyi verir. Yani **dört tohum bağımsız tekrar değildir**;
etkin n = istem sayısıdır → küme (prompt-clustered) bootstrap şarttır.

---

## 5. Sürüm kayması kapısı — ana koşudan önce

`hpc/remote_scripts/drift.py` altı testi hedef ortamda **yeniden** yapar. Proje
kuralı "ölçülmeyeni varsayma" olduğu için yerel ölçümler devralınmaz.

| test | neyi yakalar | 2026-08-19 sonucu |
|---|---|---|
| T1 | `torch_dtype` kwarg'ı yutulursa model fp32 yüklenir → 14B = 56 GB → OOM | kabul ediliyor, sessiz düşme yok |
| T2 | işlemci sırası kaydıysa SynthID'nin etkin sıcaklığı yanlış olur | yerelle **aynı** |
| T3 | `top_k` varsayılanı ezilmezse ölçülen filigran gücü kayar | açık değer eziyor |
| T4 | determinizm (K11) | **6/6 özdeş** |
| T5 | bf16'ya düşülürse koşu yavaşlar | fp16 **12,6×** bf16 |
| T6 | fp16 sapması | üretimi etkiler, **tespiti etkilemez** (üç dedektör de modelsiz) |

**Bloke edici bulguda `drift.py` çıkış kodu 2 verir ve ana koşu başlatılmaz.**

T6 hakkında bir not, çünkü ders var: ilk okumada "tespiti etkiler" sanılmıştı.
Kaynak okununca kapandı — `exp.py:161-180`, `kgw.py:142`, `synthid.py:371` üçü de
model çağırmaz. Kalan gerçek etki `exp.py:130`'daki softmax'ın fp16'da çok küçük
olasılıkları sıfırlaması (örtük kuyruk kesmesi). Açık kalem değil.

---

## 6. Ölçülmemiş olanlar — iddia edilmiyor

| bilinmeyen | nasıl ölçülecek |
|---|---|
| `/workspace` gerçekten kalıcı mı | `/workspace/.kalicilik_testi` ve `/root/.kalicilik_testi` işaretçileri bırakıldı; konteyner yeniden başladıktan sonra hangisi sağ kaldı bakılacak |
| disk kotasının değeri | mount seçeneklerinde `usrquota,grpquota` var ama `quota` komutu yok; gerçek tüketim izlenerek ölçülecek |
| `qwen3_5` + MarkLLM uyumu | çok kipli sınıf ve hibrit SSM mimarisi; model yüklenip ön-kapı fiilen koşturulacak |

---

## 7. Devralan oturum için ilk beş dakika

```bash
# 1. VPN açık mı? Değilse hiçbir şey çalışmaz.
# 2. .env içinde TFHPC_TOKEN ve TFHPC_USER var mı (editörle bak, echo ile DEĞİL)
open -e .env

# 3. Bağlantı ve envanter
python -m hpc.remote probe

# 4. Kod tazele + sürüm kapısı
python -m hpc.deploy --drift        # çıkış kodu 2 ise DUR

# 5. Uzun iş
python -m hpc.remote sh "..." --venv     # kısa işler
# uzun işler için remote.py içindeki nohup() kullanılır
```

Bir şey çalışmıyorsa sırayla bak: VPN → token geçerli mi → konteyner uyanık mı
(`ensure_server` 180 sn bekler) → `--venv` bayrağı unutuldu mu → `--config cuda`
unutuldu mu.
