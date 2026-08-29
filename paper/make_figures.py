# paper/make_figures.py — makale figürleri. HER SAYI VERİDEN türetilir;
# elle sabit yok (annotasyonlar dahil hepsi dosyalardan hesaplanır).
#
#   python paper/make_figures.py
# Çıktı: paper/figs/fig{1,2,3}.{png,pdf}
#
# Renkler dataviz doğrulayıcısından GEÇTİ (light, surface #fcfcfb):
#   kategorik: mavi #2a78d6 / turuncu #eb6834 / aqua #1baf7a
#   aqua'nın yüzeye kontrast uyarısı DOĞRUDAN ETİKETLE karşılanıyor
#   (her seri etikete sahip; kimlik asla yalnız renkte değil).
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, norm

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "paper" / "figs"
FIGS.mkdir(exist_ok=True)

RENK = {"KGW": "#2a78d6", "EXP": "#eb6834", "SynthID": "#1baf7a"}
GRI = "#5D6873"
plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#E3E6E3", "grid.linewidth": 0.6,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "font.family": "DejaVu Sans",
})


def _skorlar(dosya: str, sema: str) -> np.ndarray:
    yol = ROOT / "results_insan" / dosya
    return np.array([json.loads(l)["score"] for l in yol.open(encoding="utf-8")
                     if json.loads(l)["scheme"] == sema])


def kaydet(fig, ad: str) -> None:
    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"{ad}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  {ad}.png/.pdf")


# ---------------------------------------------------------------- Figür 1
def fig1() -> None:
    """KGW null dağılımları insan metninde — manşet figürü."""
    seriler = [
        ("Turkish (Wikipedia)",  _skorlar("skor_tr.jsonl", "KGW"),            RENK["KGW"]),
        ("Turkish (Wikisource)", _skorlar("skor_tr_wikisource.jsonl", "KGW"), RENK["EXP"]),
        ("English (Wikipedia)",  _skorlar("skor_en.jsonl", "KGW"),            RENK["SynthID"]),
    ]
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    xs = np.linspace(-6.5, 7.0, 500)
    # teorik N(0,1) — nötr, kesikli
    ax.plot(xs, norm.pdf(xs), ls="--", lw=1.4, color=GRI, zorder=2)
    ax.plot([], [], ls="--", lw=1.4, color=GRI, label="theoretical N(0,1)")
    # Etiketler LEJANTTA (tepe-konumlu açıklamalar çakışıyordu — göz
    # kontrolünde yakalandı: üç eğrinin tepe yükseklikleri ~0,28-0,30 ve
    # açıklamalar üst üste biniyordu). σ ve aşım sayısı lejant metninde.
    for ad, x, renk in seriler:
        kde = gaussian_kde(x)
        std = float(np.std(x, ddof=1))
        n4 = int((x > 4).sum())
        ax.plot(xs, kde(xs), lw=2.0, color=renk, zorder=3,
                label=f"{ad} — σ {std:.3f}, {n4}/{len(x)} > 4")
    ax.axvline(4.0, color="#B0821F", lw=1.2, ls=":")
    ax.annotate("z = 4 default\nthreshold", xy=(4.0, 0.30), xytext=(4.3, 0.29),
                fontsize=7.5, color="#B0821F")
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    ax.set_xlabel("KGW detection statistic (z-score) on unwatermarked human text")
    ax.set_ylabel("density")
    ax.set_xlim(-6.5, 7.0)
    ax.set_ylim(0, 0.46)
    kaydet(fig, "fig1_null_distributions")


