# pilot/attacks.py — model gerektirmeyen (hafif) metin saldırıları.
# Bu modüldeki morfolojik dönüşüm mantığı sandbox'ta 12 tuzak-kelimelik R1 setinden ve R2+diakritik
# testinden geçti (okuyor->okumaktadır, bekliyor->beklemektedir,
# gidiyor->gitmektedir dahil). Davranışı değiştirmeden önce
# `python -m pilot.attacks` ile birim testini koş.
from __future__ import annotations

import logging
import random
import re

logging.disable(logging.CRITICAL)  # zeyrek'in gürültülü stderr logunu kapat
import zeyrek  # noqa: E402

# ----------------------------------------------------------------------
# Zeyrek YAMASI (K11 — tekrarlanabilirlik). ÜST AKIM HATASI.
#
# BELİRTİ: aynı korpus üzerinde art arda iki geçiş 146 ve 138 düzenleme verdi;
# -AcAktIr biçimleri (olacaktır, etkileyecektir, tanıyacaktır…) ikinci geçişte
# sessizce elden kaçıyordu. Taze analizör "etkileyecektir" -> etkilemek(Cop)
# verirken, başka kelimeler analiz edildikten sonra AYNI kelime tek bir Unk
# çözümlemesine düşüyordu. Yani bir kelimenin çözümlemesi ondan önce NELERİN
# analiz edildiğine bağlıydı -> morph_v0, morph_v1 ve metrics._lemma_set
# (K10 lemma-Jaccard kanıtı) metin sırasına duyarlı hale geliyordu.
#
# BULUNAN (AMA YETERSİZ) BİR SEBEP: zeyrek/attributes.py içindeki
#     @functools.lru_cache(maxsize=128)
#     def calculate_phonetic_attributes(...) -> set[PhoneticAttribute]
# önbelleğe alınmış MUTABLE bir set döndürüyor; her çağrı AYNI nesneyi veriyor.
# Canlı doğrulandı: f("kitap") iki çağrıda aynı nesne (is True); nesneye eleman
# eklenince üçüncü çağrı kirli kümeyi döndürüyor. Aşağıdaki yama bunu kapatıyor
# (her çağrıda kopya). DÜRÜSTLÜK NOTU: bu yama TEK BAŞINA bozulmayı GİDERMİYOR
# -- yama açıkken 2525 analiz sonrası "etkileyecektir" hâlâ Unk dönüyor. Yani
# asıl durum başka bir yerde ve kök sebep BULUNAMADI. Yama yine de duruyor,
# çünkü paylaşılan mutable önbellek her hâlükârda bir hata kaynağı.
#
# FİİLİ SAVUNMA: (1) tek uzun ömürlü analizör, (2) her benzersiz kelime yalnız
# BİR kez analiz edilir (_PARSE_CACHE) -> toplam analiz sayısı korpustaki
# benzersiz kelime sayısına iner, (3) sonuçlar "kelime başına taze analizör"
# referansına karşı doğrulanır (bkz. dev_zeyrek_check). Analizörü periyodik
# YENİDEN İNŞA ETMEK denendi ve terk edildi: ölçümde fayda sağlamadı,
# kurulum başına ~4,4 s maliyeti var.
# ----------------------------------------------------------------------
import zeyrek.attributes as _zattr            # noqa: E402
import zeyrek.morphotactics as _zmorph        # noqa: E402
import zeyrek.rulebasedanalyzer as _zrule     # noqa: E402

_orig_cpa = _zattr.calculate_phonetic_attributes


def _cpa_safe(word, predecessor_attrs=None):
    return set(_orig_cpa(word, predecessor_attrs))


for _mod in (_zattr, _zmorph, _zrule):
    _mod.calculate_phonetic_attributes = _cpa_safe

_ZA = zeyrek.MorphAnalyzer()          # yama KURULDUKTAN sonra inşa edilmeli
_PARSE_CACHE: dict[str, list] = {}    # her benzersiz kelime yalnız bir kez analiz edilir
_ZA_ANALYSES = 0                      # bellek ISKALAMASI sayısı (gerçek analizler)

