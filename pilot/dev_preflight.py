# pilot/dev_preflight.py — üretici ÖN-KAPISI ve token bütçesi ayrıştırması.
#
# NEDEN: tur-2 denetimi korpusun 0/384 oranında görev uyumsuz olduğunu buldu.
# 24 istem "en az 300 kelime" istiyor; bereket 2,585 tok/kelime olduğu için bu
# ~776 token gerektirir, oysa bütçe 320'ydi (gerekenin %41'i). Metinlerin
# %95,8'i cümle ortasında kesik.
#
# İKİ KUSUR BİRBİRİNE KARIŞMIŞ DURUMDA:
#   (a) token bütçesi   -> yapısal, kesin, ücretsiz düzeltilir
#   (b) model yetersizliği -> kirlenme %36, düzeltmesi 7B (disk gerekir)
# Bu betik bütçeyi düzeltip aynı modelle küçük bir koşu yaparak ikisini ayırır.
#
# ÖN-KAPI (pilotta hiç yoktu; `short`/`clean_cut` görevi sınamıyordu):
#   1. kelime sayısı >= hedef
#   2. sonlandırıcı noktalama ile bitiyor (cümle ortasında kesik değil)
#   3. Latin-dışı yazı sistemi yok
#   4. aşırı tekrar yok (benzersiz kelime oranı)
# Kapıyı geçemeyen üretim ana korpusa ALINMAZ.
#
#   python -m pilot.dev_preflight --budgets 320 1000 --prompts 8 --seeds 2
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch  # noqa: E402

from pilot import config as C  # noqa: E402
from pilot.generate import (get_device, load_model_and_tokenizer,  # noqa: E402
                            load_prompts, render_prompt, seed_everything,
                            slice_completion)

# TEK KAYNAK: tanım pilot/generate.py'ye taşındı ki üretim yolu ile ön-kapı
# AYNI ölçütü kullansın (ikisi ayrı tanımlanırsa sessizce ayrışırlar).
from pilot.generate import FOREIGN_RE as FOREIGN  # noqa: E402
from pilot.generate import TERMINAL_CHARS as TERMINAL  # noqa: E402


def gate(text: str, hedef: int) -> dict:
    """Ön-kapı. Her ölçüt AYRI raporlanır ki hangi kusurun bağladığı görülsün."""
    w = text.split()
    uniq = len({x.lower() for x in w}) / max(1, len(w))
    checks = {
        "kelime": len(w) >= hedef,
        "sonlandirilmis": text.rstrip().endswith(TERMINAL),
        "latin": not FOREIGN.search(text),
        "tekrar": uniq >= 0.35,
    }
    return {**checks, "gecti": all(checks.values()),
            "n_kelime": len(w), "benzersiz_oran": uniq,
            "yabanci_kar": len(FOREIGN.findall(text))}