# ---------------------------------------------------------------- Figür 2
def fig2() -> None:
    """Saldırı altında AUROC — kümeli GA'larla nokta-aralık grafiği."""
    det = pd.read_csv(ROOT / "results" / "detection_metrics.csv")
    piv = det.pivot(index="condition", columns="scheme", values="auroc")
    sira = (piv.loc["clean"] - piv).drop("clean").mean(axis=1).sort_values().index
    sira = ["clean"] + list(sira)          # üstte temiz, altta en yıkıcı
    etiket = {"clean": "clean", "morph": "morph (v0)", "morph_v1": "morph (v1)",
              "dia50": "diacritic 50%", "dia100": "diacritic 100%",
              "morph+dia": "morph+dia", "morph_v1+dia": "morph v1+dia",
              "para": "paraphrase (self)", "launder": "launder (self)",
              "rtt": "round-trip transl.", "launder_api": "launder (external)"}
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    kay = {"KGW": +0.22, "EXP": 0.0, "SynthID": -0.22}
    for i, cond in enumerate(sira):
        y0 = len(sira) - 1 - i
        for sema in ("KGW", "EXP", "SynthID"):
            r = det[(det.scheme == sema) & (det.condition == cond)].iloc[0]
            y = y0 + kay[sema]
            dejenere = pd.notna(r.get("ci_lo_cp"))
            if dejenere:
                # Dejenere hücre: bootstrap GA [1,1]. ÖNCEKİ SÜRÜM burada
                # Clopper-Pearson alt sınırından 1'e ince bir çizgi çiziyordu;
                # o sınır geri çekildi (§3.3: CP bir binom oranını sınırlar,
                # AUROC ise U-istatistiğidir), dolayısıyla çizgi de kaldırıldı.
                # Geriye içi boş işaretçi kalıyor: "karşı örnek gözlenmedi",
                # sayısal bir alt sınır İDDİA ETMEDEN. Ayrışmanın gücü
                # Tablo 3'te marj ve tam permütasyon p'siyle veriliyor.
                ax.plot(r["auroc"], y, "o", ms=4.5, mfc="white",
                        mec=RENK[sema], mew=1.3, zorder=3)
            else:
                ax.plot([r["ci_lo"], r["ci_hi"]], [y, y], color=RENK[sema],
                        lw=1.6, solid_capstyle="butt")
                ax.plot(r["auroc"], y, "o", ms=4.5, color=RENK[sema], zorder=3)
    ax.set_yticks([len(sira) - 1 - i for i in range(len(sira))])
    ax.set_yticklabels([etiket[c] for c in sira])
    # Etiket kısaltıldı: uzun sürüm bbox_inches="tight" ile bile sağdan
    # kırpılıyordu ("CI" görünmüyordu, render kontrolünde yakalandı).
    ax.set_xlabel("AUROC vs. clean negatives\n"
                  "bars: prompt-clustered 95% CI")
    ax.set_xlim(0.62, 1.01)
    ax.axvline(1.0, color="#E3E6E3", lw=0.8)
    from matplotlib.lines import Line2D
    lej = [Line2D([0], [0], marker="o", color=RENK[s], lw=1.6, ms=4.5, label=s)
           for s in ("KGW", "EXP", "SynthID")]
    lej.append(Line2D([0], [0], marker="o", mfc="white", mec=GRI, color="none",
                      ms=4.5, mew=1.3,
                      label="degenerate CI (complete separation)"))
    # sol alt, launder(external) çizgisiyle çakışıyordu -> sol üst boş
    ax.legend(handles=lej, loc="upper left", fontsize=7, frameon=False)
    ax.grid(axis="y", visible=False)
    kaydet(fig, "fig2_auroc_attacks")


# ---------------------------------------------------------------- Figür 3
def fig3() -> None:
    """Sağlamlık–kalibrasyon ödünleşimi."""
    s1 = json.loads((ROOT / "results_insan" / "insan_fpr_rapor.json").read_text())
    det = pd.read_csv(ROOT / "results" / "detection_metrics.csv")
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    for sema in ("KGW", "EXP", "SynthID"):
        x = s1["tr"][sema]["null_std"]
        r = det[(det.scheme == sema) & (det.condition == "launder_api")].iloc[0]
        ax.errorbar(x, r["auroc"], yerr=[[r["auroc"] - r["ci_lo"]],
                                         [r["ci_hi"] - r["auroc"]]],
                    fmt="o", ms=7, color=RENK[sema], capsize=3, lw=1.4)
        dx = 1.25 if sema != "KGW" else 0.78
        ax.annotate(sema, xy=(x, r["auroc"]), xytext=(x * dx, r["auroc"] + 0.012),
                    fontsize=8.5, color=RENK[sema], fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlabel("null std. dev. on human Turkish (log scale)\n"
                  "← better calibrated")
    ax.set_ylabel("AUROC under external laundering\n← more fragile")
    ax.annotate("cleanest null,\nmost fragile", xy=(s1["tr"]["SynthID"]["null_std"],
                det[(det.scheme == "SynthID") & (det.condition == "launder_api")]
                ["auroc"].iloc[0]),
                xytext=(0.010, 0.775), fontsize=7.5, color=GRI)
    kaydet(fig, "fig3_tradeoff")


if __name__ == "__main__":
    fig1(); fig2(); fig3()
    print("tamam")
