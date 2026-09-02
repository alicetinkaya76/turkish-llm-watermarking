# Focused pre-submission audit — round 5

You are auditing a manuscript prepared for *Language Resources and Evaluation*
(Springer). Four audit rounds have already run against it and their confirmed
findings are applied. **This round is deliberately narrow.** A full re-review
would mostly re-litigate settled questions; what needs checking is what changed
in response to the last round, because a fix is where a new defect is most
likely.

**Manuscript version under review: `v1.5.0-paper`, `paper.md` SHA-256 prefix
`f6dd4313`.** State this identifier at the top of your report. If the file you
were given does not carry this content, say so and stop.

## What changed since the last audited version (v1.4.0-paper)

You have both versions: `paper.md` (current, v1.5.0) and `paper_ONCEKI_v1.4.0.md`.
The previous round raised four blocking issues and all four were accepted:

1. **The Table 5 interval now recalibrates the threshold.** The effect-size
   bootstrap previously fixed the clean-calibrated threshold once and resampled
   only the derived per-prompt differences, so the interval omitted calibration
   uncertainty. It now resamples prompt clusters jointly across the clean
   negatives and both attack arms and re-derives the threshold inside every
   replicate. The intervals moved; no conclusion changed sign.
2. **The null's justification was weakened to what it can carry.** "Its null
   follows from the design" became an explicit conditional-on-exchangeability
   statement, and the permutation test is now labelled two-sided throughout.
3. **A transcription error and a dropped qualifier were fixed.** A KGW interval
   endpoint disagreed with the generated source, and a Qwen-tokenizer-specific
   scope qualifier lost during an earlier condensation was restored.
4. **Two reference changes.** De-mark moved from its arXiv preprint to its final
   ICML/PMLR record, and Çöltekin et al. (2023), a *Language Resources and
   Evaluation* survey of Turkish resources, was added and cited.

Also newly disclosed: the two attack conditions carried into the focused
comparison were selected after the aggregate attack ranking was seen, and the
manuscript now says so rather than implying pre-specification.

## This is the final pre-submission check

Four rounds have already run and every one of them found real defects, so this
is not a formality. But it is the last round before submission, and that changes
what a useful report looks like.

**"Nothing blocking" is a permitted and valuable answer.** Do not manufacture
findings to justify the exercise. The previous round produced four genuine
blockers and also several suggestions that turned out to be either already
handled or based on a misidentified source; the second kind costs real time to
refute. If the fixes are sound, say so in a sentence per item and stop.

Rank anything you do find into exactly three buckets, and say which bucket each
finding is in:

- **BLOCKS SUBMISSION** — it would make a reported number, a claim's scope, or a
  conclusion wrong. These get fixed before submission.
- **FIX IF CHEAP** — real but does not change any number or claim. These may be
  fixed now or left to peer review.
- **REVIEWER WILL RAISE IT** — a defensible position a reviewer might challenge,
  where the manuscript's answer already exists or would be argued in response.
  These are not fixed now; they are noted for the response letter.

## Ground rules

1. **Verify before asserting.** If you claim a number is wrong, name the file and
   the value you checked it against. `numbers.json` and `detection_metrics.csv`
   are the generated sources; the manuscript should agree with them.
2. **If you claim a safeguard is missing, quote the function you inspected.** The
   code is in `kod/`. This rule exists because two earlier rounds reported the
   same absent safeguard that was in fact present and is still present
   (`metrics.py`, `tpr_ci_kumeli`, re-calibrates the threshold inside every
   bootstrap replicate).
3. **Read the sentence before calling it an overgeneralization.** Claims in this
   manuscript are written narrowly on purpose. Earlier rounds repeatedly flagged
   narrow sentences read broadly. Quote the exact sentence you object to.
4. **Do not pad.** If a section is sound, say so in one line and move on. A short
   report with three real findings is worth more than thirty speculative ones.
5. **Separate confidence levels.** Mark each finding CONFIRMED (you verified it
   against a file or a source) or PLAUSIBLE (you suspect it but did not verify).

---

## Role 1 — Handling Editor, *Language Resources and Evaluation*

