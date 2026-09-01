# Üçüncü-göz değerlendirme promptu — Language Resources and Evaluation

Bu dosyayı **bu makaleyi hiç görmemiş** bağımsız bir LLM oturumuna, paketteki
dosyalarla birlikte ver. Aşağıdaki `---` ayracından sonraki İngilizce metni
**aynen kopyala**; bu Türkçe başlık kısmını verme, o senin için.

**Sürüm damgası:** `v1.4.0-paper / sha256 8033571d`, 2026-09-01. Denetim raporu geldiğinde ilk iş bu
damgayı raporda arayıp doğrulamak: geçen turda denetçi eski bir kopyayı okumuş ve
çoktan düzeltilmiş beş kusuru yeniden bildirmişti.

**Atıf denetimi web erişimi ister.** Erişimi olmayan bir modelde 3. ve 4. rolü
koşturma; koşturursan doğrulama yapmadan doğruladığını söyler.

---

You are evaluating a manuscript submitted to **Language Resources and Evaluation**
(Springer). Work through four roles **in sequence** and keep them strictly separate.
Do not blend them, and do not let a judgement in one role soften another.

**Manuscript version under review: `v1.4.0-paper / sha256 8033571d` (2026-09-01).** State this identifier at
the top of your report so the authors can confirm you read the current text. If any
file you were given disagrees with another, say so rather than silently picking one.

## What you must know about the venue

- LRE publishes work on **language resources** (corpora, annotation, tools) and on the
  **evaluation** of language technology, with standing interest in **less-resourced and
  under-represented languages**.
- Review is **single-blind**: author identity is visible to you and that is correct, not
  a submission error.
- Author-year **APA 7** citations, alphabetical reference list.
- Abstract **150–250 words**, **4–6 keywords**, decimal headings, guideline length
  **18–25 pages**.
- A **"Statements and Declarations"** section is mandatory; its absence gets a
  submission returned as incomplete.

## Ground rules

1. **Honesty is not weakness.** This manuscript reports a negative result (a planned
   attack that did not fire), marks one of its own pre-registered hypotheses as
   superseded, withdraws a statistical bound an earlier version used, and states the
   limits of its own pre-registration guarantee. Do not score these as defects *because*
   they are admissions. Conversely, do not let candour buy leniency on a real problem.
2. **Check the code before claiming a method is missing.** You are given
   `metrics.py`, `dev_dejenere_kanit.py`, `dev_h2_token.py` and `dev_anahtar_supurme.py`.
   A previous reviewer asserted that threshold-estimation uncertainty was not propagated
   into the confidence intervals; the implementation does propagate it, and the claim was
   wrong. If you believe a statistical safeguard is absent, quote the function you
   checked and say what it does instead.
3. **Check numbers against `numbers.json` and the CSV, not against plausibility.** If a
   number in the text is not regenerable from those files, that is a finding. Name the
   number and its location.
4. **Distinguish "wrong" from "not to my taste."** Mark each criticism as a *defect*
   (incorrect, unsupported, or missing) or a *preference*. Preferences go in a separate
   list and must not affect any recommendation.
5. **Quote before you judge.** When you claim the manuscript says something, quote the
   sentence and give its section. Past reviews of this work were wrong because they
   paraphrased a narrow claim into a broad one.
6. **If you cannot verify something, say so.** "I could not access this source" is a
   valid and useful output. An invented verification is worse than none.

---

# ROLE 1 — HANDLING EDITOR (desk decision)

In under 500 words, decide exactly one of: **desk reject** / **send to review** /
**send to review after pre-review revisions**. Justify against LRE's criteria.

1. **Scope.** Does this fall within LRE's aims? Name the aims it meets or misses. It
   presents itself as both an evaluation-protocol paper and a released resource; judge
   whether both halves are real or one is decoration.
2. **Resource substance.** Read `BENCHMARK.md` and `DATA_LICENSE.md`. Is the resource
   documented well enough for third-party reuse? Is the licensing statement adequate, or
   does its non-uniformity make the resource impractical?
3. **Novelty, proportionate.** State exactly what is new. The paper positions itself
   against WaterBench, Mark My Words and WaterPark as a language- and
   negative-distribution-specific contribution rather than a general benchmark. Is that
   positioning accurate and is it sized to the evidence?
4. **Sufficiency.** One generator, 24 prompts, 4 seeds (384 texts); human-text study
   4,000 windows, pre-registered. Enough for LRE? State the condition under which it
   would be, and under which it would not.
5. **Compliance.** Abstract length, keyword count, heading depth, page count, APA 7
   conformance, completeness of Statements and Declarations, data availability with a
   resolvable DOI. Name anything missing.
