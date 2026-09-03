# Audit note: inferential treatments that were withdrawn

This note is the full record of statistical constructions that appeared in
drafts of *Watermarking Turkish LLM Output* and were withdrawn before
submission. It exists so that the manuscript can state the current rule
compactly without erasing the history, and so that a reader who finds one of
these quantities in an early preprint, in the `v1.1.0-paper` or
`v1.2.0-paper` archives, or in the git history can see exactly why it is gone.

Nothing described here is reported as a result. `pilot/dev_tutarlilik_kapisi.py`
fails the build if any of these quantities reappears in `paper/numbers.json`,
`results/detection_metrics.csv`, `results/dejenere_kanit.json`, or as a promise
in `paper/paper.md`.

## 1. The complete-separation cells: three withdrawals

Eleven of the 33 detection cells reach AUROC 1.000 with a bootstrap interval
that collapses to [1, 1]. A degenerate interval records that no counterexample
was observed, not that there is no uncertainty. Three successive attempts to
attach an inferential quantity to those cells were all withdrawn.

### (i) Clopper–Pearson lower bound — withdrawn

Read "zero failures in 24 clusters" as 24 Bernoulli successes and report the
one-sided 95% bound `alpha**(1/n) = 0.883` on AUROC.

**Why it is invalid.** Clopper–Pearson bounds the parameter of a binomial
proportion. AUROC is a pairwise-ranking U-statistic: by Bamber's identity it
equals `P(X⁺ > X⁻) + ½·P(X⁺ = X⁻)`, a probability over pairs drawn from two
samples, not a success proportion over trials. The probability of a
cluster-level event is therefore neither equal to nor a lower bound on the
population AUROC. Two further problems compound it: the 24 cluster events share
one pool of negatives and so are not independent trials, and the reporting is
conditional on degeneracy having been observed. The arithmetic was correct for
the quantity it computed; the quantity was not the one the sentence claimed.

Implemented as `auroc_alt_sinir_cp()` in `pilot/metrics.py`; removed, with the
reasoning kept as a comment at the former call site.

### (ii) Within-prompt label-exchangeability permutation — withdrawn

Treat the watermarked/clean labels as exchangeable inside each prompt, giving a
one-sided exact p of `(1/C(m+k, m))` per prompt and `10⁻⁴⁴·³` overall.

**Why it is invalid.** Exchangeability is not defensible for a scheme whose four
seeds are deterministic. EXP generates identically given prompt and key, so the
four "replicates" inside a prompt are not draws that could have been labelled
otherwise.

### (iii) Prompt-level sign test — withdrawn

Treat each prompt as one binary outcome — does its lowest watermarked score
exceed the maximum of the pooled clean negatives — and multiply, giving `2⁻²⁴`.

**Why it is invalid.** Two independent defects. The per-prompt success
probability of 0.5 is not derived from the design: the event is a comparison
against a pooled maximum, not a coin flip. And every prompt is compared against
the *same data-dependent comparator*, so the 24 outcomes share a common random
component and cannot be multiplied. The dependence is positive — when the
negative maximum happens to be small, all clusters separate together — so the
product can understate the true probability rather than being merely
conservative.

This one is instructive because it was introduced as a *fix* for (ii). Replacing
`10⁻⁴⁴·³` with `2⁻²⁴` corrected the wrong **unit** while keeping a wrong
**null**. The lesson recorded for future work: when repairing a test,
interrogate the unit and the null separately.

### What is reported instead

Descriptive evidence only, in Table 3 of the manuscript: the number of fully
separated prompt clusters (24/24 in all eleven cells), whether separation also
holds globally, and the margin in units of the clean-negative standard
deviation — which ranges from 0.72 (KGW, morph_v1) to 53.23 (EXP, clean) and so
shows that cells rounding to the same 1.000 are not equally secure.

A valid test here would have to permute labels at a unit whose exchangeability
can be argued and recompute the comparator inside every permutation. We did not
run one, and prefer a strong description to a p-value we cannot defend.

## 2. The D3 comparison: estimand corrected, not withdrawn

The within-scheme comparison of `launder_api` against `rtt` was run on the
**per-prompt mean raw detector statistic** in drafts through `v1.2.0-paper`.

That test is internally valid — within a scheme the detector scale is fixed —
but it estimates *mean detector-score displacement*, whereas the surrounding
prose and Table 5's own TPR columns describe *detection at the operating
threshold*. Code and text were answering different questions.

The comparison now runs on the per-prompt detection rate at each scheme's
clean-calibrated threshold (`pilot/metrics.d3_istem_duzeyi`). The conclusion
changes: under the corrected estimand the scheme that survives Bonferroni
correction is EXP, not KGW.

| Scheme | old p (raw statistic) | new p (detection rate, exact permutation) | Bonferroni α = 0.0167 |
|---|---|---|---|
| KGW | 0.0053 | 0.024 | was significant → now n.s. |
| EXP | 0.037 | 0.012 | was n.s. → now significant |
| SynthID | 0.019 | 0.415 | n.s. both ways |

The direction — laundering more destructive than translation — is consistent in
all three schemes under both estimands.

Because per-prompt rates over four seeds take only five values, zero differences
are common (6 to 11 of 24 pairs). The primary p is an exact paired sign-flip
permutation test, whose null does follow from the design: under exchangeability
of the two conditions *within a prompt*, the sign of the paired difference is
symmetric. Note the contrast with withdrawal (iii) above — there the pairing did
not exist and a single pooled comparator was shared; here each pair is a genuine
matched comparison. A Wilcoxon signed-rank test under Pratt's convention, which
ranks zero differences rather than discarding them, is reported alongside it.

