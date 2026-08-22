# Türkçe LLM Filigran Pilotu — Paket Kılavuzu (Apple MPS)

Bu paket, MarkLLM (commit `c45ddc40`, 2026-07-10) üzerine kurulan, KGW + EXP +
SynthID şemalarını Türkçe'de temiz koşulda ve 7 saldırı altında ölçen pilotun
**çalışır kodunu** içerir. Mimari kararlar ve gerekçeleri `HANDOFF.md`'de
(K1-K11); bu dosya yalnızca "nasıl çalıştırırım"ı anlatır.

## İçerik

```
pilot/            çalışır pilot paketi (config, attacks, generate, detect,
                  metrics, fertility, jsonl, run, dev_toy_smoke,
                  dev_metrics_selftest, prompts_tr.json, exp_pilot.json)
patches/mps_generator.patch   K5 yaması (yalnızca Generator/MPS hatasında)
setup_mac.sh      tek komutluk kurulum
HANDOFF.md        Claude Code için spec + kararlar + kabul kriterleri
```

## Kurulum ve çalıştırma sırası

```bash
bash setup_mac.sh          # klon + commit pin + venv + bağımlılıklar
cd MarkLLM && source .venv/bin/activate

python -m pilot.attacks                       # 1) saldırı birim testleri (~sn)
python -m pilot.dev_metrics_selftest          # 2) analiz katmanı öz-testi (~sn)
python -m pilot.dev_toy_smoke --device mps    # 3) indirmesiz E2E  (~1 dk)
python -m pilot.run --phase 0                 # 4) duman: 1.5B iner (~dk'lar)
python -m pilot.run --phase 1                 # 5) temiz + öncül   (~1-3 saat)
python -m pilot.run --phase 2                 # 6) saldırılar+rapor (~saatler)
```

Çıktılar `results/` altında: `scores.csv`, `detection_metrics.csv`,
`summary.md` (Go/No-Go başlıkta), `figs/`, `env.json`.

Model, RAM'e göre otomatik seçilir (16 GB→3B, 24 GB→7B sınırda, 32 GB+→7B).
Elle sabitlemek için: `--model Qwen/Qwen2.5-3B-Instruct`. Üretimler JSONL'e
satır satır yazılır; kesilen koşu **kaldığı yerden devam eder**.

## Claude Code ile kullanım

Claude Code kuruluysa `MarkLLM/` kökünde `claude` başlatıp ilk mesaj olarak:

> HANDOFF.md dosyasını oku. 8. bölümdeki talimatları izle: önce belirtilen
> kaynak dosyaları doğrula, bana planını söyle, onayımdan sonra Faz 0'dan
> başlayarak fazları koş ve her fazın kabul kriterini sayılarla kanıtla.

Kurulu değilse (resmî yollar): macOS'ta `curl -fsSL https://claude.ai/install.sh | bash`
veya `brew install --cask claude-code`; npm alternatifi
`npm install -g @anthropic-ai/claude-code` (güncel sürümler Node 22+ ister).
Ayrıntı: https://code.claude.com/docs/en/setup — ilk `claude` çalıştırmasında
tarayıcıdan hesapla giriş yapılır.

## Sorun giderme

- **`torch.Generator ... mps` RuntimeError** → `git apply patches/mps_generator.patch`
  (run.py hatayı yakalayıp bu komutu zaten söyler). Yama, PRF/örnekleme
  tablolarını CPU'da üretip cihaza taşır; matematiksel olarak eşdeğerdir.
- **Bellek baskısı / swap** → `--model Qwen/Qwen2.5-3B-Instruct`. Kuantizasyon
  KULLANMA (HANDOFF K4: logit dağılımını bozar).
- **HF indirme/gate hatası** → Qwen2.5 gate'sizdir; ağ/proxy kontrol et.
  Faz 3'teki Türkçe model adayı için lisans onayı gerekebilir.
- **EXP tespiti yavaş** → normaldir (Ek A): token başına `rand(vocab)` CPU'da;
  ilerleme satırları basılır.
- **Desteklenmeyen MPS op hatası** → `export PYTORCH_ENABLE_MPS_FALLBACK=1`
  (setup betiği venv'e ekler).

## Sandbox doğrulama durumu (bu paketi üreten oturum)

| Bileşen | Durum |
|---|---|
| MarkLLM API imzaları, skor yönleri, EXP tuhaflıkları | kaynak koddan doğrulandı |
| `pilot.attacks` birim testleri (12 R1 + R2 + büyük harf + diakritik) | ÇALIŞTIRILDI; 5 farklı PYTHONHASHSEED'de geçti |
| Lemma seçimi determinizmi (sürdürüyor→sürdürmektedir) | testin yakaladığı hata DÜZELTİLDİ (en-uzun-lemma kuralı) |
| `pilot.dev_metrics_selftest` (AUROC/GA/TPR, Δz-eğimi 0.149/0.15, lemma-Jaccard morph 0.97 ≫ para 0.04, figürler, summary.md) | ÇALIŞTIRILDI, geçti |
| MPS yaması: `git apply` + geri alma, iki dosyada da işaretleyici | doğrulandı |
| `py_compile` (tüm modüller) + `pilot.run --help` (repo kökünden) | geçti |
| Oyuncak E2E `dev_toy_smoke` (torch gerekir) | konteyner disk kotası torch kurulumuna yetmedi → **Mac'te ilk kanıt adımı** (indirmesiz, ~1 dk) |
| MPS cihaz yolu, HF model indirme, NLLB/e5 | Mac'te doğrulanacak (Faz 0-2) |
