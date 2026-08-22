# hpc/deploy.py — yerelden TF-HPC'ye tek komutla kurulum. [YEREL ÇALIŞIR]
#
# AKIŞ: kod gönder -> bootstrap çalıştır -> sürüm kaymasını ÖLÇ.
# Üçüncü adım isteğe bağlı değil: pilot/ kodundaki bazı kararlar yerel ortamda
# ölçülmüş davranışlara dayanıyor ve hedef ortam farklı sürümlerde (bkz. hpc/README.md).
#
# NE GÖNDERİLİR: pilot/ (bilimsel kod), hpc/ (ortam katmanı), patches/, config/.
# NE GÖNDERİLMEZ: results/ (5,8 MB, geçersiz korpus), .git, MarkLLM çekirdeği
# (o, sabit commit'ten klonlanır -> tekrarlanabilir).
#
#   python -m hpc.deploy                 # gönder + kur
#   python -m hpc.deploy --drift         # + sürüm kayması ölçümü
#   python -m hpc.deploy --only-push     # yalnız kodu tazele
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from hpc.remote import REMOTE_ROOT, connect  # noqa: E402

GONDERILECEK = ["pilot", "hpc", "patches"]


def main() -> None:
    ap = argparse.ArgumentParser(description="TF-HPC kurulumu")
    ap.add_argument("--only-push", action="store_true", help="yalnız kodu gönder")
    ap.add_argument("--drift", action="store_true", help="kurulumdan sonra sürüm kaymasını ölç")
    ap.add_argument("--system-transformers", action="store_true",
                    help="transformers'ı yerel sürüme sabitleme, HPC'dekini koru")
    ap.add_argument("--drift-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    args = ap.parse_args()

    h = connect()
    try:
        print(f"HEDEF: {REMOTE_ROOT}\n")
        print("1) kod gönderiliyor")
        for d in GONDERILECEK:
            src = _ROOT / d
            if not src.is_dir():
                print(f"   {d:10s} ATLANDI (yok)")
                continue
            n = h.push_dir(src, REMOTE_ROOT)
            print(f"   {d:10s} {n / 1024:7.0f} KiB")

        if args.only_push:
            print("\n--only-push verildi, kurulum atlandı.")
            return

        print("\n2) bootstrap (uzun sürebilir; pip + git clone)")
        bayrak = " --system-transformers" if args.system_transformers else ""
        out, err, rc = h.sh(
            f"cd {REMOTE_ROOT} && bash hpc/remote_scripts/bootstrap.sh{bayrak} 2>&1",
            timeout=2400)
        print(out)
        if rc != 0:
            print(f"\n⛔ bootstrap BAŞARISIZ (rc={rc})", file=sys.stderr)
            if err.strip():
                print(err, file=sys.stderr)
            sys.exit(1)

        if not args.drift:
            print("\nKurulum tamam. Sürüm kayması ÖLÇÜLMEDİ -- taşımadan önce şart:")
            print("  python -m hpc.deploy --drift")
            return

        print("\n3) sürüm kayması ölçümü")
        out, err, rc = h.sh(
            f"cd {REMOTE_ROOT} && python hpc/remote_scripts/drift.py "
            f"--model {args.drift_model} 2>&1", timeout=2400, venv=True)
        print(out)
        if err.strip():
            print("--- stderr ---\n" + err, file=sys.stderr)
        try:
            Path(_ROOT / "results_hpc").mkdir(exist_ok=True)
            blob = h.get_bytes(f"{REMOTE_ROOT}/results_hpc/drift.json")
            (_ROOT / "results_hpc" / "drift.json").write_bytes(blob)
            print(f"\ndrift.json yerele alındı: results_hpc/drift.json ({len(blob)} bayt)")
        except Exception as e:
            print(f"\nUYARI: drift.json indirilemedi ({type(e).__name__}) -- "
                  "ölçüm uzakta kalmış olabilir.", file=sys.stderr)
        if rc != 0:
            print("\n⛔ Sürüm kayması ölçümü BLOKE EDİCİ bulgu verdi (yukarı bak).",
                  file=sys.stderr)
            sys.exit(2)
    finally:
        h.close()


if __name__ == "__main__":
    main()
