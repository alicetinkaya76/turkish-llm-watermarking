# pilot/dev_metrics_selftest.py — analiz katmanının TORCH'SUZ uçtan uca testi.
#
# Bilinen-cevaplı sentetik bir results/ fikstürü kurar (96 örnek x 3 şema x
# 8 koşul skorları + morfolojik saldırı için GERÇEK zeyrek dönüşümlü metin
# çiftleri), sonra metrics.py'nin tamamını çalıştırır:
#   detection_table, auroc_ci, tpr_at_fpr, separation_table, dz_per_edit,
#   quality_table (kütüphane yoksa zarifçe atlama yolu), make_figs,
#   write_summary.
# Bilinen cevaplar geri kazanılıyorsa (temiz AUROC ~1, gömülü Δz/edit eğimi
# ~0.15, morph lemma-Jaccard >= 0.95 > para) analiz katmanı sağlamdır.
#
#   python -m pilot.dev_metrics_selftest
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import append_jsonl  # noqa: E402

IDS = [(p, s) for p in range(24) for s in C.SEEDS]  # 96

_BASE_SENTS = [
    "Şehir hayatı hızla değişiyor ve insanlar yeni koşullara uyum sağlıyor.",
    "Öğrenciler kütüphanede ders çalışıyor, notlarını düzenliyor.",
    "Talep arttığı için fiyatlar yükseliyor, esnaf durumu izliyor.",
    "Sabahları deniz kenarında yürüyüş yapmak zihni dinlendiriyor.",
]
_PARA_SENTS = [  # aynı anlam, farklı kelime seçimi (paraphrase taklidi)
    "Kent yaşamı süratle başkalaşıyor; bireyler taze şartlara alışıyor.",
    "Gençler okuma salonunda derslerine bakıyor, defterlerini topluyor.",
    "İstek çoğaldığından ücretler tırmanıyor; satıcılar gelişmeleri gözlüyor.",
    "Erken saatte kıyıda gezinti yapmak kafayı rahatlatıyor.",
]
_LAUNDER_SENTS = [  # tamamen yeniden yazım taklidi
    "Metropollerdeki gündelik düzen artık bambaşka bir hâl alıyor.",
    "Sınav dönemi yaklaşınca gençler kaynak taramaya ağırlık veriyor.",
    "Piyasadaki hareketlilik satıcıları temkinli davranmaya itiyor.",
    "Güne kıyı şeridinde başlamak pek çok kişiye iyi geliyor.",
]


