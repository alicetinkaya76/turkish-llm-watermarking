#!/usr/bin/env bash
# hpc/remote_scripts/bootstrap.sh — konteyner kurulumu. [KONTEYNERDE ÇALIŞIR]
#
# YENİDEN ÇALIŞTIRILABİLİR (idempotent): konteyner yeniden başlarsa tekrar koştur.
#
# TASARIM KARARLARI ve gerekçeleri:
#
# 1) HER ŞEY /workspace ALTINDA. Konteynerin kök dosya sistemi OVERLAY'dir; JupyterHub
#    idle-culler sunucuyu durdurunca yazılabilir overlay katmanı gider. /workspace ise
#    ayrı bir ext4 blok cihazdır (ölçüldü: /dev/mapper/ubuntu--vg-ubuntu--lv).
#    Varsayılan HF önbelleği ~/.cache/huggingface OVERLAY'DE olurdu -> 30 GB'lık model
#    her yeniden başlatmada uçardı. HF_HOME'u taşımak bu yüzden ZORUNLU.
#
# 2) venv --system-site-packages. torch 2.10.0+cu128 sistemde KURULU ve bu GPU'nun
#    sürücüsüyle eşleşiyor. Temiz venv 3 GB'lık torch'u yeniden indirir ve CUDA
#    eşleşmesini bozma riski taşır. Sistem paketlerini miras alıp ÜZERİNE saf-python
#    paketleri kuruyoruz. torch ASLA yükseltilmez.
#
# 3) transformers YEREL SÜRÜME SABİTLENİR (varsayılan 5.15.0). Gerekçe: pilot kodundaki
#    kararlar transformers davranışına bağlı; iki ortam farklı sürümdeyse sonuçlar
#    karşılaştırılamaz. HPC'de 5.8.0 geliyordu. Sistem sürümünü korumak için:
#      bootstrap.sh --system-transformers
#    Hangisi seçilirse seçilsin drift.py ÇALIŞTIRILMALI -- davranış ölçülmeden varsayılmaz.
#
# 4) zeyrek 0.1.3'e sabitlenir. TUZAK: `zeyrek.__version__` "0.1.2" DER ve YANLIŞTIR --
#    0.1.3 tekerleğinin içindeki sabit güncellenmemiş. Gerçek sürüm yalnız
#    importlib.metadata.version("zeyrek") ile okunur; yerelde ölçüldü: 0.1.3
#    (requirements_resolved.txt:61 ile tutarlı). İlk sürümde __version__'a bakıp
#    yanlışlıkla 0.1.2 pinlemiştim.
#
# 5) MarkLLM upstream'den SABİT COMMIT ile klonlanır (yerel klonu yüklemek yerine):
#    tekrarlanabilir ve 5.8 MB'lık results/ taşınmaz. Yerelde izlenen dosyalarda
#    değişiklik olmadığı doğrulandı -> klon birebir aynı çekirdeği verir.
#
#   bash hpc/remote_scripts/bootstrap.sh [--system-transformers]
set -euo pipefail

WS=/workspace
MARK="$WS/MarkLLM"
REPO=https://github.com/THU-BPM/MarkLLM.git
COMMIT=c45ddc40f7b761beabe55a1b8dc4690e531d1c6d
TRANSFORMERS_PIN="transformers==5.15.0"

for a in "$@"; do
  [ "$a" = "--system-transformers" ] && TRANSFORMERS_PIN=""
