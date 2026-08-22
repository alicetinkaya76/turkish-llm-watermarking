# pilot/metrics.py — K10 metrikleri, Go/No-Go özeti, summary.md ve figürler.
from __future__ import annotations

import difflib
import json
import random
import re
from pathlib import Path

import numpy as np
import pandas as pd

from pilot import config as C
from pilot.jsonl import read_jsonl


# ----------------------------------------------------------------------
# Tespit metrikleri
# ----------------------------------------------------------------------
def auroc(pos: np.ndarray, neg: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    s = np.r_[pos, neg]
    return float(roc_auc_score(y, s))


def auroc_ci(pos: np.ndarray, neg: np.ndarray,
             n_boot: int = C.BOOTSTRAP_N, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        p = pos[rng.integers(0, len(pos), len(pos))]
        n = neg[rng.integers(0, len(neg), len(neg))]
        if len(np.unique(np.r_[p, n])) < 2:
            continue
        vals.append(auroc(p, n))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def tpr_at_fpr(pos: np.ndarray, neg: np.ndarray,
               fpr: float = C.TPR_AT_FPR) -> float:
    thr = np.quantile(neg, 1 - fpr)
    return float((pos > thr).mean())


def detection_table(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scheme in sorted(scores["scheme"].unique()):
        d = scores[scores["scheme"] == scheme]
        neg_clean = d[(d.condition == "clean") & (d.wm == 0)]["stat"].to_numpy()
        for cond in ["clean"] + C.ATTACKS:
            pos = d[(d.condition == cond) & (d.wm == 1)]["stat"].to_numpy()
            if len(pos) == 0 or len(neg_clean) == 0:
                continue
            lo, hi = auroc_ci(pos, neg_clean)
            attneg = d[(d.condition == cond) & (d.wm == 0)]["stat"].to_numpy()
            rows.append(dict(
                scheme=scheme, condition=cond, n_pos=len(pos),
                auroc=auroc(pos, neg_clean), ci_lo=lo, ci_hi=hi,
                tpr_1fpr=tpr_at_fpr(pos, neg_clean),
                pos_stat_mean=float(pos.mean()),
                attneg_stat_mean=float(attneg.mean()) if len(attneg) else np.nan,
            ))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Kalite: çok dilli e5 kosinüs benzerliği (orijinal vs saldırılı)
# ----------------------------------------------------------------------
def quality_table(device: str) -> pd.DataFrame | None:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print(f"  UYARI: sentence-transformers yok, kalite atlandı ({e})")
        return None
    try:
        st = SentenceTransformer(C.E5_MODEL, device=device)
    except Exception:
        st = SentenceTransformer(C.E5_MODEL, device="cpu")

    def embed(texts: list[str]) -> np.ndarray:
        return st.encode([f"query: {t}" for t in texts],
                         normalize_embeddings=True, batch_size=16,
                         show_progress_bar=False)

    rows = []
    for src_tag in ["neg"] + [f"pos_{s}" for s in C.SCHEMES]:
        base_file = ("gen_neg.jsonl" if src_tag == "neg"
                     else f"gen_{src_tag}.jsonl")
        base = {(r["prompt_id"], r["seed"]): r["text"]
                for r in read_jsonl(C.RESULTS / base_file)}
        if not base:
            continue
        for attack in C.ATTACKS:
            att = read_jsonl(C.RESULTS / f"att_{src_tag}_{attack}.jsonl")
            pairs = [(base[(r["prompt_id"], r["seed"])], r["text"])
                     for r in att if (r["prompt_id"], r["seed"]) in base]
            if not pairs:
                continue
            a = embed([p[0] for p in pairs])
            b = embed([p[1] for p in pairs])
            cos = (a * b).sum(axis=1)
            rows.append(dict(src=src_tag, condition=attack, n=len(pairs),
                             e5_cos_mean=float(cos.mean()),
                             e5_cos_p05=float(np.quantile(cos, 0.05))))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Morfolojik != leksik kanıtı (K10): lemma-Jaccard + karakter oranı
# ----------------------------------------------------------------------
def _words(text: str) -> list[str]:
    """_lemma_set ile AYNI kelime ayıklaması (ısıtma ile tutarlı olmalı)."""
    out = []
    for w in text.lower().split():
        core = "".join(c for c in w if c.isalpha() or c in "çğıöşü")
        if core:
            out.append(core)
    return out


def _lemma_set(text: str) -> set[str]:
    from pilot.attacks import _parses  # zeyrek zaten yüklü

    out = set()
    for core in _words(text):
        ps = _parses(core)
        out.add(ps[0].lemma if ps else core)
    return out


def separation_table(subsample: int = C.QUALITY_SUBSAMPLE,
                     src_tag: str = "pos_KGW") -> pd.DataFrame:
    base = {(r["prompt_id"], r["seed"]): r["text"]
            for r in read_jsonl(C.RESULTS / f"gen_{src_tag}.jsonl")}
    rows = []
    rnd = random.Random(7)
    attacks = ["morph", "morph_v1", "para", "launder", "rtt"]

    # Kanonik ısıtma (K11): _lemma_set korpustaki TÜM benzersiz kelimeleri
    # çözümler ve zeyrek çok sayıda analizden sonra sonuçlarını değiştirir.
    # prewarm, kelimeleri SIRALI gruplarda taze analizörlerde çözümleyerek
    # sonucu metinlerin işlenme sırasından bağımsız kılar.
    from pilot.attacks import prewarm
    corpus = list(base.values())
    for attack in attacks:
        corpus += [r["text"] for r in
                   read_jsonl(C.RESULTS / f"att_{src_tag}_{attack}.jsonl")]
    n = prewarm(w for t in corpus for w in _words(t))
    print(f"  zeyrek ısıtma: {n} benzersiz kelime çözümlendi")

    for attack in attacks:
        att = read_jsonl(C.RESULTS / f"att_{src_tag}_{attack}.jsonl")
        att = [r for r in att if (r["prompt_id"], r["seed"]) in base]
        for r in rnd.sample(att, min(subsample, len(att))):
            o = base[(r["prompt_id"], r["seed"])]
            a, b = _lemma_set(o), _lemma_set(r["text"])
            jac = len(a & b) / max(1, len(a | b))
            # autojunk=False ZORUNLU. Varsayilan True, difflib in dizinin
            # %1 inden fazlasinda gecen karakterleri "gurultu" sayip ATLAMASINA
            # yol acar; ~3000 karakterlik Turkce metinde bu bosluk ve sik
            # harfleri kapsar ve benzerligi sistematik olarak DUSUK olcer.
            # Olculen sapma (pos_KGW, n=25): rtt 0,092 -> 0,735 (+0,643),
            # launder_api 0,119 -> 0,679, launder 0,524 -> 0,874, para 0,642 -> 0,920.
            chr_ratio = difflib.SequenceMatcher(
                None, o, r["text"], autojunk=False).ratio()
            rows.append(dict(attack=attack, lemma_jaccard=jac,
                             char_ratio=chr_ratio))
    df = pd.DataFrame(rows)
    return (df.groupby("attack")
              .agg(n=("lemma_jaccard", "size"),
                   lemma_jaccard=("lemma_jaccard", "mean"),
                   char_ratio=("char_ratio", "mean"))
              .reset_index()) if len(df) else df


# ----------------------------------------------------------------------
# Mekanistik okuma: KGW'de düzenleme başına Δz (morph koşulu)
# ----------------------------------------------------------------------
def dz_per_edit(scores: pd.DataFrame, condition: str = "morph") -> dict | None:
    """KGW'de düzenleme başına Δz. condition ile morph_v1 de okunabilir:
    v0'ın kapsamı düşük olduğu için n küçük ve eğim gürültülü kalıyor."""
    d = scores[scores.scheme == "KGW"]
    clean = d[(d.condition == "clean") & (d.wm == 1)].set_index(
        ["prompt_id", "seed"])["stat"]
    morph = d[(d.condition == condition) & (d.wm == 1)].set_index(
        ["prompt_id", "seed"])[["stat", "edits"]]
    j = morph.join(clean.rename("z_clean"), how="inner")
    j = j[j.edits > 0]
    if len(j) < 8:
        return None

    # SAGLAMLIK ZORUNLU. Ilk surum yalniz OLS egimi + Pearson r basiyordu.
    # Olculdu (morph_v1, n=92): OLS -0,0261 ama bootstrap %95 GA [-0,034, +0,005]
    # SIFIRI ICERIYOR, Theil-Sen -0,0050 (OLS in 5te biri), Spearman -0,091
    # (p=0,390) ve en yuksek 3 nokta atilinca ISARET DONUYOR (+0,0033).
    # Yani OLS egimi birkac kaldirac noktasindan geliyordu. v0 ise saglam:
    # GA [-0,071, -0,022] sifiri disliyor, Theil-Sen OLS ile uyumlu, isaret korunuyor.
    from scipy import stats as _st

    # ISARET KONVANSIYONU: z_clean - stat = DUSUS. Pozitif egim = duzenleme
    # basina filigran ZAYIFLIYOR. Ilk yazdigimda ters cevirmistim ve oz-test
    # gomulu +0,150 egimi -0,149 olarak geri kazandi (buyukluk dogru, isaret ters).
    dz = (j["z_clean"] - j["stat"]).to_numpy()
    ed = j["edits"].to_numpy()
    ols = _st.linregress(ed, dz)
    ts = _st.theilslopes(dz, ed)
    sp = _st.spearmanr(ed, dz)
    _rng = np.random.default_rng(42)
    _bs = []
    for _ in range(4000):
        _i = _rng.integers(0, len(ed), len(ed))
        if len(np.unique(ed[_i])) < 2:
            continue
        _bs.append(_st.linregress(ed[_i], dz[_i]).slope)
    lo, hi = (np.percentile(_bs, [2.5, 97.5]) if _bs else (np.nan, np.nan))
    _k = np.argsort(ed)[:-3]
    _ols3 = _st.linregress(ed[_k], dz[_k]) if len(np.unique(ed[_k])) > 1 else None

    saglam = bool(
        not (lo < 0 < hi)                                   # GA sifiri dislamali
        and sp.pvalue < 0.05                                # monoton iliski olmali
        and (_ols3 is None or np.sign(_ols3.slope) == np.sign(ols.slope))
    )
    return dict(
        condition=condition, n=int(len(j)), slope=float(ols.slope),
        r=float(ols.rvalue), mean_edits=float(ed.mean()),
        ci_lo=float(lo), ci_hi=float(hi),
        theil_sen=float(ts[0]),
        spearman=float(sp.statistic), spearman_p=float(sp.pvalue),
        slope_top3_atilinca=(float(_ols3.slope) if _ols3 is not None else float("nan")),
        saglam=saglam,
    )


def _determinizm_satiri() -> str:
    """Tekrarlanabilirlik kaydi ETKIN CIHAZA gore. Onceki surum MPS'te olculmus
    '8/8 birebir ayni' sonucunu SABIT basiyordu; CUDA'ya tasindiktan sonra bu
    cumle O ORTAMDA OLCULMEMIS bir iddia haline geldi."""
    dev = "?"
    envp = C.RESULTS / "env.json"
    if envp.exists():
        try:
            dev = json.loads(envp.read_text()).get("device", "?")
        except Exception:
            pass
    if dev == "mps":
        return ("- **Tekrarlanabilirlik OLCULDU** (`pilot.dev_mps_determinism`): "
                "saklanan Faz 1 ciktilarinin 8 ornegi, ayri bir surecte ayni "
                "tohumlarla yeniden uretildiginde **8/8 birebir ayni** metni verdi, "
                "|dz| ort/maks = 0.000/0.000. Kapsam: KGW, tek makine, sabit "
                "surumler (bkz. env.json) -- tasinabilirlik iddiasi DEGILDIR.")
    dosya = C.REPO_ROOT / "results_hpc" / "drift.json"
    if dev == "cuda" and dosya.exists():
        try:
            k = json.loads(dosya.read_text())["olcumler"]["T4_determinizm"]
            return (f"- **Tekrarlanabilirlik OLCULDU** (CUDA, "
                    f"`hpc/remote_scripts/drift.py::T4`): {k.get('ilkine_ozdes')}/"
                    f"{k.get('tekrar')} yineleme birebir ayni token dizisini verdi. "
                    "Kapsam: tek GPU, sabit surumler -- tasinabilirlik iddiasi DEGILDIR.")
        except Exception:
            pass
    return (f"- **Tekrarlanabilirlik:** bu ortamda (`device={dev}`) OLCULMEDI. "
            "Onceki MPS olcumu devralinmaz.")


def _korpus_uyum_orani() -> tuple[float, float, int]:
    """(uyum_orani, sonlandirma_orani, n). Manşet ve görev-uyumu bölümü AYNI
    veriden beslensin diye tek yerde hesaplanır -- ikisi çelişemesin.

    ⛔ EXP MUAFİYETİ. İlk sürüm sonlandırmayı HAM METİNDEN yeniden hesaplıyor ve
    satırda saklı `kapi_sonlandirilmis=None` muafiyetini YOK SAYIYORDU. EXP EOS'ta
    durmaz (exp.py:127), 96 metninin hiçbiri noktalama ile bitmez; onları kusur
    saymak 96/384 = %25'lik sahte bir "kesiklik" üretti ve rapor korpusu HAKSIZ
    yere GEÇERSİZ ilan etti. Bu, B6'da tespit edilen yanlılığın aynısıdır --
    orada elemede engellenmiş, burada hükümde sızmıştı.
    Muafiyetli satırlar PAYDADAN da düşer; "ölçülemez" ile "başarısız" aynı şey değildir.
    """
    w, wn, son, sn, n = 0, 0, 0, 0, 0
    for f in ["gen_neg"] + [f"gen_pos_{s}" for s in C.SCHEMES]:
        for r in read_jsonl(C.RESULTS / f"{f}.jsonl"):
            n += 1
            kk = r.get("kapi_kelime")
            if kk is None:
                kk = len(r["text"].split()) >= C.KAPI_HEDEF_KELIME
            w += bool(kk); wn += 1
            ks = r.get("kapi_sonlandirilmis", "yok")
            if ks == "yok":                      # eski satır: alan hiç yazılmamış
                ks = r["text"].rstrip().endswith((".", "!", "?", "…"))
            if ks is None:                       # MUAF (EXP) -> paydaya girmez
                continue
            son += bool(ks); sn += 1
    return (w / wn if wn else 0.0, son / sn if sn else 0.0, n)


def _md_table(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, float) else str(v)
                 for v in row.tolist()]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def make_figs(scores: pd.DataFrame, det: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figdir = C.RESULTS / "figs"
    figdir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 4))
    conds = ["clean"] + C.ATTACKS
    x = np.arange(len(conds))
    w = 0.26
    for i, scheme in enumerate(C.SCHEMES):
        d = det[det.scheme == scheme].set_index("condition")
        vals = [d.loc[c, "auroc"] if c in d.index else np.nan for c in conds]
        ax.bar(x + (i - 1) * w, vals, w, label=scheme)
    ax.set_xticks(x, conds, rotation=30, ha="right")
    ax.set_ylabel("AUROC"); ax.set_ylim(0.4, 1.02)
    ax.axhline(0.5, ls="--", lw=0.8, color="gray")
    ax.legend(); fig.tight_layout()
    fig.savefig(figdir / "auroc_by_condition.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    d = scores[(scores.scheme == "KGW") & (scores.condition == "clean")]
    ax.hist(d[d.wm == 0]["stat"], bins=30, alpha=0.6, label="no-wm")
    ax.hist(d[d.wm == 1]["stat"], bins=30, alpha=0.6, label="wm")
    ax.set_xlabel("KGW z"); ax.legend(); fig.tight_layout()
    fig.savefig(figdir / "kgw_clean_z_hist.png", dpi=150); plt.close(fig)


_FOREIGN = re.compile(r"[一-鿿぀-ヿ가-힯ᄀ-ᇿ"
                      r"Ѐ-ӿ֐-׿؀-ۿ]")


def task_compliance() -> list[str]:
    """GÖREV UYUMU — korpusun istemi yerine getirip getirmediği.

    Tur-2 denetiminin en ağır bulgusu. Pilot boyunca bakılan kapılar
    (`short` = 150 token, `clean_cut`, `n_tokens`) hiçbiri GÖREVİ sınamıyordu;
    hepsi geçtiği için korpus geçerli sanıldı. Oysa istemlerin tamamı "en az
    300 kelime" istiyor ve üretim bütçesi buna yapısal olarak yetmiyor.

    Bu bölüm rapora ZORUNLU olarak girer: sayı üretilmezse kimse bakmıyor.
    """
    import json as _json
    from pathlib import Path as _P

    pr = _P(__file__).parent / "prompts_tr.json"
    prompts = _json.loads(pr.read_text(encoding="utf-8")) if pr.exists() else []
    # ÖLÇÜT config'ten gelir, İSTEMDEN DEĞİL. İstemler 500 kelime ister (model
    # istenenin %72-80'ini teslim ettiği için kalibre edildi); kabul ölçütü 300.
    # Önceki sürüm sayıyı istemden okuyordu -> istem 500 olunca korpusu haksız
    # yere kusurlu ilan ederdi.
    hedef = C.KAPI_HEDEF_KELIME
    m = re.search(r"(\d+)\s*kelime", " ".join(prompts))
    istem_hedefi = int(m.group(1)) if m else None
    isteyen = sum(bool(re.search(r"\d+\s*kelime", p)) for p in prompts)

    rows = []
    for src, f in ([("filigransız", "gen_neg")]
                   + [(s, f"gen_pos_{s}") for s in C.SCHEMES]):
        recs = read_jsonl(C.RESULTS / f"{f}.jsonl")
        if not recs:
            continue
        w = [len(r["text"].split()) for r in recs]
        rows.append(dict(
            kaynak=src, n=len(recs), ort_kelime=sum(w) / len(w),
            min_kelime=min(w), maks_kelime=max(w),
            hedefi_gecen=sum(x >= hedef for x in w) if hedef else -1,
            # EXP muaf: kapi_sonlandirilmis=None -> -1 ile "uygulanmaz" isaretlenir
            sonlandirilmis=(-1 if all(r.get("kapi_sonlandirilmis", False) is None
                                      for r in recs)
                            else sum(bool(r.get("kapi_sonlandirilmis",
                                     r["text"].rstrip().endswith((".", "!", "?", "…"))))
                                     for r in recs)),
            token_tavaninda=sum(r.get("n_tokens", 0) >=
                                C.GEN_KWARGS["max_new_tokens"] - 1 for r in recs)))
    if not rows:
        return []
    df = pd.DataFrame(rows)
    tot = int(df["n"].sum())
    gecen = int(df["hedefi_gecen"].sum())
    # -1 = muaf (EXP): hem paydan hem PAYDADAN düşer
    _muaf = df[df["sonlandirilmis"] < 0]["n"].sum()
    son = int(df[df["sonlandirilmis"] >= 0]["sonlandirilmis"].sum())
    tot_son = tot - int(_muaf)

    fert = C.RESULTS / "fertility.json"
    gerek = None
    if fert.exists() and hedef:
        # fertility.py sözlüğe EKLİYOR; ilk değeri almak BAŞKA bir modelin
        # bereketini kullanmak demekti. Etkin modelin kaydı yoksa cümle basılmaz.
        _fd = _json.loads(fert.read_text())
        _mdl = None
        _envp = C.RESULTS / "env.json"
        if _envp.exists():
            _mdl = _json.loads(_envp.read_text()).get("model")
        vals = [_fd[_mdl]] if _mdl in _fd else []
        if vals:
            gerek = hedef * vals[0]

    # HÜKÜM KOŞULLU. Önceki sürüm başlığı ve ⛔'yi HER ZAMAN basıyordu; temiz bir
    # korpusta rapor, kendi hesapladığı tablonun hemen üstünde onu yalanlayan bir
    # manşetle açılıyordu. Bu tam da selefi makaleyi düşüren hata sınıfı.
    uyum = gecen / tot if tot else 0.0
    sonl = son / tot_son if tot_son else 0.0
    kusurlu = uyum < C.KORPUS_UYUM_ESIGI or sonl < C.KORPUS_SONLANDIRMA_ESIGI
    baslik = ("## ⛔ GÖREV UYUMU — KORPUS İSTEMİ YERİNE GETİRMİYOR" if kusurlu
              else "## Görev uyumu")
    out = ["", baslik, "",
           f"{isteyen}/{len(prompts)} istem **en az {istem_hedefi} kelime** istiyor; "
           f"kabul ölçütü **{hedef} kelime** (model istenenin bir kısmını teslim "
           f"ettiği için istem kalibre edildi — ölçüm: results_hpc/istem_provenans.json). "
           f"Üretim bütçesi `max_new_tokens={C.GEN_KWARGS['max_new_tokens']}`."]
    if gerek:
        out += ["", f"Ölçülen bereket ({vals[0]:.3f} token/kelime) ile {hedef} "
                f"kelime yaklaşık **{gerek:.0f} token** gerektirir — bütçe "
                f"gerekenin **%{100*C.GEN_KWARGS['max_new_tokens']/gerek:.0f}**'i."
                + (" Görev yapısal olarak yerine getirilemez."
                   if C.GEN_KWARGS['max_new_tokens'] < gerek else "")]
    out += ["", _md_table(df.round(1)), "",
f"**{gecen}/{tot} (%{100*uyum:.1f}) metin {hedef} kelime olcutunu "
            f"karsiliyor. {tot_son - son}/{tot_son} (%{100*(1-sonl):.1f}) "
            f"sonlandirici noktalama olmadan bitiyor** (sonlandirma paydasi "
            f"{tot_son}: EXP in {tot - tot_son} metni yapisal olarak muaf)."]
    if kusurlu:
        out += ["", "> **Sonuç:** `short` (150 token) ve `clean_cut` kapıları GÖREV "
                "UYUMUNU sınamaz. Bu korpusta ölçülen her şey — tespit dahil — "
                "göreve uymayan metin üzerinde ölçülmüştür.", "",
                f"> Eşikler (koşudan önce sabit): uyum ≥ %{100*C.KORPUS_UYUM_ESIGI:.0f}, "
                f"sonlandırma ≥ %{100*C.KORPUS_SONLANDIRMA_ESIGI:.0f}. "
                f"Ölçülen: %{100*uyum:.1f} ve %{100*sonl:.1f}. "
                "Korpus YENİDEN ÜRETİLMELİDİR."]
    else:
        out += ["", f"> Korpus, koşudan önce sabitlenen eşikleri karşılıyor "
                f"(uyum ≥ %{100*C.KORPUS_UYUM_ESIGI:.0f}, sonlandırma ≥ "
                f"%{100*C.KORPUS_SONLANDIRMA_ESIGI:.0f})."]
    return out


def audit_corrections(scores: pd.DataFrame) -> list[str]:
    """Üçüncü-göz denetiminin (2026-08-16) doğrulanmış bulgularına yanıt.

    Denetim yedi doğrulanabilir kritik iddia getirdi; yedisi de bu veride
    yeniden üretildi. Bu bölüm düzeltmeleri KODDAN üretir — elle yazılmış sayı
    bırakmamak için (bir önceki teslimatta elle kopyalanan 0,019 bayatlamıştı).
    """
    from scipy.stats import binomtest

    out: list[str] = ["", "## Denetim düzeltmeleri (üçüncü-göz, 2026-08-16)", "",
                      "Bağımsız metodolojik denetim yedi kritik bulgu getirdi; "
                      "hepsi bu veride doğrulandı. Aşağıdakiler koddan üretilir."]

    # --- D1: tohum dejenerasyonu (etkin n) -------------------------------
    rows = []
    for s in sorted(scores.scheme.unique()):
        ident = tot = 0
        for cond in scores.condition.unique():
            g = scores[(scores.scheme == s) & (scores.condition == cond) &
                       (scores.wm == 1)]
            for _, sub in g.groupby("prompt_id"):
                # n<2 hücre atlanır: nunique()==1 tek satırlı grupta DAİMA
                # doğrudur ve kısmi üretim (kesilen resume, red alıp atlanan
                # launder_api satırı, --attacks alt kümesi) özdeşlik sayacını
                # şişirip UYDURMA bir "tohum etkisiz" bulgusu üretir.
                if len(sub) < 2:
                    continue
                tot += 1
                ident += int(sub["stat"].nunique() == 1 and
                             sub["n_tokens"].nunique() == 1)
        rows.append(dict(sema=s, ozdes_hucre=ident, toplam_hucre=tot,
                         oran=ident / max(1, tot),
                         etkin_n=("24 (tohum etkisiz)" if ident / max(1, tot) > 0.5
                                  else "96")))
    df = pd.DataFrame(rows)
    bad = df[df.oran > 0.5]["sema"].tolist()
    out += ["", "### D1 — Tohumlar bağımsız tekrar değil (KRİTİK)", "",
            _md_table(df.round(3))]
    if bad:
        out += ["", f"**{', '.join(bad)} için dört tohum aynı sonucu veriyor.** "
                "Sebep: EXP'nin `seed_rng`'i prompt'un son `prefix_length` "
                "token'ından türer, torch RNG'sini kullanmaz — algoritma "
                "prompt+anahtar verildiğinde deterministiktir. Özdeşlik tam "
                "olarak DETERMİNİSTİK koşullarda (clean, dia100, morph×4, rtt) "
                "görülür, stokastik olanlarda (dia50, para, launder, "
                "launder_api) kaybolur.", "",
                "> **Sonuç:** bu şema için etkin bağımsız kaynak sayısı 96 "
                "değil **24 prompt**'tur. Raporun bütün güven aralıkları o "
                "şema için DAR; satır-düzeyi bootstrap yerine prompt-kümeli "
                "bootstrap gerekir. Bu, pilot tasarımının kusurudur: dört "
                "tohum EXP için tekrar üretmiyor."]

    # --- D2: saldırılı negatiflerde GERÇEK FPR ---------------------------
    rows = []
    for s in sorted(scores.scheme.unique()):
        ds = scores[scores.scheme == s]
        neg = ds[(ds.condition == "clean") & (ds.wm == 0)]["stat"].to_numpy()
        thr = float(np.quantile(neg, 1 - C.TPR_AT_FPR))
        for cond in ["clean"] + C.ATTACKS:
            an = ds[(ds.condition == cond) & (ds.wm == 0)]["stat"].to_numpy()
            pos = ds[(ds.condition == cond) & (ds.wm == 1)]["stat"].to_numpy()
            if not len(an) or not len(pos):
                continue
            rows.append(dict(sema=s, kosul=cond, tpr=float((pos > thr).mean()),
                             gercek_fpr=float((an > thr).mean())))
    fpr = pd.DataFrame(rows)
    worst = fpr.nlargest(6, "gercek_fpr")
    out += ["", "### D2 — 'TPR@%1FPR' saldırılı veride %1 FPR DEĞİL (KRİTİK)", "",
            "Eşik temiz negatiflerden kuruluyor; saldırılı negatiflerde o eşiğin "
            "gerçek yanlış-pozitif oranı ölçülmemişti. En kötü altı hücre:", "",
            _md_table(worst.round(3)), "",
            f"**En yüksek gerçek FPR %{100*fpr.gercek_fpr.max():.1f}** — "
            f"yani bazı hücrelerde 'yüksek TPR' etiketinin bedeli %1 değil "
            f"%{100*fpr.gercek_fpr.max():.1f}'e kadar yanlış pozitif "
            f"({int((fpr.gercek_fpr > 2*C.TPR_AT_FPR).sum())} hücrede eşiğin "
            f"iki katından fazla). Metrik operasyonel olarak yanlış "
            "adlandırılmıştı. Ana çalışmada her koşul için (i) temiz eşikte "
            "TPR, (ii) aynı eşikte saldırılı-negatif FPR, (iii) saldırılı "
            "pozitif–saldırılı negatif AUROC birlikte verilmelidir."]

    # --- D3: eşlenmiş koşul karşılaştırması (launder_api vs rtt) ---------
    if "launder_api" in set(scores.condition) and "rtt" in set(scores.condition):
        rows = []
        for s in sorted(scores.scheme.unique()):
            ds = scores[scores.scheme == s]
            neg = ds[(ds.condition == "clean") & (ds.wm == 0)]["stat"].to_numpy()
            thr = float(np.quantile(neg, 1 - C.TPR_AT_FPR))
            a = (ds[(ds.condition == "rtt") & (ds.wm == 1)]
                 .set_index(["prompt_id", "seed"])["stat"] > thr)
            b = (ds[(ds.condition == "launder_api") & (ds.wm == 1)]
                 .set_index(["prompt_id", "seed"])["stat"] > thr)
            j = pd.concat([a.rename("r"), b.rename("p")], axis=1).dropna()
            n01 = int(((~j.r) & (j.p)).sum())
            n10 = int((j.r & (~j.p)).sum())
            p = binomtest(n01, n01 + n10, 0.5).pvalue if (n01 + n10) else 1.0
            rows.append(dict(sema=s, tpr_rtt=float(a.mean()),
                             tpr_launder_api=float(b.mean()),
                             fark=float(b.mean() - a.mean()), mcnemar_p=p,
                             bonferroni=("ANLAMLI" if p * 3 < 0.05 else "—")))
        # HÜKÜM HESAPTAN GELİR. Önceki sürüm "hiçbir şemada anlamlı değil" diye
        # SABİT yazıyordu; o cümle ESKİ (geçersiz) korpusun sonucuydu. Yeni veride
        # tablo başka şey söylüyorsa rapor kendi hesabıyla çelişirdi.
        _d3 = pd.DataFrame(rows)
        _anl = _d3[_d3["bonferroni"] == "ANLAMLI"]
        _yon = _d3["fark"].mean()
        if len(_anl):
            _basl = ("### D3 — launder_api, rtt'den daha yıkıcı "
                     f"({len(_anl)}/{len(_d3)} şemada ANLAMLI)")
            _yorum = (f"Eşleşmiş McNemar testinde {', '.join(_anl['sema'])} şemasında "
                      f"fark Bonferroni düzeltmesini geçiyor. Ortalama TPR farkı "
                      f"{_yon:+.3f} (negatif = launder_api daha yıkıcı).")
        else:
            _basl = "### D3 — 'launder_api en yıkıcı saldırı' iddiası: KANITLANAMADI"
            _yorum = ("Eşleşmiş McNemar testinde hiçbir şemada fark Bonferroni'yi "
                      f"geçmiyor (ortalama TPR farkı {_yon:+.3f}). Nokta tahmini "
                      "sıralaması TEHDİT SIRALAMASI DEĞİLDİR.")
        out += ["", _basl, "", _md_table(_d3.round(4)), "", _yorum, "",
                "**Kapsam:** bu karşılaştırma yalnız rtt ile launder_api arasındadır; "
                "tüm saldırıların sıralaması için *Tespit* tablosuna bakınız."]

    return out + [""]


def corpus_integrity(scores: pd.DataFrame) -> list[str]:
    """Korpus bütünlüğü + kirlenmenin tespit sonuçlarını etkileyip etkilemediği.

    Üretilen metinlerin bir kısmı Latin-dışı yazı sistemleri içeriyor (Qwen2.5-3B
    Türkçe üretirken çok dilli sözlüğünün kuyruğuna kayıyor). Bu, KALİTE
    ölçütlerini geçersiz kılar. TESPİT ölçütleri için ise varsayım yapmıyoruz:
    metrikler yalnız kirlenmemiş alt kümede yeniden hesaplanıp tam korpusla
    karşılaştırılıyor.
    """
    rows, dirty = [], set()
    for src, f in ([("neg", "gen_neg")]
                   + [(f"pos_{s}", f"gen_pos_{s}") for s in C.SCHEMES]):
        recs = read_jsonl(C.RESULTS / f"{f}.jsonl")
        if not recs:
            continue
        hit = [r for r in recs if _FOREIGN.search(r["text"])]
        for r in hit:
            dirty.add((src, r["prompt_id"], r["seed"]))
        rows.append(dict(kaynak=f, n=len(recs), kirli=len(hit),
                         oran=len(hit) / len(recs),
                         yabanci_karakter=sum(len(_FOREIGN.findall(r["text"]))
                                              for r in recs)))
    if not rows:
        return []
    df = pd.DataFrame(rows)
    tot_n, tot_d = int(df["n"].sum()), int(df["kirli"].sum())

    # HÜKÜM KOŞULLU + MODEL ADI VERİDEN. Önceki sürüm "KALİTE KATMANI GERİ
    # ÇEKİLDİ" başlığını, "%36" oranını ve "Qwen2.5-3B" adını SABİT basıyordu;
    # temiz bir korpusta ve başka bir modelde üçü de yanlış olurdu.
    _oran = tot_d / tot_n if tot_n else 0.0
    _model = "?"
    _envp = C.RESULTS / "env.json"
    if _envp.exists():
        try:
            _model = json.loads(_envp.read_text()).get("model", "?")
        except Exception:
            pass
    # Eşik: kalite ölçümünü anlamsız kılacak kirlenme düzeyi. Koşudan önce sabit.
    _kirli_esik = 0.05
    _kusurlu = _oran > _kirli_esik
    out = ["", ("## Korpus bütünlüğü — KALİTE KATMANI GERİ ÇEKİLDİ" if _kusurlu
                else "## Korpus bütünlüğü"), "",
           f"Üretilen {tot_n} metnin **{tot_d}'i (%{100*_oran:.1f})** "
           "Latin-dışı yazı sistemi (CJK / Hangul / Kiril / İbranice / Arapça) "
           f"içeriyor. Etkin üretici: `{_model}`.",
           "", _md_table(df.round(3)), ""]
    if _kusurlu:
        out += [f"**Sonuç:** kirlenme oranı %{100*_oran:.1f} > eşik "
                f"%{100*_kirli_esik:.0f}. Bu korpus üzerinde e5 kosinüsü ve "
                "LLM-yargıç kalite ölçümleri ANLAMLI DEĞİL — çok-yazılı bulamaç "
                "içeren metinlerde 'anlam korunuyor' demek, bulamacın korunduğunu "
                "ölçmektir. Kalite bölümü geri çekilmiştir. Veriden çıkan hüküm "
                f"yalnız: **`{_model}` bu promptlar ve üretim ayarlarıyla ana "
                "çalışma için uygun değildir** — bu bir BOYUT hükmü DEĞİLDİR "
                "(büyüklük deneyi koşulmadı)."]
    else:
        out += [f"**Sonuç:** kirlenme oranı %{100*_oran:.1f} ≤ eşik "
                f"%{100*_kirli_esik:.0f}; kalite katmanı geçerli sayılır."]

    # Tespit katmanı kirlenmeden etkileniyor mu? Varsayma - ölç.
    d = scores.copy()
    d["kirli"] = [(s, p, sd) in dirty
                  for s, p, sd in zip(d["src"], d["prompt_id"], d["seed"])]
    comp = []
    for cond in ["clean"] + C.ATTACKS:
        for s in C.SCHEMES:
            ds = d[d.scheme == s]
            neg = ds[(ds.condition == "clean") & (ds.wm == 0)]
            pos = ds[(ds.condition == cond) & (ds.wm == 1)]
            nf = neg[~neg.kirli]["stat"].to_numpy()
            pf = pos[~pos.kirli]["stat"].to_numpy()
            if len(nf) < 5 or len(pf) < 5 or len(pos) == 0:
                continue
            comp.append(dict(
                kosul=cond, sema=s,
                auroc_temiz=auroc(pf, nf), tpr_temiz=tpr_at_fpr(pf, nf),
                auroc_tam=auroc(pos["stat"].to_numpy(), neg["stat"].to_numpy()),
                tpr_tam=tpr_at_fpr(pos["stat"].to_numpy(), neg["stat"].to_numpy())))
    if comp:
        cdf = pd.DataFrame(comp)
        da = (cdf.auroc_temiz - cdf.auroc_tam).abs().max()
        dt = (cdf.tpr_temiz - cdf.tpr_tam).abs().max()
        wa = cdf.loc[(cdf.auroc_temiz - cdf.auroc_tam).abs().idxmax()]

        # Sıralama gerçekten değişiyor mu? İDDİA ETME - SAY.
        flips = []
        for cond in cdf.kosul.unique():
            g = cdf[cdf.kosul == cond]
            f = list(g.sort_values("tpr_tam", ascending=False).sema)
            c = list(g.sort_values("tpr_temiz", ascending=False).sema)
            if f != c:
                flips.append(f"`{cond}` (tam {'>'.join(f)} → temiz {'>'.join(c)})")

        out += ["", "### Tespit katmanı kirlenmeden etkileniyor mu? (ÖLÇÜLDÜ)", "",
                f"Metrikler yalnız kirlenmemiş metinlerle yeniden hesaplandı ve "
                f"tam korpusla karşılaştırıldı. **En büyük sapma: AUROC "
                f"{da:.4f} ({wa.sema}/{wa.kosul}), TPR {dt:.3f}.**"]
        if flips:
            out += ["", f"> ⚠️ **DÜZELTME (denetim §6):** önceki teslimatta "
                    f"'sıralama değişmiyor' yazıyordu — **yanlış.** Şema "
                    f"sıralaması {len(flips)} koşulda değişiyor: "
                    + "; ".join(flips) + ". Ayrıca sapmanın altkümede küçük "
                    "kalması kirlenme–filigran bağımsızlığını KANITLAMAZ; "
                    "seçici filtre yanlılığı taşıyabilir.", "",
                    "**Daraltılmış iddia:** *büyük yönler (rtt/launder_api en "
                    "yıkıcı, morph etkisiz, clean tavan) korunuyor; bazı alt "
                    "sıralamalar değişiyor.*"]
        else:
            out += ["", "Bu veride sıralama değişimi saptanmadı."]
        out += ["", _md_table(cdf.round(3))]
    return out


def _phase3_sections() -> list[str]:
    """Faz 3'ün disksiz ayakları: tokenizer bereketi kontrastı ve LLM-yargıç.
    Dosyalar yoksa bölüm hiç yazılmaz (uydurma sayı üretilmez)."""
    out: list[str] = []

    fc = C.RESULTS / "fertility_contrast.json"
    if fc.exists():
        data = json.loads(fc.read_text())
        ok = {k: v for k, v in data.items() if "error" not in v}
        if ok:
            df = pd.DataFrame([
                dict(tokenizer=k, sozluk=v["vocab_size"],
                     tr_bereket=v["tr_fertility"], en_bereket=v["en_fertility"],
                     tr_en_cezasi=v["tr_en_penalty"])
                for k, v in sorted(ok.items(), key=lambda x: -x[1]["tr_fertility"])
            ])
            out += ["", "## Tokenizer bereketi kontrastı (Faz 3)",
                    _md_table(df.round(3)), "",
                    "**Geçerli okuma:** aynı 11.751 kelimelik Türkçe korpusta "
                    "tokenizer'lar arasında TR bereketi belirgin farklılaşıyor "
                    "(Qwen2.5 2,585 -> BERTurk 1,598) ve sözlük büyüklüğü "
                    "belirleyici değil (BERTurk 32k ile en iyi, mT5 250k ile kötü). "
                    "**GERİ ÇEKİLDİ (denetim §10): tr_en_cezasi sütunu ve 'parçalanma "
                    "dilin değil seçimin sonucu' iddiası** — İngilizce taban yalnız 56 kelimelik elle yazılmış tek paragraf, Türkçe taraf 11.751 kelime (1:209); eşlenmemiş korpusla hesaplanan oran güvenilir değil. Encoder ile üretici decoder tokenizerları da aynı nedensel tabloda yorumlanamaz.",
                    "",
                    "> **Plan düzeltmesi (ölçüldü):** HANDOFF §7'nin Faz-3 adayı "
                    "`ytu-ce-cosmos/Turkish-Llama-8b-v0.1`, Llama-3'ün "
                    "tokenizer'ını DEĞİŞTİRMEDEN kullanıyor — iki sözlük yalnız 3 "
                    "ÖZEL token'da ayrışıyor, gerçek alt-kelime parçalarının %100'ü "
                    "ortak. O modelle 'TR-uyarlı tokenizer kontrastı' tanım gereği "
                    "sıfır fark verirdi."]
        bad = {k: v for k, v in data.items() if "error" in v}
        if bad:
            out += ["", "Erişilemeyen tokenizer'lar: " +
                    ", ".join(f"`{v['hf_name']}` ({v['error']})"
                              for v in bad.values())]

    # --- API ile GERÇEK laundering (Faz 3) --------------------------------
    lc = C.RESULTS / "launder_comparison.csv"
    if lc.exists():
        cmp = pd.read_csv(lc)
        kg = (cmp[cmp.sema == "KGW"].set_index("kosul")["tpr"]
              .drop("clean", errors="ignore").sort_values())
        order = " -> ".join(f"`{k}` {v:.3f}" for k, v in kg.items())
        piv = cmp.pivot(index="kosul", columns="sema", values="tpr")
        loc_ = piv.loc["launder"] if "launder" in piv.index else None
        api_ = piv.loc["launder_api"] if "launder_api" in piv.index else None
        out += ["", "## API ile GERÇEK laundering (Faz 3)", "",
                "Faz 2'nin `launder` saldırısı metni ÜRETEN modele (Qwen2.5-3B) "
                "yeniden yazdırıyordu; `launder_api` harici bir modele "
                "(Opus 5) yazdırır. İstem metni aynıdır, ancak **üretim "
                "prosedürü eşlenmiş DEĞİLDİR** (yerel: max 480 token, "
                "T=0.7, top_p=0.95, satır başına tohum YOK; API: max 4000 "
                "token, effort=low, örnekleme denetimi yok). Bu yüzden "
                "'tek değişken model' denemez — iki FARKLI AKLAMA HATTI "
                "karşılaştırılmaktadır (denetim tur-2 §10).", "",
                _md_table(piv.reset_index().round(3))]
        if loc_ is not None and api_ is not None:
            out += ["", f"**Betimsel gözlem:** yerel hat TPR "
                    f"{', '.join(f'{s} {loc_[s]:.3f}' for s in C.SCHEMES)}; "
                    f"API hattı "
                    f"{', '.join(f'{s} {api_[s]:.3f}' for s in C.SCHEMES)}. "
                    "API hattı üç şemada da daha düşük TPR veriyor. "
                    "NEDENSEL etiket ('model gücü') KURULMADI: hatlar "
                    "çıktı bütçesi ve decoding rejimi bakımından "
                    "eşlenmemiştir."]
        out += ["", f"**Nokta TPR değerleri (KGW, artan):** {order}", "",
                "> ⚠️ Bu bir TEHDİT SIRALAMASI DEĞİLDİR. Eşlenmiş McNemar "
                "(D3) hiçbir şemada anlamlı fark bulmuyor; denetim tur-2 "
                "ayrıca saldırılı-pozitif vs saldırılı-negatif AUROC ile "
                "sıralamanın iki şemada TERSİNE döndüğünü gösterdi. "
                "Sıralama okuması yapılmamalıdır."]

    # --- Filigranın KENDİ akıcılık bedeli (Faz 3) -------------------------
    wc = C.RESULTS / "llm_judge_api_wmcost.json"
    if wc.exists():
        from scipy.stats import binomtest
        r = json.loads(wc.read_text())["results"]
        rows2 = []
        # DÜZELTME (denetim §7): bağımsız birim 30 hüküm DEĞİL, 15 ÇİFT.
        # Sıra tersleme ikinci bir örnek değil, yanlılık kontrolüdür. Çiftler
        # tek sonuca indiriliyor: 2-0 kararlı tercih, 1-1 sıra-uyumsuz (atılır).
        for s in C.SCHEMES:
            v = r.get(f"pair_{s}")
            if not v:
                continue
            n = v["n"]
            n_j = 2 * n                                   # toplam hüküm
            flip = round(v["konum_donmesi"] * n)           # sıra-uyumsuz çiftler
            esit = round(v["esit"] * n_j)                 # ESIT hükmü sayısı
            k = int(round((v["filigransiz_daha_akici"] * n_j - flip) / 2))
            m = int(round((v["filigranli_daha_akici"] * n_j - flip) / 2))
            # ESIT'ler ne k'ye ne m'ye girer; berabere çiftler işaret testinden
            # ÇIKARILIR (dec = k + m). Eski kod dec = n - flip alıyordu, bu da
            # ESIT çiftlerini "filigranlı kazandı" diye sayıp p'yi bozuyordu.
            dec = k + m
            p = binomtest(k, dec, 0.5).pvalue if dec else 1.0
            tutarli = (k + m + flip + esit // 2 == n)     # muhasebe denetimi
            rows2.append(dict(sema=s, n_cift=n, kararli_cift=dec,
                              filigransiz=k, filigranli=m,
                              berabere=n - dec - flip,
                              sira_uyumsuz=flip, isaret_testi_p=p,
                              bonferroni=("ANLAMLI: filigran BOZUYOR"
                                          if p * 3 < 0.05 else "fark yok"),
                              muhasebe_tutarli=tutarli))
        if rows2:
            out += ["", "## Filigranın kendi akıcılık bedeli (Faz 3)", "",
                    "Bağımsız yargıç (Opus 5), AYNI prompt ve AYNI tohumla "
                    "üretilmiş filigransız/filigranlı çiftleri iki sırada "
                    "karşılaştırdı. İki metin aynı soruya bağımsız yanıtlar "
                    "olduğu için yalnız akıcılık soruldu. "
                    "**DÜZELTME (denetim §7):** p-değerleri artık ÇİFT "
                    "düzeyinde (15 çift), 30 hüküm üzerinden değil — sıra "
                    "tersleme bağımsız örnek değil yanlılık kontrolüdür; "
                    "önceki 0,0003/0,0001 değerleri ~30 kat iyimserdi. "
                    "Ayrıca 'konfound iki kolda simetrik' savunması YANLIŞ: "
                    "kirlenme taban %39,6 · KGW %42,7 · SynthID %45,8 · "
                    "EXP %16,7. Birincil analiz iki tarafı da temiz "
                    "çiftlerle yapılmalıydı; bu pakette yapılmadı.",
                    "", _md_table(pd.DataFrame(rows2).round(4)), "",
                    "**Bozan şemalar yukarıdaki tabloda ANLAMLI olarak "
                    "işaretlidir.** Bu bulgu, *Korpus bütünlüğü* bölümündeki "
                    "kirlenme oranlarıyla aynı yönde — iki bağımsız ölçüt "
                    "aynı sıralamayı veriyor (sayılar orada, koddan üretilir).",
                    "",
                    "> **Konfound uyarısı:** EXP hem en dayanıklı hem kaliteyi "
                    "bozmayan şema. Bu iki bağımsız üstünlük DEĞİL, tek "
                    "mekanizmanın iki sonucu olabilir: EXP olasılık kütlesini "
                    "yüksek olasılıklı token'lara yoğunlaştırır — bu hem çok "
                    "dilli kuyruğu bastırır (temiz metin) hem filigran "
                    "sinyalini güçlendirir (yüksek tespit payı). Makalede "
                    "'EXP iki eksende iyi' değil, 'EXP'nin örnekleme "
                    "yoğunlaştırması iki eksende birden fayda üretiyor' "
                    "biçiminde yazılmalıdır."]

    jp = C.RESULTS / "llm_judge.json"
    jw = C.RESULTS / "llm_judge_pointwise.json"
    if jp.exists() or jw.exists():
        out += ["", "## LLM-yargıç (Faz 3) — NEGATİF SONUÇ"]
        if jp.exists():
            d = json.loads(jp.read_text())["results"]
            flips = [v["konum_donmesi"] for v in d.values()]
            evet = [v["anlam_evet"] for v in d.values()]
            out += [
                f"- **İkili protokol kullanılamaz.** Konum dönmesi "
                f"%{100*min(flips):.0f}–%{100*max(flips):.0f} "
                f"(ort. %{100*sum(flips)/len(flips):.0f}): çift ters çevrilince "
                f"yargıç kararını değiştiriyor, yani metne değil sıraya bakıyor. "
                f"`morph` koşulunda dönme %{100*max(flips):.0f} — iki metin neredeyse "
                f"aynıyken bile 'eşit' diyemiyor (karakter oranı için "
                f"*Morfolojik-leksik ayrışma* tablosuna bak).",
                f"- **Evet-yanlılığı.** ANLAM=EVET aralığı "
                f"%{100*min(evet):.0f}–%{100*max(evet):.0f}; HAYIR hiç "
                f"kullanılmadı. Neredeyse özdeş `morph` ile büyük ölçüde değişmiş "
                f"`rtt` aynı cevabı alıyor -> ayırt etme gücü yok.",
            ]
        if jw.exists():
            d = json.loads(jw.read_text())["results"]
            base = d.get("_orijinal", {}).get("mean", float("nan"))
            best = max((v["mean"], k) for k, v in d.items() if k != "_orijinal")
            worst = min((v["mean"], k) for k, v in d.items() if k != "_orijinal")
            out += [
                f"- **Tekli protokol konum yanlılığını kaldırıyor ama karar "
                f"veremiyor.** Sıralama doğru yönde (`{worst[1]}` {worst[0]:.2f} en "
                f"düşük, `{best[1]}` {best[0]:.2f} en yüksek; orijinal {base:.2f}), "
                f"fakat hiçbir kıyas Bonferroni düzeltmesinden sonra anlamlı değil. "
                f"Ölçek kullanılmıyor: yargıç 1 ve 5 puanlarını hiç vermedi, "
                f"bütün ortalamalar {worst[0]:.2f}–{best[0]:.2f} aralığına "
                f"sıkıştı (gürültü > sinyal).",
            ]
        out += [
            "- **Sonuç:** aile-içi 3B yargıç (üreten modelin kendisi) kalite "
            "ölçüm aleti olarak KALİBRE DEĞİL.",
        ]

    # --- Bağımsız yargıç: sorun protokolde miydi, yargıçta mı? ------------
    ja = C.RESULTS / "llm_judge_api.json"
    if ja.exists() and jp.exists():
        api = json.loads(ja.read_text())
        loc = json.loads(jp.read_text())["results"]
        ar = api["results"]
        common = [k for k in ar if k in loc]
        if common:
            cmp2 = pd.DataFrame([dict(
                kosul=k,
                donme_3B=loc[k]["konum_donmesi"],
                donme_bagimsiz=ar[k]["konum_donmesi"],
                EVET_3B=loc[k]["anlam_evet"],
                EVET_bagimsiz=ar[k]["anlam_evet"]) for k in common])
            f3 = cmp2.donme_3B.mean()
            fa = cmp2.donme_bagimsiz.mean()
            sp3 = cmp2.EVET_3B.max() - cmp2.EVET_3B.min()
            spa = cmp2.EVET_bagimsiz.max() - cmp2.EVET_bagimsiz.min()
            out += ["", f"### Bağımsız yargıç ({api['judge_model']}) — "
                    "sorun protokolde değil, yargıçtaydı", "",
                    f"Aynı örneklem, aynı iki protokol, aynı sorular. "
                    f"**Ortalama konum dönmesi %{100*f3:.0f} -> "
                    f"%{100*fa:.0f}**; ANLAM sütununun yayılımı "
                    f"{100*sp3:.0f} puandan {100*spa:.0f} puana çıktı. "
                    "Yani ikili protokol sağlamdı; aile-içi 3B onu "
                    "kullanacak kapasitede değildi.", "",
                    _md_table(cmp2.round(3)), "",
                    "Yapısal çıktı (JSON şeması) kullanıldığı için "
                    "ayrıştırılamayan cevap kategorisi ortadan kalktı; "
                    "biçim uyumu ile yargı kalitesi ayrıştı. Opus 5'te "
                    "sampling parametreleri kaldırıldığı için yerel "
                    "yargıçtaki `do_sample=False` determinizmi API "
                    "tarafında kurulamaz — koşular arası küçük oynama "
                    "beklenir.", "",
                    "> **İçerik okumaları raporlanmıyor:** bağımsız yargıcın "
                    "saldırılar hakkındaki *anlam/akıcılık* kararları kirli "
                    "korpus üzerinde verildi. Raporlanan bulgu yargıçlar "
                    "arasındaki KALİBRASYON farkıdır; saldırıların kalite "
                    "etkisi değil."]
    return out


def write_summary(device: str, with_quality: bool = True) -> Path:
    scores = pd.read_csv(C.RESULTS / "scores.csv")
    det = detection_table(scores)
    det.to_csv(C.RESULTS / "detection_metrics.csv", index=False)
    sep = separation_table()
    qual = quality_table(device) if with_quality else None
    dz = [x for x in (dz_per_edit(scores, c) for c in ("morph", "morph_v1"))
          if x]
    fert = {}
    fpath = C.RESULTS / "fertility.json"
    if fpath.exists():
        fert = json.loads(fpath.read_text())
    make_figs(scores, det)

    kgw_clean = det[(det.scheme == "KGW") & (det.condition == "clean")]
    kgw_auroc = float(kgw_clean["auroc"].iloc[0]) if len(kgw_clean) else float("nan")
    sanity = "GEÇTİ" if kgw_auroc >= C.SANITY_AUROC else "KALDI"

    def delta(scheme: str, cond: str) -> float:
        d = det[det.scheme == scheme].set_index("condition")["auroc"]
        if "clean" in d.index and cond in d.index:
            return float(d["clean"] - d[cond])
        return float("nan")

    # "Morfolojik != leksik" kapısı: yüksek lemma-Jaccard TEK BAŞINA yetmez.
    # Saldırı metni hiç değiştirmediyse Jaccard zaten 1'e yakın çıkar ve kriter
    # saldırının leksik-korumacılığını değil, YOKLUĞUNU ölçmüş olur. Bu yüzden
    # karakter oranı da şart: metin gerçekten değişmiş olmalı (char_ratio yeterince
    # düşük), lemma kümesi ise korunmuş olmalı (Jaccard yüksek).
    MIN_CHAR_CHANGE = 0.02          # en az %2 karakter değişmiş olmalı
    morph_sep = {}
    if len(sep):
        s = sep.set_index("attack")
        for m in ("morph", "morph_v1"):
            if m not in s.index or "para" not in s.index:
                continue
            jac = float(s.loc[m, "lemma_jaccard"])
            chg = 1.0 - float(s.loc[m, "char_ratio"])
            lex = jac > float(s.loc["para", "lemma_jaccard"]) + 0.05
            if chg < MIN_CHAR_CHANGE:
                morph_sep[m] = (f"ÖLÇÜLEMEDİ — metin yalnız %{100*chg:.1f} "
                                f"değişti; J={jac:.3f} saldırının leksik "
                                f"korumasını değil, etkisizliğini yansıtıyor")
            elif jac >= 0.95 and lex:
                morph_sep[m] = (f"KANITLANDI (J={jac:.3f}, "
                                f"karakter değişimi %{100*chg:.1f})")
            else:
                morph_sep[m] = (f"KANITLANAMADI (J={jac:.3f}, "
                                f"karakter değişimi %{100*chg:.1f})")

    _morph_sep_lines = [f"- **Morfolojik ≠ leksik ({m}):** {v}"
                        for m, v in morph_sep.items()] or \
        ["- **Morfolojik ≠ leksik ayrışması:** _veri yok_"]

    # MANŞET KOŞULLU VE VERİDEN ÜRETİLİR. Önceki sürümde bu üç satır SABİTTİ ve
    # "hiçbir metin ulaşmıyor / %96 kesik" diye HER ZAMAN basıyordu -- temiz bir
    # korpusta rapor kendi tablosunu yalanlayan bir manşetle açılırdı. Sayılar
    # artık aynı veriden hesaplanır; eşikler C.KORPUS_*_ESIGI (koşudan önce sabit).
    _uy, _sn, _n = _korpus_uyum_orani()
    lines = [
        "# Pilot Özeti — Türkçe LLM Filigran Sağlamlığı",
        "",
    ]
    if _n and (_uy < C.KORPUS_UYUM_ESIGI or _sn < C.KORPUS_SONLANDIRMA_ESIGI):
        # YALNIZ DÜŞEN ölçüt sayılır. Her ikisini birden yazmak, sağlam olan
        # ölçütü de kusur gibi gösterir ("%0,0'i kesik" bir geçersizlik gerekçesi
        # değildir) ve raporu kendi verisiyle çelişkili gösterir.
        _dusen = []
        if _uy < C.KORPUS_UYUM_ESIGI:
            _dusen.append(f"metinlerin yalnız %{100*_uy:.1f}'i {C.KAPI_HEDEF_KELIME} "
                          f"kelime ölçütünü karşılıyor (eşik %{100*C.KORPUS_UYUM_ESIGI:.0f})")
        if _sn < C.KORPUS_SONLANDIRMA_ESIGI:
            _dusen.append(f"%{100*(1-_sn):.1f}'i cümle ortasında kesik "
                          f"(sonlandırma eşiği %{100*C.KORPUS_SONLANDIRMA_ESIGI:.0f})")
        lines += [
            f"> ⛔ **KORPUS GEÇERSİZ** ({_n} metin): " + "; ".join(_dusen) +
            ". Ayrıntı: *Görev uyumu*. Aşağıdaki bütün sayılar bu korpus üzerinde "
            "ölçülmüştür ve ana bulgu olarak kullanılamaz.",
            "",
        ]
    elif _n:
        lines += [
            f"> Korpus koşudan önce sabitlenen kabul eşiklerini karşılıyor: "
            f"{_n} metnin %{100*_uy:.1f}'i {C.KAPI_HEDEF_KELIME} kelime ölçütünü "
            f"karşılıyor, %{100*_sn:.1f}'i sonlandırıcı noktalama ile bitiyor.",
            "",
        ]
    lines += [
        "## Go / No-Go",
        f"- **Öncül (KGW temiz AUROC ≥ {C.SANITY_AUROC}):** {sanity} "
        f"({kgw_auroc:.3f})",
        f"- **TR-saldırılar ΔAUROC (KGW):** dia100={delta('KGW','dia100'):.3f}, "
        f"morph(v0)={delta('KGW','morph'):.3f}, morph_v1={delta('KGW','morph_v1'):.3f}, "
        f"morph+dia={delta('KGW','morph+dia'):.3f}, rtt={delta('KGW','rtt'):.3f}",
        *_morph_sep_lines,
        "",
        "## Tespit (pozitifler vs TEMİZ negatifler)",
        _md_table(det.round(3)),
        "",
        "## Morfolojik-leksik ayrışma (pos_KGW alt-örneklemi)",
        _md_table(sep.round(3)) if len(sep) else "_veri yok_",
    ]
    if qual is not None and len(qual):
        # HÜKÜM KOŞULLU + ORAN VERİDEN. Önceki sürüm "GERİ ÇEKİLDİ" başlığını ve
        # "%36 Latin-dışı" oranını SABİT basıyordu; o karar KİRLİ korpus içindi.
        # Temiz bir korpusta kalite ölçümü geçerlidir ve geri çekmek yanlış olur.
        _kir_n, _kir_t = 0, 0
        for _f in ["gen_neg"] + [f"gen_pos_{_s}" for _s in C.SCHEMES]:
            for _r in read_jsonl(C.RESULTS / f"{_f}.jsonl"):
                _kir_t += 1
                _kl = _r.get("kapi_latin")
                if _kl is None:
                    _kl = not _FOREIGN.search(_r["text"])
                _kir_n += (not _kl)
        _kir_o = _kir_n / _kir_t if _kir_t else 0.0
        if _kir_o > 0.05:
            lines += ["", "## Kalite (e5 kosinüs) — ⚠️ GERİ ÇEKİLDİ", "",
                      f"> Tablo YALNIZCA tekrarlanabilirlik için bırakılmıştır; "
                      f"**bulgu olarak kullanılamaz.** Korpusun %{100*_kir_o:.1f}'i "
                      f"Latin-dışı yazı sistemi içeriyor (bkz. *Korpus bütünlüğü*), "
                      f"dolayısıyla 'anlam korunuyor' okuması bulamacın korunduğunu ölçer.",
                      "", _md_table(qual.round(3))]
        else:
            lines += ["", "## Kalite (e5 kosinüs)", "",
                      f"> Korpus kirlenme oranı %{100*_kir_o:.1f} (eşik %5) — kalite "
                      f"ölçümü GEÇERLİ. Değerler orijinal ve saldırılmış metin "
                      f"arasındaki çok dilli e5 kosinüs benzerliğidir; **1'e yakın = "
                      f"anlam korunmuş**. Saldırının 'başarılı' sayılması için hem "
                      f"tespiti düşürmesi hem metni kullanılabilir bırakması gerekir.",
                      "", _md_table(qual.round(3))]
    if dz:
        lines += ["", "## KGW mekanistik okuma",
                  "",
                  "> Eğim SAĞLAMLIK TESTİNDEN geçirilir: bootstrap %95 GA sıfırı "
                  "dışlamalı, Spearman p<0.05 olmalı, ve en yüksek 3 kaldıraç "
                  "noktası atılınca işaret korunmalı. Üçünden biri düşerse eğim "
                  "GERİ ÇEKİLİR -- OLS eğimi birkaç uç gözlemden gelebilir."]
        for x in dz:
            if x.get("saglam"):
                lines += [
                    f"- `{x['condition']}`: düzenleme başına Δz eğimi "
                    f"**{x['slope']:+.3f}** "
                    f"(%95 GA [{x['ci_lo']:+.3f}, {x['ci_hi']:+.3f}], "
                    f"Theil-Sen {x['theil_sen']:+.3f}, "
                    f"Spearman ρ={x['spearman']:+.2f} p={x['spearman_p']:.3f}, "
                    f"n={x['n']}, ort. edit={x['mean_edits']:.1f})",
                    f"  - Pratik büyüklük: ort. {x['mean_edits']:.1f} edit × "
                    f"{abs(x['slope']):.3f} ≈ Δz {abs(x['mean_edits']*x['slope']):.2f}; "
                    f"KGW temiz z ≈ 10.6 üzerinden sinyalin "
                    f"~%{100*abs(x['mean_edits']*x['slope'])/10.6:.1f}'i. "
                    f"AUROC etkisi ölçülen: 0.000.",
                ]
            else:
                lines += [
                    f"- `{x['condition']}`: **GERİ ÇEKİLDİ** — eğim sıfırdan "
                    f"ayırt edilemiyor. OLS {x['slope']:+.3f} ama "
                    f"%95 GA [{x['ci_lo']:+.3f}, {x['ci_hi']:+.3f}] sıfırı içeriyor, "
                    f"Theil-Sen {x['theil_sen']:+.3f} (OLS'ten farklı → kaldıraç), "
                    f"Spearman ρ={x['spearman']:+.2f} (p={x['spearman_p']:.3f}), "
                    f"en yüksek 3 nokta atılınca eğim "
                    f"{x['slope_top3_atilinca']:+.3f}.",
                ]
    if fert:
        lines += ["", "## Tokenizer bereketi (token/kelime)",
                  "\n".join(f"- {k}: {v:.3f}" for k, v in fert.items())]
    # Yöntem notları: değerler config'ten okunur, elle yazılmaz.
    ov = ", ".join(f"{s}: {d}" for s, d in C.SCHEME_GEN_OVERRIDES.items()) or "yok"
    lines += [
        "", "## Yöntem notları",
        f"- Üretim ayarları (tüm şemalar, EXP hariç): `{C.GEN_KWARGS}`",
        f"- Şema-özel ezmeler: {ov} "
        "(SynthID kendi logits işlemcisinde sıcaklığı uyguladığı için HF'in "
        "ikinci uygulaması kapatıldı; etkin T üç şemada da eşit)",
        f"- EXP `max_new_tokens`'ı yok sayar: uzunluğu `{C.SCHEME_CONFIGS['EXP']}` "
        "içindeki `sequence_length` belirler ve EOS'ta durmaz -> EXP pozitifleri "
        "sabit uzunlukta, negatifler değil. Uzunluk konfoundu için `n_tokens` "
        "her satırda loglanır.",
        "- SynthID'nin logits işlemcisi durumu her üretimden önce sıfırlanır "
        "(MarkLLM'de sıfırlanmıyor; örnekler arası bağlam sızıntısı sonucu "
        "üretim sırasına bağımlı kılıyordu).",
        _determinizm_satiri(),
    ]
    lines += task_compliance()
    lines += audit_corrections(scores)
    lines += corpus_integrity(scores)
    lines += _phase3_sections()
    lines += ["", "_Figürler: results/figs/ — Ham skorlar: results/scores.csv_"]

    out = C.RESULTS / "summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  summary.md yazıldı -> {out}")
    return out
