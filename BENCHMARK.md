# TR-WM-EVAL: a Turkish watermark-evaluation benchmark

This repository releases the corpora, detector scores and judge annotations behind
the paper *Watermarking Turkish LLM Output: Detector Calibration, Scheme Fragility,
and a Released Evaluation Benchmark*. It is meant to be reusable independently of
that paper: the score files let you check our numbers, and the texts let you
evaluate a different detector or a different attack on the same material.

Everything here was produced by the code in this repository. The project rule is
that no reported number is written by hand; every figure in the paper is
regenerated from these files by `pilot/make_paper_numbers.py` into
`paper/numbers.json`.

## What is in it

| Component | Records | File(s) |
|---|---|---|
| Human Turkish windows (Wikipedia) | 1,500 | `results_insan/insan_tr.jsonl` |
| Human English windows (Wikipedia), word-matched | 1,500 | `results_insan/insan_en.jsonl` |
| Human Turkish windows (Wikisource, second register) | 1,000 | `results_insan/insan_tr_wikisource.jsonl` |
| Generated Turkish texts (4 arms) | 384 | `results/gen_neg.jsonl`, `results/gen_pos_*.jsonl` |
| Attacked texts (10 attacks × 4 arms) | 3,840 in 40 files | `results/att_*.jsonl` |
| Detector scores on human text (3 schemes) | 12,000 | `results_insan/skor_{tr,en,tr_wikisource}.jsonl` |
| Length-controlled rescoring (4 token budgets) | 14,161 | `results_insan/skor_h2_token.jsonl` |
| Key sweep (8 watermark keys × 4,000 windows) | 32,000 | `results_insan/skor_anahtar.jsonl` |
| Pairwise judge verdicts (2 judges) | 788 | `results_insan/s2_fayda.jsonl` |
| Combined score table | 6,336 | `results/scores.csv` |

The three schemes are KGW (green-list logit bias), EXP (Gumbel sampling) and
SynthID (tournament sampling). The ten attacks are diacritic stripping at two
rates, two morphological variants, each of those crossed with diacritics,
self-paraphrase, self-laundering, round-trip machine translation, and laundering
through an external commercial model.

## Provenance

- Generator: `Qwen/Qwen3-14B`, fp16, on the hardware recorded in `results/env.json`.
- Watermarking toolkit: MarkLLM at commit `c45ddc40f7b7`.
- Prompt file is content-addressed; SHA-256 prefix `8fcbe4074b46`.
- Pre-registrations are commits in this repository's history, each made before the
  corresponding data was collected: `8f8df72` (S1 hypotheses), `cbcb988` (S2
  protocol and decision rule), `5c4f323` (second register).

Because the pre-registrations are commits rather than documents, they can be dated
against the data files independently of anything we assert.

## Known limitations of the resource

These are properties of the data, not of the paper's argument, and you should know
them before reusing it.

- **One generator.** All generated text comes from Qwen3-14B. Five candidates were
  run through a pre-registered acceptance gate and only this one passed; the gate
  records are in `results_hpc/`.
- **One watermark key on the attack axis.** The key sweep covers the human-text
  null only, because that needs no regeneration. Every AUROC and robustness number
  is conditional on the single study key.
- **EXP texts are fixed-length.** EXP emits a fixed token count and never stops at
  a sentence boundary, so its texts differ structurally from the other arms. Any
  cross-scheme comparison of text quality is confounded by this.
- **EXP replicates are not independent.** Under deterministic decoding EXP's four
  seeds produce identical output, so the effective unit is the prompt rather than
  the text: 96 EXP records contain 24 distinct texts.
- **Judge verdicts cover one arm.** Meaning and fluency were judged on KGW-sourced
  texts only. They are not measurements of the EXP or SynthID arms.
- **Windows are word-matched, not token-matched.** The human windows target 365
  words, which is a median of 1,017 tokens in Turkish and 529 in English. This
  matters for any length-sensitive statistic; `skor_h2_token.jsonl` provides the
  token-matched rescoring at four budgets.
- **One judge produced one of the attacks.** Claude Opus 5 generated the
  `launder_api` texts and also served as one of the two judges. The second judge is
  from a different model family for exactly this reason, but the conflict is
  inherent and is not fully removed.

## Reproducing the paper's numbers

```bash
python pilot/make_paper_numbers.py     # -> paper/numbers.json
python paper/make_figures.py           # -> paper/figs/
```

The measurement scripts that produced the newer blocks are
`pilot/dev_h2_token.py` (length control), `pilot/dev_anahtar_supurme.py` (key
sweep) and `pilot/dev_dejenere_kanit.py` (separation evidence for the cells with
AUROC 1.000). Each writes a JSON report that `make_paper_numbers.py` reads.

## Licensing

Not uniform, because the components have different origins. See `DATA_LICENSE.md`.
In short: Wikimedia-derived text is CC BY-SA and requires attribution
(`ATTRIBUTION.md`, with the page list in `ATTRIBUTION_pages.tsv`); round-trip
translations are labelled CC BY-NC under the restrictive reading of the
translation model's licence; generated and laundered texts and judge verdicts are
CC BY 4.0; score and metric files are CC0; code is Apache-2.0.

## Citation

Until the paper has a DOI, cite this repository and the Zenodo deposit it is
archived in. If you use only the score files, the texts they were computed from are
still the thing that needs attribution, because they are Wikimedia-derived.
