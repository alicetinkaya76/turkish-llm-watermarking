# pilot/dev_anahtar_supurme.py — D2/D4/D5: S1 null'unun anahtara duyarliligi.
#
# SORUN. Butun kosu TEK anahtarla yapildi (config/KGW.json hash_key=15485863,
# upstream MarkLLM varsayilani; SynthID 30-anahtarlik varsayilan vektor).
# Anahtarli bir filigranin null dagilimi ilke olarak anahtara ozgu olabilir:
# KGW'de anahtar, kelime dagarcigini sabit bir yesil/kirmizi boluntuye ayirir;
# belirli bir anahtar belirli bir tokenizer ve korpusta idiosinkratik ortalama,
# varyans veya kuyruk uretebilir. Tek anahtarla olculen "TR null std 1.479"
# bulgusu bu yuzden sema-duzeyi bir kestirim degildir.
#
# NEDEN UCUZ. S1 URETIM GEREKTIRMEZ: insan metni zaten filigransiz, dedektorler
# modelsiz (model=None). Anahtari degistirip ayni pencereleri yeniden skorlamak
# yeterli. (Saldiri/AUROC eksenleri icin durum farkli: orada korpusun yeniden
# uretilmesi gerekir, ~7 GPU-saat/anahtar — bu betik ONA GIRMEZ.)
#
# CIKTI: results_insan/anahtar_supurme_rapor.json + skor_anahtar.jsonl
#
#   python pilot/dev_anahtar_supurme.py --n-anahtar 8
#
# HUKUM KOSULLU: sonuc manseti destekleyebilir de zayiflatabilir de; betik
# yalnizca olcer ve "hepsi >1 mi", "kosunun anahtari nerede duruyor" gibi
# turetilmis bayraklar uretir. Elle yazilmis sayi YOKTUR.
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pilot import config as C  # noqa: E402
from pilot.jsonl import append_jsonl, read_jsonl  # noqa: E402

VERI = C.REPO_ROOT / "results_insan"
KORPUSLAR = [("tr", ""), ("en", ""), ("tr", "_wikisource")]
Z_ESIK = 4.0


def _anahtarlar(n: int, kosu_anahtari: int) -> list[int]:
    """Kosunun anahtari HER ZAMAN ilk sirada; kalanlar sabit tohumlu uretilir.
    Boylece 'kosunun anahtari havuzda nerede' sorusu yeniden uretilebilir."""
    rng = np.random.default_rng(C.SEEDS[0])
    ek = []
    while len(ek) < n - 1:
        a = int(rng.integers(1, 2**31 - 1))
        if a != kosu_anahtari and a not in ek:
            ek.append(a)
    return [kosu_anahtari] + ek


def _kgw(hash_key: int, tok):
    """Anahtari YAPICIYA gecirerek tam bir KGW kur.

    TUZAK (yakalandi, sayi uretmeden once): KGWUtils.__init__ yalnizca
    hash_key'i saklamiyor; onunla tohumlayip `self.prf = randperm(vocab)`
    tablosunu da uretiyor (kgw.py:61-62), ve yesil-liste tohumu
    (hash_key * prf[onceki_token]) % vocab olarak HER IKISINI de kullaniyor.
    Anahtari nesne kurulduktan SONRA degistirmek prf'yi ESKI anahtarda birakir;
    skorlar yine degisir, dolayisiyla hata sessizdir. Bu yuzden her anahtar
    icin gecici bir config yazip nesneyi bastan kuruyoruz."""
    import tempfile
    from utils.transformers_config import TransformersConfig
    from watermark.auto_watermark import AutoWatermark

    taban = json.loads(Path(C.SCHEME_CONFIGS["KGW"]).read_text())
    taban["hash_key"] = hash_key
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        json.dump(taban, f)
        yol = f.name
    tcfg = TransformersConfig(model=None, tokenizer=tok, device="cpu")
    tcfg.temperature = C.TEMPERATURE
    tcfg.top_k = -1
    w = AutoWatermark.load("KGW", algorithm_config=yol, transformers_config=tcfg)
    Path(yol).unlink(missing_ok=True)
    assert w.config.hash_key == hash_key, "anahtar yapiciya gecmedi"
    return w