done

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------- 1. dizinler + ortam
say "1/6  kalıcı dizinler ve ortam değişkenleri"
mkdir -p "$WS"/{hf,logs,runs,MarkLLM}
cat > "$WS/env.sh" <<'EOF'
# /workspace/env.sh — her oturumda source edilmeli. bootstrap.sh üretir.
# HF_HUB_CACHE, HF_HOME/hub DEĞİL doğrudan /workspace/hf: paralel çalışan diğer oturum
# snapshot_download(cache_dir="/workspace/hf") kullandığı için modeller ORADA duruyor
# (models--Qwen--Qwen3.8-27B, 52 GB). Alt dizini işaret etseydik aynı modeli yeniden
# indirirdik. Önbellek bilinçli olarak PAYLAŞILIYOR.
export HF_HOME=/workspace/hf
export HF_HUB_CACHE=/workspace/hf
export TRANSFORMERS_CACHE=/workspace/hf
export NLTK_DATA=/workspace/hf/nltk
export TOKENIZERS_PARALLELISM=false
export PATH=/workspace/venv/bin:$PATH
export PYTHONPATH=/workspace/MarkLLM:${PYTHONPATH:-}
EOF
grep -q "workspace/env.sh" ~/.bashrc 2>/dev/null || echo 'source /workspace/env.sh' >> ~/.bashrc
# shellcheck disable=SC1091
source "$WS/env.sh"
echo "  HF_HOME=$HF_HOME  (overlay DEĞİL -- yeniden başlatmada korunur)"

# ---------------------------------------------------------------- 2. kota ölçümü
say "2/6  disk kotası (mount seçeneklerinde usrquota,grpquota var; değer bilinmiyordu)"
df -h "$WS" | tail -1 | awk '{print "  dosya sistemi: "$2" toplam, "$4" boş, %"$5" dolu"}'
if command -v quota >/dev/null 2>&1; then quota -s 2>&1 | head -4 | sed 's/^/  /'
else echo "  quota komutu yok -> kota SINIRI OKUNAMIYOR; gerçek tüketim izlenerek ölçülecek"; fi
du -sh "$WS" 2>/dev/null | awk '{print "  /workspace şu an: "$1}'

# ---------------------------------------------------------------- 3. venv
say "3/6  sanal ortam (sistem paketlerini miras alır; torch KORUNUR)"
# SİSTEM python'u MUTLAK yolla sabitlenir. env.sh PATH'in başına /workspace/venv/bin
# koyuyor; o dizin silindikten sonra kabuk `python3`ü ÖNBELLEKTEN eski yolda arayıp
# rc=127 veriyordu (ölçüldü). hash -r + mutlak yol ikisini birden kapatır.
SYSPY=/usr/bin/python3
[ -x "$SYSPY" ] || SYSPY=$(PATH=/usr/local/bin:/usr/bin:/bin command -v python3)
hash -r 2>/dev/null || true

# Konteynerde ensurepip YOK (ölçüldü: "apt install python3.12-venv" hatası).
# Konteynerde root'uz, apt kullanılabilir.
if ! "$SYSPY" -c "import ensurepip" 2>/dev/null; then
  echo "  ensurepip yok -> python3-venv kuruluyor"
  apt-get update -qq && apt-get install -y -qq "python3-venv" >/dev/null 2>&1 || \
    apt-get install -y -qq "python$("$SYSPY" -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')-venv" >/dev/null
  "$SYSPY" -c "import ensurepip" 2>/dev/null || { echo "  ⛔ python3-venv kurulamadı"; exit 1; }
  echo "  kuruldu"
fi
# VARLIK değil KULLANILABİLİRLİK sınanır: ensurepip'siz ilk denemeden kalan venv'de
# bin/python VAR ama pip YOK. Sadece dosya varlığına bakmak o kırık venv'i sağlam sanar.
if "$WS/venv/bin/python" -m pip --version >/dev/null 2>&1; then
  echo "  zaten var ve çalışıyor: $WS/venv"
else
  [ -e "$WS/venv" ] && { echo "  mevcut venv kırık (pip yok) -> siliniyor"; rm -rf "$WS/venv"; hash -r 2>/dev/null || true; }
  "$SYSPY" -m venv --system-site-packages "$WS/venv"
  echo "  oluşturuldu: $WS/venv"
fi
"$WS/venv/bin/python" -m pip install -q --upgrade pip
TORCH_ONCE=$("$WS/venv/bin/python" -c "import torch;print(torch.__version__)")
echo "  kurulum öncesi torch: $TORCH_ONCE"

