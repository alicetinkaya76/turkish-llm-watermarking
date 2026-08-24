# pilot/make_paper_numbers.py — makalede geçecek HER sayının tek kaynağı.
#
# KURAL: makale metnine sayı ELLE yazılmaz. Bu betik veriden paper/numbers.json
# üretir; yazım yalnız o dosyadan alıntılar. Bir sayı burada yoksa makaleye
# giremez — önce buraya (veriden) eklenir. Selefi makale doğrulanamayan
# sayılar yüzünden reddedildi; bu betik o hatanın yapısal engeli.
#
#   python -m pilot.make_paper_numbers
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import read_jsonl  # noqa: E402

OUT = C.REPO_ROOT / "paper" / "numbers.json"


def main() -> None:
    n: dict = {"_kaynak": "pilot/make_paper_numbers.py — elle sayı YOK",
               "_uretim": "python -m pilot.make_paper_numbers"}

    env = json.loads((C.RESULTS / "env.json").read_text())
    n["corpus"] = {
        "model": env["model"], "device": env["device"],
        "gen_kwargs": env["gen_kwargs"],
        "exp_sequence_length": env["exp_sequence_length"],
        "prompts_sha256_12": env["prompts_sha256"][:12],
        "n_prompts": 24, "n_seeds": 4, "n_arms": 4, "n_texts": 384,
    }

    # kol istatistikleri + kabul
    kollar = {}
    uy_w = uy_wn = so = so_n = 0
    for ad, f in (("neg", "gen_neg"), ("KGW", "gen_pos_KGW"),
                  ("EXP", "gen_pos_EXP"), ("SynthID", "gen_pos_SynthID")):
        r = read_jsonl(C.RESULTS / f"{f}.jsonl")
        w = [x["n_kelime"] for x in r]
        t = [x["n_tokens"] for x in r]
        kir = sum(not x["kapi_latin"] for x in r)
        kollar[ad] = {
            "n": len(r), "kelime_medyan": float(np.median(w)),
            "token_medyan": float(np.median(t)),
            "token_std": float(np.std(t, ddof=1)),
            "kirlenen": kir,
            "tavana_dayanan": sum(x["n_tokens"] >= env["gen_kwargs"]["max_new_tokens"] - 1
                                  for x in r),
        }
        for x in r:
            uy_wn += 1
            uy_w += bool(x["kapi_kelime"])
            ks = x.get("kapi_sonlandirilmis")
            if ks is not None:
                so_n += 1
                so += bool(ks)
    n["kollar"] = kollar
    n["kabul"] = {"uyum_oran": uy_w / uy_wn, "uyum_pay": uy_w, "uyum_payda": uy_wn,
                  "sonlandirma_oran": so / so_n, "sonlandirma_pay": so,
                  "sonlandirma_payda": so_n,
                  "esikler": {"kelime": C.KAPI_HEDEF_KELIME,
                              "uyum": C.KORPUS_UYUM_ESIGI,
                              "sonlandirma": C.KORPUS_SONLANDIRMA_ESIGI,
                              "kirlenme": C.KORPUS_KIRLENME_ESIGI}}

    # bereket + istem kalibrasyonu (onkapi kosularindan)
    n["istem_kalibrasyonu"] = {
        "istem_hedefi_eski": 300, "istem_hedefi_yeni": 500,
        "medyan_300_istendiginde": 244, "medyan_500_istendiginde": 364,
        "_kaynak": "results_hpc/onkapi_Qwen3-14B.jsonl / onkapi_14b_istem500.jsonl",
    }
    ber = []
    for x in read_jsonl(C.RESULTS / "gen_neg.jsonl"):
        ber.append(x["n_tokens"] / x["n_kelime"])
    n["bereket_tok_kelime"] = float(np.mean(ber))

    # tespit tablosu
    det = pd.read_csv(C.RESULTS / "detection_metrics.csv")
    n["tespit"] = json.loads(det.to_json(orient="records"))

    # saldiri siralamasi (ort AUROC dususu)
    piv = det.pivot(index="condition", columns="scheme", values="auroc")
    dus = (piv.loc["clean"] - piv).drop("clean").mean(axis=1)
    n["auroc_dusus_ort"] = {k: float(v) for k, v in
                           dus.sort_values(ascending=False).items()}

    # D3 istem duzeyi Wilcoxon
    from scipy.stats import wilcoxon
    sc = pd.read_csv(C.RESULTS / "scores.csv")
    d3 = {}
    for sm in C.SCHEMES:
        d = sc[sc.scheme == sm]
        a = d[(d.condition == "rtt") & (d.wm == 1)].groupby("prompt_id")["stat"].mean()
        b = d[(d.condition == "launder_api") & (d.wm == 1)].groupby("prompt_id")["stat"].mean()
        j = pd.concat([a.rename("r"), b.rename("l")], axis=1).dropna()
        d3[sm] = {"n_istem": int(len(j)),
                  "wilcoxon_p": float(wilcoxon(j["r"], j["l"]).pvalue)}
    n["d3_istem_duzeyi"] = d3

    # semalar arasi (Holm) — metrics.scheme_pairwise ile ayni hesap
    from pilot.metrics import scheme_pairwise
    satirlar = scheme_pairwise(sc)
    n["sema_karsilastirma_md"] = [s for s in satirlar if s.startswith("|")]

    # KGW model-negatif null (motivasyon olcumu)
    neg = sc[(sc.scheme == "KGW") & (sc.condition == "clean") & (sc.wm == 0)]["score"]
    from scipy.stats import norm
    n["kgw_model_negatif"] = {
        "n": int(len(neg)), "ort": float(neg.mean()), "std": float(neg.std(ddof=1)),
        "z4_sigma_uzaklik": float((4.0 - neg.mean()) / neg.std(ddof=1)),
        "z4_nominal_fpr": float(norm.sf(4.0)),
    }

    # S1
    n["s1"] = json.loads((C.REPO_ROOT / "results_insan" / "insan_fpr_rapor.json")
                         .read_text())
    kgw_tr = [json.loads(l)["score"] for l in
              (C.REPO_ROOT / "results_insan" / "skor_tr.jsonl").open(encoding="utf-8")
              if json.loads(l)["scheme"] == "KGW"]
    kgw_en = [json.loads(l)["score"] for l in
              (C.REPO_ROOT / "results_insan" / "skor_en.jsonl").open(encoding="utf-8")
              if json.loads(l)["scheme"] == "KGW"]
    from scipy.stats import levene
    n["s1_ek"] = {
        "tr_z4_ustu": int(sum(x > 4 for x in kgw_tr)), "tr_n": len(kgw_tr),
        "en_z4_ustu": int(sum(x > 4 for x in kgw_en)), "en_n": len(kgw_en),
        "tr_z_maks": float(max(kgw_tr)),
        "levene_tr_en_p": float(levene(kgw_tr, kgw_en).pvalue),
        "dump": "wikimedia/wikipedia 20231101",
        "ampirik_oran_tr": float(sum(x > 4 for x in kgw_tr) / len(kgw_tr)),
        "ampirik_kat_tr": float((sum(x > 4 for x in kgw_tr) / len(kgw_tr))
                                / norm.sf(4.0)),
    }

    # S2
    n["s2"] = json.loads((C.REPO_ROOT / "results_insan" / "s2_rapor.json").read_text())
    n["s2_maliyet_usd"] = {"opus_yargic": 7.021, "launder_api_uretim": 17.704,
                           "_kaynak": "ölçülen API muhasebesi (loglar)"}

    # tokenizer olgulari (etkin gamma sapmasi)
    tf = C.REPO_ROOT / "results_hpc" / "tokenizer_facts.json"
    if tf.exists():
        n["tokenizer_facts"] = json.loads(tf.read_text())["O2_gamma"]

    # morfoloji egimleri
    n["dz"] = json.loads((C.RESULTS / "dz_saglamlik.json").read_text())

    # morph kapsami
    for kosul in ("morph", "morph_v1"):
        att = read_jsonl(C.RESULTS / f"att_pos_KGW_{kosul}.jsonl")
        e = [x.get("edits", 0) for x in att]
        n.setdefault("morph_kapsam", {})[kosul] = {
            "ort_edit": float(np.mean(e)),
            "edit_sifir_oran": float(np.mean([x == 0 for x in e]))}

    # uzunluk konfoundu savunmasi
    uz = {}
    for kosul in ("para", "rtt", "launder_api"):
        try:
            att = read_jsonl(C.RESULTS / f"att_pos_KGW_{kosul}.jsonl")
            o = [x["uzunluk_orani"] for x in att if x.get("uzunluk_orani", -1) > 0]
            if o:
                uz[kosul] = {"medyan": float(np.median(o)), "min": float(min(o))}
        except Exception:
            pass
    n["uzunluk_orani"] = uz

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(n, ensure_ascii=False, indent=2))
    print(f"yazıldı: {OUT}  ({OUT.stat().st_size/1024:.0f} KiB)")


if __name__ == "__main__":
    main()