def _hizli_skorlar(w, diziler: list) -> list[float]:
    """score_sequence ile BIREBIR ayni z'leri, tohuma gore gruplayarak uretir.

    prefix_length=1 ve f_scheme='time' oldugunda yesil liste yalnizca bir
    onceki tokene baglidir: tohum = (hash_key * prf[prev]) % vocab_size.
    Referans uygulama her KONUM icin randperm(151.936) cagiriyor (4M cagri);
    burada her BENZERSIZ TOHUM icin bir kez cagirip uyeligi toplu test
    ediyoruz. Ayni tohum + ayni generator => ayni permutasyon, yani cikti
    birebir ozdes. Esdegerlik --dogrula ile ampirik olarak sinaniyor."""
    import torch

    V = w.config.vocab_size
    g = int(V * w.config.gamma)
    prf = w.utils.prf
    hk = w.config.hash_key

    # tum dizilerden (tohum, curr, dizi_no) uclulerini topla
    tohumlar, currlar, dizi_no = [], [], []
    for d, ids in enumerate(diziler):
        prev = ids[:-1]
        curr = ids[1:]
        s = (hk * prf[prev.long()]) % V
        tohumlar.append(s)
        currlar.append(curr.long())
        dizi_no.append(torch.full((len(curr),), d, dtype=torch.long))
    S = torch.cat(tohumlar); Cc = torch.cat(currlar); D = torch.cat(dizi_no)

    # Tohuma gore SIRALA ve bitisik gruplarda gez. Naif "(S == s).nonzero()"
    # her benzersiz tohum icin tum diziyi tarardi (O(benzersiz x N)); 4M konum
    # ve ~150k tohumda bu tek basina saatler surer.
    sira = torch.argsort(S)
    S_s, C_s = S[sira], Cc[sira]
    sinir = torch.cat([torch.tensor([0]),
                       (S_s[1:] != S_s[:-1]).nonzero(as_tuple=True)[0] + 1,
                       torch.tensor([len(S_s)])])
    yesil_s = torch.zeros(len(S_s), dtype=torch.bool)
    rng = torch.Generator(device="cpu")
    maske = torch.zeros(V, dtype=torch.bool)
    for i in range(len(sinir) - 1):
        a, b = int(sinir[i]), int(sinir[i + 1])
        rng.manual_seed(int(S_s[a]))
        perm = torch.randperm(V, generator=rng)
        maske.zero_()
        maske[perm[:g]] = True
        yesil_s[a:b] = maske[C_s[a:b]]
    yesil = torch.empty(len(S), dtype=torch.bool)
    yesil[sira] = yesil_s

    out = []
    for d in range(len(diziler)):
        y = yesil[D == d]
        T = int(y.numel())
        say = int(y.sum())
        out.append((say - w.config.gamma * T) /
                   (T * w.config.gamma * (1 - w.config.gamma)) ** 0.5)
    return out


def olc(n_anahtar: int, n_sinir: int | None) -> dict:
    from transformers import AutoTokenizer
    env = json.loads((C.RESULTS / "env.json").read_text())
    model_adi = env["model"]
    tok = AutoTokenizer.from_pretrained(model_adi)

    kosu = json.loads(Path(C.SCHEME_CONFIGS["KGW"]).read_text())["hash_key"]
    anahtarlar = _anahtarlar(n_anahtar, kosu)
    print(f"kosu anahtari: {kosu}   supurme: {anahtarlar}")

    cikti = VERI / "skor_anahtar.jsonl"
    hazir = {(r["pageid"], r["korpus"], r["hash_key"]) for r in read_jsonl(cikti)}

    # Tokenleri BIR KEZ hesapla; anahtar degisince yeniden tokenlemeye gerek yok.
    korpus_ids: dict[str, list[tuple[int, object]]] = {}
    for dil, ek in KORPUSLAR:
        kaynak = VERI / f"insan_{dil}{ek}.jsonl"
        if not kaynak.exists():
            print(f"  {dil}{ek}: veri yok, ATLANDI"); continue
        rows = read_jsonl(kaynak)
        if n_sinir:
            rows = rows[:n_sinir]
        korpus_ids[f"{dil}{ek}"] = [
            (r["pageid"], tok(r["text"], return_tensors="pt",
                              add_special_tokens=False)["input_ids"][0])
            for r in rows]
        print(f"  {dil}{ek}: {len(korpus_ids[f'{dil}{ek}'])} pencere tokenlendi")

    for a in anahtarlar:
        w = _kgw(a, tok)
        # Esdegerlik her ANAHTAR icin yeniden kanitlanir: hizli yol yalnizca
        # referansla birebir ayni ciktiyi verdiginde kullanilir.
        ornek = next(iter(korpus_ids.values()))[:3]
        ref = [w.utils.score_sequence(i)[0] for _, i in ornek]
        hiz = _hizli_skorlar(w, [i for _, i in ornek])
        sapma = max(abs(r - h) for r, h in zip(ref, hiz))
        if sapma > 0.0:
            raise SystemExit(f"HATA: anahtar {a} icin hizli yol referanstan "
                             f"sapiyor (max |D| = {sapma:.3e}); kosum durduruldu")
        for korpus, kayitlar in korpus_ids.items():
            eksik = [(pid, ids) for pid, ids in kayitlar
                     if (pid, korpus, a) not in hazir]
            if not eksik:
                continue
            t0 = time.time()
            skorlar = _hizli_skorlar(w, [ids for _, ids in eksik])
            for (pid, _), z in zip(eksik, skorlar):
                append_jsonl(cikti, {"pageid": pid, "korpus": korpus,
                                     "hash_key": a, "score": float(z)})
            print(f"  anahtar {a} {korpus}: {len(eksik)} pencere, "
                  f"{time.time()-t0:.1f} sn (esdegerlik kanitlandi)", flush=True)

    return _rapor(cikti, anahtarlar, kosu)