Give a desk decision: **desk reject / send to review / send to review after
pre-review revisions**, with reasons.

Judge scope fit (the journal covers language resources and the evaluation of
language technology, including less-resourced languages), whether the released
resource is a genuine contribution, and whether the disclosed limitations are
disqualifying or creditable.

Then address length specifically. The article runs 33 pages against the
guideline's "typically 18–25". The cover letter contains an "On length"
paragraph that explains why and names, in order, the material the author would
move to supplementary if asked. Assess: is that an acceptable way to handle the
overage, or would you still return the manuscript? Is the named material the
right material to move first? Is anything currently in the article that you would
move *ahead* of what the author named?

## Role 2 — Reviewer A: the corrected statistic

This is the highest-risk item in the manuscript. Three successive inferential
treatments of a *different* quantity (the degenerate AUROC cells) were withdrawn
across earlier rounds, so the author's track record on this exact kind of
reasoning is mixed, and you should assume nothing.

Read Section 3.3, Section 4.2 ("Is laundering more destructive than
translation?"), Table 5, and `kod/metrics.py` (`d3_istem_duzeyi`,
`_tam_isaret_permutasyon_p`).

Answer these, each explicitly:

- **Is the estimand now the one the text describes?** The unit is the per-prompt
  detection rate at each scheme's own clean-calibrated threshold. Does the code
  compute that, and does every sentence around Table 5 describe that and not
  something else?
- **Is the null defensible this time?** The primary p-value is an exact paired
  sign-flip permutation test. The stated justification is that under
  exchangeability of the two conditions *within a prompt*, the sign of the paired
  difference is symmetric. Is that a design-derived null, or is it the same
  mistake as the withdrawn prompt-level sign test in a new costume? The
  manuscript claims the difference is that the pairing is genuine here and there
  is no shared data-dependent comparator. Test that claim. Note that the
  threshold *is* estimated from the clean negatives and is shared across prompts
  within a scheme — does that reintroduce the dependence the earlier test died
  of, and if so how much does it matter?
- **Zero differences.** Rates over four seeds take only five values, so 6 to 11
  of 24 pairs have exactly zero difference. The permutation test drops zeros; the
  Wilcoxon column uses Pratt's convention. Is dropping zeros in the permutation
  test correct here, or does it bias the result? Should the primary test have
  been something else?
- **Two-sidedness and conditionality.** The test is now labelled two-sided, and
  the p-value is described as conditional on the observed calibration sample
  while the interval carries calibration uncertainty. Is that split coherent, or
  should both be conditional, or neither?
- **The recalibrated interval.** Verify that `d3_istem_duzeyi` now resamples the
  clean negatives, the rtt arm and the launder_api arm on the *same* prompt
  clusters and re-derives the threshold per replicate, and that Table 5's numbers
  match `numbers.json`. Is joint cluster resampling the right dependence
  structure here? The KGW interval still excludes zero, [−0.271, −0.052], while
  its permutation p of 0.024 does not clear Bonferroni α = 0.0167; the manuscript
  labels the interval marginal and uncorrected and reports both. Is that
  defensible, or is presenting both a way of having it both ways?
- **Multiplicity.** Bonferroni over three schemes. Is the family right? The
  cross-scheme family (Table 6) is a separate set of six Holm-corrected tests. Is
  the division into two families defensible or is it a garden of forking paths?
- **The degenerate cells.** Section 3.3 now attaches no p-value and no confidence
  bound to the eleven AUROC = 1.000 cells, reporting counted separation and
  margin only. `DENETIM_NOTU_geri_cekilen_cikarimlar.md` gives the full history of
  the three withdrawals. Is the current descriptive treatment finally correct, or
  is there a valid test the author is now wrongly refusing to run? If you propose
  one, state the exchangeability unit and how the comparator is recomputed inside
  each permutation.

## Role 3 — Reviewer B: did the fixes break anything?

The previous round found that a condensation had silently dropped a scope
qualifier. Fixes are the same kind of risk. Compare the two versions and check:

