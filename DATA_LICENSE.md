# Licensing of the data in this repository

This repository is a derivative of [MarkLLM](https://github.com/THU-BPM/MarkLLM)
(Apache-2.0). The upstream code and the code added here are under Apache-2.0; see
`LICENSE`. The **data** is not uniformly licensed, because different parts derive
from sources with different terms. Each component is listed below with its origin
and the terms we redistribute it under. Where we could not fully resolve a term,
we say so rather than choosing the convenient reading.

## Summary table

| Path | Content | Origin | Redistributed under |
|---|---|---|---|
| `results_insan/insan_tr.jsonl`, `insan_en.jsonl` | 3,000 human text windows | Wikipedia dumps `20231101.tr` / `20231101.en` | **CC BY-SA 3.0 (or later) and GFDL** — see `ATTRIBUTION.md` |
| `results_insan/insan_tr_wikisource.jsonl` | 1,000 human text windows | Turkish Wikisource dump `20231201` | **CC BY-SA 3.0 (or later) and GFDL** — see `ATTRIBUTION.md` |
| `results/gen_neg.jsonl`, `gen_pos_*.jsonl` | 384 generated texts | Qwen3-14B (Apache-2.0 model) | **CC BY 4.0** |
| `results/att_*_{dia50,dia100,morph,morph_v1,morph+dia,morph_v1+dia,para,launder}.jsonl` | Attacked texts produced locally | Transformations of the Qwen3-14B texts above | **CC BY 4.0** |
| `results/att_*_rtt.jsonl` | Round-trip machine translations | NLLB-200-distilled-600M | **CC BY-NC 4.0** — see the caveat below |
| `results/att_*_launder_api.jsonl` | Externally rewritten texts | Claude Opus 5 (Anthropic API) | **CC BY 4.0** — see the note below |
| `results_insan/s2_fayda.jsonl` | 788 judge verdicts | Claude Opus 5 and gpt-oss-120b | **CC BY 4.0** |
| `results/scores.csv`, `detection_metrics.csv`, `results_insan/skor_*.jsonl`, all `*_rapor.json` | Detector scores and derived metrics | Computed measurements | **CC0 1.0** (facts, below the threshold of originality) |
| `pilot/`, `hpc/`, `paper/*.py`, `paper/*.js` | Code | This work, on top of MarkLLM | **Apache-2.0** |

## Round-trip translation outputs (`att_*_rtt.jsonl`) — unresolved, restrictively labelled

These files contain Turkish text that was translated to English and back using
`facebook/nllb-200-distilled-600M`. That **model** is released under CC BY-NC 4.0.
Whether a non-commercial licence on model weights extends to the model's outputs is
genuinely contested and we do not assert an answer. We therefore take the
restrictive reading and label these ten files **CC BY-NC 4.0**: research use is
fine, commercial redistribution is not. If you need a commercially usable corpus,
exclude `att_*_rtt.jsonl`; every other component permits commercial use, and the
detector scores derived from these files (in `scores.csv`) are facts and are CC0.

## Externally laundered outputs (`att_*_launder_api.jsonl`)

These were produced through the Anthropic API using Claude Opus 5. Anthropic's
Commercial Terms assign to the customer Anthropic's right, title and interest in
outputs, so redistribution is permitted and we license these files CC BY 4.0.
Two usage restrictions travel with the source rather than with the licence, and we
record them here as information, not as licence terms: Anthropic's Usage Policy
prohibits using inputs and outputs to train or distil a competing model without
authorisation. We do not add that restriction to the CC BY 4.0 grant, because
adding conditions to a Creative Commons licence would invalidate it; we simply ask
that downstream users respect the source terms.

## ShareAlike is contagious — read this before combining files

The Wikipedia and Wikisource windows are CC BY-SA. If you create an **adaptation**
that merges those windows with other components, the result must also be licensed
CC BY-SA. Using them alongside other files in the same analysis is not an
adaptation; producing a new derived corpus that incorporates their text is. The
CC0 score files are deliberately kept separate from the text files so that
score-only reuse carries no ShareAlike obligation.

## Personal data

The human windows are excerpts from public encyclopedic and literary articles.
They were not selected by or about any private individual, and no attempt was made
to collect information about people. Named individuals may appear incidentally, as
they do in any encyclopedic text; these are public-figure mentions in already
published material. No personal data was gathered from the authors of those
articles beyond the public revision history that CC BY-SA attribution requires.

## If you find a licensing error here

Open an issue. We would rather correct an over-permissive label than leave one
standing.
