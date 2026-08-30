30 August 2026

To the Editors-in-Chief
*Language Resources and Evaluation*

Dear Editors,

I submit for your consideration the manuscript **"Watermarking Turkish LLM Output:
Detector Calibration, Scheme Fragility, and a Released Evaluation Benchmark"** as a
single-authored Original Paper. I suggest it be handled under the journal's scope for
**less-resourced languages and the evaluation of language technology**, since its two
contributions are an evaluation protocol for a language technology measured outside
English and a released, documented language resource.

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
after pre-registration: at matched token length the two languages are
indistinguishable, and Turkish contributes exposure through subword fertility rather
than a distinct mechanism. Two further findings are a robustness–calibration
trade-off (SynthID has the cleanest null yet is the most fragile under attack) and a
laundering attack that degrades all three schemes while preserving meaning, at a
measured cost of USD 17.704. A planned morphological attack did not fire, and that
negative result is reported with its coverage measurements rather than omitted.

**Why LRE.** The paper is a protocol-and-resource contribution, not a new watermark.
Alongside it I release **TR-WM-EVAL**, a Turkish watermark-evaluation benchmark:
4,000 human text windows across three registers, 384 generated texts, 3,840 attacked
texts, 58,161 detector scores including a length-controlled rescoring and an
eight-key sweep, and 788 pairwise judge verdicts. The resource is documented for
reuse independently of the paper: `BENCHMARK.md` states its known limitations at the
top level, `DATA_LICENSE.md` gives per-component licensing (which is deliberately
**not** uniform, and says so where a term is genuinely unresolved), and
`ATTRIBUTION.md` carries the Wikimedia attribution the CC BY-SA licence requires. The
three pre-registrations are commits made before the corresponding data was collected,
so their dating can be verified independently of any claim I make. Repository:
<https://github.com/alicetinkaya76/turkish-llm-watermarking>, release tag
`v1.1.0-paper`; archived at Zenodo under DOI 10.5281/zenodo.22168553
(<https://doi.org/10.5281/zenodo.22168553>).

**Author identification.** As requested by the journal:

| | |
|---|---|
| Name | Ali Çetinkaya (sole author) |
| Affiliation | Department of Computer Engineering, Faculty of Technology, Selçuk University, Konya, Türkiye |
| E-mail | ali.cetinkaya@selcuk.edu.tr |
| ORCID | <https://orcid.org/0000-0002-7747-6854> |
| Institutional page | [[KURUM PROFİL URL'Sİ, Selçuk Üniversitesi personel sayfan; doğrulanmış URL'yi yapıştır]] |
| CV / publication list | [[CV veya Google Scholar URL'si, doğrulanmış olanı yapıştır]] |

**Declaration on parallel and related submissions.** The manuscript is original, has
not been published, and is not under consideration by any other journal. Three other
manuscripts of mine are currently under review elsewhere, and I list them so that the
editorial office can satisfy itself that there is no overlap:

1. ACM *Transactions on Asian and Low-Resource Language Information Processing*,
   manuscript **TALLIP-26-0165**, submitted 24 March 2026, status Under Review.
2. *Natural Language Processing* (Cambridge University Press; the journal was
   titled *Natural Language Engineering* until its 2024 renaming), manuscript
   **NLP-2026-0191**, submitted 8 June 2026, status Under Review.
3. *Information Processing & Management* (Elsevier), manuscript [[NUMARA, elindeki
   IPM el yazması numarasını yaz]], status Minor Revision.

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
