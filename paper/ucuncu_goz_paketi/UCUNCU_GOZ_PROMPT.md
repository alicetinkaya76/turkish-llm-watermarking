# Üçüncü-göz değerlendirme promptu — Language Resources and Evaluation

Bu dosyayı **bu makaleyi hiç görmemiş** bağımsız bir LLM oturumuna, yanındaki
dosyalarla birlikte ver. Aşağıdaki ayraç içindeki metni **aynen kopyala**;
bu satırların üstünü verme.

**Paketteki dosyalar** (`paper/ucuncu_goz_paketi/`):

| dosya | ne için |
|---|---|
| `paper.md` | makalenin tam metni (Word'ün kaynağı) |
| `title_page.md` | ayrı yüklenen başlık sayfası |
| `cover_letter.md` | editöre giden kapak mektubu |
| `numbers.json` | makaledeki HER sayının veriden üretilmiş hâli |
| `detection_metrics.csv` | AUROC / TPR / GA tablosunun ham kaynağı |
| `insan_fpr_rapor.json`, `register2_rapor.json` | S1 insan-metni ölçümleri |
| `s2_rapor.json` | S2 yargıç ölçümleri |
| `citation_verification.json` | 30 Ağu atıf denetimi kaydı — §3'te **sınanacak bir iddia**, kanıt değil |
| `BENCHMARK.md`, `DATA_LICENSE.md` | yayımlanan kaynağın kapsamı ve lisansı |

---

You are evaluating a manuscript submitted to **Language Resources and Evaluation**
(Springer). Work through three roles **in sequence** and keep them strictly
separate. Do not blend them, and do not let a judgement from one role soften
another.

## What you must know about the venue

- LRE publishes work on **language resources** (corpora, annotation, tools) and on
  the **evaluation** of language technology, with standing interest in
  **less-resourced and under-represented languages**.
- Review is **single-blind**: author identity is visible to you and that is correct,
  not a submission error.
- Author-year **APA 7** citations, alphabetical reference list.
- Abstract **150–250 words**, **4–6 keywords**, decimal headings, guideline length
  **18–25 pages**.
- A **"Statements and Declarations"** section is mandatory; its absence gets a
  submission returned as incomplete.

## Ground rules for your evaluation

1. **Honesty is not weakness.** This manuscript deliberately reports a negative
   result (a planned attack that did not fire), marks one of its own
   pre-registered hypotheses as superseded by later evidence, and withdraws a
   statistical bound an earlier version used. Do not score these as defects
   *because* they are admissions. Conversely, do not let candour buy leniency on a
   real problem.
2. **Check numbers against `numbers.json`, not against plausibility.** Every figure
   in the manuscript is supposed to be regenerable from the data. If a number in
   the text does not appear in `numbers.json` or the CSV, that is a finding. Say
   which number and where.
3. **Distinguish "wrong" from "not to my taste."** For each criticism, state
   whether it is a *defect* (something is incorrect, unsupported, or missing) or a
   *preference* (you would have done it differently). Preferences go in a separate,
   clearly-labelled list and must not affect the recommendation.
4. **Quote before you judge.** When you claim the manuscript says something, quote
   the sentence and give its section. Several past reviews of this work were wrong
   because they paraphrased a narrow claim into a broad one.
5. **If you cannot verify something, say so.** "I could not access this source" is
   a valid and useful output. An invented verification is worse than none.

---

# ROLE 1 — HANDLING EDITOR (desk decision)

In under 500 words, decide exactly one of: **desk reject** / **send to review** /
**send to review after pre-review revisions**. Justify against LRE's actual
criteria, not general impressions.

Answer each explicitly:

1. **Scope.** Does this fall within LRE's aims? Name the specific aims it meets or
   misses. It presents itself as *both* an evaluation-protocol paper and a released
   resource; judge whether both halves are real or whether one is decoration.
2. **Resource substance.** The paper releases a benchmark (TR-WM-EVAL) under a DOI.
   Read `BENCHMARK.md` and `DATA_LICENSE.md`. Is the resource documented well
   enough for third-party reuse? Is the licensing statement adequate, or does its
   non-uniformity make the resource impractical? Would you require changes before
   review?
3. **Novelty, proportionate.** State exactly what is new. Then ask whether the
   claims are sized to the evidence. Flag any sentence that claims more than the
   design can support.
4. **Sufficiency for this venue.** The generation corpus is one generator, 24
   prompts, 4 seeds (384 texts). The human-text study is larger (4,000 windows,
   pre-registered). Is this enough for LRE? State the condition under which it
   would be enough, and the condition under which it would not.
5. **Compliance.** Abstract length, keyword count, heading depth, page count,
   APA 7 conformance, presence and completeness of Statements and Declarations,
   data availability with a resolvable DOI. Name anything missing.
6. **Desk-reject triggers.** Unverifiable numbers, citation padding,
   self-contradiction, undeclared parallel submission, ethics gaps, salami
   slicing. The cover letter declares three parallel submissions by the same
   author; assess whether that declaration is adequate or whether it raises a
   real overlap concern.

End Role 1 with the recommendation on its own line.

---

# ROLE 2 — PEER REVIEWERS (two, with different lenses)

Write **two independent reviews**. Do not let them agree by construction; if they
reach the same verdict, they must reach it by different routes.

## Reviewer A — methods and statistics

Focus on whether the numbers mean what the paper says they mean.

- **Design.** EXP is deterministic given prompt and key, so its four seeds are not
  independent replicates. The paper handles this with prompt-clustered bootstrap
  (effective n = 24). Is that the right correction? Is it applied everywhere it
  should be?
- **Degenerate cells.** Eleven AUROC cells equal 1.000 with a collapsed bootstrap
  interval. The paper withdraws a Clopper–Pearson bound (arguing CP bounds a
  binomial proportion whereas AUROC is a U-statistic, via Bamber's identity) and
  reports counted separation, margins and exact permutation p-values instead. Is
  the withdrawal correct? Is the replacement adequate? Would you accept it?
- **The calibration finding.** KGW's null standard deviation is 1.479 on human
  Turkish against a theoretical 1, and the shipped z = 4 threshold yields 3
  exceedances in 1,500 windows. Check the uncertainty treatment: the paper reports
  an exact binomial interval (13× to 184×) rather than the point ratio alone. Is
  3/1500 enough to carry the claim the paper builds on it?
- **The mediation.** A post-hoc token-length control shows the inflation is present
  in English too, grows with tokens scored, and vanishes as a language effect at
  matched token count. The paper concludes Turkish contributes *exposure* via
  subword fertility rather than a distinct mechanism, and marks the pre-registered
  H2 superseded. Is that conclusion supported, or is it over-read from a control
  that was not pre-registered?
- **Multiplicity.** Holm and Bonferroni corrections appear in different places.
  Check that the correction family is declared and that nothing significant
  survives only because the family was drawn narrowly.
- **The key sweep.** Eight keys; the null standard deviation stays above 1 for all
  of them, but the z > 4 tail count ranges 3–143 and the study key gives the
  smallest tail. The paper argues this makes its headline the most conservative
  reading. Is that argument sound, or is it a favourable framing of an unstable
  statistic?

## Reviewer B — resources, reproducibility, and language coverage

Focus on whether this is a resource an LRE reader can actually use.

- **The benchmark.** Read `BENCHMARK.md`. Are the stated limitations the real ones,
  or is something material missing from that list? Could you rerun the paper's
  analysis from the release?
- **Pre-registration as git commits.** The paper claims its three pre-registrations
  are commits made before the corresponding data was collected, and that their
  dates can be checked against the data independently of the author's assertion.
  Is that a real guarantee or a rhetorical one? What could a determined author
  still fake, and does the paper's claim overreach?
- **Turkish specifically.** The subword-fertility argument is central. Is the
  linguistic reasoning right? Is the morphological attack's failure (coverage too
  low because formal register lacks the targeted suffix) diagnosed correctly, or
  does it indicate a design flaw the paper glosses as a negative result?
- **Generalisation.** One generator (Qwen3-14B) survived a pre-registered
  acceptance gate that four others failed. Does the paper's scope-limiting language
  match what the design licenses? Is any sentence in the Discussion broader than
  Section 6 allows?
- **Licensing.** `DATA_LICENSE.md` labels round-trip translations CC BY-NC under a
  deliberately restrictive reading of an unresolved question. Is that defensible or
  is it over-cautious to the point of harming reuse? Does the record's single
  licence field mislead?
- **Judge study.** Meaning-preservation verdicts come from two LLM judges and cover
  only the KGW arm. The paper says so. Is the resulting claim correctly scoped?

Each reviewer ends with: **accept / minor revision / major revision / reject**, a
numbered list of **required** changes, and a separate list of **optional**
suggestions.

---

# ROLE 3 — CITATION AND REFERENCE AUDITOR

This is the role the authors most want executed carefully. A previous review of an
earlier version of this work found four incorrect citations and missed a fifth.
Assume nothing is verified.

**Do not trust `citation_verification.json`.** It records an audit the authors ran
on 2026-08-30 which found and fixed eight defects, including two wrong attributions
and two claim mismatches. It is a **claim to be tested, not evidence**. Three of its
entries were verified by hand after an automated check failed; those are the ones
most worth re-testing. If that record is wrong anywhere, or if it missed something,
say so — an audit that only confirms a previous audit has told you nothing.

## 3.1 Per-reference bibliographic check

For **every** entry in the reference list, verify against the primary source
(publisher page, DOI resolution, ACL Anthology, PMLR, OpenReview, arXiv):

- author list — order and spelling, including diacritics
- year — and specifically **whether a preprint was later published**; an entry
  frozen at the arXiv version when a peer-reviewed version exists is a defect
- title, venue, volume/issue, page range
- DOI resolves to *this* work and not another
- APA 7 form: 21+ authors take the first 19, an ellipsis, then the final author;
  sentence case for titles; the reference list alphabetised with Ç collating as C

Report per entry: **verified** / **defect (describe)** / **could not verify (say
what you tried)**.

## 3.2 In-text claim matching — the part that matters most

For **every** in-text citation, the manuscript attributes something to a source.
Read the source and decide whether it actually supports that attribution. Look
specifically for:

- a number or result attributed to a source that does not report it
- a narrow finding reported as a general one
- an attribution that belongs to a different paper
- a purely decorative citation: the source is topically adjacent but does not
  support the sentence it is attached to

**Discipline:** a claim that is written narrowly in the manuscript ("for Turkish",
"at default settings", "in their setting") is **not** an overgeneralisation. Quote
the manuscript sentence before judging it.

Pay particular attention to these, which carry argumentative weight:

- **Fernandez et al. (2023)** — the manuscript says this work already measured
  false-positive inflation from repeated context and narrows its own mechanism
  claim accordingly. Is that characterisation right, and is the narrowing enough?
- **Kirchenbauer et al. (2024)** — the manuscript treats its ~800-token reliability
  result as a boundary condition its own result qualifies. Check the token budget,
  the nominal FPR, and the attack model actually used there.
- **Zhang et al. (2024)** — the manuscript claims an impossibility result and says
  its own attack is a crude realisation of that paper's perturbation oracle. Is
  that a fair reading?
- **Han et al. (2025)**, **Nemecek et al. (2026)**, **Al Ghanim et al. (2025)**,
  **Park et al. (2025)**, **Mohamed & Gubri (2025)** — recent and in several cases
  preprints. Verify they exist as cited, and that the closest-antecedent claims the
  manuscript makes against them are accurate.
- **Panickssery et al. (2024)** and **Zheng et al. (2023)** — cited to justify the
  judge design. Do they support the specific failure modes named?

## 3.3 Coverage in both directions

- Every reference cited at least once? Name any orphan.
- Every in-text citation present in the reference list? Name any missing.
- **Missing literature**: name any work that a specialist would expect and that is
  absent, and say what the manuscript would have to change if it engaged with it.
  Distinguish "should have cited" from "could also cite" — only the first is a
  finding.

---

# HOW TO REPORT

Produce, in this order:

1. **Audit boundary** — one short paragraph: what you could access, what you could
   not, and what that leaves unverified.
2. **Role 1 — editor decision.**
3. **Role 2 — Reviewer A**, then **Reviewer B**.
4. **Role 3 — citation audit**, as a table: `reference | bibliographic | claim
   match | action needed`.
5. **Blocking issues** — a numbered list of everything that must be fixed before
   this can be submitted, most serious first. For each: the exact location, what is
   wrong, and the corrected text you propose.
6. **Preferences** — clearly separated, explicitly not affecting any verdict.

Do not soften findings to be agreeable, and do not manufacture findings to appear
rigorous. If the manuscript is sound in some respect, say so plainly and move on.
