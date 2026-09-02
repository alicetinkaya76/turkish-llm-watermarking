1 September 2026

To the Editors-in-Chief
*Language Resources and Evaluation*

Dear Editors,

I submit for your consideration the manuscript **"Watermarking Turkish LLM Output:
Detector Calibration, Scheme Fragility, and a Released Evaluation Benchmark"** as a
single-authored Original Paper, and I would like it to be considered for the **special
focus section on Less-resourced Languages**. Its principal contributions for this journal
are an evaluation protocol for a language technology measured outside English and a
released, documented language resource for Turkish, whose resource landscape Çöltekin
et al. (2023) survey critically and find uneven in accessibility, licensing and register
coverage.

I should be precise about one thing, because the special focus section invites papers that
apply an established method to a less-resourced language for the first time and this is
not such a paper. Watermarking has already been measured on Turkish: Nemecek et al. (2026)
include it among eleven languages in a cross-lingual fairness audit, and Mohamed and Gubri
(2025) scale watermark robustness to over a hundred languages. What that literature does
not yet supply, and what this paper contributes, is a null distribution measured on human
text rather than on model output, together with register, token-length and watermark-key
controls on that distribution, in an agglutinative language other than Korean. The
manuscript states this boundary in Section 2 rather than leaving a novelty claim implicit.

**What the paper does.** Statistical watermarks for LLM output are designed and
validated almost entirely on English, and their detectors ship with thresholds whose
false-positive guarantees follow from a null distribution assumed rather than
measured. I measure three schemes, the green-list KGW, the Gumbel-sampling EXP, and
SynthID, on Turkish, using a pilot-scale but tightly instrumented protocol: 384
generated texts under ten removal attacks, a pre-registered false-positive study on
2,500 Turkish and 1,500 English human windows, and a two-judge meaning-preservation
study. The central result is a calibration failure. On human Turkish the KGW null
standard deviation is 1.479 against a theoretical 1, and the shipped z = 4 threshold
produces 3 exceedances in 1,500 windows, roughly 63 times nominal, with an exact
binomial interval of 13× to 184×. I also report, in full, that the pre-registered
hypothesis attributing this to Turkish does **not** survive a length control added
after pre-registration: at the matched token budgets we evaluated no Turkish–English
difference is detectable, and Turkish contributes exposure through subword fertility
rather than a distinct mechanism. Two further findings are a no-dominance pattern
across the three tested configurations (SynthID flags the fewest human windows at its
own shipped threshold yet is the most fragile under attack in all four paired
comparisons it enters, each with a Holm-adjusted p below .05 within that six-test
family, though the pattern is not monotone across all three) and a laundering attack that degrades all three schemes
while both judges rated meaning preserved on the sampled KGW-arm pairs, at a
measured cost of USD 17.704. A planned morphological attack did not fire, and that
negative result is reported with its coverage measurements rather than omitted.