- Does the weakened null statement in Section 3.3 now **under**-claim? It must
  still justify why this test is not the withdrawn prompt-level sign test in a
  new costume. The distinguishing argument is a genuine matched unit and a
  comparator invariant to the swap. Is that argument still present and correct?
- Do Section 3.3, Section 4.2, Table 5's caption and Section 5 agree with each
  other and with `numbers.json` on every D3 number, on two-sidedness, and on what
  the interval covers?
- The restored Qwen qualifier and the new attack-selection disclosure were
  inserted into existing paragraphs. Do they sit correctly, and does the
  attack-selection disclosure now contradict any surviving sentence that still
  implies the family was fully pre-specified?
- Does anything in the manuscript still claim the condensation removed nothing?
  The verification record was corrected to say that some supporting robustness
  diagnostics were shortened; the article should not contradict that.
- Is anything still redundant, given that length remains live?

## Role 4 — Citation audit

Two tasks.

**(a) The six new references.** For each, verify the bibliographic record against
a primary source (Crossref, ACL Anthology, arXiv, publisher page) *and* verify
that the manuscript's characterisation matches what the source actually says:

- Meral et al. (2009), *Computer Speech & Language* 23(1) — Turkish
  morphosyntactic watermarking, cited as the direct linguistic antecedent of the
  paper's morphological attack.
- Huang et al. (2025), B⁴, NAACL — black-box scrubbing.
- Chen et al. (2025), De-mark — query-based removal of n-gram watermarks.
- Zhang et al. (2026), NDSS — character-level perturbations disrupting
  tokenization.
- Ganesan (2025) — cross-lingual summarisation as removal.
- Harel-Canada et al. (2025), ACL — qualifying the strong-watermarking
  impossibility result.

The author already corrected two of their own attribution errors while adding
these: an initial draft credited Harel-Canada et al. with a finding they do not
report, and credited Meral et al. with a specific list of transformations that no
primary record could confirm. Check whether the corrected characterisations are
now accurate, and whether any *other* claim attributed to these six overstates
the source.

**(b) Test the verification record.** `citation_verification.json` is the
author's own audit record, including the round in which they verified these six.
It is a **claim to be tested, not evidence**. If you accept it without checking
anything in it, this role has not functioned. Check at least: does the reference
count it states match the manuscript, does its account of what was verified when
hold up, and is its description of the two self-corrected attribution errors
accurate?

Also confirm, mechanically: every reference is cited in the text, every in-text
citation resolves to a reference, and APA 7 author–year formatting is consistent
(sentence case for article titles, Ç collating as C, hanging indent, 21+ authors
using first-19-ellipsis-last).

**(c) LRE's own corpus.** Search for work published in *Language Resources and
Evaluation* (DOI prefix `10.1007/s10579-`) that this manuscript should engage
with, in evaluation methodology, Turkish resources, subword tokenization,
Wikipedia/Wikisource corpus construction, resource-description papers, LLM-judge
annotation, or machine-generated text detection.

**A warning specific to this task.** Asking a model for references from a named
journal is the request most likely to produce a fabricated or misidentified
citation, and in the previous round exactly that happened: a suggested "UWBench"
turned out to be an underwater vision-language benchmark with no connection to
watermarking. **Verify every DOI resolves and says what you claim before listing
it.** Split your output into *should cite* / *could cite* / *checked and does not
fit*. The last category is required, not optional — it shows what you rejected
and why. If LRE has published little that is genuinely relevant, say so plainly;
do not manufacture relevance.

---

## Output format

1. The version stamp `v1.5.0-paper / sha256 f6dd4313`.
2. Role 1 verdict, with the length assessment stated separately.
3. Role 2: one answer per bullet, each marked CONFIRMED or PLAUSIBLE.
4. Role 3: what the condensation lost, or an explicit statement that you checked
   and it lost nothing. Name the sections you compared.
5. Role 4: (a) six-reference table, (b) your test of the verification record,
   (c) LRE citations in three groups.
6. A final list of blocking issues, ordered, with the minimum acceptable fix for
   each. If there are none, say so — that is a permitted and useful answer.