6. **Desk-reject triggers.** Unverifiable numbers, citation padding, self-contradiction,
   undeclared parallel submission, ethics gaps, salami slicing. The cover letter declares
   three parallel submissions; assess whether that declaration is adequate.

End Role 1 with the recommendation on its own line.

---

# ROLE 2 — PEER REVIEWERS (two, different lenses)

Write **two independent reviews**. If they reach the same verdict they must reach it by
different routes.

## Reviewer A — methods and statistics

- **Dependence.** EXP is deterministic given prompt and key, so its four seeds are not
  independent replicates. The paper uses prompt-clustered bootstrap (effective n = 24).
  Is that correction right, and is it applied everywhere it should be? Check
  `metrics.py` rather than inferring from the prose.
- **Degenerate cells.** Eleven AUROC cells equal 1.000. The paper has now withdrawn
  *three* successive inferential treatments of this: a Clopper–Pearson bound (CP bounds a
  binomial proportion; AUROC is a U-statistic, via Bamber), a within-prompt
  exchangeability p-value of 10⁻⁴⁴·³, and a prompt-level sign test of 2⁻²⁴. Section 3.3
  explains each withdrawal; the separation is now reported descriptively only, with
  counted clusters and margins in negative-SD units. Is withdrawing the p-value the right
  call, or is a valid test available that the authors have missed? If you propose one,
  state the exchangeability unit and how the comparator is recomputed under permutation.
- **The calibration finding.** KGW's null SD is 1.479 in Turkish against a theoretical 1;
  the shipped z = 4 threshold gives 3 exceedances in 1,500 windows with an exact binomial
  interval of 13× to 184×. Is 3/1500 enough to carry what is built on it?
- **The commensurability fix.** The cross-scheme axis was changed from raw null standard
  deviations to realized false-positive rate at each scheme's own shipped threshold
  (SynthID 0/1500, KGW 3/1500, EXP 13/1500). Is that axis genuinely commensurable? The
  paper now says the pattern is not monotone and declines to call it a trade-off. Is that
  the right level of restraint, or does even the weakened claim outrun three data points?
- **The mediation.** A post-hoc token-length control shows inflation in English too,
  growing with tokens scored and vanishing as a language effect at matched token count.
  The paper calls this an exposure pathway and explicitly declines a causal-mediation
  claim. Is the restraint sufficient?
- **Multiplicity and units.** Holm and Bonferroni families are declared in different
  places. Table 7 is now presented descriptively because its 96 rows are four per prompt
  across 24 clusters. Is anything still resting on an invalid unit?
- **Key sweep.** Eight keys; null SD stays above 1 for all, tail count ranges 3–143, the
  study key gives the smallest tail. The paper now says this is conditional on the
  sampled key. Sound?

## Reviewer B — resources, reproducibility, language coverage

- **The benchmark.** Read `BENCHMARK.md`. Are the stated limitations the real ones, or is
  something material missing? Could you rerun the analysis from the release?
- **Pre-registration.** The paper states that the commit hashes bind content and ordering
  but that the wall-clock dates are **not** independently anchored, because the repository
  was first published on 2026-08-29, after the data was collected. Is that disclosure
  adequate, or does the word "pre-registered" still carry more weight than the evidence?
- **Turkish specifically.** The subword-fertility argument is central. Is the linguistic
  reasoning right? Is the morphological attack's failure diagnosed correctly as a register
  mismatch, and is that labelled as hypothesis rather than established mechanism?
- **Generalisation.** One generator survived a pre-registered gate that four others
  failed. Does the scope-limiting language match what the design licenses? Is any sentence
  in the Discussion broader than Section 6 allows?
- **Licensing.** `DATA_LICENSE.md` labels round-trip translations CC BY-NC under a
  deliberately restrictive reading, and the archive-level field is "Other (Open)" with the
  per-path manifest declared authoritative. Defensible, or over-cautious to the point of
  harming reuse?
- **Judge study.** Meaning verdicts cover 40 unique pairs per condition, KGW arm only, and
  fluency conclusions are withheld where the position-flip bound was exceeded. Is the
  scoping correct and consistently stated?

Each reviewer ends with **accept / minor revision / major revision / reject**, a numbered
list of **required** changes, and a separate list of **optional** suggestions.

---

# ROLE 3 — CITATION AND REFERENCE AUDITOR

Assume nothing is verified. `citation_verification.json` records two audits the authors
already ran; treat it as **a claim to be tested, not evidence**. If it is wrong anywhere,
or missed something, say so. An audit that only confirms a previous audit has told you
nothing.

## 3.1 Per-reference bibliographic check

For **every** entry, verify against the primary source (publisher page, DOI resolution,
ACL Anthology, PMLR, OpenReview, arXiv):

- author list, order and spelling, diacritics included
- year, and specifically **whether a preprint has since been published**; an entry frozen
  at the preprint when a version of record exists is a defect
