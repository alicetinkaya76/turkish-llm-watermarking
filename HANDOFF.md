# Proje Handoff — Türkçe LLM Filigran Sağlamlığı: Pilot (Apple MPS) — v2

> v1'den fark: pilot kodu artık YAZILMIŞ ve kısmen sandbox'ta doğrulanmış
> durumda (`pilot/` paketi). Senin görevin sıfırdan yazmak değil:
> **kur → doğrula → fazları koş → MPS'e özgü sorunları onar → kabul
> kriterlerini sayılarla kanıtla.**

## 1. Bağlam (Ne ve Neden)

LLM metin filigranlarının Türkçe'deki sağlamlığını ölçen bir SCI-E makalesinin
**pilot** çalışması. Literatürde çok dilli filigranların düşük/orta kaynaklı
dillerde ve çeviri altında çöktüğü gösterildi; Bangla için dil-özel çalışma
var, Türkçe için yok. Türkçe'nin eklemeli morfolojisi + tokenizer parçalanması
bu kırılganlık sınıfının merkezinde. AB YZ Yasası Md. 50(2) 2 Ağustos 2026'da
yürürlüğe girdi; sağlayıcılar metin filigranı uygulamaya başladı — motivasyon
güncel.

Pilotun 4 amacı: (1) zincir MPS'te uçtan uca çalışıyor mu, (2) temiz koşulda
Türkçe'de tespit edilebilirlik (öncül), (3) saldırı etki büyüklükleri
(ΔAUROC) + varyans → ana çalışmanın güç analizi, (4) iki yeni Türkçe saldırı
(diakritik soyma, morfolojik dönüşüm) temiz operasyonelleşiyor mu.

## 2. Mevcut Durum

Kod hazır: `pilot/` paketi (config, attacks, generate, heavy_attacks, detect,
metrics, fertility, run, dev_toy_smoke) + `patches/mps_generator.patch` +
`setup_mac.sh`. Çalışma dizini: MarkLLM klonunun kökü (commit
`c45ddc40f7b761beabe55a1b8dc4690e531d1c6d`, 2026-07-10 — SynthID bu commit'te
var, PyPI paketinde YOK).

Sandbox'ta doğrulananlar: MarkLLM API imzaları/skor formatları (kaynak
okuma); `pilot.attacks` birim testleri (5 farklı PYTHONHASHSEED'de GEÇTİ —
test, küme-sıralı lemma seçimindeki determinizm hatasını yakaladı ve
en-uzun-lemma kuralıyla düzeltildi); `pilot.dev_metrics_selftest` (sentetik
fikstürde AUROC/GA/TPR, gömülü Δz-eğiminin 0.149/0.15 geri kazanımı,
gerçek-zeyrek lemma-Jaccard ayrışması morph 0.97 ≫ para 0.04, figürler ve
summary.md üretimi GEÇTİ); yamanın `git apply` + geri alma uyumu; tüm
modüllerin derlenmesi ve CLI'ın repo kökünden çalışması. Sandbox'ta
YAPILAMAYAN: torch kurulumu (disk kotası) → `dev_toy_smoke` senin ilk
kanıt adımın. Mac'te doğrulanacaklar: MPS cihaz yolu, HF model indirme,
NLLB/e5, gerçek üretim hızı.

## 3. Kararlar (Nasıl — ve Neden)

K1 — **GitHub + commit pin, PyPI değil.** `markllm==0.1.5`te `synthid` yok
(paket içi dosya listesiyle doğrulandı); üretim-sınıfı şema bizim için kritik.

K2 — **Şemalar: KGW + EXP + SynthID**, üçü de `AutoWatermark.load(...)` ortak
arayüzünde. SynthID `detector_type:"mean"` (eğitimsiz) kullanılır; Bayesian
dedektör eğitim ister, pilotta YASAK.

K3 — **Skor yönleri:** KGW z (yüksek=wm), SynthID mean (yüksek=wm), EXP
**p-value (DÜŞÜK=wm)** → kodda EXP istatistiği `-log10(p)`. Bu yön düzeltmesi
`detect._stat`ta; oynama.