# ---------------------------------------------------------------- 4. paketler
say "4/6  paketler (torch ASLA yükseltilmez)"
"$WS/venv/bin/pip" install -q \
  ${TRANSFORMERS_PIN:+"$TRANSFORMERS_PIN"} \
  "zeyrek==0.1.3" \
  sentence-transformers nltk scikit-learn scipy pandas numpy matplotlib \
  python-dotenv requests urllib3 websocket-client anthropic \
  sacrebleu sentencepiece accelerate datasets
TORCH_SONRA=$("$WS/venv/bin/python" -c "import torch;print(torch.__version__)")
if [ "$TORCH_ONCE" != "$TORCH_SONRA" ]; then
  echo "  ⛔ HATA: torch değişti ($TORCH_ONCE -> $TORCH_SONRA). CUDA eşleşmesi bozulmuş olabilir."
  exit 1
fi
echo "  torch korundu: $TORCH_SONRA"
"$WS/venv/bin/python" -m nltk.downloader -d "$NLTK_DATA" punkt punkt_tab >/dev/null 2>&1 || \
  echo "  UYARI: nltk verisi indirilemedi (rtt/para saldırıları için gerekebilir)"

# ---------------------------------------------------------------- 5. MarkLLM çekirdeği
say "5/6  MarkLLM çekirdeği (sabit commit)"
if [ ! -d "$MARK/.git" ]; then
  git clone -q "$REPO" "$MARK.tmp"
  # pilot/ ve hpc/ önceden gönderilmiş olabilir; klonu üzerine taşı, onları koru
  mv "$MARK.tmp/.git" "$MARK/.git"
  rm -rf "$MARK.tmp"
  git -C "$MARK" checkout -q --force "$COMMIT"
else
  git -C "$MARK" fetch -q origin && git -C "$MARK" checkout -q --force "$COMMIT"
fi
echo "  commit: $(git -C "$MARK" rev-parse HEAD)"
[ "$(git -C "$MARK" rev-parse HEAD)" = "$COMMIT" ] || { echo "  ⛔ commit eşleşmedi"; exit 1; }

# ---------------------------------------------------------------- 6. doğrulama
say "6/6  doğrulama"
cd "$MARK"
"$WS/venv/bin/python" - <<'PY'
import sys, torch, transformers
print(f"  python       {sys.version.split()[0]}")
print(f"  torch        {torch.__version__}  cuda={torch.cuda.is_available()}")
print(f"  transformers {transformers.__version__}")
if torch.cuda.is_available():
    p = torch.cuda.get_device_properties(0)
    print(f"  gpu          {p.name}  sm_{p.major}{p.minor}  {p.total_memory/1e9:.1f} GB")
eksik = []
import importlib.metadata as _md
for _pkg, _bek in (("zeyrek", "0.1.3"),):
    try:
        _g = _md.version(_pkg)   # __version__ DEGIL: 0.1.3 tekerlegi "0.1.2" der
        _not = "" if _g == _bek else f"  UYARI: {_bek} bekleniyordu"
        print(f"  {_pkg:13s}: {_g}{_not}")
    except Exception as _e:
        print(f"  {_pkg:13s}: surum okunamadi ({type(_e).__name__})")
for m in ("zeyrek", "sentence_transformers", "nltk", "sklearn", "scipy",
          "pandas", "numpy", "dotenv", "anthropic", "websocket"):
    try:
        __import__(m)
    except ImportError:
        eksik.append(m)
print("  eksik paket  :", eksik or "yok")
try:
    from utils.transformers_config import TransformersConfig       # noqa: F401
    from watermark.auto_watermark import AutoWatermark             # noqa: F401
    print("  MarkLLM      : içe aktarıldı")
except Exception as e:
    print(f"  MarkLLM      : ⛔ {type(e).__name__}: {e}")
    sys.exit(1)
sys.exit(1 if eksik else 0)
PY

say "KURULUM TAMAM"
cat <<EOF
  kök       : $MARK
  venv      : $WS/venv     (source /workspace/env.sh)
  HF önbellek: $HF_HOME
  loglar    : $WS/logs

  SIRADAKİ ADIM -- sürüm kayması ölçümü (taşımanın ön koşulu):
    cd $MARK && python hpc/remote_scripts/drift.py
EOF
