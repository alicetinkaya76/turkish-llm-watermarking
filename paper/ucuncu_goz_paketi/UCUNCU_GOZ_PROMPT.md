# Üçüncü-göz değerlendirme promptu

Bu dosyayı bağımsız bir LLM'e (tercihen bu makaleyi hiç görmemiş bir oturuma)
makale dosyalarıyla birlikte ver. **Aşağıdaki ayraç içindeki metni aynen kopyala.**

**Verilecek dosyalar:** `paper/paper.md` (veya `paper.docx`), `paper/numbers.json`,
`paper/citation_verification.json`. Mümkünse `results/detection_metrics.csv` ve
`results_insan/*.json` de verilebilir (sayı doğrulaması için).

---

You are reviewing a manuscript submitted to **Computers & Security** (Elsevier;
alternative target: **ACM TALLIP**). Adopt three roles in sequence and keep them
separate. Do not blend them.

**Context you must respect:** the authors deliberately report negative results,
retracted claims, and a long limitations section. Do not treat honesty as
weakness. Conversely, do not let it buy leniency on real defects.

---

## ROLE 1 — HANDLING EDITOR (desk decision)

Decide, in under 400 words, one of: **desk reject** / **send to review** /
**send to review with pre-review revisions**. Justify with the journal's actual
criteria, not general impressions.

Answer explicitly:
1. **Scope fit.** Is this within the journal's aims? Name the aims it matches or
   misses. If it fits the alternative venue better, say which and why.
2. **Novelty claim.** What exactly is new? Is the claim proportionate to the
   evidence? Flag any claim that overreaches.
3. **Sufficiency.** Is a single-generator, 24-prompt corpus enough for this
   journal, given the authors' pre-registered human-text study (n = 2,500
   Turkish + 1,500 English)? State what would have to be true for it to be enough.
4. **Presentation.** Title, abstract, structure, figure/table quality, length.
   Is anything missing that this journal requires (highlights, CRediT statement,
   data availability, competing interests, ethics)?
5. **Red flags.** Anything that would make you desk-reject: unverifiable numbers,
   citation padding, self-contradiction, missing ethics/consent, dual submission
   risk, LLM-generated text without disclosure.

---

## ROLE 2 — ADVERSARIAL REVIEWER (full technical review)

Write a standard review: **Summary → Strengths → Major concerns → Minor concerns
→ Recommendation** (reject / major revision / minor revision / accept).

Attack the work where it is weakest. Be specific: cite section numbers, table
numbers, and the exact sentence you object to. For every objection, state what
evidence would resolve it.

Interrogate at least these, and add your own:

**Statistical validity**
- Prompt-clustered bootstrap: is clustering on prompts the right unit? Are the
  intervals correctly constructed for a paired design?
- Degenerate AUROC = 1.000 cells with a Clopper–Pearson lower bound: is this
  defensible, or should the analysis be reformulated?
- Multiplicity: Holm over a family of 6, Bonferroni over 3. Were the families
  declared before seeing results, and is the correction adequate given how many
  comparisons appear across the whole paper?
- The empirical-vs-parametric false-positive estimates (~63× vs ~96×): is the
  choice of the empirical figure as primary correct, and is the parametric one
  presented with enough caution?
- n = 1,500 per language: what precision does that actually support? Is any
  claim in the paper finer than the data can carry?

**Causal and mechanistic claims**
- The proposed mechanism (prefix_length = 1 plus recurring suffix subtokens
  causing dependent green-list draws) is offered as a hypothesis. Is it kept
  hypothetical everywhere, including the abstract and discussion? Is there an
  experiment the authors could have run to test it that they did not?
- Is the variance inflation actually attributable to Turkish morphology, or
  could it be tokenizer-specific, corpus-specific, or an artifact of the
  windowing procedure?

**Experimental design**
- Five generator candidates were tested against a pre-registered gate and only
  one passed. Does that strengthen or weaken the generalization claim? Should
  the failed candidates be in the main text or an appendix?
- EXP generates fixed-length text and does not consume sampling parameters. Does
  this confound the cross-scheme comparison beyond what the authors admit?
- The laundering attack uses a closed, versioned commercial model. Is the result
  reproducible in any meaningful sense? Is the cost figure relevant or padding?
- The LLM-judge utility study: two judges, blind calibration pairs, one judge
  produced the laundered texts. Is the conflict-of-interest mitigation adequate?
  Would a human evaluation be required for this journal?

**Threats to validity the authors may have missed**
- Length confounds, register confounds, the windowing of human text, selection
  effects in which prompts were used, and anything else you can identify.

**Reporting**
- Does any number in the text contradict a number in a table or figure?
- Is any exploratory finding presented with the weight of a confirmatory one?
- Are the limitations complete, or is something material missing from them?

---

## ROLE 3 — CITATION AND REFERENCE AUDITOR

This is a mechanical audit. Be exhaustive and report findings as a table.

**A. Every in-text citation**
For each bracketed key in the body text: does it appear in the reference list?
Report orphans (cited but not listed) and unused entries (listed but not cited).

**B. Every reference entry**
For each entry, verify **from the DOI or a source you can actually check**:
- Do the authors, title, year, and venue match the DOI?
- Is the venue correct (preprint vs. published version; conference vs. journal)?
- Is the DOI well-formed and resolvable?
- For entries marked "no DOI" (a talk, software, a dataset): is that
  justification correct, or does a citable DOI exist?

The authors provide `paper/citation_verification.json` recording what they
checked. **Verify their verification.** They state that only bibliographic
identity was confirmed and that the papers' contents were not read. Judge
whether the in-text uses are consistent with that limitation.

**C. Citation appropriateness — the substantive check**
For each in-text use, ask whether the cited work actually supports the sentence.
Flag:
- citations that support a weaker claim than the sentence makes,
- citations used for a general area where a specific result is claimed,
- missing citations: places where a claim needs support and has none,
- any citation that appears to be padding.

Pay attention to the related-work section: is the coverage of multilingual and
cross-lingual watermarking adequate, or are there obvious omissions? Name any
paper you believe must be cited and is not.

**D. Verdict**
State whether the reference apparatus is publication-ready, and list every
required fix in priority order.

---

## OUTPUT FORMAT

Three clearly separated sections (`# EDITOR`, `# REVIEWER`, `# CITATION AUDIT`),
then a short final block:

```
BLOCKING ISSUES (must fix before submission)
1. ...

SHOULD FIX (reviewer will raise these)
1. ...

OPTIONAL
1. ...
```

Do not soften findings to be agreeable. If a claim is unsupported, say so
plainly and point at the sentence. If the paper is sound in a place a reviewer
would normally attack, say that too, so the authors know where they are safe.