# Bozulma "etkileyecektir" için 750 analizde henüz yok, 1000'de var (ölçüldü).
# Saldırı yolu bellekle ~300 analizde kalır ve bu sınıra hiç değmez -> kararları
# "kelime başına taze analizör" referansıyla BİREBİR aynı (dev_zeyrek_check A).
#
# _parses içinde SAYAÇ TEMELLİ yenileme DENENDİ ve KALDIRILDI: bir kelimenin
# hangi analizöre denk geldiğini "ondan önce kaç kelime geldi"ye bağladığı için
# sıra bağımlılığını geri getiriyordu (dev_zeyrek_check B düştü). Bunun yerine
# çok sayıda kelime analiz edecek olan çağıran (metrics._lemma_set) prewarm()
# kullanır: kelimeler SIRALI ve sabit boyutlu gruplar hâlinde çözümlenir, yani
# grup sınırları metin sırasından bağımsız ve koşular arasında aynıdır.
_PREWARM_BATCH = 500

# ----------------------------------------------------------------------
# Saldırı 1: Diakritik soyma (asciify)
# ----------------------------------------------------------------------
_DIA_SRC = "çğıöşüÇĞİÖŞÜ"
_DIA = str.maketrans(_DIA_SRC, "cgiosuCGIOSU")


def strip_diacritics(text: str, p: float = 1.0, seed: int = 42) -> str:
    """Türkçe diakritikleri ASCII karşılıklarına indirger.

    p < 1.0 ise her diakritikli karakter bağımsız olarak p olasılıkla
    dönüştürülür (kısmî soyma; gündelik yazışma gerçekçiliği).
    """
    if p >= 1.0:
        return text.translate(_DIA)
    rnd = random.Random(seed)
    return "".join(
        c.translate(_DIA) if c in _DIA_SRC and rnd.random() < p else c
        for c in text
    )


# ----------------------------------------------------------------------
# Saldırı 2: Zeyrek-doğrulamalı morfolojik dönüşüm
#   R1: -Iyor (3.tekil şimdiki zaman) -> -mAktAdIr
#   R2: "-DIğI için" -> "-DIğIndAn"
# İlke: kural ADAY üretir, morfolojik analizör (zeyrek) DOĞRULAR.
# R1 sözlük-güdümlüdür: gövde, yüzey biçiminden değil zeyrek'in verdiği
# lemmadan kurulur; ünlü düşmesi (bekle-) ve ünsüz yumuşaması (git-)
# vakalarını bu yüzden doğru çözer. Sonuç zeyrek'e geri-parse edilip
# "aynı lemma + Prog2 (-mAktA)" şartı aranır; sağlanmazsa edit yapılmaz.
# ----------------------------------------------------------------------
_FRONT = set("eiöü")
_VOWELS = "aıoueiöü"


def _harmony_makta(stem: str) -> str:
    for ch in reversed(stem.lower()):
        if ch in _VOWELS:
            return "mektedir" if ch in _FRONT else "maktadır"
    return "maktadır"


def _parses(word: str):
    """Morfolojik çözümleme. Yukarıdaki yama sayesinde sonuç, daha önce hangi
    kelimelerin analiz edildiğinden BAĞIMSIZ; bellek yalnız hız içindir."""
    global _ZA_ANALYSES
    cached = _PARSE_CACHE.get(word)
    if cached is not None:
        return cached
    res = _ZA.analyze(word)
    _ZA_ANALYSES += 1
    ps = res[0] if res else []
    _PARSE_CACHE[word] = ps
    return ps


def prewarm(words) -> int:
    """Çok sayıda kelime çözümleyecek çağıranlar için kanonik ısıtma.

    Kelimeler SIRALANIP sabit boyutlu gruplara bölünür ve her grup TAZE bir
    analizörde çözümlenir. Böylece hem grup sınırları hem her kelimenin hangi
    analizörde çözümlendiği, çağıranın metinleri hangi sırayla verdiğinden
    bağımsızdır -> sonuç koşular arasında birebir tekrarlanır (K11). Zaten
    bellekte olan kelimeler atlanır. Döner: yeni çözümlenen kelime sayısı.
    """
    global _ZA, _ZA_ANALYSES
    todo = sorted({w for w in words if w and w not in _PARSE_CACHE})
    for i in range(0, len(todo), _PREWARM_BATCH):
        _ZA = zeyrek.MorphAnalyzer()
        _ZA_ANALYSES = 0
        for w in todo[i:i + _PREWARM_BATCH]:
            _parses(w)
    return len(todo)