**Why LRE.** The paper is a protocol-and-resource contribution, not a new watermark.
Alongside it I release **TR-WM-EVAL**, a Turkish watermark-evaluation benchmark:
4,000 human text windows spanning two registers and three corpus-language strata
(Turkish and English Wikipedia, and Turkish Wikisource), 384 generated texts, 3,840 attacked
texts, 58,161 detector scores including a length-controlled rescoring and an
eight-key sweep, and 788 pairwise judge verdicts. The resource is documented for
reuse independently of the paper: `BENCHMARK.md` states its known limitations at the
top level, `DATA_LICENSE.md` gives per-component licensing (which is deliberately
**not** uniform, and says so where a term is genuinely unresolved), and
`ATTRIBUTION.md` carries the Wikimedia attribution the CC BY-SA licence requires. The
three pre-registrations are commits made before the corresponding data was collected,
so their content and ordering are cryptographically fixed. I note in the Data Availability statement that the wall-clock dates are not independently anchored, because the repository was first published after the data was collected. Repository:
<https://github.com/alicetinkaya76/turkish-llm-watermarking>, release tag
`v1.6.0-paper`; archived at Zenodo under the concept DOI 10.5281/zenodo.22168552
(<https://doi.org/10.5281/zenodo.22168552>). That concept DOI resolves to the most recent
archived version and lists the version DOI of each; the version corresponding to this
submission is the one tagged `v1.6.0-paper`.

**Author identification.** As requested by the journal:

| | |
|---|---|
| Name | Ali Çetinkaya (sole author) |
| Affiliation | Department of Computer Engineering, Faculty of Technology, Selçuk University, Konya, Türkiye |
| E-mail | ali.cetinkaya@selcuk.edu.tr |
| ORCID | <https://orcid.org/0000-0002-7747-6854> |

As the sole author I offer, per the journal's cover-letter requirement, a verified ORCID
profile that is kept current with my publications and linked to my institution:
<https://orcid.org/0000-0002-7747-6854>. My work is in Turkish natural language
processing and digital humanities, and the present manuscript sits in that line: it
measures an English-developed language technology on Turkish and releases the evaluation
material as a documented resource.

**Declaration on parallel and related submissions.** The manuscript is original, has
not been published, and is not under consideration by any other journal. Three other
manuscripts of mine are currently under review elsewhere, and I list them so that the
editorial office can satisfy itself that there is no overlap:

1. ACM *Transactions on Asian and Low-Resource Language Information Processing*,
   manuscript **TALLIP-26-0165**, submitted 24 March 2026, status Under Review.
2. *Natural Language Processing* (Cambridge University Press; the journal was
   titled *Natural Language Engineering* until its 2024 renaming), manuscript
   **NLP-2026-0191**, submitted 8 June 2026, status Under Review.
3. *Information Processing & Management* (Elsevier), status Minor Revision. The
   manuscript number is available on request; I have omitted it here only because
   the revision is not yet resubmitted.

These three works and the present manuscript **share no corpus, no data, no text and
no analysis**. They use different materials, address different research questions,
and report disjoint results; no figure, table, number or passage is common to any two
of them. The only feature they have in common is that they concern Turkish natural
language processing, which is my research area, not a shared contribution. Should the
editors wish to verify this, I will supply the full texts of the other manuscripts on
request.

**Declarations.** The submission includes a separate title page and a Statements and
Declarations section covering funding, competing interests, ethics approval, consent,
data/material/code availability, author contributions, and a declaration of
generative AI use. On the last point I draw the editors' attention to one item, since
it is verifiable by any reviewer who opens the public repository: generative AI was
used in this project in three separate roles, as the attack instrument under study,
as the two judges of Study S2 (both documented in Methods), and as a coding and
drafting assistant, and the git history of the repository contains commits carrying
a `Co-Authored-By: Claude Opus 5` trailer. That trailer is a tooling convention that
records AI participation in a commit; it is not an authorship claim, no AI system is
an author of this paper, and I take sole responsibility for the content. The
declaration in the manuscript sets this out in full rather than leaving a reviewer to
interpret the repository unaided.

**On length.** The manuscript runs longer than the 18–25 pages the guidelines give as
typical, and I would rather raise this than leave it unexplained. Three things drive
it: the paper reports two separately pre-registered studies (a false-positive study on
4,000 human windows and a two-judge meaning-preservation study) alongside a ten-attack
robustness suite; it prints the full 33-cell realized false-positive table rather than
a summary, which the Introduction commits to explicitly because a truncated version of
that table is what would hide the finding; and it states the scope limits of each
claim individually rather than in a single blanket paragraph. I have already removed
what could go without loss, condensing the history of three withdrawn statistical
treatments to a single paragraph that points to a repository audit note carrying the
full derivations, and compressing the declarations. If the editors
would prefer it shorter, I would move material in this order: the 33-cell realized
false-positive table with its accompanying paragraph, retaining in the article the
maximum observed rate, the number of flagged cells and the clustering caveat; then
the detail of the eight-key sweep, retaining its range and conclusion; then the
version and timestamp discussion in the Data Availability statement and the
long-form licensing narrative, retaining the access route and the warning that the
licensing is not uniform; then the exploratory re-scoring and contamination
observations. I would keep the length control of Section 4.3 in the article even
under pressure, since it is what prevents the Turkish-English comparison from being
read as a token-budget confound, and it changed a pre-registered conclusion. That
sequence would bring the article close to the typical range, and I am happy to do it
on request.

I confirm that the manuscript has been prepared in accordance with the journal's
instructions for authors, and I have no objection to single-blind review.

Thank you for your consideration.

Yours sincerely,

**Ali Çetinkaya**
Department of Computer Engineering, Faculty of Technology
Selçuk University, Alaeddin Keykubat Campus, 42075 Selçuklu, Konya, Türkiye
ali.cetinkaya@selcuk.edu.tr · +90 332 241 11 02
ORCID 0000-0002-7747-6854

---