K4 — **`device="mps"`, `float16`, kuantizasyon YASAK** (logit dağılımını
bozup filigranla karışan konfound yaratır). Bellek yetmezse küçük modele in.

K5 — **Bilinen MPS riski:** `kgw.py` ve `synthid.py` `torch.Generator(device=…)`
kuruyor (satırlar yamada). Önce yamasız dene; `RuntimeError` gelirse
`git apply patches/mps_generator.patch`. Yama Generator'ı CPU'da kurup türetilen
tensörleri cihaza taşır (init-zamanı PRF/tablolar → eşdeğer). `run.py` bu
hatayı yakalayıp komutu söyler (`MpsGeneratorError`). DİKKAT: KGW yaması
üretim sırasındaki `_get_greenlist_ids_*` randperm çağrılarını da kapsar —
yalnız init'i yamalamak yetmez, ikisi birlikte gider.

K6 — **Model: Qwen2.5-Instruct, RAM kademesi** (`config.MODEL_TIERS`):
<16→1.5B, 16→3B, 24→7B (sınırda), ≥32→7B. Gerekçe: gate'siz, güçlü çok
dilli. `--model` ile ezilebilir.

K7 — **Üretim:** `max_new_tokens=320, min_new_tokens=200, do_sample,
T=0.8, top_p=0.95`. İki doğrulanmış tuhaflık: (a) EXP `max_new_tokens`'ı
YOK SAYAR, `pilot/exp_pilot.json`daki `sequence_length:300`u kullanır;
(b) EXP sıcaklığı tcfg ATTRIBUTE'undan okur, kwargs'tan değil —
`make_tcfg` bu yüzden `tcfg.temperature`'ı elle atar. Bu iki satırı silme.

K8 — **Yalnız completion skorlanır.** MarkLLM üretimleri prompt DAHİL döner;
`generate.slice_completion` chat-template'li prompt'u ayıklar. Prompt'u da
skorlamak z'yi yapay şişirir. 150 token altı completion `short=1` işaretlenir.

K9 — **Matris:** 24 prompt × 4 tohum = koşul başına 96. Negatifler BİR kez
üretilir, üç dedektör de aynı negatifleri skorlar. Saldırılar (dia100, dia50,
morph, morph+dia, rtt, para, launder) hem pozitif hem negatiflere uygulanır
(saldırılı-negatif = sahte-sinyal kontrolü). AUROC negatif referansı DAİMA
temiz negatiflerdir.

K10 — **Metrikler:** AUROC + 1000-bootstrap %95 GA + TPR@%1FPR; kalite = e5
kosinüs (PPL YASAK — çok dilli PPL güvenilmez); morfolojik≠leksik kanıtı =
zeyrek lemma-Jaccard + karakter oranı; KGW Δz/edit regresyonu; tokenizer
bereketi; uzunluk konfoundu için `n_tokens` her satırda loglu.

K11 — **Tekrarlanabilirlik:** tohumlar sabit, `env.json` sürüm+commit+yama
durumunu yazar. MPS tam determinizmi zayıf → summary'de sınırlama notu.

Reddedilenler: PyPI paketi (K1), repo `requirements.txt`in aynen kurulumu
(eski `openai==0.28`/`Pillow==9.4.0` pinleri; çekirdek yolun gerçek bağımlılığı
torch+transformers+numpy+scipy — import zinciri doğrulandı), API-tabanlı model
(logit yok), kuantizasyon, SynthID-Bayesian, `evaluation/` pipeline'ları
(cuda-varsayımlı yardımcılar), gate'li modeller (Faz 0-2).

## 4. Bu İterasyonun Kapsamı (Görevler)

1. **Kurulum:** `bash setup_mac.sh` (veya adımlarını elle). `python -m
   pilot.attacks` ve `python -m pilot.dev_metrics_selftest` → 0 dönmeli.
   `python -m pilot.dev_toy_smoke --device mps`
   → MPS boru hattını İNDİRMESİZ kanıtlar; Generator hatası ilk burada
   yakalanır (çık, yamayı uygula, tekrar).
2. **Faz 0:** `python -m pilot.run --phase 0` (Qwen2.5-1.5B iner). KGW z
   ayrımını raporla; EXP/SynthID duman satırlarını raporla.