- title, venue, volume/issue, page range
- DOI resolves to *this* work
- APA 7 form: 21+ authors take the first 19, an ellipsis, then the final author; sentence
  case; alphabetical order with Ç collating as C

Report per entry: **verified** / **defect (describe)** / **could not verify (say what you
tried)**.

## 3.2 In-text claim matching

For **every** in-text citation, read the source and decide whether it supports what the
manuscript attributes to it. Look for:

- a number or result attributed to a source that does not report it
- a narrow finding reported as general
- an attribution that belongs to a different paper
- a decorative citation: topically adjacent, does not support the sentence

**Discipline:** a claim written narrowly in the manuscript ("for Turkish", "at default
settings", "in their setting") is **not** an overgeneralisation. Quote the sentence first.

These carry argumentative weight and were changed in a previous audit round — re-check
them rather than trusting the change:

- **Kuditipudi et al. (2024)** — now cited for the distortion-free *family*, with an
  explicit note that their EXP-Edit and ITS-Edit algorithms were not run. Correct now?
- **Rust et al. (2021)** — now cited for subword fertility and proportion of continued
  words, not for suffix repetition. Does the source support the narrowed claim?
- **Liu et al. (2024)** — SIR is now described as token-level with a semantic seed rather
  than a sentence-level scheme. Accurate?
- **Bulat (2022)** — zeyrek is now described as a same-lemma reparse filter, not a
  grammaticality guarantee. Consistent with Section 3.2?
- **Fernandez et al. (2023)**, **Kirchenbauer et al. (2024)**, **Zhang et al. (2024)**,
  **Panickssery et al. (2024)**, **Zheng et al. (2023)**, **Han et al. (2025)**,
  **Nemecek et al. (2026)**, **Piet et al. (2025)**, **Liang et al. (2025)**,
  **Tu et al. (2024)**.

## 3.3 Coverage in both directions

- Every reference cited at least once? Name any orphan.
- Every in-text citation present in the reference list? Name any missing.
- **Missing literature**: name work a specialist would expect and that is absent, and say
  what would have to change if the paper engaged with it. Distinguish "should have cited"
  from "could also cite" — only the first is a finding.

---

# ROLE 4 — CITATIONS FROM THE TARGET JOURNAL

Editors notice whether a submission engages with its own venue. Independently of whether
you think the paper is good, identify work **published in *Language Resources and
Evaluation* itself** that this manuscript should cite.

Search LRE's own corpus (Springer's journal page, DOI prefix `10.1007/s10579-`, and
indexes such as OpenAlex, Crossref, Semantic Scholar or Google Scholar restricted to that
journal). Look across the areas this paper touches:

- evaluation methodology and protocol design for language technology
- Turkish corpora, treebanks, morphological analyzers, and Turkish NLP resources
- subword tokenization, morphological segmentation, and their effect on evaluation
- corpus construction from Wikipedia and Wikisource, and register/genre sampling
- benchmark and shared-resource description papers, including their documentation norms
- annotation with LLM judges, inter-annotator agreement, and reliability reporting
- machine-translation evaluation, including round-trip translation as a method
- detection of machine-generated text, if LRE has published on it

For each candidate give: full APA 7 reference, DOI, **one sentence on what it actually
shows**, and — most important — **the specific sentence or section of this manuscript it
should attach to, and whether citing it would change any claim**.

Then apply a filter and be honest about it. Split your list into:

- **Should cite** — genuinely relevant; the manuscript is weaker or less accurate without
  it. Say what changes.
- **Could cite** — real but optional; would strengthen framing, changes nothing.
- **Do not cite** — you found it but it does not belong; say so explicitly so the authors
  do not add it for appearances.

**Do not pad.** Recommending LRE papers merely because they are LRE papers is citation
padding, it is visible to editors, and it is worse than citing nothing. If the honest
answer is that LRE has published little that bears on this topic, say that plainly and
give the short list anyway. If you cannot search the journal's corpus, say so and do not
guess titles — fabricated references are the most damaging possible output here.

---

# HOW TO REPORT

1. **Version and audit boundary** — the manuscript identifier you were given, what you
   could access, what you could not, and what that leaves unverified.
2. **Role 1 — editor decision.**
3. **Role 2 — Reviewer A**, then **Reviewer B**.
4. **Role 3 — citation audit**, as a table: `reference | bibliographic | claim match |
   action needed`.
5. **Role 4 — LRE citations**, in the three-way split above.
6. **Blocking issues** — numbered, most serious first; for each, the exact location, what
   is wrong, and the corrected text you propose.
7. **Preferences** — clearly separated, explicitly not affecting any verdict.

Do not soften findings to be agreeable, and do not manufacture findings to appear
rigorous. Where the manuscript is sound, say so plainly and move on.
