# pilot/detect.py — saldırılı metinlerin üretimi ve tespit skorlaması.
#
# Veri düzeni (results/ altında):
#   gen_neg.jsonl            : filigransız üretimler (BİR kez; üç dedektör de bunu skorlar)
#   gen_pos_{S}.jsonl        : S şemasıyla filigranlı üretimler
#   att_{src}_{attack}.jsonl : saldırılı kopyalar (src: neg | pos_KGW | ...)
#   scores.csv               : uzun-form skor tablosu (metrics.py girdisi)
from __future__ import annotations

import csv
import math
from pathlib import Path

from pilot import config as C
from pilot.attacks import apply_light_attack
from pilot.generate import count_tokens
from pilot.jsonl import append_jsonl, read_jsonl
from pilot.config import SCORES_CSV_FIELDS  # şema config'te (torch'suz erişim)


def _att_path(src_tag: str, attack: str) -> Path:
    return C.RESULTS / f"att_{src_tag}_{attack}.jsonl"


def build_attacked_texts(
    src_tag: str,
    base_rows: list[dict],
    attacks: list[str],
    tok,
    device: str,
    model=None,
    rtt=None,
) -> None:
    """base_rows'taki her metnin saldırılı kopyalarını üretir (cache'li).
    Hafif saldırılar anında; rtt için RoundTripTranslator, para/launder için
    ana model gerekir (None ise o saldırı atlanır ve uyarı basılır)."""
    for attack in attacks:
        path = _att_path(src_tag, attack)
        done = {(r["prompt_id"], r["seed"]) for r in read_jsonl(path)}
        todo = [r for r in base_rows if (r["prompt_id"], r["seed"]) not in done]
        if not todo:
            continue
        if attack in C.LIGHT_ATTACKS:
            if attack.startswith("morph"):
                # K11 sözleşmesi: zeyrek'in sonuçları çok sayıda analizden sonra
                # değişiyor; ısıtma tüm çözümlemeleri kanonik (sıralı) düzende
                # yaptırarak sonucu metin sırasından bağımsız kılar.
                from pilot.attacks import prewarm_corpus
                prewarm_corpus(r["text"] for r in base_rows)
            for r in todo:
                seed = r["seed"] * 100000 + r["prompt_id"]
                new_text, meta = apply_light_attack(attack, r["text"], seed=seed)
                append_jsonl(path, {
                    **{k: r[k] for k in ("prompt_id", "seed", "wm")},
                    "text": new_text,
                    "n_tokens": count_tokens(tok, new_text),
                    "edits": meta["edits"], "rejected": meta["rejected"],
                })
        elif attack == "rtt":
            if rtt is None:
                print(f"  UYARI: rtt atlandı ({src_tag}); çevirmen yüklenmedi.")
                continue
            for i, r in enumerate(todo):
                new_text = rtt.round_trip(r["text"])
                _yeni_tok = count_tokens(tok, new_text)
                append_jsonl(path, {
                    **{k: r[k] for k in ("prompt_id", "seed", "wm")},
                    "text": new_text,
                    "n_tokens": _yeni_tok,
                    "edits": -1, "rejected": 0,
                    # UZUNLUK KONFOUNDU DENETLENEBİLİR OLSUN: saldırılmış metin
                    # kaynaktan kısaysa filigran doğal olarak zayıflar (KGW z ~ √T);
                    # "saldırı sildi" ile "kısaldı" sonradan ayrılabilsin.
                    # rtt'de METİN DÜZEYİNDE tavan yoktur -- NLLB cümle cümle çevirir
                    # (heavy_attacks.py:67 max_new_tokens=256 CÜMLE BAŞINA), o yüzden
                    # burada None. Ceiling alanını buraya yanlışlıkla kopyalamıştım
                    # ve Faz 2 UnboundLocalError ile düştü.
                    "tavan": None,
                    "kaynak_n_tokens": r.get("n_tokens", -1),
                    "uzunluk_orani": round(_yeni_tok / max(1, r.get("n_tokens", 1)), 3),
                })
                if (i + 1) % 10 == 0:
                    print(f"  [rtt {src_tag}] {i + 1}/{len(todo)}", flush=True)
        elif attack in ("para", "launder"):
            if model is None:
                print(f"  UYARI: {attack} atlandı ({src_tag}); model verilmedi.")
                continue
            from pilot.heavy_attacks import rewrite

            for i, r in enumerate(todo):
                # rewrite artik (metin, tavan) donuyor ve TOHUMLANIYOR:
                # onceki surum do_sample=True ile tohumsuz kosuyordu (K11 ihlali).
                new_text, _tavan = rewrite(model, tok, device, r["text"],
                                           attack, seed=r["seed"] * 1000 + r["prompt_id"])
                _yeni_tok = count_tokens(tok, new_text)
                append_jsonl(path, {
                    **{k: r[k] for k in ("prompt_id", "seed", "wm")},
                    "text": new_text,
                    "n_tokens": _yeni_tok,
                    "edits": -1, "rejected": 0,
                    # UZUNLUK KONFOUNDU DENETLENEBİLİR OLSUN: saldırılmış metin
                    # kaynaktan kısaysa filigran doğal olarak zayıflar (KGW z ~ √T).
                    # Kullanılan tavan ve kaynak uzunluğu satıra yazılıyor ki
                    # "saldırı sildi" ile "kısaldı" sonradan ayrılabilsin.
                    "tavan": _tavan,
                    "kaynak_n_tokens": r.get("n_tokens", -1),
                    "uzunluk_orani": round(_yeni_tok / max(1, r.get("n_tokens", 1)), 3),
                })
                if (i + 1) % 10 == 0:
                    print(f"  [{attack} {src_tag}] {i + 1}/{len(todo)}", flush=True)
        elif attack == "launder_api":
            # Harici API ile üretilir (pilot.dev_launder_api), burada üretilmez.
            # Eksikse skorlamayı düşürmek yerine o koşulu atla: kalan sekiz
            # koşulun tablosu yine de üretilsin.
            print(f"  UYARI: {attack}/{src_tag} eksik ({len(todo)} metin) — "
                  f"bu koşul atlandı. Tamamlamak için: "
                  f"python -m pilot.dev_launder_api")
            continue
        else:
            raise ValueError(attack)


