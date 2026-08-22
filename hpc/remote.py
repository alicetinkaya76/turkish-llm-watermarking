# hpc/remote.py — Selçuk TF-HPC (JupyterHub) uzaktan yürütme istemcisi. [YEREL ÇALIŞIR]
#
# Bu dosya pilot/dev_hpc.py'den TAŞINDI: ortama ait her şey hpc/ altında toplanıyor,
# pilot/ yalnız bilimsel kodu tutuyor. İki kaynak doğruluk olmasın.
#
# ORTAM (2026-08-19 ölçüldü, hpc/README.md'de tam envanter):
#   JupyterHub 4.1.6 -> kullanıcı başına Docker konteyneri, içinde root, cwd=/workspace.
#   SSH/SLURM YOK. tfhpc.selcuk.edu.tr -> 172.22.202.23 (RFC1918), yalnız VPN üzerinden.
#   Kendinden imzalı sertifika -> verify=False ZORUNLU; ALLOWED_HOST ile sınırlandırıldı.
#
# KİMLİK DOĞRULAMA: JupyterHub API token'ı (.env -> TFHPC_TOKEN). PAROLA KULLANILMAZ:
# token iptal edilebilir ve kapsamı sınırlıdır, parola değildir.
#
#   python -m hpc.remote probe
#   python -m hpc.remote sh "nvidia-smi"
#   python -m hpc.remote push pilot --dest /workspace/MarkLLM
#   python -m hpc.remote get /workspace/MarkLLM/results/scores.csv ./scores.csv
from __future__ import annotations

import argparse
import base64
import io
import json
import pathlib
import ssl
import sys
import tarfile
import time
import uuid
from pathlib import Path

import requests
import urllib3
import websocket
from dotenv import dotenv_values

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# verify=False yalnız bu host için. Hedef kayarsa sessizce güvensiz istek
# atmayalım diye açık beyaz liste.
ALLOWED_HOST = "tfhpc.selcuk.edu.tr"
DEFAULT_URL = f"https://{ALLOWED_HOST}"
REMOTE_ROOT = "/workspace/MarkLLM"

PROBE = r"""
echo "=== GPU ==="
nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu,driver_version --format=csv 2>&1 | head -10
echo "=== CPU / RAM ==="
echo "konteynere ayrilan cekirdek: $(nproc)"; free -g 2>/dev/null | head -2
echo "=== DISK ==="
df -h /workspace / 2>&1
echo "=== KALICILIK ==="
mount 2>/dev/null | grep -E " /workspace | / " | head -4
echo "=== HF ONBELLEGI (overlay'de OLMAMALI) ==="
echo "HF_HOME=${HF_HOME:-<AYARSIZ - overlay riski>}"
du -sh "${HF_HOME:-$HOME/.cache/huggingface}" 2>/dev/null || echo "  onbellek yok"
echo "=== YIGIN ==="
python3 -V
python3 -c "import torch,transformers;print(f'torch {torch.__version__} | transformers {transformers.__version__} | cuda {torch.cuda.is_available()}')" 2>&1 | tail -1
[ -x /workspace/venv/bin/python ] && /workspace/venv/bin/python -c "import torch,transformers;print(f'venv: torch {torch.__version__} | transformers {transformers.__version__}')" || echo "venv: kurulu degil"
"""