## 3. Tables 5 and 6: inferential status narrowed, asymmetrically

Through `v1.5.0-paper` the article described both focused comparisons as
error-controlled tests: EXP "survives Bonferroni correction", four contrasts
were "Holm-significant", SynthID was "significantly more fragile". Section 3.3
of the same drafts already disclosed that the two conditions carried into those
comparisons, `rtt` and `launder_api`, were chosen after the aggregate attack
ranking of Table 4 had been inspected. Those two statements do not sit together:
an adjustment applied to the contrasts that survive a selection does not control
error across the selection itself.

The correction is a narrowing of claimed status, not a change to any number. It
is deliberately **asymmetric**, because the two tables are not equally exposed.

**Table 5 is exposed.** The ranking that selected the pair also ordered it,
placing `launder_api` above `rtt`. Table 5 then asks, within each scheme,
whether `launder_api` is the more destructive of exactly that pair. The
selection functional and the test functional are the same quantity, so the
p-values are selection-conditional. Table 5 is now labelled an exploratory
post-selection contrast; its decision column no longer reads "significant" and
"n.s." but records only whether the p-value lies below or above the displayed
family's α; and the effect sizes with their clustered intervals, which do not
depend on the ordering that drove the selection, are stated to be the primary
quantity. The p-values are retained rather than deleted.

**Table 6 is largely protected.** The ranking that selected the conditions
averages over schemes; Table 6 contrasts schemes within a condition. The
quantity that drove the selection is therefore not the quantity being tested,
and the two axes are different. The Holm adjustment over the six displayed
tests keeps its ordinary interpretation within them, and the table says so while
also stating that it carries no guarantee about the choice of the two conditions
it is computed in. Relabelling Table 6 "exploratory" was considered and
rejected: it would understate what was in fact controlled, since the six-test
family was fixed before any per-scheme result was seen.

An open question is recorded rather than resolved. An earlier, independent pilot
cohort (`results_pilot_gecersiz_20260821/`, not published) already ranks
`launder_api` (AUROC 0.847) below `rtt` (0.889) below `launder` (0.932). If the
pair was in fact chosen there, the selection and the analysis would rest on
different data and the objection to Table 5 would largely dissolve. That is a
claim about the order in which the author did things; it does not follow from
the timestamps, and it is not asserted here. The article states the conservative
reading, which is the one against its own interest.

**Provenance located (3 September 2026).** The open question above was answered from
the record, not from an attestation. The pilot report of an earlier cohort (generator
Qwen2.5-3B-Instruct, corpus failed the acceptance gate) states in its narrowed audit
claim that `rtt` and `launder_api` were the most destructive attacks; its files are
dated 15–18 August 2026 locally, the study corpus was generated on 20–21 August, and
the analysis code that fixes the pair was written on 23 August (`pilot/metrics.py`,
commit 4c597d0). The report, its detection table and its environment record are now
released as `audit/pilot_20260818/`. Because the designation preceded the study data,
Table 5's Bonferroni decision is again read as familywise within its three-scheme
family, with one limit stated in the paper: the record cannot show that Table 4, which
reproduced the pilot ordering, played no part in confirming the choice. The
"exploratory post-selection" label of `v1.5.0`–`v1.7.2` is withdrawn in favour of this
provenance statement; the asymmetry argument for Table 6 stands and is now moot.

## 4. A number that reached the manuscript without the pipeline

Table 6's first row was printed as p = 0.001 through `v1.5.0-paper`. The value
is 0.000322. Two mechanisms combined: `_md_table` formatted with a hardcoded
`{:.3f}` that silently overrode the `.round(4)` applied to the frame, so the
generator itself could not distinguish 0.0003 from 0.0012; and the value in the
manuscript had been copied from `results/summary.md`, a report nine days stale,
rather than from `paper/numbers.json`. The consequence was not only a wrong
digit but a collapsed ordering, two rows differing by a factor of about four
printed as the same number.

Both mechanisms are now closed. The scheme-comparison table renders at four
decimals, and `pilot/dev_tutarlilik_kapisi.py` compares every cell of Tables 5
and 6 against `numbers.json` positionally rather than searching the manuscript
for a bare substring. The gate's earlier p-check would pass whenever a
three-digit string occurred anywhere in a 116 KB document.

## 5. Where these appeared

| Quantity | Last release containing it | Status |
|---|---|---|
| `ci_lo_cp` = 0.883 | `v1.2.0-paper` | removed from all production artifacts |
| `log10_p_tam_permutasyon` = −44.28 | `v1.2.0-paper` | removed |
| `log10_p_isaret_cevirme` = −7.22 | `v1.2.0-paper` | removed |
| D3 p from raw statistics | `v1.2.0-paper` | replaced by detection-rate estimand |
| Confirmatory reading of Tables 5–6 | `v1.5.0-paper` | narrowed in v1.5.0; Table 5 restored to within-family decision in v1.8.0 on pilot-cohort provenance (`audit/pilot_20260818/`) |
| Table 6 row 1 printed as p = 0.001 | `v1.5.0-paper` | corrected to 0.0003 |

The `v1.1.0-paper` and `v1.2.0-paper` Zenodo archives retain their DOIs and are
not deleted; a DOI should not silently change what it points to. Neither should
be used to reproduce the submitted article.
