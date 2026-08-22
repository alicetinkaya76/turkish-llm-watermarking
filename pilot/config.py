# pilot/config.py — Türkçe LLM filigran pilotu: tüm sabitler burada.
# Gerekçeler için HANDOFF.md §3 (K1-K11).
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent   # MarkLLM kökü
RESULTS = REPO_ROOT / "results"
PROMPTS_PATH = Path(__file__).resolve().parent / "prompts_tr.json"

# ---- Deney boyutu ----
SEEDS = [11, 12, 13, 14]          # örnek başına tohum (prompt x seed = 24x4 = 96)
N_PROMPTS = 24
SMOKE_PROMPTS = 2                 # Faz 0
SMOKE_SEEDS = [11]

# ---- Üretim (K7) ----
# top_k ve repetition_penalty AÇIKÇA veriliyor: transformers>=5'te bu iki alanın
# GenerationConfig varsayılanı None olduğu için değerler MODELİN kendi
# generation_config.json'undan geliyordu (Qwen2.5-7B: top_k=20,
# repetition_penalty=1.05; 1.5B: 1.1). K7'de yazılı olmayan bu iki parametre
# örneklem entropisini -- ve dolayısıyla ölçtüğümüz filigran gücünü --
# etkilerdi. Kapatarak üretim ayarını tam belirlenmiş hâle getiriyoruz.
# ⛔ BU AYAR KORPUSU GEÇERSİZ KILDI (tur-2 denetimi + preflight taraması):
#   * max_new_tokens=320 -> istemler 300 KELİME istiyor, bereket 2,585 ile bu
#     ~776 token gerektirir. 0/384 metin hedefe ulaştı, %95,8'i kesik.
#   * top_k=0 / repetition_penalty=1.0 (S3 düzeltmesi) -> ölçüldü: modelin
#     KENDİ ayarına (top_k=20, rep=1.05) kıyasla 7B'de ortalama kelime
#     160 vs 239, kesik bitiş 4 vs 8, temiz metin 2/16 vs 4/16. S3'ün
#     gerekçesi (şemalar arası karşılaştırılabilirlik) doğruydu ama metin
#     kalitesine etkisi hiç ölçülmemişti.
# Ana çalışma için önerilen: max_new_tokens>=1000, top_k=20 (SABİT, üç şemada
# da aynı -> hem kuyruk kapalı hem karşılaştırılabilir), rep=1.0.
# Tarama sonuçları: results/preflight_sweep.json · ön-kapı: pilot.dev_preflight
GEN_KWARGS = dict(max_new_tokens=320, min_new_tokens=200,
                  do_sample=True, temperature=0.8, top_p=0.95,
                  top_k=0, repetition_penalty=1.0)
TEMPERATURE = 0.8                 # K7b: EXP bunu tcfg ATTRIBUTE'undan okur; run.py elle atar.
MIN_COMPLETION_TOKENS = 150       # altı "short" bayrağı (filigran kısa metinde zayıf)

# ---- Şemalar (K2, K3) ----
SCHEMES = ["KGW", "EXP", "SynthID"]
SCHEME_CONFIGS = {
    "KGW":     "config/KGW.json",        # repo varsayılanı: gamma .5, delta 2.0
    "EXP":     "pilot/exp_pilot.json",   # sequence_length 300 (repo config'ine dokunmuyoruz)
    "SynthID": "config/SynthID.json",    # mean dedektör, eğitimsiz
}
# stat = yön-düzeltilmiş istatistik; her şemada YÜKSEK stat = filigranlı (K3 / Ek D).
# KGW: z-skoru (+), SynthID: mean g-skoru (+), EXP: p-value (-) -> stat = -log10(p)
SCORE_DIRECTION = {"KGW": +1, "SynthID": +1, "EXP": -1}

# EXP'in üreteceği token sayısı. exp_pilot.json'daki 300 ile AYNI -> pilot davranışı
# DEĞİŞMEZ. Buraya taşınmasının sebebi: EXP EOS'ta durmaz, uzunluğu bu değer sabitler;
# max_new_tokens ile ayrı yerlerde tutulursa sessizce ayrışırlar. Artık tek yerden
# verilebiliyor (generate.load_scheme -> AutoWatermark.load kwargs; watermark/base.py:44
# config_dict.update(kwargs) ile JSON'u eziyor -- kaynaktan doğrulandı).
EXP_SEQUENCE_LENGTH = 300