def build_fixture(res: Path) -> None:
    from pilot.attacks import morph_attack, strip_diacritics

    # write_summary artik rejim dogrulamasi yapiyor (_rejim_dogrula): canli
    # C.GEN_KWARGS, korpusu ureten env.json'la eslesmiyorsa DURUYOR. Fikstur
    # sentetik oldugu icin env.json'u CANLI config'ten uretiyoruz -- boylece
    # kapi gecer ve gercek kosuda gercek uyusmazligi yakalamaya devam eder.
    import json as _j
    (res / "env.json").write_text(_j.dumps({
        "model": "selftest-fixture", "device": "cpu",
        "gen_kwargs": dict(C.GEN_KWARGS),
        "exp_sequence_length": C.EXP_SEQUENCE_LENGTH,
        "config_adi": "selftest",
    }, ensure_ascii=False))

    rng = np.random.default_rng(0)
    # --- skorlar: şema başına (temiz_neg, temiz_pos, koşul->pos_ort, sahte-neg) ---
    scales = {  # stat uzayında ortalamalar
        "KGW":     dict(neg=0.0, pos=6.0, sd=1.0,
                        att=dict(dia100=2.5, dia50=4.0, morph=None,  # morph özel
                                 **{"morph+dia": 2.0}, rtt=1.0, para=0.8, launder=0.5)),
        "EXP":     dict(neg=0.3, pos=8.0, sd=1.2,
                        att=dict(dia100=3.0, dia50=5.0, morph=6.5,
                                 **{"morph+dia": 2.5}, rtt=1.0, para=0.8, launder=0.6)),
        "SynthID": dict(neg=0.500, pos=0.560, sd=0.008,
                        att=dict(dia100=0.520, dia50=0.545, morph=0.552,
                                 **{"morph+dia": 0.515}, rtt=0.505, para=0.503,
                                 launder=0.501)),
    }
    edits_map = {pid_seed: int(rng.poisson(6)) + 1 for pid_seed in IDS}
    TRUE_SLOPE = 0.15  # KGW morph: geri kazanılacak gömülü eğim

    rows = []
    for scheme, sc in scales.items():
        clean_pos_stats = {}
        for (p, s) in IDS:
            n = float(rng.normal(sc["neg"], sc["sd"]))
            v = float(rng.normal(sc["pos"], sc["sd"]))
            clean_pos_stats[(p, s)] = v
            rows.append((scheme, "clean", 0, p, s, n, 0))
            rows.append((scheme, "clean", 1, p, s, v, 0))
        for att, mu in sc["att"].items():
            for (p, s) in IDS:
                rows.append((scheme, att, 0, p, s,
                             float(rng.normal(sc["neg"], sc["sd"])), 0))
                if scheme == "KGW" and att == "morph":
                    e = edits_map[(p, s)]
                    v = clean_pos_stats[(p, s)] - TRUE_SLOPE * e \
                        + float(rng.normal(0, 0.15))
                    rows.append((scheme, att, 1, p, s, v, e))
                else:
                    e = edits_map[(p, s)] if att.startswith("morph") else 0
                    rows.append((scheme, att, 1, p, s,
                                 float(rng.normal(mu, sc["sd"])), e))

    import csv
    from pilot.config import SCORES_CSV_FIELDS
    with open(res / "scores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SCORES_CSV_FIELDS)
        w.writeheader()
        for scheme, cond, wm, p, s, stat, e in rows:
            w.writerow(dict(scheme=scheme, condition=cond, wm=wm, prompt_id=p,
                            seed=s, score=stat, stat=stat, n_tokens=300,
                            edits=e, rejected=0, short=0, src="fixture"))

    # --- metin çiftleri (separation_table için; morph GERÇEK zeyrek yolu) ---
    for i, (p, s) in enumerate(IDS[:12]):
        base = " ".join(_BASE_SENTS[(i + j) % 4] for j in range(3))
        append_jsonl(res / "gen_pos_KGW.jsonl",
                     dict(prompt_id=p, seed=s, wm=1, text=base))
        m, meta = morph_attack(base)
        append_jsonl(res / "att_pos_KGW_morph.jsonl",
                     dict(prompt_id=p, seed=s, wm=1, text=m, **meta))
        append_jsonl(res / "att_pos_KGW_rtt.jsonl",
                     dict(prompt_id=p, seed=s, wm=1,
                          text=strip_diacritics(base, p=0.15, seed=i)))
        para = " ".join(_PARA_SENTS[(i + j) % 4] for j in range(3))
        append_jsonl(res / "att_pos_KGW_para.jsonl",
                     dict(prompt_id=p, seed=s, wm=1, text=para))
        lau = " ".join(_LAUNDER_SENTS[(i + j) % 4] for j in range(3))
        append_jsonl(res / "att_pos_KGW_launder.jsonl",
                     dict(prompt_id=p, seed=s, wm=1, text=lau))

    (res / "fertility.json").write_text(
        json.dumps({"fixture-model": 2.31}), encoding="utf-8")


def main() -> None:
    td = Path(tempfile.mkdtemp(prefix="pilot_selftest_"))
    res_backup = C.RESULTS
    C.RESULTS = td / "results"
    C.RESULTS.mkdir(parents=True)
    fails = []
    try:
        build_fixture(C.RESULTS)

        import pandas as pd
        from pilot import metrics as M

        scores = pd.read_csv(C.RESULTS / "scores.csv")
        det = M.detection_table(scores)
        kgw = det[(det.scheme == "KGW") & (det.condition == "clean")].iloc[0]
        print(f"temiz KGW  AUROC={kgw.auroc:.3f}  "
              f"GA=[{kgw.ci_lo:.3f},{kgw.ci_hi:.3f}]  TPR={kgw.tpr_temiz_esikte:.2f}")
        if not (kgw.auroc > 0.99 and kgw.tpr_temiz_esikte > 0.9):
            fails.append("temiz KGW metrikleri beklenen aralıkta değil")
        laund = det[(det.scheme == "KGW") & (det.condition == "launder")].iloc[0]
        print(f"launder KGW AUROC={laund.auroc:.3f} (beklenen ~0.5-0.7)")
        if not (0.35 < laund.auroc < 0.80):
            fails.append("launder AUROC makul aralık dışı")

        dz = M.dz_per_edit(scores)
        print(f"Δz/edit eğimi={dz['slope']:.3f} (gömülü 0.15), r={dz['r']:.2f}, "
              f"n={dz['n']}")
        # KAPI GUCLENDIRILDI: Pearson r tek basina KALDIRACA duyarli.
        # morph_v1 gercek veride r=0,60 verirken Spearman p=0,39 ve
        # bootstrap GA sifiri iceriyordu -- yani r yuksek ama iliski YOK.
        # Sentetik fiksturde gomulu egim gercek oldugu icin ucu de gecmeli.
        if not (dz and abs(dz["slope"] - 0.15) < 0.05 and dz["r"] > 0.6
                and dz.get("spearman_p", 1.0) < 0.05
                and dz.get("saglam") is True):
            fails.append(
                f"Δz/edit gomulu egim geri kazanilamadi "
                f"(egim={dz['slope']:.3f} r={dz['r']:.2f} "
                f"rho_p={dz.get('spearman_p', float('nan')):.3f} "
                f"saglam={dz.get('saglam')})" if dz else "dz_per_edit None dondu")

        sep = M.separation_table(subsample=12)
        print(sep.to_string(index=False))
        s = sep.set_index("attack")
        if not (s.loc["morph", "lemma_jaccard"] >= 0.95
                > s.loc["para", "lemma_jaccard"]):
            fails.append("morph/para lemma-Jaccard ayrışması sağlanamadı")

        q = M.quality_table(device="cpu")  # kütüphane yoksa None dönmeli
        print(f"quality_table -> {'atlandı (None)' if q is None else f'{len(q)} satır'}")

        M.make_figs(scores, det)
        out = M.write_summary(device="cpu", with_quality=False)
        head = out.read_text(encoding="utf-8").splitlines()[:8]
        print("--- summary.md ilk satırlar ---")
        print("\n".join(head))
        for fpath in ("figs/auroc_by_condition.png", "figs/kgw_clean_z_hist.png",
                      "detection_metrics.csv", "summary.md"):
            if not (C.RESULTS / fpath).exists():
                fails.append(f"çıktı eksik: {fpath}")
    finally:
        C.RESULTS = res_backup
        shutil.rmtree(td, ignore_errors=True)

    if fails:
        print("\nSELFTEST KALDI:\n- " + "\n- ".join(fails))
        sys.exit(1)
    print("\nANALİZ KATMANI ÖZ-TESTİ: GEÇTİ ✔ (AUROC/GA/TPR, Δz-eğimi, "
          "lemma-Jaccard ayrışması, figürler, summary.md)")


if __name__ == "__main__":
    main()