def main() -> None:
    ap = argparse.ArgumentParser(description="üretici ön-kapı preflight")
    ap.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--budgets", type=int, nargs="+", default=[320, 1000])
    ap.add_argument("--prompts", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--hedef", type=int, default=300, help="istemdeki kelime hedefi")
    # S3 düzeltmesi top_k=0/rep=1.0 dayatıyor. 7B preflight'ı 3B'den KÖTÜ
    # çıkınca (daha kısa, daha kesik, daha kirli) baş şüpheli bu oldu:
    # top_k=0, 152k sözlüğün tamamını örneklemeye açar. Modeli suçlamadan
    # önce modelin KENDİ ayarıyla karşılaştırılabilsin diye parametreleştirdim.
    ap.add_argument("--top-k", type=int, default=0)
    ap.add_argument("--rep", type=float, default=1.0)
    # K7 T=0.8 sabitliyor; ama K7 max_new_tokens=320 de diyordu ve o
    # yanlış çıktı. Sıcaklık, kirlenmeyi bastırmak için test edilmemiş
    # son düğme: düşük T çok dilli kuyruğu doğrudan kapatır.
    ap.add_argument("--temp", type=float, default=0.8)
    # Cihaz SABIT KODLUYDU ("mps"). TF-HPC gecisinde bulundu: CUDA makinesinde
    # model yuklenip generate.py:42 model.to("mps") satirinda cokuyordu.
    ap.add_argument("--device", default=None, choices=["mps", "cuda", "cpu"],
                    help="varsayilan: otomatik tespit")
    # TEŞHİS: istemler "en az 300 kelime" diyor ve Qwen3-14B 16/16 bunun ALTINDA
    # kaliyor (medyan 244). Bu, modelin uzunluk talimatina hic tepki vermedigi mi
    # yoksa sadece az mi hedefledigi sorusunu acik birakiyor. Bu bayrak istemdeki
    # SAYIYI degistirir; KAPI HEDEFI (--hedef) ayridir ve degismez -> esik oynatmak
    # DEGIL, modelin talimat duyarliligini olcmektir.
    ap.add_argument("--istem-hedefi", type=int, default=None,
                    help="istemlerdeki kelime sayisini bununla degistir (teshis)")
    ap.add_argument("--kayit", default=None,
                    help="uretimlerin yazilacagi JSONL (varsayilan: results_hpc/"
                         "onkapi_<model>.jsonl). 'yok' verilirse yazilmaz.")
    args = ap.parse_args()

    device = get_device(args.device)

    kayit = None
    if args.kayit != "yok":
        kp = Path(args.kayit) if args.kayit else Path(
            "results_hpc") / f"onkapi_{args.model.split('/')[-1]}.jsonl"
        kp.parent.mkdir(parents=True, exist_ok=True)
        kayit = kp.open("w", encoding="utf-8")
        print(f"uretimler kaydediliyor: {kp}")
    print(f"Model: {args.model} ({device}) | hedef {args.hedef} kelime | "
          f"top_k={args.top_k} rep={args.rep} T={args.temp}")
    model, tok = load_model_and_tokenizer(args.model, device)
    prompts = load_prompts(args.prompts)
    if args.istem_hedefi:
        eski = str(args.hedef)
        prompts = [x.replace(f"{eski} kelime", f"{args.istem_hedefi} kelime")
                   for x in prompts]
        n_deg = sum(f"{args.istem_hedefi} kelime" in x for x in prompts)
        print(f"TESHIS: istemlerdeki '{eski} kelime' -> '{args.istem_hedefi} kelime' "
              f"({n_deg}/{len(prompts)} istemde degisti). KAPI HEDEFI hala {args.hedef}.")
    seeds = list(range(11, 11 + args.seeds))

    print(f"\n{'bütçe':>6s} {'n':>3s} {'KAPI':>6s} {'kelime':>7s} {'>=hedef':>8s} "
          f"{'bitmiş':>7s} {'latin':>6s} {'tekrar':>7s} {'s/örnek':>8s}")
    print("-" * 74)
    for budget in args.budgets:
        res, t0 = [], time.time()
        for pi, p in enumerate(prompts):
            rendered = render_prompt(tok, p)
            enc = tok(rendered, return_tensors="pt").to(device)
            for seed in seeds:
                seed_everything(seed * 1000 + pi, device)
                with torch.no_grad():
                    out = model.generate(
                        **enc, max_new_tokens=budget,
                        min_new_tokens=min(200, budget // 2),
                        do_sample=True, temperature=args.temp, top_p=0.95,
                        top_k=args.top_k, repetition_penalty=args.rep,
                        pad_token_id=tok.pad_token_id)
                txt, _ = slice_completion(
                    tok, rendered, tok.batch_decode(out, skip_special_tokens=True)[0])
                g = gate(txt, args.hedef)
                res.append(g)
                # METİNLER SAKLANIR. İlk sürüm yalnız sayı basıyordu; kapı düşünce
                # "hangi metinde ne oldu" sorusu VERİDEN cevaplanamadı (Latin-dışı
                # karakter hangisiydi, kelime dağılımı nasıl). Denetlenemeyen kapı
                # zayıf kapıdır ve projenin "her sayı koddan yeniden üretilebilir"
                # kuralını ihlal eder.
                if kayit is not None:
                    kayit.write(json.dumps(
                        {"model": args.model, "butce": budget, "prompt_id": pi,
                         "seed": seed, "hedef": args.hedef, "top_k": args.top_k,
                         "rep": args.rep, "temp": args.temp,
                         "yabanci_karakterler": sorted(set(FOREIGN.findall(txt))),
                         **g, "text": txt}, ensure_ascii=False) + "\n")
                    kayit.flush()
        n = len(res)
        el = (time.time() - t0) / n
        print(f"{budget:6d} {n:3d} {sum(r['gecti'] for r in res):5d} "
              f"{sum(r['n_kelime'] for r in res)/n:7.0f} "
              f"{sum(r['kelime'] for r in res):8d} "
              f"{sum(r['sonlandirilmis'] for r in res):7d} "
              f"{sum(r['latin'] for r in res):6d} "
              f"{sum(r['tekrar'] for r in res):7d} {el:8.1f}", flush=True)

    if kayit is not None:
        kayit.close()

    print("\nOKUMA: 'KAPI' dört ölçütü birden geçen üretim sayısıdır. Bütçe "
          "artınca '>=hedef' ve 'bitmiş' yükselmiyorsa sorun bütçe değil "
          "modeldir; 'latin' düşük kalıyorsa kirlenme bütçeden bağımsızdır.")


if __name__ == "__main__":
    main()
