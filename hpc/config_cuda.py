# hpc/config_cuda.py — pilot/config.py'nin CUDA/RTX 8000 için EZMELERİ.
#
# pilot/config.py DEĞİŞTİRİLMEZ. Oradaki sabitler iki turluk bağımsız denetimden geçti;
# fork'lamak iki kaynak doğruluk yaratır. Burada yalnız ORTAMA bağlı olanlar eziliyor ve
# her ezmenin gerekçesi ÖLÇÜLMÜŞ bir sayıdır.
#
#   from hpc import config_cuda as H
#   H.dogrula()                       # ortam beklenene uyuyor mu
#   H.vram_tahmini_gb(14)             # 14B fp16 kaç GB
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot.config import *            # noqa: F401,F403  — taban sabitler
from pilot import config as _P

# ---------------------------------------------------------------- cihaz ve dtype
DEVICE = "cuda"

# fp16 ZORUNLU. Ölçüldü (2026-08-19, Quadro RTX 8000, 4096^2 matmul):
#     fp16 82,1 TFLOPS | bf16 7,3 TFLOPS | fp32 13,4 TFLOPS
# sm_75 (Turing) native bf16 tensor çekirdeği İÇERMEZ; bf16 emülasyondur ve
# fp32'den bile yavaştır. torch.cuda.is_bf16_supported() True döner -- YANILTICIDIR;
# including_emulation=False ile False döner. dtype="auto" çoğu modern modelin
# config'inden bf16 seçeceği için ASLA kullanılmaz.
DTYPE = "float16"
BF16_YASAK_GEREKCE = "sm_75 native bf16 yok; ölçülen fp16/bf16 hız oranı 11,2x"

# transformers v5'te from_pretrained parametresi `torch_dtype` -> `dtype` olarak
# yeniden adlandırıldı. HANGİSİNİN geçerli olduğu ORTAMDA ölçülür:
#     python hpc/remote_scripts/drift.py     -> T1_dtype_kwarg
# Yanlış ad sessizce yutulursa model fp32 yüklenir (14B = 56 GB) ve OOM olur.
DTYPE_KWARG_OLCULMELI = "hpc/remote_scripts/drift.py :: T1_dtype_kwarg"

# Turing FlashAttention-2 desteklemez (ölçüldü: is_flash_attn_2_available() False).
# ⚠ PROVENANS NOTU: bu deger denetime kadar KOSUYA HIC GIRMEDI -- run.py'nin
# ezme listesi elle tutuluyordu ve bu ad listede yoktu; generate.py None gorup
# transformers'in kendi secimine dusuyordu (v5'te bu da sdpa'dir, yani FIILEN
# ayni cekirdek kullanildi ama bunu BIZ secmedik ve env.json'a yazilmadi).
# Mevcut korpus O REJIMDE uretildi; bu satir artik gelecek kosulari baglar.
ATTN_IMPLEMENTATION = "sdpa"

# ---------------------------------------------------------------- VRAM bütçesi
VRAM_TOPLAM_GB = 50.8            # ölçüldü: torch.cuda.get_device_properties(0)
VRAM_GUVENLI_GB = 46.0           # KV önbelleği + aktivasyonlar + parçalanma payı


def vram_tahmini_gb(param_milyar: float, dtype_bayt: int = 2) -> float:
    """Yalnız AĞIRLIKLAR. KV önbelleği ve aktivasyonlar HARİÇ -- onlar için
    VRAM_GUVENLI_GB tamponu var. Nicemleme K4 ile YASAK, bu yüzden 2 bayt sabit."""
    return param_milyar * dtype_bayt


