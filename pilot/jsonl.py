# pilot/jsonl.py — torch'suz JSONL okuma/yazma.
# metrics.py ve fertility.py bu modüle bağlanır; böylece analiz katmanı
# torch kurulu olmayan bir ortamda da (ör. sadece sonuç inceleme) çalışır.
from __future__ import annotations

import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path: Path, row: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