def _core(tok: str) -> str:
    return re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", tok).lower()


def prewarm_corpus(texts) -> int:
    """morph_* saldırılarının SÖZLEŞMESİ: saldırıları uygulamadan önce çağır.

    İki geçişlidir, çünkü kurallar yüzey kelimelerinin yanında TÜRETİLMİŞ aday
    biçimleri de çözümletir (R1 geri-doğrulaması, R3 gövdesi). Geçiş 1 yüzey
    kelimelerini, geçiş 2 onlardan türeyen adayları ısıtır; ikisi de sıralı
    olduğu için tüm çözümlemeler metin sırasından bağımsız hale gelir.
    """
    texts = list(texts)
    surface = {_core(tok) for t in texts for tok in t.split(" ")}
    surface.discard("")
    n = prewarm(surface)

    derived = set()
    for w in surface:
        if w.endswith("yor"):
            for p in _parses(w):
                if p.pos == "Verb" and "Prog1" in p.morphemes and \
                        p.lemma.endswith(("mek", "mak")):
                    stem = p.lemma[:-3]
                    derived.add(stem + _harmony_makta(stem))
        elif w.endswith(_COP_SUFFIXES):
            for suf in _COP_SUFFIXES:
                if w.endswith(suf) and len(w) - len(suf) >= 3:
                    derived.add(w[: -len(suf)])
                    break
    return n + prewarm(derived)


def _tr_capitalize(word: str) -> str:
    if not word:
        return word
    first = {"i": "İ", "ı": "I"}.get(word[0], word[0].upper())
    return first + word[1:]


def r1_iyor_to_makta(word_lower: str) -> str | None:
    """Doğrulanmış -Iyor -> -mAktAdIr adayı; yoksa None."""
    src_lemmas = {
        p.lemma
        for p in _parses(word_lower)
        if p.pos == "Verb" and "Prog1" in p.morphemes
    }
    # En uzun lemma önce: ettirgen/edilgen gibi türetim eklerini koruyan en
    # spesifik çözümleme tercih edilir (ör. sürdürüyor -> sürdürmek, sürmek
    # değil). Sıralama ayrıca sonucu PYTHONHASHSEED'den bağımsızlaştırır.
    for lem in sorted(src_lemmas, key=lambda x: (-len(x), x)):
        if lem.endswith(("mek", "mak")):
            stem = lem[:-3]
            cand = stem + _harmony_makta(stem)
            back = {
                p.lemma
                for p in _parses(cand)
                if p.pos == "Verb" and "Prog2" in p.morphemes
            }
            if lem in back:
                return cand
    return None


# ----------------------------------------------------------------------
# R3 (yalnız morph_v1): kopula -DIr düşürme  "önemlidir" -> "önemli"
# Gerekçe: v0'ın R1 hedefi (-Iyor) LLM'in resmî Türkçesinde 4,8/1000 kelime
# sıklığında; ölçülen kapsam %0,46 -> saldırı istatistiği oynatamıyor. Kopula
# -DIr 13,3/1000 ile en sık GÜVENİLİR sınıf ve lemmayı korur, yani "morfolojik
# != leksik" savını bozmaz. v0 DEĞİŞMEDEN kalır; bu kural yalnız v1'de.
# ----------------------------------------------------------------------
_COP_SUFFIXES = ("dır", "dir", "dur", "dür", "tır", "tir", "tur", "tür")


