# Üçüncü-göz promptu — tur 4 (ODAKLI), Language Resources and Evaluation

**Sürüm damgası:** `v1.4.0-paper / sha256 8033571d`, 2026-09-01. Rapor geldiğinde
ilk iş bu damgayı aramak.

**Bu tur öncekilerden FARKLI.** Önceki üç tur makalenin iddialarını baştan sona
inceledi ve doyum noktasına yaklaştı: son turda önerilen yedi dil düzeltmesinin
dördü zaten kapalıydı, bir kaynak önerisi de yanlış makaleye aitti. Bu tur onun
yerine **yalnızca son turda DEĞİŞENİ** denetliyor, çünkü risk orada: bir estimand
değişti ve manşet sonuç yer değiştirdi, altı yeni kaynak girdi, ve makale 1.754
kelime kısaltıldı.

Aşağıdaki `---` ayracından sonraki İngilizce metni aynen kopyalayıp denetim
oturumuna yapıştır. Türkçe başlık kısmını verme.

---

# Focused pre-submission audit — round 4

You are auditing a manuscript prepared for *Language Resources and Evaluation*
(Springer). Three full audit rounds have already run against it and their
confirmed findings are applied. **This round is deliberately narrow.** A fourth
full re-review would mostly re-litigate settled questions; what needs checking is
what changed since the last audited version, because that is where new defects
would be.

**Manuscript version under review: `v1.4.0-paper`, `paper.md` SHA-256 prefix
`8033571d`.** State this identifier at the top of your report. If the file you
were given does not carry this content, say so and stop.

## What changed since the last audited version (v1.3.0-paper)

You have both versions: `paper.md` (current) and `paper_ONCEKI_v1.3.0.md`
(previous). Three kinds of change:

1. **A statistical estimand was corrected and a headline result moved.** The
   within-scheme comparison of external laundering (`launder_api`) against
   round-trip translation (`rtt`) had been running on the per-prompt *mean raw
   detector statistic*, while the manuscript described the per-prompt *detection
   rate at the operating threshold*. Corrected to detection rates, the scheme
   surviving Bonferroni correction changed from KGW to EXP.
2. **Six references were added** with accompanying prose, narrowing the novelty
   claim.
3. **The manuscript was condensed from 19,369 to 17,615 words (36 to 32 pages).**
   The author's stated rule was to remove only duplication and process narration,
   never a finding, table, figure, limitation, disclosure or scope qualifier.

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

Then address length specifically. The article runs 32 pages against the
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
- **Two-sidedness.** The permutation test is two-sided while the surrounding
  claim is directional. Conservative, or a mismatch that should be stated?
- **The KGW cell.** Its bootstrap interval excludes zero, [−0.292, −0.042], while
  its permutation p of 0.024 does not clear Bonferroni α = 0.0167. The manuscript
  reports both and says they answer different questions. Is that the right call,
  or is presenting both a way of having it both ways?
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

## Role 3 — Reviewer B: what the condensation removed

You have both versions. The author's claim is that the 1,754 removed words were
**only** duplication and process narration, and that no finding, table, figure,
limitation, disclosure or scope qualifier was lost. Test that claim; it is the
kind of claim that is easy to make and easy to violate accidentally.

Per-section word deltas: Introduction −301, Section 4.2 −86, Section 4.3 −72,
Section 5.1 −124, Section 5.2 −152, Section 5.3 −226, Section 6 −488, Section 7
−127, declarations −186.

Concentrate on the largest cuts, Section 6 (−488) and Section 5 (−502 combined).
For each, answer:

- Did any **scope qualifier** disappear? Earlier audit rounds specifically
  *added* qualifiers to this manuscript — that a claim holds only for the KGW
  arm, only at the evaluated token budgets, only for surface-context-seeded
  schemes, only on this sample. If one of those was dropped while compressing the
  paragraph around it, the manuscript has silently re-broadened a claim that a
  previous round narrowed. This is the single most likely defect in this version.
- Did any **limitation** lose its substance while keeping its heading? Section 6
  went from paragraph-per-limitation to statement-per-limitation. Check that each
  of the ten still says what it needs to.
- Did any **disclosure** in Statements and Declarations lose required content?
  Springer requires funding, competing interests, ethics, consent, data
  availability, author contributions, and AI-use declarations to be complete, not
  merely present.
- Did the condensation **break a dependency** — a sentence that now refers to
  something no longer stated, a number that lost the caveat that qualified it, a
  claim whose supporting detail moved to the repository audit note without a
  pointer?
- Conversely: **is anything still redundant?** If the article still says the same
  thing three times anywhere, name it, since the length question is live.

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

1. The version stamp `v1.4.0-paper / sha256 8033571d`.
2. Role 1 verdict, with the length assessment stated separately.
3. Role 2: one answer per bullet, each marked CONFIRMED or PLAUSIBLE.
4. Role 3: what the condensation lost, or an explicit statement that you checked
   and it lost nothing. Name the sections you compared.
5. Role 4: (a) six-reference table, (b) your test of the verification record,
   (c) LRE citations in three groups.
6. A final list of blocking issues, ordered, with the minimum acceptable fix for
   each. If there are none, say so — that is a permitted and useful answer.