class HPC:
    def __init__(self, base: str, user: str, token: str):
        if ALLOWED_HOST not in base:
            raise SystemExit(f"HATA: yalnız {ALLOWED_HOST} destekleniyor (verify=False bu hosta bağlı).")
        self.base, self.user, self.token = base.rstrip("/"), user, token
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"token {token}"
        self.s.verify = False          # kendinden imzalı sertifika (yukarıdaki not)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.srv = f"{self.base}/user/{user}"
        self.kid: str | None = None

    # --- sunucu / çekirdek yaşam döngüsü ---
    def ensure_server(self, wait: int = 180) -> None:
        """Kullanıcı sunucusu uykudaysa uyandır. JupyterHub idle-culler konteyneri
        durdurmuş olabilir; bu durumda overlay katmanı sıfırlanır (bkz. README)."""
        r = self.s.get(f"{self.base}/hub/api/users/{self.user}", timeout=30)
        if r.status_code == 403:
            raise SystemExit("HATA: token reddedildi (403). Token başka kullanıcıya ait olabilir.")
        r.raise_for_status()
        if r.json().get("server"):
            return
        print("sunucu kapalı, başlatılıyor...", flush=True)
        self.s.post(f"{self.base}/hub/api/users/{self.user}/server", timeout=30)
        for _ in range(wait // 3):
            time.sleep(3)
            if self.s.get(f"{self.base}/hub/api/users/{self.user}", timeout=30).json().get("server"):
                print("sunucu ayakta.", flush=True)
                return
        raise SystemExit("HATA: sunucu süresinde başlamadı.")

    def start_kernel(self) -> str:
        r = self.s.post(f"{self.srv}/api/kernels", json={"name": "python3"}, timeout=60)
        r.raise_for_status()
        self.kid = r.json()["id"]
        return self.kid

    def close(self) -> None:
        if self.kid:
            try:
                self.s.delete(f"{self.srv}/api/kernels/{self.kid}", timeout=30)
            except Exception:
                pass
            self.kid = None

    # --- yürütme ---
    def execute(self, code: str, timeout: int = 600) -> tuple[str, str]:
        """Çekirdekte Python çalıştır. (stdout, stderr) döndürür.

        BİTİŞ TESPİTİ: kendi msg_id'mize ait iopub status=idle. PTY tabanlı terminal
        websocket'inde çıktının nerede bittiği belirsizdir; çekirdek protokolü açık
        bitiş sinyali verdiği için onu seçtim.
        """
        if not self.kid:
            self.start_kernel()
        sid, mid = uuid.uuid4().hex, uuid.uuid4().hex
        url = self.srv.replace("https://", "wss://") + f"/api/kernels/{self.kid}/channels?session_id={sid}"
        ws = websocket.create_connection(
            url, header=[f"Authorization: token {self.token}"],
            sslopt={"cert_reqs": ssl.CERT_NONE}, timeout=timeout)
        ws.send(json.dumps({
            "header": {"msg_id": mid, "username": self.user, "session": sid,
                       "msg_type": "execute_request", "version": "5.3"},
            "parent_header": {}, "metadata": {},
            "content": {"code": code, "silent": False, "store_history": False,
                        "user_expressions": {}, "allow_stdin": False,
                        "stop_on_error": True},
            "channel": "shell", "buffers": []}))
        out, err, deadline = [], [], time.time() + timeout
        try:
            while time.time() < deadline:
                msg = json.loads(ws.recv())
                if msg.get("parent_header", {}).get("msg_id") != mid:
                    continue
                t, c = msg["header"]["msg_type"], msg.get("content", {})
                if t == "stream":
                    (out if c.get("name") == "stdout" else err).append(c.get("text", ""))
                elif t == "execute_result":
                    out.append(c.get("data", {}).get("text/plain", ""))
                elif t == "error":
                    err.append("\n".join(c.get("traceback", [])))
                elif t == "status" and c.get("execution_state") == "idle":
                    break
            else:
                err.append(f"[ZAMAN AŞIMI {timeout}s]")
        finally:
            ws.close()
        return "".join(out), "".join(err)

    def sh(self, cmd: str, timeout: int = 600, venv: bool = False) -> tuple[str, str, int]:
        """Kabuk komutu. Çıkış kodu AYRI döndürülür -- sessiz başarısızlık olmasın.

        venv=True ise /workspace/venv etkinleştirilir (bootstrap sonrası ana yol).
        """
        if venv:
            # env.sh TEK kaynak doğruluktur (bootstrap üretir). Buraya yol SABİT YAZMA:
            # önceki sürüm HF_HUB_CACHE'i /workspace/hf/hub sanıyordu, oysa önbellek
            # doğrudan /workspace/hf altında -> 52 GB'lık model yeniden indirilirdi.
            cmd = "source /workspace/env.sh 2>/dev/null; " + cmd
        # errors="replace": `tail -c N` bir UTF-8 karakterini ORTADAN kesebilir ve
        # text=True çözümlemesi UnicodeDecodeError ile TÜM çağrıyı düşürür (ölçüldü:
        # Türkçe log kuyruğu alınırken). Log izlemenin veri bozulmasından ölmemesi
        # gerekir; bozuk bayt yerine U+FFFD konur.
        code = ("import subprocess as _s;"
                f"_r=_s.run({cmd!r},shell=True,capture_output=True,text=True,"
                "errors='replace',executable='/bin/bash');"
                "print(_r.stdout,end='');"
                "import sys as _y;print(_r.stderr,end='',file=_y.stderr);"
                "print(f'\\n__RC__{_r.returncode}')")
        out, err = self.execute(code, timeout)
        rc = -1
        if "__RC__" in out:
            out, _, tail = out.rpartition("__RC__")
            rc = int(tail.strip() or -1)
        return out.rstrip("\n"), err, rc

    def nohup(self, cmd: str, log: str) -> tuple[str, int]:
        """Uzun işi konteynerde ARKA PLANA al. VPN veya websocket koparsa iş devam eder.

        Bu, çekirdek hücresinde uzun iş çalıştırmaya tercih edilir: websocket kopunca
        çekirdek öldürülebilir, nohup'lanmış süreç öldürülmez.
        """
        full = (f"source /workspace/env.sh 2>/dev/null; "
                f"mkdir -p $(dirname {log}); "
                f"setsid nohup bash -c {cmd!r} > {log} 2>&1 < /dev/null & echo $!")
        out, _, rc = self.sh(full, timeout=60)
        return out.strip().splitlines()[-1] if out.strip() else "", rc

    # --- dosya aktarımı ---
    @staticmethod
    def _rel(yol: str) -> str:
        """contents API yolları SUNUCU KÖKÜNE göredir (= /workspace), mutlak değil.
        '/workspace/MarkLLM/x' mutlak verilince 'workspace/MarkLLM/x' aranıp 404 olurdu
        (ölçüldü: drift.json indirilemedi)."""
        y = yol.lstrip("/")
        return y[len("workspace/"):] if y.startswith("workspace/") else y

    def put_bytes(self, remote: str, data: bytes) -> None:
        # DİKKAT: dosya adı NOKTA ile başlamamalı. jupyter_server'da
        # ContentsManager.allow_hidden varsayılan False'tur ve gizli yollar 400 döner
        # (ölçüldü: '.push_pilot.tar.gz' -> 400 Bad Request).
        r = self.s.put(f"{self.srv}/api/contents/{self._rel(remote)}",
                       json={"type": "file", "format": "base64",
                             "content": base64.b64encode(data).decode()}, timeout=600)
        if not r.ok:
            raise SystemExit(f"HATA: yükleme reddedildi ({r.status_code}) {remote}\n"
                             f"  {r.text[:400]}")

    def get_bytes(self, remote: str) -> bytes:
        r = self.s.get(f"{self.srv}/api/contents/{self._rel(remote)}",
                       params={"format": "base64"}, timeout=600)
        if not r.ok:
            raise SystemExit(f"HATA: indirilemedi ({r.status_code}) {remote}\n  {r.text[:300]}")
        return base64.b64decode(r.json()["content"])

    def push_dir(self, local: Path, dest_parent: str, arcname: str | None = None) -> int:
        """Dizini TEK tar olarak gönder ve aç.

        Dosya dosya PUT hem yavaş hem yarım kalabilir; tar tek işlemdir ve boyutu
        tek yerde raporlanır. contents API kullanıcı köküne yazar (=/workspace),
        oradan hedefe açılır.
        """
        name = arcname or local.name
        buf = io.BytesIO()
        skip = ("__pycache__", ".pyc", ".venv", ".git/", ".DS_Store", ".ipynb_checkpoints")
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            tf.add(local, arcname=name,
                   filter=lambda ti: None if any(p in ti.name for p in skip) else ti)
        blob = buf.getvalue()
        tmp = f"_push_{name}.tar.gz"          # nokta ile BAŞLAMAZ (bkz. put_bytes)
        self.put_bytes(tmp, blob)
        out, err, rc = self.sh(
            f"set -e; mkdir -p {dest_parent}; "
            f"tar xzf /workspace/{tmp} -C {dest_parent}; rm -f /workspace/{tmp}")
        if rc != 0:
            raise SystemExit(f"HATA: açma başarısız (rc={rc})\n{out}\n{err}")

        # BAYAT DOSYA TEMİZLİĞİ. tar ÜZERİNE açılır; uzakta duran ama artık
        # gönderilmeyen dosyaları KALDIRMAZ. Ölçüldü: pilot/dev_hpc.py,
        # hpc/remote.py'ye taşındıktan sonra HPC'de KALMIŞTI -> kaynak içerik
        # özeti iki tarafta tutmuyordu (yerel 30 dosya / uzak 31), yani
        # "iki ortam aynı kodu koşuyor" kanıtı bozuluyordu.
        # Karşılaştırma PYTHON tarafında; uzak kabukta liste kurmak kırılgan.
        uzak_out, _, _ = self.sh(
            f"cd {dest_parent} && find {name} -type f "
            f"\\( -name '*.py' -o -name '*.json' -o -name '*.sh' \\) "
            f"! -path '*__pycache__*' | sort")
        uzak = {x.strip() for x in uzak_out.splitlines() if x.strip()}
        yerel = {f"{name}/" + f.relative_to(local).as_posix()
                 for f in local.rglob("*")
                 if f.is_file() and f.suffix in (".py", ".json", ".sh")
                 and "__pycache__" not in str(f)}
        bayat = sorted(uzak - yerel)
        if bayat:
            print(f"  bayat dosya siliniyor ({len(bayat)}): "
                  f"{', '.join(b.split('/')[-1] for b in bayat[:4])}")
            self.sh(f"cd {dest_parent} && rm -f "
                    + " ".join(f"'{b}'" for b in bayat))
        return len(blob)


def _kullanici(env: dict) -> str:
    """Kullanıcı adı .env'den GELİR, sabit kodlanmaz. Önceki sürümde varsayılan
    olarak gerçek hesap adı gömülüydü; depo paylaşılırsa kurumsal hesap adı
    sızardı ve başka birinin .env'i eksikse SESSİZCE yanlış hesaba bağlanırdı."""
    u = (env.get("TFHPC_USER") or "").strip()
    if not u:
        raise SystemExit(
            "HATA: .env içinde TFHPC_USER yok.\n"
            "  Editörle ekle:  TFHPC_USER=<JupyterHub kullanıcı adın>")
    return u


def connect(quiet: bool = False) -> HPC:
    env = dotenv_values(_ROOT / ".env")
    tok = (env.get("TFHPC_TOKEN") or "").strip()
    if not tok:
        raise SystemExit(
            "HATA: .env içinde TFHPC_TOKEN yok.\n"
            f"  1) VPN açıkken {DEFAULT_URL}/hub/token adresine git\n"
            "  2) 'Request new API token' -> kopyala\n"
            "  3) .env'e EDİTÖRLE ekle (kabuk geçmişine yazma):\n"
            "       TFHPC_TOKEN=...\n"
            "       TFHPC_USER=<kullanıcı adın>")
    h = HPC(env.get("TFHPC_URL", DEFAULT_URL),
            _kullanici(env), tok)
    h.ensure_server()
    return h


def main() -> None:
    ap = argparse.ArgumentParser(description="TF-HPC uzaktan yürütme")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe", help="hızlı ortam envanteri")
    p_sh = sub.add_parser("sh", help="kabuk komutu çalıştır")
    p_sh.add_argument("command")
    p_sh.add_argument("--timeout", type=int, default=600)
    p_sh.add_argument("--venv", action="store_true", help="/workspace/venv içinde çalıştır")
    p_push = sub.add_parser("push", help="yerel dizini gönder")
    p_push.add_argument("path", help="repo köküne göre dizin (örn: pilot)")
    p_push.add_argument("--dest", default=REMOTE_ROOT)
    p_get = sub.add_parser("get", help="uzak dosyayı indir")
    p_get.add_argument("remote")
    p_get.add_argument("local")
    p_log = sub.add_parser("log", help="uzak log dosyasının sonunu göster")
    p_log.add_argument("path")
    p_log.add_argument("-n", type=int, default=40)
    args = ap.parse_args()

    h = connect()
    try:
        if args.cmd == "probe":
            out, err, _ = h.sh(PROBE, timeout=180)
            print(out)
            if err.strip():
                print("--- stderr ---\n" + err, file=sys.stderr)
        elif args.cmd == "sh":
            out, err, rc = h.sh(args.command, timeout=args.timeout, venv=args.venv)
            print(out)
            if err.strip():
                print("--- stderr ---\n" + err, file=sys.stderr)
            sys.exit(0 if rc == 0 else 1)
        elif args.cmd == "push":
            src = (_ROOT / args.path).resolve()
            if not src.is_dir():
                raise SystemExit(f"HATA: dizin yok: {src}")
            n = h.push_dir(src, args.dest)
            print(f"gönderildi: {n / 1024:.0f} KiB -> {args.dest}/{src.name}")
        elif args.cmd == "get":
            Path(args.local).write_bytes(h.get_bytes(args.remote))
            print(f"indirildi: {args.remote} -> {args.local}")
        elif args.cmd == "log":
            out, _, _ = h.sh(f"tail -n {args.n} {args.path}", timeout=60)
            print(out)
    finally:
        h.close()


if __name__ == "__main__":
    main()
