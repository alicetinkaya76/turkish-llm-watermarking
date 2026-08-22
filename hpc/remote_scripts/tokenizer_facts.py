# hpc/remote_scripts/tokenizer_facts.py — model/tokenizer OLGULARI. [KONTEYNERDE ÇALIŞIR]
#
# NEDEN: pilot Qwen2.5 için yazıldı. Aday modeller farklı ailelerden ve pilotun
# sessizce doğru saydığı üç şey artık doğru olmayabilir. Üçü de ana koşudan ÖNCE
# ölçülür; hiçbiri varsayılmaz. GPU GEREKTİRMEZ (yalnız tokenizer + config).
#
#   O1 DÜŞÜNME KİPİ. Qwen3 sohbet şablonu varsayılan olarak <think>...</think>
#      üretir. 300 kelimelik Türkçe kompozisyon görevinde bu, token bütçesinin
#      çoğunu yer ve ön-kapıyı SAHTE biçimde düşürür. pilot/generate.py:114-121
#      render_prompt() enable_thinking'i HİÇ geçmiyor -- Qwen2.5'te böyle bir
#      parametre olmadığı için. Şablonda bu anahtar var mı, ölçülür.
#
#   O2 ETKİN GAMMA. KGW yeşil listeyi int(vocab*gamma) ile kuruyor. `len(tokenizer)`
#      (eklenen özel tokenlarla) ile `config.vocab_size` (logit genişliği) farklıysa
#      etkin gamma yazılı 0,5'ten sapar. Qwen2.5-7B'de sapma ölçülmüştü; her yeni
#      model için yeniden ölçülmeli.
#
#   O3 İSTEM PARMAK İZİ. render_prompt çıktısının sha256'sı. Sürümler/ortamlar
#      arasında bit-birebir aynı mı -- sonuçlar karşılaştırılırken kanıt olur.
#
#   python hpc/remote_scripts/tokenizer_facts.py --model Qwen/Qwen3-14B
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from transformers import AutoConfig, AutoTokenizer  # noqa: E402

from pilot import config as C  # noqa: E402
from pilot.generate import load_prompts, render_prompt  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="tokenizer/model olguları")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default="results_hpc/tokenizer_facts.json")
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model)
    cfg = AutoConfig.from_pretrained(args.model)
    tcfg = getattr(cfg, "text_config", cfg)
    r: dict = {"model": args.model}

    # --- O1 düşünme kipi ---
    sablon = getattr(tok, "chat_template", None) or ""
    p0 = load_prompts(1)[0]
    r["O1_dusunme"] = {
        "sablon_var": bool(sablon),
        "enable_thinking_anahtari": "enable_thinking" in sablon,
        "think_etiketi_sablonda": "<think>" in sablon,
    }
    for ad in ("<think>", "</think>"):
        tid = tok.convert_tokens_to_ids(ad)
        r["O1_dusunme"][f"{ad}_id"] = None if tid is None or tid < 0 else tid

    varsayilan = render_prompt(tok, p0)
    r["O1_dusunme"]["varsayilan_istem_think_ile_bitiyor"] = varsayilan.rstrip().endswith("<think>")
    if r["O1_dusunme"]["enable_thinking_anahtari"]:
        try:
            kapali = tok.apply_chat_template(
                [{"role": "user", "content": p0}], tokenize=False,
                add_generation_prompt=True, enable_thinking=False)
            r["O1_dusunme"]["kapali_farkli_mi"] = kapali != varsayilan
            r["O1_dusunme"]["kapali_token_farki"] = (
                len(tok(kapali).input_ids) - len(tok(varsayilan).input_ids))
        except Exception as e:
            r["O1_dusunme"]["kapali_hata"] = f"{type(e).__name__}: {str(e)[:120]}"
    r["O1_dusunme"]["_karar"] = (
        "DÜŞÜNME KİPİ VAR -> render_prompt'a enable_thinking=False geçilmeli"
        if r["O1_dusunme"]["enable_thinking_anahtari"] else
        "düşünme kipi yok -> render_prompt olduğu gibi kullanılabilir")

    # --- O2 etkin gamma ---
    n_tok, n_cfg = len(tok), int(getattr(tcfg, "vocab_size", 0))
    gamma = 0.5
    try:
        gamma = float(json.loads(Path(_ROOT / C.SCHEME_CONFIGS["KGW"]).read_text())["gamma"])
    except Exception:
        pass
    etkin = (int(n_tok * gamma) / n_cfg) if n_cfg else float("nan")
    r["O2_gamma"] = {
        "len_tokenizer": n_tok, "config_vocab_size": n_cfg,
        "yazili_gamma": gamma, "etkin_gamma": round(etkin, 6),
        "sapma": round(etkin - gamma, 6),
        "_karar": ("SAPMA YOK" if n_tok == n_cfg else
                   f"SAPMA {etkin - gamma:+.6f} -- SINIRLAMALAR bölümüne yazılmalı"),
    }

    # --- O3 istem parmak izi ---
    hepsi = load_prompts(C.N_PROMPTS)
    r["O3_istem"] = {
        "n_istem": len(hepsi),
        "istem0_sha256": hashlib.sha256(varsayilan.encode()).hexdigest()[:32],
        "tum_istemler_sha256": hashlib.sha256(
            "\n---\n".join(render_prompt(tok, p) for p in hepsi).encode()).hexdigest()[:32],
        "istem0_token": len(tok(varsayilan).input_ids),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

    for blok, d in r.items():
        if not isinstance(d, dict):
            continue
        print(f"\n{blok}")
        for k, v in d.items():
            print(f"  {k:38s} {v}")
    print(f"\nyazıldı: {out}")


if __name__ == "__main__":
    main()