def r3_drop_copula(word_lower: str) -> str | None:
    """Doğrulanmış kopula düşürmesi; yoksa None.

    Kural ADAY üretir (son eki kes), zeyrek DOĞRULAR: kaynak çözümlemede 'Cop'
    morfemi bulunmalı VE aday, kaynakla aynı lemmayı vermelidir. Bu iki şart
    "bildir/kaldır/aldır" gibi emir kiplerini (Cop yok) eler. Lemma sıralaması
    v0'daki gerekçeyle en-uzun-önce: sonucu PYTHONHASHSEED'den bağımsız kılar.
    """
    for suf in _COP_SUFFIXES:
        if not word_lower.endswith(suf):
            continue
        stem = word_lower[: -len(suf)]
        if len(stem) < 3:
            return None
        ps = _parses(word_lower)
        # Emir kipi vetosu: zeyrek "kaldır" (kal-dır ettirgen emir) için emir
        # çözümlemelerinin YANINDA sahte bir kopula çözümlemesi de üretiyor;
        # tek başına 'Cop' şartı bu sınıfı eliyemiyor (birim testi yakaladı).
        # -DIr ile biten ettirgen emirler karışan sınıfın tamamı, o yüzden
        # herhangi bir çözümlemede 'Imp' varsa dokunmuyoruz (sınırda vakayı
        # zorlamak yerine atlıyoruz).
        if any("Imp" in p.morphemes for p in ps):
            return None
        src = {p.lemma for p in ps if "Cop" in p.morphemes}
        if not src:
            return None
        back = {p.lemma for p in _parses(stem)}
        for lem in sorted(src, key=lambda x: (-len(x), x)):
            if lem in back:
                return stem
        return None
    return None


_R2_PATTERN = re.compile(
    r"\b([a-zçğıöşü]+(?:dığı|diği|duğu|düğü|tığı|tiği|tuğu|tüğü))\s+için\b"
)


def _r2_digi_icin(text: str) -> tuple[str, int]:
    def rep(m: re.Match) -> str:
        w = m.group(1)
        last = next((c for c in reversed(w) if c in _VOWELS), "a")
        return w + ("nden" if last in _FRONT else "ndan")

    return _R2_PATTERN.subn(rep, text)


def morph_attack(text: str) -> tuple[str, dict]:
    """Döner: (yeni_metin, {"edits": int, "rejected": int}).

    edits  = uygulanan R1 + R2 dönüşüm sayısı
    rejected = R1 adayı üretilip zeyrek doğrulamasını GEÇEMEYEN kelime sayısı
               (summary.md'de kapsam raporu için loglanır)
    """
    out: list[str] = []
    r1_edits = rejected = 0
    for tok in text.split(" "):
        core = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", tok)
        if core and core.lower().endswith("yor"):
            cand = r1_iyor_to_makta(core.lower())
            if cand:
                if core[0].isupper():
                    cand = _tr_capitalize(cand)
                out.append(tok.replace(core, cand, 1))
                r1_edits += 1
                continue
            rejected += 1
        out.append(tok)
    joined = " ".join(out)
    joined, r2_edits = _r2_digi_icin(joined)
    return joined, {"edits": r1_edits + r2_edits, "rejected": rejected}


def morph_attack_v1(text: str) -> tuple[str, dict]:
    """v0'ın R1+R2'si + R3 (kopula düşürme). v0 dokunulmadan durur; ikisi
    ayrı koşul olarak raporlanır, böylece kapsam-etki ilişkisi kendisi bir
    bulgu olur. Bir token'a yalnız BİR kural uygulanır (R1 önce): R1'in ürettiği
    -mAktAdIr'ın R3 tarafından yeniden kesilmesini engeller.
    """
    out: list[str] = []
    edits = rejected = 0
    for tok in text.split(" "):
        core = re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", tok)
        if not core:
            out.append(tok)
            continue
        low = core.lower()
        cand = None
        if low.endswith("yor"):
            cand = r1_iyor_to_makta(low)
            if cand is None:
                rejected += 1
        elif low.endswith(_COP_SUFFIXES):
            cand = r3_drop_copula(low)
            if cand is None:
                rejected += 1
        if cand:
            if core[0].isupper():
                cand = _tr_capitalize(cand)
            out.append(tok.replace(core, cand, 1))
            edits += 1
            continue
        out.append(tok)
    joined = " ".join(out)
    joined, r2_edits = _r2_digi_icin(joined)
    return joined, {"edits": edits + r2_edits, "rejected": rejected}


