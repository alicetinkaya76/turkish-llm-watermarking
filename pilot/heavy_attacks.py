# pilot/heavy_attacks.py — model gerektiren saldırılar:
#   rtt     : TR -> EN -> TR gidiş-dönüş çeviri (NLLB-200-distilled-600M, yerel)
#   para    : hafif paraphrase   (ana modelin FİLİGRANSIZ üretimi ile)
#   launder : tam yeniden yazım  (aynı mekanizma; sıfır-beceri aklama modeli)
from __future__ import annotations

import gc
import re

import torch

from pilot import config as C
from pilot.generate import render_prompt, seed_everything, slice_completion


def _sent_split_tr(text: str) -> list[str]:
    try:
        import nltk

        return [s for s in nltk.sent_tokenize(text, language="turkish") if s.strip()]
    except Exception:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _free(device: str) -> None:
    """Cihaz onbellegini bosalt. CUDA dali YOKTU: ana model 29,5 GB tutarken
    NLLB de yuklenince VRAM baskisi olusuyor ve torch.cuda.empty_cache() kodun
    HICBIR yerinde cagrilmiyordu."""
    gc.collect()
    if device == "mps" and hasattr(torch, "mps"):
        try:
            torch.mps.empty_cache()
        except Exception:
            pass
    elif device == "cuda" and torch.cuda.is_available():
        torch.cuda.empty_cache()


class RoundTripTranslator:
    """NLLB ile cümle-cümle TR<->EN. 600M model MPS'te sorun çıkarırsa
    otomatik CPU'ya düşer (çeviri hacmi küçük, kabul edilebilir)."""

    def __init__(self, device: str):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(C.NLLB_MODEL)
        try:
            self.model = (
                AutoModelForSeq2SeqLM.from_pretrained(
                    C.NLLB_MODEL, torch_dtype=torch.float32
                )
                .to(device)
                .eval()
            )
            self.device = device
        except Exception as e:
            # SESSIZ DUSUS: onceki surum hicbir sey basmiyordu. RTT asamasi aniden
            # yavaslarsa sebebi logdan anlasilamiyordu; artik acikca yaziliyor.
            print(f"  UYARI: NLLB {device} uzerine yuklenemedi ({type(e).__name__}), "
                  f"CPU'ya dusuldu -> rtt saldirisi belirgin YAVAS olacak", flush=True)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(C.NLLB_MODEL).eval()
            self.device = "cpu"

    def _translate(self, sents: list[str], src: str, tgt: str) -> list[str]:
        self.tok.src_lang = src
        bos = self.tok.convert_tokens_to_ids(tgt)
        out: list[str] = []
        B = 8
        for i in range(0, len(sents), B):
            batch = sents[i : i + B]
            enc = self.tok(
                batch, return_tensors="pt", padding=True, truncation=True, max_length=384
            ).to(self.device)
            with torch.no_grad():
                gen = self.model.generate(
                    **enc, forced_bos_token_id=bos, max_new_tokens=256, num_beams=1
                )
            out += self.tok.batch_decode(gen, skip_special_tokens=True)
        return out

    def round_trip(self, text: str) -> str:
        sents = _sent_split_tr(text)
        if not sents:
            return text
        en = self._translate(sents, "tur_Latn", "eng_Latn")
        tr = self._translate(en, "eng_Latn", "tur_Latn")
        return " ".join(tr)

    def close(self):
        del self.model
        _free(self.device)


_REWRITE_PROMPTS = {
    "para": (
        "Aşağıdaki Türkçe metni, anlamını tamamen koruyarak hafifçe yeniden ifade "
        "et. Cümle sırasını ve içeriği koru; yalnızca ifade biçimini değiştir. "
        "Açıklama ekleme, sadece yeniden yazılmış metni ver:\n\n{t}"
    ),
    "launder": (
        "Aşağıdaki Türkçe metindeki bilgiyi eksiksiz koruyarak metni baştan, "
        "tamamen kendi cümlelerinle yeniden yaz. Açıklama ekleme, sadece yeni "
        "metni ver:\n\n{t}"
    ),
}


def rewrite(model, tok, device: str, text: str, mode: str,
            seed: int | None = None) -> tuple[str, int]:
    """Ana model, filigran işlemcisi OLMADAN paraphrase/aklama yapar.
    (Panel-3 tehdit modeli: filigransız bir sağlayıcıdan geçirme — burada
    API'siz 'laundering-lite'; gerçek GPT-laundering Faz 3.)

    Döner: (yeniden_yazilmis_metin, kullanilan_tavan).

    ⛔ TAVAN SABİT 480'Dİ VE BİLİMSEL BİR HATAYDI (denetimde bulundu).
    Pilotta taban metinler ~320 token'dı, bu yüzden min(480, ...) nadiren bağlıyordu.
    Yeni rejimde taban ~950 token; n_in >= 309 olduğu anda min() DAİMA 480 döner,
    yani saldırılmış metin kaynağın yaklaşık YARISI uzunlukta olur. KGW z-skoru
    yaklaşık sqrt(T) ile ölçeklendiği için bu tek başına z'yi ~0,71 katına indirir
    ve "paraphrase filigranı siliyor" bulgusunun büyük kısmı UZUNLUK ARTEFAKTI olur.
    Tavan artık üretim bütçesinden türetiliyor; ikinci bir sabit YOK.

    TOHUM: do_sample=True idi ama seed_everything HİÇ çağrılmıyordu -> saldırı
    çıktısı tekrarlanamazdı (K11 ihlali). Artık tohum açıkça veriliyor.
    """
    prompt = _REWRITE_PROMPTS[mode].format(t=text)
    rendered = render_prompt(tok, prompt)
    enc = tok(rendered, return_tensors="pt", add_special_tokens=True).to(device)
    n_in = len(tok(text, add_special_tokens=False).input_ids)
    tavan = min(int(C.GEN_KWARGS["max_new_tokens"]), int(n_in * 1.6) + 64)
    if seed is not None:
        seed_everything(seed, device)
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens=tavan,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            top_k=C.GEN_KWARGS.get("top_k", 20),
            repetition_penalty=C.GEN_KWARGS.get("repetition_penalty", 1.0),
            pad_token_id=tok.pad_token_id,
        )
    full = tok.batch_decode(out, skip_special_tokens=True)[0]
    comp, _ = slice_completion(tok, rendered, full)
    return comp.strip().strip('"').strip(), tavan