def _rapor(cikti: Path, anahtarlar: list[int], kosu: int) -> dict:
    ham: dict[str, dict[int, list[float]]] = {}
    for r in read_jsonl(cikti):
        ham.setdefault(r["korpus"], {}).setdefault(r["hash_key"], []).append(r["score"])

    rap: dict = {"kosu_anahtari": kosu, "anahtarlar": anahtarlar, "korpus": {}}
    for korpus, per_a in ham.items():
        satirlar = []
        for a in anahtarlar:
            v = per_a.get(a)
            if not v:
                continue
            x = np.asarray(v, dtype=float)
            k = int((x > Z_ESIK).sum())
            ci = binomtest(k, x.size).proportion_ci(0.95, method="exact")
            satirlar.append({"hash_key": a, "n": int(x.size),
                             "mean": float(x.mean()),
                             "std": float(x.std(ddof=1)),
                             "z_max": float(x.max()), "n_z4": k,
                             "fpr": k / x.size,
                             "fpr_ci": [float(ci.low), float(ci.high)],
                             "kosu_anahtari_mi": a == kosu})
        if not satirlar:
            continue
        stds = [s["std"] for s in satirlar]
        z4 = [s["n_z4"] for s in satirlar]
        kosu_satir = next((s for s in satirlar if s["kosu_anahtari_mi"]), None)
        rap["korpus"][korpus] = {
            "satirlar": satirlar,
            "std_min": min(stds), "std_max": max(stds),
            "std_medyan": float(np.median(stds)),
            "z4_min": min(z4), "z4_max": max(z4), "z4_medyan": float(np.median(z4)),
            # turetilmis hukumler — elle yazilmaz
            "hepsi_std_1_ustu": bool(all(s > 1.0 for s in stds)),
            "kosu_std_siralamasi": (sorted(stds).index(kosu_satir["std"]) + 1
                                    if kosu_satir else None),
            "kosu_z4_siralamasi": (sorted(z4).index(kosu_satir["n_z4"]) + 1
                                   if kosu_satir else None),
            "n_anahtar": len(satirlar),
        }
    return rap


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-anahtar", type=int, default=8)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()

    rap = olc(a.n_anahtar, a.n)
    yol = VERI / "anahtar_supurme_rapor.json"
    yol.write_text(json.dumps(rap, ensure_ascii=False, indent=2), encoding="utf-8")

    for korpus, d in rap["korpus"].items():
        print(f"\n=== {korpus}  ({d['n_anahtar']} anahtar) ===")
        for s in d["satirlar"]:
            im = " <- KOSUNUN ANAHTARI" if s["kosu_anahtari_mi"] else ""
            print(f"  {s['hash_key']:>11}  std {s['std']:.4f}  ort {s['mean']:+.4f}  "
                  f"z>4 {s['n_z4']:>4}/{s['n']}  z_max {s['z_max']:.2f}{im}")
        print(f"  std araligi [{d['std_min']:.4f}, {d['std_max']:.4f}] "
              f"medyan {d['std_medyan']:.4f}   hepsi >1: {d['hepsi_std_1_ustu']}")
        print(f"  z>4 araligi [{d['z4_min']}, {d['z4_max']}] "
              f"medyan {d['z4_medyan']:.1f}")
        print(f"  kosunun anahtari std siralamasinda {d['kosu_std_siralamasi']}., "
              f"kuyruk siralamasinda {d['kosu_z4_siralamasi']}. "
              f"(1 = en dusuk/en muhafazakar)")
    print(f"\nyazildi -> {yol}")


if __name__ == "__main__":
    main()