# ---- Korpus kabul ölçütleri (ön-kapı ile AYNI, hpc/README.md'de ön-kayıtlı) ----
# İSTEMDEKİ sayı ile ÖLÇÜTTEKİ sayı ARTIK FARKLI ve bu bilinçli:
# istemler 500 kelime ister çünkü model istenenin %72-80'ini teslim ediyor
# (ölçüldü: Qwen3-14B, results_hpc/onkapi_*.jsonl); kabul ölçütü 300'de kaldı.
# metrics bu değeri istemden OKUMAMALI -- okusa 500 sanır ve korpusu haksız yere
# kusurlu ilan eder.
KAPI_HEDEF_KELIME = 300
# Oranlar ön-kapının KAPI >= 12/16 ölçütüyle aynı ruhta; rapor bu eşiklerin
# ALTINDA kalırsa ⛔ hükmü basar, ÜSTÜNDE kalırsa basmaz. Koşudan önce sabit.
KORPUS_UYUM_ESIGI = 0.75          # hedef kelimeye ulaşan metin oranı
KORPUS_SONLANDIRMA_ESIGI = 0.90   # sonlandırıcı noktalama ile biten oran
# Kalite katmanının (e5 kosinüsü, LLM-yargıç) ANLAMLI sayılabilmesi için azami
# Latin-dışı kirlenme oranı. Bu değer İKİ ayrı yerde sabit yazılıydı
# (corpus_integrity ve Kalite bölümü); biri değişirse rapor kendi içinde
# çelişirdi ("korpus temiz" + "kalite geri çekildi"). Tek kaynağa alındı.
KORPUS_KIRLENME_ESIGI = 0.05

# Şema-özel gen_kwargs ezmeleri (yalnız filigranlı üretim yolunu etkiler).
# SynthID'nin logits işlemcisi scores'u KENDİSİ config.temperature'a bölüyor
# (synthid.py: `scores_processed = scores / self.config.temperature`).
# transformers 5.10.2'de özel logits_processor HF'in TemperatureLogitsWarper'ından
# ÖNCE çalışıyor (ölçüldü: ['<özel>', 'TemperatureLogitsWarper', 'TopPLogitsWarper'])
# -> sıcaklık iki kez uygulanıyor, SynthID etkin T=0.64 iken KGW/EXP/negatifler
# 0.8'de kalıyordu. gen_kwargs'ta temperature=1.0 vererek HF'in ikinci
# uygulamasını kapatıyoruz; etkin sıcaklık üç şemada da 0.8 oluyor.
SCHEME_GEN_OVERRIDES = {"SynthID": {"temperature": 1.0}}

# ---- Saldırılar (K9) ----
# morph = v0 (R1 -Iyor->-mAktAdIr, R2 -DIğI için->-DIğIndAn) — DEĞİŞMEDEN durur.
# morph_v1 = v0 + R3 (kopula -DIr düşürme). Gerekçe: v0'ın ölçülen kapsamı bu
# korpusta kelimelerin %0,36'sı (LLM resmî Türkçe yazıyor, -Iyor kaydını
# kullanmıyor) -> ΔAUROC 0,000. v1 kapsamı %1,08. İkisi de ayrı koşul olarak
# raporlanır; kapsam-etki ilişkisi kendisi bir bulgudur.
ATTACKS = ["dia100", "dia50", "morph", "morph+dia", "morph_v1", "morph_v1+dia",
           "rtt", "para", "launder", "launder_api"]
LIGHT_ATTACKS = {"dia100", "dia50", "morph", "morph+dia",
                 "morph_v1", "morph_v1+dia"}   # model gerektirmez

# ---- Modeller (K6) ----
MODEL_TIERS = [                    # (min birleşik RAM GB, HF model adı)
    (32, "Qwen/Qwen2.5-7B-Instruct"),
    (24, "Qwen/Qwen2.5-7B-Instruct"),   # sınırda; bellek baskısında --model ile 3B'ye in
    (16, "Qwen/Qwen2.5-3B-Instruct"),
    (0,  "Qwen/Qwen2.5-1.5B-Instruct"),
]
SMOKE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
NLLB_MODEL = "facebook/nllb-200-distilled-600M"
E5_MODEL = "intfloat/multilingual-e5-base"

# ---- Metrikler (K10) ----
BOOTSTRAP_N = 1000
TPR_AT_FPR = 0.01
SANITY_AUROC = 0.90               # Faz 1 öncül eşiği (KGW temiz)
QUALITY_SUBSAMPLE = 40            # morf-vs-para ayrışma analizi örneklem boyutu

# scores.csv sütun şeması (detect.py yazar, metrics.py okur)
SCORES_CSV_FIELDS = [
    "scheme", "condition", "wm", "prompt_id", "seed",
    "score", "stat", "n_tokens", "edits", "rejected", "short", "src",
]


def detect_ram_gb() -> float:
    """macOS: sysctl hw.memsize; Linux fallback: /proc/meminfo."""
    import subprocess
    try:
        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
        return int(out.strip()) / 1e9
    except Exception:
        try:
            with open("/proc/meminfo") as f:
                return int(f.readline().split()[1]) / 1e6
        except Exception:
            return 16.0


def pick_model(ram_gb: float | None = None) -> tuple[str, float]:
    ram = detect_ram_gb() if ram_gb is None else float(ram_gb)
    for min_gb, name in MODEL_TIERS:
        if ram >= min_gb:
            return name, ram
    return MODEL_TIERS[-1][1], ram
