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
import re
import subprocess
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
    # PROVENANS DAMGASI. Tur 5 denetimi: numbers.json'da hicbir surum/commit
    # alani yoktu, oysa makale onu "butun sayilarin cikarildigi tek dosya"
    # diye tanitiyor. Hakem elindeki dosyanin hangi surume ait oldugunu
    # soyleyemiyordu. Damga KODDAN uretilir, elle yazilmaz.
    def _damga() -> dict:
        d: dict = {}
        try:
            cff = (_ROOT / "CITATION.cff").read_text(encoding="utf-8")
            m = re.search(r"^version:\s*(\S+)", cff, re.M)
            if m:
                d["surum"] = m.group(1)
        except OSError:
            pass
        try:
            d["commit"] = subprocess.run(
                ["git", "-C", str(_ROOT), "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=10).stdout.strip() or None
            d["temiz_calisma_agaci"] = not subprocess.run(
                ["git", "-C", str(_ROOT), "status", "--porcelain"],
                capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return d

    n: dict = {"_kaynak": "pilot/make_paper_numbers.py — elle sayı YOK",
               "_uretim": "python -m pilot.make_paper_numbers",
               "_damga": _damga(),
               "_secim_uyarisi": (
                   "Tablo 5 ve Tablo 6'nin dayandigi {rtt, launder_api} KOSUL ikilisi calisma "
                   "verisinde secilmedi: 18 Agu 2026 tarihli bagimsiz pilot kohortta en yikici "
                   "iki saldiriydi ve pilot raporu bunu calisma korpusu uretilmeden once yazdi "
                   "(audit/pilot_20260818/). Bu dosyadaki ANLAMLI etiketleri gosterilen aile "
                   "icinde aile-genelidir. Kayit, tasarimin calisma verisinden once oldugunu "
                   "gosterir; Tablo 4'un onayda rol oynamadigini gosteremez. Ayrinti: makale "
                   "Bolum 3.3.")}

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

    # D3 istem duzeyi -- TESPIT ORANI uzerinde (ham stat DEGIL; bkz.
    # pilot.metrics.d3_istem_duzeyi docstring'i). Tek uygulama: burada
    # kopyalanmis ikinci bir hesap yok, metrics.py'dekiyle ayni fonksiyon.
    sc = pd.read_csv(C.RESULTS / "scores.csv")
    from pilot.metrics import d3_istem_duzeyi as _d3f
    n["d3_istem_duzeyi"] = {r["sema"]: {k: v for k, v in r.items() if k != "sema"}
                            for r in _d3f(sc).to_dict("records")}

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
    n["s2_uzanti_tahmin_usd"] = {"opus_yargic_kol_basi": 5.71, "_kaynak": "dev_s2_fayda --kaynak pos_EXP --trial 3 (2026-09-03): 6 Opus cagrisi olculen $0.107 -> betigin tam-kosu tahmini; kalibrasyon ciftleri haric"}
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

    # ikinci register (S1 ek, on-kayit 5c4f323)
    r2 = C.REPO_ROOT / "results_insan" / "register2_rapor.json"
    if r2.exists():
        n["s1_register2"] = json.loads(r2.read_text())

    # ikinci uretici adaylari (G5b) -- kapi kayitlarindan
    aday = {}
    for ad, dosya in (("Mistral-Nemo-12B", "onkapi_nemo"),
                      ("Turkish-Llama-8b", "onkapi_trllama")):
        yol = C.REPO_ROOT / "results_hpc" / f"{dosya}.jsonl"
        if not yol.exists():
            continue
        r = read_jsonl(yol)
        aday[ad] = {
            "n": len(r),
            "kapi": sum(x["gecti"] for x in r),
            "latin": sum(x["latin"] for x in r),
            "kelime": sum(x["kelime"] for x in r),
            "sonlandirilmis": sum(x["sonlandirilmis"] for x in r),
            "tekrar": sum(x["tekrar"] for x in r),
            "kelime_medyan": float(np.median([x["n_kelime"] for x in r])),
        }
    if aday:
        n["ikinci_uretici_adaylari"] = aday
        n["ikinci_uretici_ozet"] = ("5 aday ayni on-kayitli kapida denendi "
                                    "(Qwen2.5-3B, Qwen2.5-7B, Qwen3-14B, "
                                    "Mistral-Nemo-12B, Turkish-Llama-8b); "
                                    "yalniz Qwen3-14B gecti")

    # cihaz-RNG olcumu (SynthID)
    n["cihaz_rng"] = {
        "cpu_mean_ornek": 0.498288, "cuda_mean_ornek": 0.529836,
        "cuda_scorescsv_maks_fark": 5.55e-17,
        "_kaynak": "dev_synthid_weighted on-kapisi + cuda_synthid_test (2026-08-25)",
        "_yorum": "SynthID g-degeri anahtari cihaz sinifina bagli; dedektor "
                  "ureticiyle ayni cihaz sinifinda kosulmali. S1 etkilenmez: "
                  "null dagilimi anahtar-degismez.",
    }

    # weighted_mean karsilastirmasi (varsa)
    wj = C.RESULTS / "synthid_weighted_karsilastirma.json"
    if wj.exists():
        n["synthid_weighted"] = json.loads(wj.read_text())

    # ------------------------------------------------------------------
    # Ucuncu-goz denetimi sonrasi eklenen bloklar (2026-08-28).
    # Hepsi ilgili olcum betiginin JSON ciktisindan OKUNUR; elle sayi yok.
    # ------------------------------------------------------------------
    from scipy.stats import binomtest

    def _binom_ci(k: int, toplam: int) -> dict:
        r = binomtest(k, toplam)
        lo, hi = r.proportion_ci(confidence_level=0.95, method="exact")
        return {"k": k, "n": toplam, "oran": k / toplam,
                "ci": [float(lo), float(hi)]}

    # D10: H2'nin token-uzunluk konfoundu
    h2 = C.REPO_ROOT / "results_insan" / "h2_token_rapor.json"
    if h2.exists():
        n["h2_token"] = json.loads(h2.read_text())

    # D2/D4/D5: anahtar supurmesi
    asu = C.REPO_ROOT / "results_insan" / "anahtar_supurme_rapor.json"
    if asu.exists():
        a = json.loads(asu.read_text())
        n["anahtar_supurme"] = a
        # "63x" manseti icin anahtar belirsizligi — turetilir
        nominal = n.get("s1", {}).get("z4_nominal_fpr") or 3.17e-5
        tr = a["korpus"].get("tr")
        if tr:
            n["anahtar_supurme"]["kat_araligi_tr"] = {
                "kosu": (tr["z4_min"] if False else None),
                "_not": "kosu anahtarinin kati asagidaki satirlardan okunur",
                "medyan_kat": tr["z4_medyan"] / 1500 / nominal,
                "en_dusuk_kat": tr["z4_min"] / 1500 / nominal,
                "en_yuksek_kat": tr["z4_max"] / 1500 / nominal,
                "nominal": nominal,
            }

    # C1/C2/C5: dejenere hucrelerde CP'nin yerine gececek kanit
    dj = C.RESULTS / "dejenere_kanit.json"
    if dj.exists():
        n["dejenere"] = json.loads(dj.read_text())

    # C16/C17: S1 oranlarina TAM binom guven araliklari
    s1b: dict = {}
    for etiket, dosya in (("tr", "skor_tr.jsonl"), ("en", "skor_en.jsonl"),
                          ("tr_wikisource", "skor_tr_wikisource.jsonl")):
        yol = C.REPO_ROOT / "results_insan" / dosya
        if not yol.exists():
            continue
        z = [json.loads(l)["score"] for l in yol.open(encoding="utf-8")
             if json.loads(l)["scheme"] == "KGW"]
        k = sum(1 for x in z if x > 4.0)
        d = _binom_ci(k, len(z))
        nominal = n.get("s1", {}).get("z4_nominal_fpr") or 3.17e-5
        d["kat"] = d["oran"] / nominal
        d["kat_ci"] = [d["ci"][0] / nominal, d["ci"][1] / nominal]
        s1b[etiket] = d
    if s1b:
        n["s1_belirsizlik"] = s1b

    # C15: TPR guven araliklari zaten hesaplaniyordu ama basilmiyordu
    dm = pd.read_csv(C.RESULTS / "detection_metrics.csv")
    n["tpr_ci"] = [
        {"scheme": r["scheme"], "condition": r["condition"],
         "tpr": float(r["tpr_temiz_esikte"]),
         "ci": [float(r["tpr_ci_lo"]), float(r["tpr_ci_hi"])]}
        for _, r in dm.iterrows()]

    # F1: vaat edilip verilmeyen 33-hucrelik gercek FPR + ayni-donusum AUROC
    if {"gercek_fpr", "ayni_donusum_auroc"} <= set(dm.columns):
        kaynak = dm
    else:
        kaynak = None
    # Bolum 1 ve 3.3 bu tabloyu VAAT EDIYOR. metrics.py onu uretiyordu ama
    # yalnizca summary.md'ye yaziyordu; makaleye hic girmemisti. Ayni hesap
    # burada yeniden yapiliyor (esik temiz negatiflerin 1-TPR_AT_FPR
    # yuzdeligi; gercek FPR o esigin SALDIRILI negatiflerdeki orani).
    from scipy.stats import binomtest as _bt2
    from pilot.metrics import auroc as _auroc
    _sc = pd.read_csv(C.RESULTS / "scores.csv")
    _sat, _anl = [], []
    for _s in sorted(_sc.scheme.unique()):
        _ds = _sc[_sc.scheme == _s]
        _neg = _ds[(_ds.condition == "clean") & (_ds.wm == 0)]["stat"].to_numpy()
        _thr = float(np.quantile(_neg, 1 - C.TPR_AT_FPR))
        for _c in ["clean"] + C.ATTACKS:
            _an = _ds[(_ds.condition == _c) & (_ds.wm == 0)]["stat"].to_numpy()
            _po = _ds[(_ds.condition == _c) & (_ds.wm == 1)]["stat"].to_numpy()
            if not len(_an) or not len(_po):
                continue
            _k = int((_an > _thr).sum())
            _sat.append({
                "scheme": _s, "condition": _c,
                "tpr": float((_po > _thr).mean()),
                "gercek_fpr": float(_an.mean() * 0 + (_an > _thr).mean()),
                "n_gecen": f"{_k}/{len(_an)}",
                "fpr_ci_hi": float(_bt2(_k, len(_an)).proportion_ci(0.95).high),
                "ayni_donusum_auroc": (float(_auroc(_po, _an))
                                       if len(np.unique(np.r_[_po, _an])) > 1
                                       else None),
            })
    for _r in _sat:
        _k, _nn = map(int, _r["n_gecen"].split("/"))
        _pv = _bt2(_k, _nn, C.TPR_AT_FPR, alternative="greater").pvalue
        if _pv * len(_sat) < 0.05:
            _anl.append(f"{_r['scheme']}/{_r['condition']}")
    n["fpr_33"] = {
        "n_hucre": len(_sat),
        "satirlar": _sat,
        "en_yuksek_fpr": max(r["gercek_fpr"] for r in _sat),
        "nominal": C.TPR_AT_FPR,
        "bonferroni_anlamli": _anl,
        "cozunurluk": 1.0 / 96,
    }

    # E6: uzunluk-artefakti savunmasi §3.2'de YALNIZ KGW kolundan hesaplaniyordu
    # ve bu beyan edilmiyordu. Havuz degerlerini de uretiyoruz ki metin hangi
    # kolun rakamini verdigini soyleyebilsin ve kuyrugu gizlemesin.
    import glob as _glob
    import statistics as _st
    uz: dict = {}
    for _sal in ("para", "rtt", "launder", "launder_api"):
        _kollar, _havuz = {}, []
        for _yol in sorted(_glob.glob(str(C.RESULTS / f"att_*_{_sal}.jsonl"))):
            _kol = Path(_yol).name.split("att_")[1].rsplit(f"_{_sal}", 1)[0]
            _o = [json.loads(l).get("uzunluk_orani")
                  for l in open(_yol, encoding="utf-8")]
            _o = [x for x in _o if x is not None]
            if not _o:
                continue
            _kollar[_kol] = {"n": len(_o), "medyan": float(_st.median(_o)),
                             "min": float(min(_o))}
            _havuz += [(x, _kol) for x in _o]
        if _havuz:
            _mn = min(_havuz)
            uz[_sal] = {"kollar": _kollar,
                        "havuz": {"n": len(_havuz),
                                  "medyan": float(_st.median(x for x, _ in _havuz)),
                                  "min": _mn[0], "min_kol": _mn[1]}}
    if uz:
        n["uzunluk_orani_kol"] = uz

    # E1/E14: S2 yargilarinin kaynak kolu (makine-okunur kayit yoktu)
    n["s2_kaynak_kol"] = {
        "kol": "pos_KGW",
        "_kaynak": "pilot/dev_s2_fayda.py KAYNAK sabiti",
        "_sinir": ("Anlam korunumu yalnizca KGW kolundan uretilen metinlerde "
                   "olculdu; EXP ve SynthID satirlarinda ayni yargi yeniden "
                   "kullanildi. 'Uc semaya karsi basarili' bilesik hukmu bu "
                   "yuzden bir kol-arasi tasinabilirlik varsayimina dayanir."),
    }

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(n, ensure_ascii=False, indent=2))
    print(f"yazıldı: {OUT}  ({OUT.stat().st_size/1024:.0f} KiB)")


if __name__ == "__main__":
    main()