def _stat(scheme: str, score: float) -> float:
    """Yön düzeltmesi (K3/Ek D): her şemada yüksek stat = filigranlı."""
    if C.SCORE_DIRECTION[scheme] > 0:
        return float(score)
    return float(-math.log10(max(float(score), 1e-300)))  # EXP p-value


def score_rows(scheme_obj, scheme: str, condition: str, rows: list[dict],
               writer: csv.DictWriter, src: str) -> None:
    n = len(rows)
    for i, r in enumerate(rows):
        res = scheme_obj.detect_watermark(r["text"])
        score = float(res["score"])
        writer.writerow(dict(
            scheme=scheme, condition=condition, wm=r["wm"],
            prompt_id=r["prompt_id"], seed=r["seed"],
            score=score, stat=_stat(scheme, score),
            n_tokens=r.get("n_tokens", -1),
            edits=r.get("edits", 0), rejected=r.get("rejected", 0),
            short=r.get("short", 0), src=src,
        ))
        if scheme == "EXP" and (i + 1) % 20 == 0:  # EXP tespiti yavaştır (Ek A)
            print(f"    [EXP detect {condition} {src}] {i + 1}/{n}", flush=True)


def run_detection(scheme_obj, scheme: str, attacks: list[str],
                  csv_path: Path, append: bool = True) -> None:
    """Bir şemanın tüm koşullarını skorlar: temiz neg + temiz pos +
    saldırılı(neg, pos). scores.csv'ye ekler."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if (append and csv_path.exists()) else "w"
    with open(csv_path, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SCORES_CSV_FIELDS)
        if mode == "w":
            w.writeheader()

        neg = read_jsonl(C.RESULTS / "gen_neg.jsonl")
        pos = read_jsonl(C.RESULTS / f"gen_pos_{scheme}.jsonl")
        print(f"  [{scheme}] temiz skorlar: {len(neg)} neg + {len(pos)} pos")
        score_rows(scheme_obj, scheme, "clean", neg, w, src="neg")
        score_rows(scheme_obj, scheme, "clean", pos, w, src=f"pos_{scheme}")

        for attack in attacks:
            for src_tag, base in (("neg", neg), (f"pos_{scheme}", pos)):
                rows = read_jsonl(_att_path(src_tag, attack))
                if not rows:
                    continue
                print(f"  [{scheme}] {attack}/{src_tag}: {len(rows)} metin")
                score_rows(scheme_obj, scheme, attack, rows, w, src=src_tag)