3. **Faz 1:** `--phase 1`. Temiz AUROC tablosu + bereket. KGW temiz AUROC <
   0.90 ise betik 3 ile çıkar → DUR, kullanıcıya danış (anlatı değişir).
4. **Faz 2:** `--phase 2`. Saldırı metinleri (cache'li), tam skorlama,
   `summary.md` + figürler. EXP tespiti en yavaş adımdır; ilerleme
   satırlarını izle, süreyi raporla.
5. **Onarım yetkin:** MPS'e özgü hataları (op fallback, dtype, bellek) çöz;
   çözümün K1-K11 ile çelişiyorsa ÖNCE sor. `pilot/` içinde düzeltme serbest,
   MarkLLM çekirdeğinde yalnız K5 yaması.

Faz 3 (Türkçe-uyarlı modelle tokenizer kontrastı, API'li gerçek laundering,
LLM-yargıç) kullanıcı onayı olmadan BAŞLAMA.

## 5. Kabul Kriterleri (Bitti ne demek?)

- [ ] `pilot.attacks`, `dev_metrics_selftest` ve `dev_toy_smoke` exit 0 (MPS'te).
- [ ] Faz 0: z(wm)−z(no-wm) > 2 raporlu; EXP `is_watermarked=True`, SynthID
      skoru basılı. Yama gerektiyse `env.json.mps_patch_applied=true`.
- [ ] Faz 1: `results/scores.csv`te 96 neg + 3×96 pos temiz satır; üç şema
      AUROC+GA `summary`/stdout'ta; öncül kararı açık.
- [ ] Faz 2: 7 saldırı × 3 şema tablosu + saldırılı-negatif ortalamaları +
      e5 kalite + morph lemma-Jaccard ≥ 0.95 iken para/launder belirgin düşük
      + Δz/edit eğimi `results/summary.md`de; Go/No-Go üç satırı başta.
- [ ] `env.json` dolu; koşu ikinci başlatmada üretimleri atlayıp devam ediyor
      (JSONL resume çalışıyor).

## 6. Kısıtlar ve Yapılmayacaklar

Kuantizasyon YOK; bf16 YOK (fp16). Hiperparametre taraması YOK (KGW γ=.5,
δ=2). MarkLLM çekirdeğine K5 dışında dokunma. `evaluation/` kullanma.
API çağrısı Faz-3 onayına dek YOK. İçerik doğruluğu umursanmaz (akıcılık
yeter). Makale metni yazımı bu iterasyonda yok.

## 7. Varsayımlar (yanlışsa düzelt)

Apple Silicon + güncel torch (MPS'li) varsayıldı; RAM bilinmiyor → otomatik
kademe. `torch.Generator(mps)` güncel torch'ta çalışıyor OLABİLİR (yama
şartlı). NLLB'nin MPS'te koştuğu varsayıldı (kod CPU'ya düşmeyi bilir).
Zeyrek bazı fiilleri ıskalayabilir → `rejected` sayacı loglanır. Türkçe-uyarlı
Faz-3 model adayının (ytu-ce-cosmos Turkish-Llama-8b) erişimi DOĞRULANMADI.

## 8. İlk Adım — Senden İstediğim

Lütfen kodlamaya/koşmaya HEMEN başlama. Önce:
1. Şu dosyaları oku ve bu dokümanla tutarlılığını teyit et:
   `pilot/config.py`, `pilot/generate.py`, `pilot/detect.py`,
   `pilot/attacks.py`, `pilot/run.py`, `patches/mps_generator.patch`,
   MarkLLM'de `watermark/kgw/kgw.py`, `watermark/exp/exp.py`,
   `utils/transformers_config.py`, `config/SynthID.json`.
2. `sysctl -n hw.memsize` ve `python -c "import torch; print(torch.__version__,
   torch.backends.mps.is_available())"` çıktılarını bana raporla.
3. Belirsiz/çelişkili bulduğunu SOR; kısa bir koşu planı öner.
4. Onayımdan sonra §4 sırasıyla ilerle; her faz sonunda kabul kriterini
   sayılarla kanıtla ve bir sonraki faz için onay iste.
İlk denemeni nihai sayma; bu bir diyalog.