def sigar_mi(param_milyar: float) -> tuple[bool, str]:
    a = vram_tahmini_gb(param_milyar)
    if a > VRAM_GUVENLI_GB:
        return False, (f"{param_milyar}B fp16 = {a:.0f} GB ağırlık > {VRAM_GUVENLI_GB:.0f} GB "
                       f"güvenli sınır. Nicemleme K4 ile yasak -> SIĞMAZ.")
    return True, f"{param_milyar}B fp16 = {a:.0f} GB ağırlık, KV için ~{VRAM_GUVENLI_GB - a:.0f} GB kalır."


# ---------------------------------------------------------------- üretim ayarları
# pilot/config.py:22-32 bu korpusun NEDEN geçersiz olduğunu ve düzeltmenin ne olduğunu
# koddan üretilen ölçümlerle yazıyor. Buradaki değerler O TAVSİYENİN birebir uygulanmış
# hâlidir; yeni bir karar DEĞİLDİR:
#   * max_new_tokens 320 -> istem 300 kelime istiyor, bereket 2,585 tok/kelime,
#     yani ~776 token gerekir. 0/384 metin hedefe ulaşmıştı.
#   * top_k=0 ölçülen ZARAR verdi (7B'de ortalama 160 vs 239 kelime, temiz metin 2/16
#     vs 4/16). Modelin kendi değeri olan 20, ÜÇ ŞEMADA DA SABİT veriliyor: hem çok
#     dilli kuyruk kapanıyor hem şemalar arası karşılaştırılabilirlik korunuyor.
# max_new_tokens ÖLÇÜMDEN türetildi (Qwen3-14B, istem 500 kelime, bereket 2,623 tok/kelime):
#   bütçe 1024 -> 2/16 metin tavanda kesildi (en uzunu 408 kelime)
#   bütçe 1400 -> 1/16 metin HÂLÂ kesildi (566 kelime ~ 1485 token > 1400)
#   bütçe 1800 -> ~686 kelimeye kadar pay; kesilen metnin 566'sı rahat sığar
# Tavanı yükseltmenin süre maliyeti İHMAL EDİLEBİLİR: üretim süresi ÜRETİLEN token ile
# ölçeklenir, tavanla değil. Metinlerin çoğu ~950 token'da EOS ile doğal biter; tavanı
# yalnız uç örnekler kullanır. Kesiklik, pilot korpusunu geçersiz kılan kusurun ta
# kendisiydi (%95,8) -- %6,25'e inmiş olması onu kabul edilebilir yapmaz.
GEN_KWARGS = dict(
    _P.GEN_KWARGS,
    max_new_tokens=1800,
    min_new_tokens=400,
    top_k=20,
    repetition_penalty=1.0,
)

# ⚠ EXP TAVANA BAĞLANMAZ. EXP EOS'ta DURMAZ: tam olarak sequence_length kadar token
# üretir. KGW/SynthID/negatifler ise doğal olarak biter (ölçülen medyan 926 token).
# EXP'i max_new_tokens'a (1400) eşitlemek EXP metinlerini ~534 kelime, diğerlerini
# ~358 kelime yapar -- şemalar arasında SİSTEMATİK UZUNLUK ASİMETRİSİ, yani tam da
# önlemek istediğimiz şey. Bu dosyanın ilk sürümünde tam bu hata vardı
# (EXP_SEQUENCE_LENGTH = max_new_tokens + eşitlik assert'i).
#
# Doğru bağlanma noktası GÖZLENEN MEDYAN'dır. 926, bütçe 1024 iken ölçüldü ve
# 2/16 metin tavanda kesikti; tavan kalkınca medyan bir miktar YÜKSELİR.
# Bu yüzden değer, resmî koşunun kendi verisinden yeniden ölçülmeli.
EXP_SEQUENCE_LENGTH = 950                  # ölçülen medyan 926 + küçük pay
EXP_UZUNLUK_OLCULMELI = (
    "results_hpc/onkapi_*.jsonl üzerinden KGW/SynthID token medyanını yeniden "
    "hesapla; EXP_SEQUENCE_LENGTH ondan sapıyorsa güncelle (şema uzunlukları "
    "karşılaştırılabilir kalmalı)")

