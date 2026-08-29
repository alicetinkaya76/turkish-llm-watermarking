# Title Page

## Title

Watermarking Turkish LLM Output: Detector Calibration, Scheme Fragility, and a
Released Evaluation Benchmark

## Author

**Ali Çetinkaya**

Department of Computer Engineering, Faculty of Technology, Selçuk University,
Alaeddin Keykubat Campus, 42075 Selçuklu, Konya, Türkiye

ORCID: 0000-0002-7747-6854 · <https://orcid.org/0000-0002-7747-6854>

This manuscript has a single author.

## Corresponding author

Ali Çetinkaya
Department of Computer Engineering, Faculty of Technology, Selçuk University,
Alaeddin Keykubat Campus, 42075 Selçuklu, Konya, Türkiye
E-mail: ali.cetinkaya@selcuk.edu.tr
Telephone: +90 332 241 11 02

## Keywords

LLM watermarking; Turkish; detector calibration; false-positive rate; subword
fertility; evaluation benchmark

## Acknowledgments

The generation and detection experiments were run on the high-performance computing
facility of the Faculty of Technology, Selçuk University; the author thanks the
facility's staff for access to the GPU node (NVIDIA Quadro RTX 8000) on which the
entire corpus was produced.

The author thanks the developers of the MarkLLM toolkit (Pan et al., 2024) for
releasing reference implementations of the three watermarking schemes under a
permissive licence; this study is a research fork of that toolkit and could not have
been carried out at this level of implementation fidelity without it. The findings
reported here concern the toolkit's shipped default configuration and were reached
independently of, and without consultation with, its developers.

The human-text baseline of Study S1 consists of excerpts from Turkish and English
Wikipedia and Turkish Wikisource. The author thanks the contributors to those
projects, whose work is reused here under CC BY-SA; per-window attribution is
provided in `ATTRIBUTION.md` and `ATTRIBUTION_pages.tsv` in the accompanying
repository.

Use of generative AI systems in this work, as the attack instrument, as the two
judges, and as a coding and drafting assistant, is declared in full under
"Declaration of generative AI use" in the Statements and Declarations section, as
required, and is deliberately not acknowledged here: no AI system is credited as a
contributor.

## Author contributions

Ali Çetinkaya is the sole author. CRediT contribution taxonomy: Conceptualization;
Methodology; Software; Validation; Formal analysis; Investigation; Resources; Data
curation; Writing – original draft; Writing – review and editing; Visualization;
Project administration. The author read and approved the final manuscript.

## Declarations (summary; full statements appear in the manuscript)

- **Funding.** No funds, grants, or other support were received during the
  preparation of this manuscript.
- **Competing interests.** The author has no competing interests to declare. Three
  transparency items, purchased API services, a declared and mitigated structural
  conflict inside the S2 judging design, and the fork relationship to the evaluated
  toolkit, are set out in full in the manuscript.
- **Ethics approval.** Not required: no human participants, no animals, no personal
  data. The LLM judges are measurement instruments, not participants; the reasoning,
  and a dual-use statement on the laundering attack, are given in the manuscript.
- **Consent to participate / Consent to publish.** Not applicable.
- **Data, material and code availability.** Openly available at
  <https://github.com/alicetinkaya76/turkish-llm-watermarking> (release tag
  `v1.0.0-paper`); archived at Zenodo, DOI [[10.5281/zenodo.XXXXXXX, atanmadı]].
  **Licensing is not uniform across components; see `DATA_LICENSE.md`.**
- **Generative AI use.** Declared in full in the manuscript. No AI system is an
  author.

---