# ----------------------------------------------------------------------
# Dağıtıcı (hafif saldırılar)
# ----------------------------------------------------------------------
def apply_light_attack(name: str, text: str, seed: int = 42) -> tuple[str, dict]:
    if name == "dia100":
        return strip_diacritics(text, p=1.0), {"edits": -1, "rejected": 0}
    if name == "dia50":
        return strip_diacritics(text, p=0.5, seed=seed), {"edits": -1, "rejected": 0}
    if name == "morph":
        return morph_attack(text)
    if name == "morph+dia":
        t, meta = morph_attack(text)
        return strip_diacritics(t, p=1.0), meta
    if name == "morph_v1":
        return morph_attack_v1(text)
    if name == "morph_v1+dia":
        t, meta = morph_attack_v1(text)
        return strip_diacritics(t, p=1.0), meta
    raise ValueError(f"bilinmeyen hafif saldırı: {name}")


# ----------------------------------------------------------------------
# Birim test:  python -m pilot.attacks
# ----------------------------------------------------------------------
if __name__ == "__main__":
    cases = {
        "artıyor": "artmaktadır",
        "geliyor": "gelmektedir",
        "okuyor": "okumaktadır",        # tuzak: oku+yor / ok+uyor belirsizliği
        "gidiyor": "gitmektedir",       # ünsüz yumuşaması geri alınmalı
        "bekliyor": "beklemektedir",    # ünlü düşmesi geri alınmalı
        "izliyor": "izlemektedir",
        "sunuyor": "sunmaktadır",
        "söylüyor": "söylemektedir",
        "sürdürüyor": "sürdürmektedir",
        "yapıyor": "yapmaktadır",
        "ediyor": "etmektedir",
        "koşuyor": "koşmaktadır",
    }
    bad = 0
    for w, want in cases.items():
        got = r1_iyor_to_makta(w)
        ok = got == want
        bad += not ok
        print(f"{'OK ' if ok else 'FAIL'} {w:12s} -> {got}")

    t, meta = morph_attack("Talep arttığı için fiyatlar Yükseliyor.")
    print(t, meta)
    assert "arttığından" in t and "Yükselmektedir" in t and meta["edits"] == 2, t
    d = strip_diacritics("çğışöü ÇĞİŞÖÜ")
    assert d == "cgisou CGISOU", d

    # --- R3 (yalnız morph_v1): kopula düşürme ---
    r3_yes = {"önemlidir": "önemli", "gereklidir": "gerekli",
              "gelecektir": "gelecek", "olmuştur": "olmuş",
              "değildir": "değil", "artmaktadır": "artmakta"}
    r3_no = ["bildir", "kaldır", "aldır", "getir", "müdür"]  # Cop yok -> dokunma
    for w, want in r3_yes.items():
        got = r3_drop_copula(w)
        ok = got == want
        bad += not ok
        print(f"{'OK ' if ok else 'FAIL'} R3 {w:14s} -> {got}")
    for w in r3_no:
        got = r3_drop_copula(w)
        ok = got is None
        bad += not ok
        print(f"{'OK ' if ok else 'FAIL'} R3 {w:14s} -> {got} (None beklenir)")

    # v0 DEĞİŞMEMELİ: v1 kuralları v0'a sızmamalı
    t0, m0 = morph_attack("Bu konu önemlidir ve talep artıyor.")
    assert "önemlidir" in t0 and m0["edits"] == 1, (t0, m0)
    t1, m1 = morph_attack_v1("Bu konu önemlidir ve talep artıyor.")
    assert "önemli " in t1 and "artmaktadır" in t1 and m1["edits"] == 2, (t1, m1)
    # R1 çıktısı R3 tarafından yeniden kesilmemeli
    assert "artmakta " not in t1 and "artmaktadır" in t1, t1
    print(f"v0: {t0}  {m0}")
    print(f"v1: {t1}  {m1}")

    print("BÜYÜK HARF + SAYAÇ + DİAKRİTİK + R3 + v0/v1 yalıtım testleri geçti."
          if bad == 0 else f"{bad} vaka FAIL")
    raise SystemExit(bad)