# SynthID çift-sıcaklık ezmesi pilot/config.py:50-58'de AMPİRİK olarak ölçülmüş bir
# logits_processor SIRALAMASINA dayanıyor; ölçüm transformers 5.10.2'de yapıldı ve o
# sürüm artık hiçbir ortamda kurulu değil (yerel 5.15.0, HPC 5.8.0).
# drift.py :: T2_islemci_sirasi bunu YENİDEN ölçer. Sonuç "SONRA" çıkarsa bu ezme
# YANLIŞ olur ve kaldırılmalıdır -- ölçüm görülmeden koşu başlatılmaz.
SCHEME_GEN_OVERRIDES_OLCULMELI = "hpc/remote_scripts/drift.py :: T2_islemci_sirasi"

# ---------------------------------------------------------------- model seçimi
# pilot/config.py MODEL_TIERS'i macOS birleşik belleğine göre kuruluyordu
# (detect_ram_gb -> sysctl hw.memsize). Burada kısıt VRAM'dir.
#
# ⚠ MODEL KARARI AÇIK. Qwen2.5-3B ve 7B ön-kapıyı 5 konfigürasyonda geçemedi
# (%36 Latin-dışı kirlenme). Groq duman testi görevin YAPILABİLİR ve kapının doğru
# kalibre olduğunu kanıtladı, ama oradaki kazananlar bu GPU'ya sığmıyor:
#     qwen3.6-27b  -> 54 GB  SIĞMAZ
#     gpt-oss-20b  -> 40 GB  sınırda + MoE (filigran logits işlemcisiyle riskli)
# Aday seçimi ayrı bir analizle yürüyor. Karar verilene kadar VARSAYILAN YOK:
# model AÇIKÇA verilmeli ki sessizce yanlış modelle koşu başlamasın.
VARSAYILAN_MODEL = None


def model_sec(ad: str | None, param_milyar: float | None = None) -> str:
    if not ad:
        raise SystemExit(
            "HATA: model açıkça verilmeli (--model). Varsayılan bilinçli olarak YOK:\n"
            "  Qwen2.5-3B/7B ön-kapıyı geçemedi, kapıyı geçen 27B bu GPU'ya sığmıyor.\n"
            "  Aday listesi ve VRAM hesabı için: hpc/README.md")
    if param_milyar is not None:
        ok, mesaj = sigar_mi(param_milyar)
        print(("  VRAM: " if ok else "  ⛔ VRAM: ") + mesaj)
        if not ok:
            raise SystemExit(1)
    return ad


# ---------------------------------------------------------------- ortam doğrulaması
def dogrula(katı: bool = True) -> dict:
    """Koşudan ÖNCE ortamın beklenene uyduğunu doğrula. Sessiz sapma olmasın."""
    import torch

    r: dict = {}
    r["cuda"] = torch.cuda.is_available()
    if not r["cuda"]:
        if katı:
            raise SystemExit("⛔ CUDA yok. Bu modül yalnız TF-HPC içindir.")
        return r
    p = torch.cuda.get_device_properties(0)
    r |= {"gpu": p.name, "sm": f"{p.major}.{p.minor}",
          "vram_gb": round(p.total_memory / 1e9, 1),
          "bos_vram_gb": round(torch.cuda.mem_get_info()[0] / 1e9, 1)}
    r["bf16_native"] = False
    try:
        r["bf16_native"] = torch.cuda.is_bf16_supported(including_emulation=False)
    except TypeError:
        r["bf16_native"] = "BELIRSIZ"
    if r["bf16_native"] is True:
        print("  NOT: bu GPU native bf16 destekliyor -- DTYPE kararı yeniden ölçülmeli "
              "(bu dosyadaki fp16 gerekçesi RTX 8000'e özgüdür).")
    for k, v in r.items():
        print(f"  {k:14s} {v}")
    return r
