# Watermarking Turkish LLM Output: Detector Calibration, Scheme Fragility, and a Released Evaluation Benchmark

**Corresponding author:** Ali Çetinkaya, Department of Computer Engineering,
Faculty of Technology, Selçuk University, Alaeddin Keykubat Campus, 42075
Selçuklu, Konya, Türkiye. E-mail: ali.cetinkaya@selcuk.edu.tr ·
Tel: +90 332 241 11 02 · ORCID: 0000-0002-7747-6854

## Abstract

Statistical watermarks for large language model (LLM) output are designed and evaluated predominantly on English. We measure three schemes (KGW, EXP, SynthID) on Turkish with MarkLLM and Qwen3-14B: 384 generated texts under ten removal attacks, a pre-registered false-positive study on 4,000 human windows, and a two-judge meaning-preservation study. First, KGW's detector is miscalibrated on human text: its null standard deviation is 1.479 against a theoretical 1, and the shipped z = 4 threshold gives 3 exceedances in 1,500 windows, about 63 times nominal (exact interval 13 to 184). The inflation holds across eight keys though the tail count does not (3 to 143), and it is not Turkish-specific: English shows the same tail count, and at matched token length the two are indistinguishable. Turkish contributes exposure, not mechanism: its subword fertility turns a given reading length into twice as many tokens, and inflation grows with tokens scored. Second, the best-behaved detector is the most fragile: at its own shipped threshold SynthID flags none of the 1,500 human windows against KGW's 3 and EXP's 13, yet loses the most AUROC under both attacks. With three schemes this is an observed pattern, not a trade-off. Third, laundering through an external LLM is the only attack that both degrades detection for all three schemes and preserves meaning, though meaning was judged on KGW text. A planned morphological attack did not fire; we report it with its coverage and release the corpus, scores and judge annotations.

**Keywords:** LLM watermarking; Turkish; detector calibration; false-positive rate; subword fertility; evaluation benchmark

## 1 Introduction

Statistical watermarking embeds a detectable but, ideally, quality-neutral signal into the sampling process of a large language model, so that a detector holding the key can later test whether a given text was produced by the watermarked model. The main scheme families are logit-biasing green-list watermarks (Kirchenbauer et al., 2023), distortion-free Gumbel-sampling watermarks (Aaronson, 2023; Aaronson & Kirchner, 2022; Kuditipudi et al., 2024), and tournament-sampling SynthID, which has been deployed at scale (Dathathri et al., 2024). In all three, detection is a hypothesis test: the detector computes a statistic whose distribution on unwatermarked text is assumed known, and a threshold (for KGW, a z-score threshold) is chosen for the false-positive rate that this null implies. The practical value of a watermark rests on that calibration. If the null distribution on real, unwatermarked text is wider than assumed, the advertised false-positive rate is wrong, and every downstream decision that consumes the detector's verdict (academic-misconduct cases, provenance labeling, content-policy enforcement) inherits the error.

These schemes were developed and are evaluated mostly on English (Al Ghanim et al., 2025; He et al., 2024). Turkish differs from English in a way that plausibly reaches into watermark internals: it is agglutinative, expressing through chains of suffixes what English expresses through separate function words. Under a subword tokenizer these suffixes surface as a small set of high-frequency subtokens; on our corpus the generator's tokenizer produces 2.552 tokens per word. For a green-list scheme whose pseudo-random vocabulary partition is keyed on a context window of a single preceding token (prefix_length = 1, the MarkLLM default configuration we test), recurring suffix subtokens mean that successive green-list decisions revisit the same partitions rather than behaving independently. We put this forward as a proposed mechanism for the calibration results below; we explicitly do not claim to have established it causally.

This paper reports a pilot-scale but tightly instrumented measurement of the three schemes on Turkish. Using MarkLLM (Pan et al., 2024) at a fixed commit (c45ddc40) with Qwen3-14B (Yang et al., 2025) as generator, we build a corpus of 24 Turkish prompts × 4 seeds × {no watermark, KGW, EXP, SynthID} = 384 texts and subject it to ten removal attacks: diacritic stripping at two intensities, two morphological-transform variants built on the zeyrek analyzer (Bulat, 2022) together with their diacritic combinations, round-trip translation through English with NLLB (NLLB Team et al., 2024), self-paraphrase and self-laundering by the generator itself, and laundering through an external, closed-weight LLM outside the defender's control (Claude Opus 5). Two studies were pre-registered before their data were collected. We use that term in
a specific and limited sense throughout, and Section 7 gives the full statement: the
hypotheses, protocol and decision rule were committed to version control before the
corresponding data existed, and the commit hashes bind their content and ordering, but
no independent third-party timestamp anchors the dates, so this is not a registry
entry in the sense the term carries in clinical or psychological research. The two
studies are: S1 measures false-positive rates on 1,500 Turkish and 1,500 English human-written Wikipedia excerpts (Wikimedia Foundation, 2023a) (commit 8f8df72), and S2 measures whether attacks preserve meaning, using two LLM judges from different model families, blind calibration pairs, and a decision rule declared before the run (commit cbcb988); corpus acceptance thresholds were fixed before Phase 1. The measurement protocol takes the corpus's dependence structure seriously: because EXP is deterministic given prompt and key, its four seeds are not independent replicates, so all confidence intervals are prompt-clustered bootstrap intervals (effective n = 24 prompts); for degenerate AUROC = 1.000 cells we report counted separation, its margin, and an exact permutation p-value rather than the Clopper–Pearson bound an earlier version of this analysis used and Section 3.3 withdraws; and we report the full realized false-positive table rather than assuming that a threshold calibrated on clean negatives keeps its nominal rate under attack.

The headline finding is a calibration failure. On human Turkish, the KGW null standard deviation is 1.479 against a theoretical value of 1; at the shipped z = 4 threshold, 3 of 1,500 Turkish excerpts cross the line, an empirical false-positive rate of 0.002 or approximately 63× the nominal 3.17 × 10⁻⁵, with an exact binomial interval spanning 13× to 184×. Two of the three pre-registered S1 hypotheses are confirmed. The third, which attributed the inflation to Turkish rather than to English, does not survive a control for sequence length that we added after pre-registration and that we report in full: matched on tokens rather than words, the two languages are indistinguishable, and the inflation tracks how many tokens are scored. Turkish still matters in deployment, because its subword fertility turns a given reading length into roughly twice as many tokens, but it worsens a failure common to both languages instead of creating a Turkish-specific one. An exploratory analysis further indicates that thresholds calibrated on model-generated negatives do not transfer to human text: EXP's model-calibrated 1% threshold yields a 7.4% false-positive rate on human Turkish. The second finding is a fragility pattern: SynthID falsely flags none of the 1,500 human Turkish windows at its own shipped threshold, fewer than KGW (3) or EXP (13), yet is the most fragile scheme under attack, with AUROC 0.816 under round-trip translation and 0.747 under external laundering, and is significantly more fragile than KGW or EXP in 4 of 6 Holm-corrected paired comparisons. The third finding is the laundering attack: rewriting watermarked text through an external model outside the defender's control is the only attack that satisfies the pre-declared success rule (ΔAUROC > 0.05 with meaning preserved by both judges) for all three schemes, dropping AUROC to 0.917 (KGW), 0.863 (EXP), and 0.747 (SynthID), and the true-positive rate at the clean-calibrated threshold to 0.427, 0.490, and 0.250. Averaged over schemes, laundering removes 0.158 AUROC versus 0.091 for round-trip translation, at a measured API cost of USD 17.704 for the attack corpus.

We also report a negative result plainly, because the study was originally motivated by the conjecture that Turkish morphology itself would furnish a meaning-preserving removal attack. It does not, on this corpus. The v0 morphological transform averages 1.1 edits per text and leaves 60.4% of texts untouched, with a mean AUROC change of 0.000; the more aggressive v1 variant reaches 7.5 edits per text, but its apparent per-edit effect on the detection statistic is retracted after robustness testing (the bootstrap confidence interval includes zero, the Spearman correlation is non-significant, and the sign flips when the three highest-leverage points are removed). The v0 per-edit slope (+0.052 z per edit) survives the same tests but is practically negligible against a clean-text baseline z of 11.467. The proximate cause is coverage: the formal register that Qwen3-14B produces rarely contains the -Iyor progressive forms the transforms target. Whether informal-register Turkish is more vulnerable is an open question, not a finding of this paper.

The remainder of the paper is organized as follows. Section 2 reviews related work. Section 3 describes corpus construction (including the transparent prompt-length calibration), the attack suite, and the measurement protocol. Section 4 presents results: clean-text detection, the attack ordering, the S1 calibration study, and the S2 utility study. Section 5 discusses practical consequences and the threat model. Section 6 lists limitations in full, including the single generator model and single GPU environment, and Section 7 states the reproducibility provisions. In sum, this paper makes the following contributions:

1. **Calibration failure on human text, measured on Turkish (pre-registered; commit 8f8df72).** The KGW detector's null distribution on human Turkish has standard deviation 1.479 against a theoretical 1, and the default z = 4 threshold produces an empirical false-positive rate of 0.002 (3/1,500), approximately 63× nominal (exact interval 13×–184×). The inflation holds under all eight watermark keys we swept, though the tail count ranges from 3 to 143 across them, so the headline figure is the most conservative of the eight. Controlling for token length shows the effect is not Turkish-specific but length-driven, with Turkish exposed further along the same curve through subword fertility. An exploratory follow-up shows that thresholds calibrated on model-generated negatives reach up to 7.4% FPR on human text. Default thresholds are portable neither across negative distributions nor across document lengths.
2. **The best-calibrated detector is the most fragile.** At its own shipped threshold SynthID falsely flags none of the 1,500 human Turkish windows, against 3 for KGW and 13 for EXP, but it takes the largest attack losses (AUROC 0.816 under round-trip translation, 0.747 under laundering), and is significantly more fragile in 4 of 6 Holm-corrected paired comparisons (test family specified before the per-scheme results were inspected); no significant fragility difference between KGW and EXP is found.
3. **The laundering attack (utility axis pre-registered; commit cbcb988).** Rewriting through an external LLM is the only attack among ten whose detection damage clears the pre-declared threshold for all three schemes: AUROC falls to 0.917/0.863/0.747 and TPR at the clean-calibrated threshold to 0.427/0.490/0.250 for KGW/EXP/SynthID, at a measured attack cost of USD 17.704. The utility half of the rule is established only for KGW, because every judged pair was drawn from the KGW arm; meaning was preserved in 1.00 of those pairs under both judges. Extending the verdict to EXP and SynthID assumes that meaning preservation transfers across arms, and we mark it as an assumption rather than a measurement.
4. **A documented negative result and a disciplined measurement protocol.** The planned Turkish morphological attack does not fire on formal-register model output (1.1 edits per text on average; 60.4% of texts unchanged; ΔAUROC 0.000), and the morph_v1 per-edit slope is retracted after robustness testing. Every reported number regenerates from data via code; confidence intervals are prompt-clustered; degenerate cells report counted separation with an exact permutation p-value; exploratory observations are labeled as exploratory; and where a later control overturned a pre-registered conclusion we report the reversal rather than the original.
## 2 Related Work

Three families of decoding-time watermarks dominate current practice. The green-list scheme of Kirchenbauer et al. (2023) pseudorandomly partitions the vocabulary at each step using a hash of the preceding context and adds a bias delta to the logits of "green" tokens; detection is a one-proportion z-test whose null model treats successive green/red outcomes as independent Bernoulli trials with parameter gamma. The exponential-minimum (Gumbel-trick) approach proposed by Aaronson and Kirchner (2022; see also Aaronson, 2023) couples token selection to a pseudorandom sequence keyed on the context, leaving the sampling distribution unchanged in expectation; Kuditipudi et al. (2024) develop distortion-free variants of this idea with robustness guarantees for the detector. SynthID (Dathathri et al., 2024) modifies sampling through a tournament procedure and has been deployed at production scale. All three report detection behavior primarily on English text, and the calibration of their detection thresholds (the mapping from a score threshold to a false-positive rate on unwatermarked text) inherits distributional assumptions that were validated, where they were validated at all, on English.

Watermark evaluation already has benchmarks, and this paper is not the first. WaterBench (Tu et al., 2024) equalises watermark strength before comparing schemes and evaluates generation and detection across nine tasks; Mark My Words (Piet et al., 2025) scores schemes on quality, the number of tokens needed for detection, and tamper resistance; and WaterPark (Liang et al., 2025) assembles ten watermarkers against twelve attacks in one platform. All three are cross-scheme and English-centred, and all three calibrate against model-generated negatives. What we add is orthogonal to their axes: a human-written negative distribution in a language none of them covers, together with register, token-length and watermark-key controls on that distribution. Our contribution is therefore language- and negative-distribution-specific, not a more general benchmark.

We build on the MarkLLM toolkit (Pan et al., 2024), which provides reference implementations and detectors under a common interface; its published version documents the KGW and Christ families, and SynthID was added to the repository afterwards, so all three of our schemes are taken from the pinned repository state rather than from the paper; all experiments pin MarkLLM commit c45ddc40 so that scheme behavior is reproducible at the code level.

A separate line of work studies robustness of watermarks to post-hoc text transformations, in particular paraphrasing and translation (He et al., 2024; Krishna et al., 2023; Sadasivan et al., 2025). Our laundering attack belongs to this family: it routes watermarked text through a rewriting model. We distinguish self-laundering (the generator rewrites its own output) from laundering through an external model, and we evaluate both under a pre-registered decision rule that requires meaning preservation, not only detection loss.

Work on watermarking outside English is thin but no longer absent, and most of it is recent: cross-lingual consistency of the watermark signal under translation (He et al., 2024), robustness under real-world cross-lingual manipulation (Al Ghanim et al., 2025), a linguistics-aware scheme that modulates watermark strength by syntactic predictability and is evaluated on analytic English, isolating Chinese and agglutinative Korean (Park et al., 2026), a back-translation search that restores watermark strength in medium- and low-resource languages and traces the failure it repairs to tokenizers with too few whole-word tokens (Mohamed & Gubri, 2025), and a cross-lingual fairness audit over six schemes and eleven languages, Turkish among them (Nemecek et al., 2026). Two things that literature does not yet supply are a null distribution measured on human text and an agglutinative language other than Korean under typological scrutiny. Turkish is a stress case for the assumptions above: it is agglutinative, with long suffix chains governed by vowel harmony, and subword tokenizers over-segment it relative to English: Rust et al. (2021) report that mBERT's subword fertility and its proportion of words split into more than one subword are both far higher for Turkish than for English. Whether that over-segmentation also makes particular suffix subtokens recur often enough to disturb a watermark's null model is a separate question, which Section 4.3 measures rather than assumes. Repeated suffix subtokens provide a candidate mechanism for interaction with context-hash schemes such as KGW when the hashing window is short. Morphological analysis for Turkish is available through the zeyrek analyzer (Bulat, 2022), an alpha-stage partial port of Zemberek, which we use to build a morphological attack and, in the re-inflection variant only, to check that the edited form still parses to the same lemma. That check certifies word-level morphological analyzability, not sentence-level grammaticality; Section 3.2 states the limit and the subordinate-clause variant carries no analyzer check at all. What the closest antecedent calibrates against, however, is model output: the null sets of Nemecek et al. (2026) are matched-prompt unwatermarked generations. We are aware of no published measurement of watermark detector calibration on Turkish text *written by humans*, the negative class a deployed detector actually screens and one that Section 4.3 shows model negatives do not stand in for, since a threshold set to 1% false positives on model negatives realizes 7.4% on human Turkish. Sections 4–5 report one.
## 3 Methods

### 3.1 Corpus construction

The generation corpus crosses 24 Turkish prompts with 4 sampling seeds and 4 arms (no watermark, KGW, EXP, and SynthID) for 384 texts, 96 per arm. The prompt file is content-addressed (SHA-256 prefix 8fcbe4074b46); prompts cover expository topics and request essays of at least 500 words. The generator is Qwen3-14B (Yang et al., 2025) in fp16 on a Quadro RTX 8000 (Turing), driven through MarkLLM commit c45ddc40 (Pan et al., 2024). Sampling uses temperature 0.8, top_p 0.95, top_k 20, repetition penalty 1.0, max_new_tokens 1800, and min_new_tokens 400. Two implementation details matter for cross-scheme comparability: SynthID applies temperature inside its own logits processor, so the Hugging Face temperature is disabled for that arm to avoid applying temperature twice and keep the effective temperature equal across schemes; and the SynthID processor state is reset before every generation, since the toolkit otherwise carries state across samples and makes output depend on generation order. Bit-identical regeneration under fixed seeds was verified on the target GPU; this is a single-environment reproducibility statement, not a portability claim.

Scheme configurations follow the toolkit defaults: KGW uses gamma 0.5, delta 2.0, prefix_length 1, and detection threshold z = 4 (Kirchenbauer et al., 2023); EXP (Aaronson, 2023; Aaronson & Kirchner, 2022) generates a fixed sequence_length of 950 tokens, does not consume the sampling kwargs above, and never stops at an end-of-sequence token; SynthID (Dathathri et al., 2024) uses the mean detector without a trained scoring layer.

Prompt calibration is reported transparently because it is easy to misread as threshold tuning. In a preflight run whose prompts requested at least 300 words, the model delivered a median of 244 words, below the acceptance criterion; with prompts requesting at least 500 words, the median rose to 364. The prompts were therefore recalibrated to request 500 words, while the acceptance criterion itself stayed at 300 words: it was fixed, together with all corpus acceptance thresholds, before Phase 1 and before any corpus data was seen (pre-registered in the repository). What was calibrated is the instruction, not the bar. Measured tokenizer fertility on this corpus is 2.552 tokens per word, so the 1800-token budget covers the 300-word criterion with a wide margin.

The pre-registered acceptance thresholds are: at least 300 words per text with corpus-level compliance of at least 0.75; terminal punctuation at the end of at least 0.90 of texts; and non-Latin-script contamination in at most 0.05 of the corpus (above which the quality layer is retracted). The realized corpus passes all three (Table 1): 375/384 texts (97.7%) meet the word criterion, and 283/288 (98.3%) end in terminal punctuation. EXP is structurally exempt from the termination criterion (it emits a fixed-length sequence by design and cannot stop at a sentence boundary), so its 96 texts are removed from that denominator (hence 288). The 0.90 and 0.05 values were fixed before the data but are not externally justified; no sensitivity analysis was run (see Limitations).

**Table 1.** Corpus statistics per arm.

| arm | n | median words | median tokens | non-Latin contaminated | at 1800-token ceiling |
|---|---|---|---|---|---|
| no watermark | 96 | 365 | 935 | 2 | 0 |
| KGW | 96 | 382 | 983.5 | 8 | 2 |
| EXP | 96 | 376 | 947 | 0 | 0 |
| SynthID | 96 | 371.5 | 950.5 | 9 | 2 |

The pooled contamination rate stays below the 0.05 ceiling, so the quality layer is retained; the per-arm contamination counts and the four ceiling-truncated texts are revisited in the Limitations. The token-length standard deviation of the EXP arm is 1.5 tokens (versus three-digit values in the other arms), the signature of its fixed-length design; token counts are logged per text so that length can be inspected as a confounder in every analysis.

### 3.2 Attacks

Ten transformations are applied to every positive text and, in parallel, to every negative text (the attacked negatives feed the false-positive analysis of Section 3.3). All attacks are seeded for reproducibility.

Diacritic stripping maps the Turkish-specific characters ç, ğ, ı, ö, ş, ü (and uppercase forms) to their ASCII counterparts: dia100 converts every occurrence; dia50 converts each occurrence independently with probability 0.5, imitating informal keyboard usage. The morphological attacks generate candidate edits by rule. The re-inflection transform accepts an edit only if the zeyrek analyzer (Bulat, 2022) re-parses the result to the same lemma; the subordinate-clause alternation is a purely regular substitution with no analyzer check, although its edits are counted the same way. Same-lemma reparsing is a filter, not a guarantee of grammaticality or of preserved meaning, and we did not validate the edits with human annotators. The transforms are: morph (v0) applies a progressive-to-formal re-inflection (-Iyor to -mAktAdIr) and a subordinate-clause alternation; morph_v1 additionally drops copular suffixes, raising coverage. Measured coverage is low by construction of the register the model produces: morph makes a mean of 1.14 edits per text with 60.4% of texts receiving zero edits; morph_v1 makes 7.52 edits per text with 4.2% zero-edit texts. The combinations morph+dia and morph_v1+dia compose each morphological attack with full diacritic stripping. rtt is round-trip translation Turkish–English–Turkish with NLLB-200-distilled-600M (NLLB Team et al., 2024), translated sentence by sentence. para and launder are self-rewrites by the generator itself with the watermark processor disabled: para instructs a light paraphrase preserving sentence order, launder a complete rewrite "in your own sentences", a zero-cost laundering model. launder_api is real laundering through an external LLM outside the defender's control (Claude Opus 5) via its API; we call it external rather than stronger, because we ran no benchmark that would license a capability ordering; its measured generation cost for the full corpus was USD 17.704, a figure we report because attack economics are part of the threat model.

Because rewriting attacks can shorten text, and detector statistics scale with length (for KGW the z-score grows roughly with the square root of token count), any detection loss could in principle be a length artifact. We therefore report the attacked-to-source token-length ratio for the rewriting attacks, computed on the KGW-watermarked arm: para has median ratio 0.992 (minimum 0.669), rtt 0.899 (minimum 0.781), and launder_api 0.976 (minimum 0.541). Pooled over all four arms the minima are lower, 0.321 for rtt and 0.146 for launder_api, both occurring in the SynthID arm, so the reassurance the medians provide is weaker in the tail than these three numbers alone suggest. The most damaging attack, launder_api, barely shortens text at the median, and rtt shortens it by about 10%; under square-root scaling this bounds the length contribution well below the observed drops, so shortening cannot account for the bulk of the effects reported in Section 4. An earlier pilot version of the rewrite attacks had a fixed output cap that halved text length and would have manufactured exactly this artifact; the cap is now derived from the generation budget, and we flag the episode as a caution for replication.

### 3.3 Detection measurement

The primary metric is AUROC of the detector statistic, computed per scheme and condition from the 96 attacked positives against the 96 clean negatives. Confidence intervals come from a nonparametric bootstrap that resamples prompts, not rows. Analytic intervals for this estimand exist (Newcombe, 2006), but they assume independence within each class and lose their coverage precisely at the boundary values that the degenerate cells of Table 3 occupy, so we resample throughout and, for those cells, report counted evidence in place of an interval. The rationale is an audit finding: EXP derives its pseudorandom key from the final prompt token(s) rather than from the torch generator, so under deterministic transformations its four seeds produce identical outputs; the four "replicates" are one measurement, and the effective number of independent units is the 24 prompts. Row-level resampling would understate uncertainty for EXP; prompt-clustered resampling is applied to all three schemes because the inferential target throughout is generalization to new prompts, not new samples of the same prompts.

Eleven cells reach AUROC 1.000 with a degenerate bootstrap interval of [1, 1]. A degenerate interval does not mean the absence of uncertainty; it means no counterexample was observed. An earlier version of this analysis attached a one-sided Clopper–Pearson lower bound to these cells, reading "zero failures in 24 clusters" as 24 Bernoulli successes and reporting a bound of 0.883 on AUROC. We withdraw that construction. Clopper–Pearson bounds the parameter of a binomial proportion, whereas AUROC is a pairwise-ranking U-statistic: by Bamber's identity (Bamber, 1975) it equals P(X⁺ > X⁻) + ½·P(X⁺ = X⁻), a probability over pairs drawn from two samples rather than a success proportion over trials. The probability of a cluster-level event is therefore neither equal to nor a lower bound on the population AUROC, and the 24 cluster events are not independent trials because they share one pool of negatives and because the reporting itself is conditional on degeneracy having been observed. The arithmetic was correct for the quantity it computed; the quantity was not the one the sentence claimed.

In place of that bound we report the separation directly, counted rather than assumed (Table 3). In all eleven degenerate cells every one of the 24 prompt clusters separates completely, and separation also holds globally: the lowest watermarked statistic exceeds the highest of the 96 clean negatives. We report the width of that gap in units of the negative standard deviation, because it differs by nearly two orders of magnitude across schemes and reporting the cells as interchangeable would obscure that. The margin is 53.23 negative standard deviations for EXP on clean text but only 0.74 for KGW, so KGW's perfect separation is far more precarious than EXP's even though both round to AUROC 1.000. We attach no p-value to this separation, and the reason is worth stating because two
earlier versions of this analysis did. A within-prompt label-exchangeability test
gives 10⁻⁴⁴·³, but exchangeability is not defensible for a scheme whose four seeds
are deterministic. Treating each prompt as one binary outcome and applying a sign
test gives 2⁻²⁴, but that is arithmetic rather than a test: the per-prompt success
probability of 0.5 is not derived from the design, and every prompt is compared
against the same data-dependent comparator, the maximum of the pooled clean
negatives, so the 24 outcomes share a common random component and cannot be
multiplied. We therefore report the separation descriptively: the count of separated
clusters, the margin in units of the negative standard deviation, and the underlying
score distributions. A valid inferential test here would have to permute labels at a
unit whose exchangeability can be argued and recompute the comparator inside every
permutation; we did not run one, and we prefer a strong description to a p-value we
cannot defend.

The operating-point metric is named honestly. A detection threshold is set on the clean negatives at their 1% false-positive point, and we report the true-positive rate at this clean-calibrated threshold, not "TPR at 1% FPR", because under attack the negatives are transformed too and the realized false-positive rate at that threshold is an empirical question. We answer it directly: the full 33-cell table (3 schemes by 11 conditions, the untransformed clean reference included) of realized FPR at that threshold on the corresponding negatives is reported, with one-sided binomial comparisons against the nominal rate under Bonferroni correction across the 33 cells. Those comparisons treat the 96 attacked negatives in a cell as independent, which they are not: they are four per prompt across 24 prompts, and the threshold is itself estimated from the 96 clean negatives. We therefore read the table descriptively and do not rest any conclusion on its cell-level significance. At n = 96 the FPR resolution is 1/96, which motivates Study S1 (Section 3.4). As a robustness check we also report the same-transformation AUROC, in which both classes are transformed; this is ecologically meaningful for diacritic stripping and round-trip translation (which occur in natural text) but not for laundering (no one launders human text to remove a watermark), so the headline remains the clean-negative AUROC.

Cross-scheme comparisons never compare raw statistics, whose scales are incommensurable; the unit is the per-prompt detection rate at each scheme's own clean-calibrated threshold. The test family was specified before the per-scheme results were inspected: {rtt, launder_api} crossed with the three scheme pairs, six paired Wilcoxon tests at prompt level (n = 24), Holm-corrected. Within each scheme, rtt and launder_api are compared by prompt-level paired Wilcoxon with Bonferroni correction across the three schemes (α = 0.05/3 ≈ 0.0167); row-level McNemar tests are retained only descriptively because they violate the independence structure identified above.

### 3.4 Study S1: false-positive rate on human text

S1 asks whether the detectors flag unwatermarked human Turkish, and whether the effect is specific to Turkish. It was pre-registered (commit 8f8df72) before any human-text data was collected, with three hypotheses: H1, the KGW null standard deviation on human Turkish exceeds 1 (the variance inflation seen on model negatives is not an artifact of model text); H2, the inflation on a matched English sample is smaller than on Turkish; H3, EXP and SynthID nulls show no comparable inflation (SynthID's null standard deviation predicted ≈ 0.003). The registered motivation came from the 96 model negatives: the KGW null there has mean 0.012 and standard deviation 1.313, placing the shipped threshold z = 4 (nominal one-sided false-positive rate 3.17 × 10⁻⁵ under the N(0,1) null (Kirchenbauer et al., 2023)) only 3.04 standard deviations from the observed mean.

The sample is drawn from the Wikipedia dump of 2023-11-01 (Wikimedia Foundation, 2023a): random Turkish articles and a matched English set, one contiguous window per article, length-matched to the generation corpus, never cut mid-sentence, with page identifiers recorded for exact re-retrieval. The pre-registration targeted at least 1000 documents per language; the achieved n is 1500 per language. All three detectors run with model=None; we verified in the toolkit source that all three detection statistics are model-free, so scoring human text requires no generator. For each scheme and language we report the null mean and standard deviation, the observed FPR at the shipped configuration threshold, and the observed FPR at the threshold calibrated to 1% on the model negatives of Section 3.1 (testing whether model-derived calibration transfers to human text). The primary quantity is the empirical exceedance count; a Gaussian parametric estimate is reported only as an approximation, since H1 itself implies the parametric form is wrong. At n = 1500 the study resolves order of magnitude, not tenths of a percent; the single-register (encyclopedic) scope is a stated limitation.

### 3.5 Study S2: meaning and fluency under attack

An attack that destroys the text is destruction, not evasion. Embedding cosine similarity under multilingual E5 (Wang et al., 2024) cannot make this distinction (it scores destructive and benign edits alike near the ceiling), so S2 measures utility with pairwise LLM judging. The protocol was pre-registered (commit cbcb988) before the run, including the decision rule: an attack counts as successful only if (i) its AUROC drop exceeds 0.05 and (ii) the judges rule meaning preserved.

Judging is pairwise only (original versus attacked), never pointwise, because a pointwise pilot pinned all scores to the scale floor. The conditions are rtt, para, launder, and launder_api, sourced from KGW positives; each condition contributes 40 unique pairs, every pair presented in both orders, giving 80 ordered presentations but 40 independent pair units per condition per judge; the inferential unit is the pair, and the two orders are a repeated measure used to detect position bias. Blind calibration items are interleaved with the real pairs: identical pairs, where the expected verdict is a tie, and different-prompt pairs, where the expected verdict is meaning-not-preserved; both calibration sets were passed. EXP texts are excluded from calibration material because of the seed-duplication issue of Section 3.3.

Two judges are used, deliberately from different model families: Claude Opus 5 and gpt-oss-120b (served via Groq). The design breaks a conflict of interest: the launder_api texts were produced by Opus 5, so a meaning or fluency verdict on them from Opus 5 alone would be self-grading, and Panickssery et al. (2024) show that LLM evaluators recognize and favor their own generations, which makes the conflict a measured bias rather than a merely theoretical one; the pre-registration therefore requires agreement of both judges for any launder_api verdict, and fluency conclusions are drawn only from the independent judge. Position bias is a documented failure mode of pairwise LLM judging rather than a hypothetical one: Zheng et al. (2023) show that LLM judges change their verdict when the two candidates are swapped. Position-flip rates (verdict changes when pair order is reversed) are therefore reported per condition as a reliability measure, with a pre-registered acceptance bound of 30%; where flip rates exceed it, the corresponding dimension is reported as indistinguishable rather than as a difference in either direction. Measured judging cost for the Opus 5 judge was USD 7.021.
## 4 Results

### 4.1 Detection on clean text

On clean, unmodified Turkish output, all three schemes separate watermarked from unwatermarked text completely: AUROC is 1.000 for KGW, EXP, and SynthID (Table 2, first row), scored with each scheme's own MarkLLM detector (Pan et al., 2024) under the prompt-clustered bootstrap of Section 3.3 (24 clusters). These cells are degenerate: the bootstrap interval collapses to [1.000, 1.000], which reflects the absence of counterexamples in the sample, not the absence of uncertainty. Section 3.3 explains why we report counted separation and an exact permutation p-value for these cells instead of the Clopper–Pearson bound used in an earlier version, and Table 3 gives them. The separation behind these cells differs sharply in scale. KGW's (Kirchenbauer et al., 2023) mean z-statistic is 10.550 on watermarked text against 0.012 on clean negatives; EXP's (Aaronson, 2023; Aaronson & Kirchner, 2022) mean statistic is 55.883 against 0.446; SynthID's (Dathathri et al., 2024) mean detector score (untrained mean detector) is 0.535 against 0.501. Raw statistic scales are not comparable across schemes, but the narrow absolute margin of the SynthID mean detector foreshadows its behavior under attack (Section 4.2). The true-positive rate at each scheme's clean-calibrated threshold (set at nominal 1% FPR on clean model negatives) is 1.000 for all three schemes.

**Table 2.** AUROC (watermarked positives vs. clean negatives) for all 11 conditions, per scheme. Brackets give prompt-clustered bootstrap 95% CIs (n = 96 texts, 24 clusters per cell). † marks degenerate cells (bootstrap CI [1.000, 1.000]); Table 3 reports their counted separation, margin, and exact p-value in place of the Clopper–Pearson bound withdrawn in Section 3.3. Attacks: dia50/dia100 = diacritic stripping (50%/100%); morph/morph_v1 = morphological transforms via zeyrek (Bulat, 2022); rtt = NLLB round-trip translation TR→EN→TR (NLLB Team et al., 2024); para/launder = self-paraphrase by the generator (Yang et al., 2025); launder_api = laundering through an external LLM.

| Condition | KGW | EXP | SynthID |
|---|---|---|---|
| clean | 1.000† | 1.000† | 1.000† |
| dia50 | 0.999 [0.996, 1.000] | 1.000† | 0.996 [0.989, 0.999] |
| dia100 | 0.994 [0.986, 0.999] | 0.983 [0.946, 1.000] | 0.929 [0.887, 0.963] |
| morph | 1.000† | 1.000† | 1.000† |
| morph+dia | 0.994 [0.986, 0.999] | 0.982 [0.944, 1.000] | 0.926 [0.884, 0.960] |
| morph_v1 | 1.000† | 1.000† | 1.000† |
| morph_v1+dia | 0.993 [0.984, 0.999] | 0.982 [0.945, 1.000] | 0.923 [0.882, 0.958] |
| para | 0.998 [0.995, 1.000] | 1.000† | 0.998 [0.994, 1.000] |
| launder | 0.999 [0.996, 1.000] | 0.997 [0.990, 1.000] | 0.981 [0.955, 0.997] |
| rtt | 0.954 [0.926, 0.979] | 0.956 [0.896, 0.998] | 0.816 [0.758, 0.870] |
| launder_api | 0.917 [0.865, 0.956] | 0.863 [0.790, 0.924] | 0.747 [0.650, 0.834] |

**Table 3.** Complete separation in the eleven cells with AUROC 1.000, replacing the withdrawn Clopper-Pearson bound. Clusters are the 24 prompts; a cluster is counted as separated only if every watermarked score in it exceeds the maximum of all 96 clean negatives. Margin is that gap in units of the negative standard deviation. "Global separation" records whether the lowest watermarked score in the cell exceeds the maximum of all 96 clean negatives. No p-value is attached: as Section 3.3 explains, the 24 cluster outcomes are compared against a single data-dependent comparator and cannot be treated as independent Bernoulli trials.

| Scheme | Condition | Clusters separated | Margin (negative SD) | Global separation |
|---|---|---|---|---|
| EXP | clean | 24/24 | 53.23 | yes |
| EXP | dia50 | 24/24 | 4.74 | yes |
| EXP | morph | 24/24 | 53.23 | yes |
| EXP | morph_v1 | 24/24 | 51.30 | yes |
| EXP | para | 24/24 | 8.87 | yes |
| KGW | clean | 24/24 | 0.74 | yes |
| KGW | morph | 24/24 | 0.74 | yes |
| KGW | morph_v1 | 24/24 | 0.72 | yes |
| SynthID | clean | 24/24 | 3.79 | yes |
| SynthID | morph | 24/24 | 3.79 | yes |
| SynthID | morph_v1 | 24/24 | 3.45 | yes |

### 4.2 Robustness under attack

**Attack ranking.** Table 4 ranks the ten attacks by mean AUROC drop relative to the clean condition, averaged over the three schemes. Two attacks dominate. Laundering through an external LLM (launder_api) is the most damaging, with a mean drop of 0.158; round-trip translation (rtt) follows at 0.091. The diacritic family produces small but non-zero drops (0.031–0.034 for the 100% variants), self-paraphrase attacks are near zero (launder 0.008, para 0.001), and the two purely morphological attacks produce a drop of exactly 0.000: the planned morphological attack does not fire on this corpus, a negative result analyzed in Section 6. Laundering through the generator itself (launder, mean drop 0.008) is nearly harmless, while the same operation through an external model (launder_api) is the strongest attack observed: per scheme, launder_api reduces AUROC from 1.000 to 0.917 (KGW), 0.863 (EXP), and 0.747 (SynthID).

![Figure 1: AUROC per condition and scheme with clustered CIs](figs/fig2_auroc_attacks.png)

**Figure 1.** AUROC per attack condition and scheme (dots), with prompt-clustered bootstrap 95% CIs (bars). Conditions are ordered by mean AUROC drop; open markers denote degenerate bootstrap intervals ([1.000, 1.000]), which record that no counterexample was observed rather than a numerical lower bound; Table 3 gives the counted separation and exact p-value for those cells. Generated by `paper/make_figures.py` from `results/detection_metrics.csv`.

**Table 4.** Attacks ranked by mean AUROC drop vs. clean, averaged across the three schemes.

| Rank | Attack | Mean AUROC drop |
|---|---|---|
| 1 | launder_api | 0.158 |
| 2 | rtt | 0.091 |
| 3 | morph_v1+dia | 0.034 |
| 4 | morph+dia | 0.033 |
| 5 | dia100 | 0.031 |
| 6 | launder | 0.008 |
| 7 | dia50 | 0.002 |
| 8 | para | 0.001 |
| 9 | morph | 0.000 |
| 9 | morph_v1 | 0.000 |

AUROC understates the operational damage. At each scheme's clean-calibrated threshold, launder_api collapses the true positive rate to 0.427 (KGW), 0.490 (EXP), and 0.250 (SynthID); rtt yields 0.594, 0.792, and 0.312 respectively (Table 5). These are small-sample estimates and we give their prompt-clustered intervals rather than the point values alone: under launder_api, [0.198, 0.729] for KGW, [0.344, 0.698] for EXP, and [0.073, 0.385] for SynthID; under rtt, [0.385, 0.844], [0.667, 0.958], and [0.146, 0.438]. The intervals are wide enough that the ordering among schemes at a fixed attack should not be read from these numbers; the paired tests below, which use the prompt as the unit, are the basis for that comparison. A detector deployed at its clean operating point misses half or more of laundered watermarked text under all three schemes.

**Is laundering more destructive than translation?** We compare launder_api against rtt (the two strongest attacks) with prompt-level paired Wilcoxon tests on per-prompt detection rates (n = 24 prompts; row-level tests would violate the clustering structure identified above). The direction is consistent in all three schemes: launder_api is more destructive. Nominal p-values are 0.0053 (KGW), 0.037 (EXP), and 0.019 (SynthID); after Bonferroni correction across the three schemes (α = 0.05/3 ≈ 0.0167), only KGW remains significant (Table 5). The ordering launder_api > rtt is therefore established for KGW and directionally consistent, but not individually significant, for EXP and SynthID.

**Table 5.** Prompt-level paired comparison of launder_api vs. rtt (Wilcoxon signed-rank on per-prompt detection rates at the clean-calibrated threshold; n = 24 prompts per scheme; Bonferroni over 3 schemes, α = 0.05/3 ≈ 0.0167; n.s. = not significant).

| Scheme | TPR (rtt) | TPR (launder_api) | Wilcoxon p | Bonferroni |
|---|---|---|---|---|
| KGW | 0.594 | 0.427 | 0.0053 | significant |
| EXP | 0.792 | 0.490 | 0.037 | n.s. |
| SynthID | 0.312 | 0.250 | 0.019 | n.s. |

**Scheme comparison.** Because raw detection statistics are not comparable across schemes, scheme-pairwise comparisons use per-prompt detection rates at each scheme's own clean-calibrated threshold. The test family ({rtt, launder_api} × 3 scheme pairs = 6 paired Wilcoxon tests with Holm correction) was specified before the per-scheme results were inspected (Section 3.3; Table 6). SynthID is significantly more fragile than both alternatives under both attacks: all four tests involving SynthID survive Holm correction (4/6), with mean per-prompt detection-rate differences of 0.479 (EXP vs. SynthID, rtt), 0.281 (KGW vs. SynthID, rtt), 0.240 (EXP vs. SynthID, launder_api), and 0.177 (KGW vs. SynthID, launder_api). KGW and EXP are not distinguishable from each other under either attack (p = 0.104 and p = 0.513).

**Table 6.** Scheme-pairwise robustness comparison: paired Wilcoxon on per-prompt detection rates (positive mean difference = first scheme more robust), Holm correction over the family of 6 tests specified before the per-scheme results were inspected; n.s. = not significant.

| Condition | Pair | Mean diff. | n prompts | p | Holm threshold | Holm |
|---|---|---|---|---|---|---|
| rtt | EXP vs SynthID | 0.479 | 24 | 0.001 | 0.008 | significant |
| rtt | KGW vs SynthID | 0.281 | 24 | 0.001 | 0.010 | significant |
| launder_api | EXP vs SynthID | 0.240 | 24 | 0.003 | 0.013 | significant |
| launder_api | KGW vs SynthID | 0.177 | 24 | 0.013 | 0.017 | significant |
| rtt | KGW vs EXP | −0.198 | 24 | 0.104 | 0.025 | n.s. |
| launder_api | KGW vs EXP | −0.062 | 24 | 0.513 | 0.050 | n.s. |

A threshold calibrated on clean negatives does not keep its nominal rate once the negatives are attacked, and Section 1 promised the full table rather than a summary of it. Table 7 gives all 33 cells. The highest realized false-positive rate is 6.2%, against the 1% the threshold was set for. Under a one-sided binomial comparison with Bonferroni correction over the 33 cells, 2 cells depart from nominal (EXP/launder_api, SynthID/morph_v1+dia). Because these comparisons ignore the prompt clustering described above, the intervals are anticonservative and we report the flag as descriptive rather than as a test result. With 96 negatives per cell the resolution is 1/96 = 1.0%, so smaller departures cannot be distinguished here; that limit is precisely why S1 measures false positives on human text at n ≥ 3,000 instead.

**Table 7.** Realized false-positive rate of the clean-calibrated threshold on attacked negatives, for all 33 scheme-condition cells. The table is descriptive: the 95% upper bound is a binomial bound over 96 rows, but those rows are four per prompt across 24 prompt clusters, so the bound is anticonservative, and the threshold is estimated from the same small clean sample. The threshold is set to 1% FPR on the 96 clean negatives; the fourth column is the rate that same threshold actually achieves once the negatives have been through the attack. The last column gives AUROC when both classes carry the same transformation, which is an ecologically meaningful question for diacritic stripping and translation but not for the laundering attacks, since nobody launders human text to remove a watermark it does not carry.

| Scheme | Condition | TPR | Realized FPR | Exceeding | FPR 95% upper | Same-transform AUROC |
|---|---|---|---|---|---|---|
| EXP | clean | 1.000 | 0.010 | 1/96 | 0.057 | 1.000 |
| EXP | dia100 | 0.917 | 0.042 | 4/96 | 0.103 | 0.982 |
| EXP | dia50 | 1.000 | 0.031 | 3/96 | 0.089 | 1.000 |
| EXP | morph | 1.000 | 0.010 | 1/96 | 0.057 | 1.000 |
| EXP | morph+dia | 0.875 | 0.042 | 4/96 | 0.103 | 0.981 |
| EXP | morph_v1 | 1.000 | 0.010 | 1/96 | 0.057 | 1.000 |
| EXP | morph_v1+dia | 0.917 | 0.021 | 2/96 | 0.073 | 0.980 |
| EXP | rtt | 0.792 | 0.021 | 2/96 | 0.073 | 0.960 |
| EXP | para | 1.000 | 0.010 | 1/96 | 0.057 | 1.000 |
| EXP | launder | 0.990 | 0.031 | 3/96 | 0.089 | 0.996 |
| EXP | launder_api | 0.490 | 0.062 | 6/96 | 0.131 | 0.840 |
| KGW | clean | 1.000 | 0.010 | 1/96 | 0.057 | 1.000 |
| KGW | dia100 | 0.865 | 0.010 | 1/96 | 0.057 | 0.993 |
| KGW | dia50 | 0.979 | 0.000 | 0/96 | 0.038 | 0.999 |
| KGW | morph | 1.000 | 0.010 | 1/96 | 0.057 | 1.000 |
| KGW | morph+dia | 0.865 | 0.010 | 1/96 | 0.057 | 0.994 |
| KGW | morph_v1 | 1.000 | 0.021 | 2/96 | 0.073 | 1.000 |
| KGW | morph_v1+dia | 0.844 | 0.010 | 1/96 | 0.057 | 0.995 |
| KGW | rtt | 0.594 | 0.010 | 1/96 | 0.057 | 0.961 |
| KGW | para | 0.990 | 0.000 | 0/96 | 0.038 | 0.999 |
| KGW | launder | 0.938 | 0.000 | 0/96 | 0.038 | 0.999 |
| KGW | launder_api | 0.427 | 0.000 | 0/96 | 0.038 | 0.941 |
| SynthID | clean | 1.000 | 0.010 | 1/96 | 0.057 | 1.000 |
| SynthID | dia100 | 0.677 | 0.021 | 2/96 | 0.073 | 0.927 |
| SynthID | dia50 | 0.948 | 0.010 | 1/96 | 0.057 | 0.996 |
| SynthID | morph | 1.000 | 0.021 | 2/96 | 0.073 | 1.000 |
| SynthID | morph+dia | 0.656 | 0.021 | 2/96 | 0.073 | 0.924 |
| SynthID | morph_v1 | 1.000 | 0.031 | 3/96 | 0.089 | 1.000 |
| SynthID | morph_v1+dia | 0.656 | 0.062 | 6/96 | 0.131 | 0.915 |
| SynthID | rtt | 0.312 | 0.042 | 4/96 | 0.103 | 0.825 |
| SynthID | para | 0.990 | 0.021 | 2/96 | 0.073 | 0.998 |
| SynthID | launder | 0.948 | 0.021 | 2/96 | 0.073 | 0.980 |
| SynthID | launder_api | 0.250 | 0.010 | 1/96 | 0.057 | 0.807 |

Under the pre-registered S2 decision rule (commit cbcb988; an attack is successful iff it reduces AUROC by more than 0.05 while preserving meaning, Section 4.4), launder_api qualifies against all three schemes, and rtt qualifies only against SynthID (Table 11 gives the per-scheme ΔAUROC values). Laundering through an external model is thus the only attack in this study that satisfies the rule for every scheme tested. SynthID's position is the mirror image of its calibration behavior reported in Section 4.3 (Figure 2): the scheme most fragile under attack is also the one that falsely flags the fewest human windows at its own shipped threshold, an inverse pattern across the three schemes that we return to in the Discussion. With three schemes this is a described pattern, not an established trade-off.

![Figure 2: fragility against realized false-positive rate](figs/fig3_tradeoff.png)

**Figure 2.** Fragility under attack against realized false-positive behaviour. Horizontal axis: the share of the 1,500 human Turkish windows each detector flags at its own shipped threshold, a unit comparable across schemes (an earlier version used raw null standard deviations, which are on incommensurable scales; Section 3.3). Vertical axis: AUROC under external laundering with prompt-clustered 95% CIs (lower = more fragile). SynthID flags no human window yet is the most fragile. The pattern is not monotone across all three: KGW both flags fewer windows than EXP and resists the attack better, so the figure shows one scheme at an extreme rather than a clean trade-off curve. Generated by `paper/make_figures.py`.

**Exploratory: SynthID's weighted-mean detector.** As a post-hoc check we re-scored every SynthID text with MarkLLM's alternative untrained detector (`weighted_mean`), after first verifying that our re-scoring pipeline reproduces the shipped `mean` scores bit-exactly (maximum absolute difference 5.55 × 10⁻¹⁷ over an 88-row sample). The alternative detector improves SynthID moderately (AUROC 0.816 → 0.857 under round-trip translation, 0.747 → 0.773 under laundering, 0.929 → 0.955 under full diacritic stripping) but does not change the ordering: SynthID remains the most fragile of the three schemes under both headline attacks. The pre-registered headline numbers use the default `mean` detector; this paragraph is exploratory.

### 4.3 Calibration on human text (S1)

The clean-text results of Section 4.1 are threshold-free: AUROC ranks watermarked against unwatermarked text without committing to an operating point. Deployment, however, requires a threshold, and a threshold is only as good as the null distribution it assumes. The KGW detector's (Kirchenbauer et al., 2023) z-statistic is assumed approximately N(0,1) on unwatermarked text, so the configuration threshold z = 4 implies a one-sided nominal false-positive rate of 3.17 × 10⁻⁵, an assumption already contradicted by the 96 unwatermarked model generations (null standard deviation 1.313; Section 3.4). Study S1 (pre-registered at commit 8f8df72, hypotheses H1–H3 as stated in Section 3.4) measures the null directly on the human-text sample of Section 3.4: 1,500 windows per language from random Wikipedia articles (dump 20231101 (Wikimedia Foundation, 2023a)), scored by all three detectors with `model=None`. Table 8 reports, per scheme and language, the null mean and standard deviation, the false-positive rate at the configuration threshold, and the false-positive rate at the threshold calibrated to 1% FPR on the 96 clean model negatives.

**Table 8.** S1 null distributions on human Wikipedia text (pre-registration 8f8df72). Model-calibrated thresholds are fixed at 1% FPR on the 96 clean model negatives: 3.285 (KGW), 1.609 (EXP), 0.507 (SynthID).

| Scheme | Language | n | Null mean | Null std | FPR @ config threshold | FPR @ model-calibrated threshold |
|---|---|---:|---:|---:|---:|---:|
| KGW | TR | 1500 | −0.055 | 1.479 | 0.2% | 0.8% |
| EXP | TR | 1500 | 0.590 | 0.749 | 0.9% | 7.4% |
| SynthID | TR | 1500 | 0.499 | 0.003 | 0% | 1.1% |
| KGW | EN | 1500 | 0.278 | 1.321 | 0.2% | 0.9% |
| EXP | EN | 1500 | 0.452 | 0.470 | 0% | 3.2% |
| SynthID | EN | 1500 | 0.500 | 0.004 | 0% | 4.1% |

**Table 9.** Robustness of the S1 null to two controls added after pre-registration. Left: KGW null standard deviation with every window truncated to a common token budget T (n.a. where fewer than 100 windows survive truncation). Right: range across eight watermark keys at native length, the study key included. Variance inflation survives both controls; the tail count does not survive the key sweep, and the language difference does not survive the length control.

| Corpus | SD at T=300 | SD at T=400 | SD at T=500 | SD at T=800 | SD range over 8 keys | z>4 count range |
|---|---|---|---|---|---|---|
| Turkish (Wikipedia) | 1.177 | 1.229 | 1.281 | 1.383 | 1.465–2.533 | 3–143 |
| English (Wikipedia) | 1.206 | 1.253 | 1.301 | n.a. | 1.308–1.499 | 2–33 |
| Turkish (Wikisource) | 1.214 | 1.237 | 1.268 | 1.385 | 1.420–1.576 | 2–8 |

**H1 is confirmed, and it survives both controls we added afterwards.** On human Turkish, the KGW null standard deviation is 1.479 against the theoretical value of 1; the largest observed statistic is z = 5.08, well above the detection threshold. Empirically, 3 of 1,500 Turkish windows exceed z = 4, a rate of 2.0 × 10⁻³, approximately 63 times the nominal rate. We treat this count-based estimate as primary. A Gaussian fit to the observed null implies 3.05 × 10⁻³ (i.e. 3.05 × 10⁻³ / 3.17 × 10⁻⁵ ≈ 96 times nominal), but H1 itself establishes that the Gaussian model is misspecified, so the parametric figure is reported only as approximate corroboration of the order of magnitude, never as the headline estimate.

Three exceedances in 1,500 windows is a small count and we attach its uncertainty rather than reporting the ratio alone: the exact two-sided 95% binomial interval is [0.041%, 0.583%], which is 13 to 184 times nominal. The Wikisource register gives 4 of 1,000, or 126 times nominal with interval [34×, 322×]. Every claim we make from these counts is an order-of-magnitude claim, as pre-registered.

The second control is the watermark key. The whole study runs on one key, the MarkLLM default, and a keyed scheme could in principle owe its null behaviour to that particular vocabulary partition. Because S1 requires no generation (the text is human and the detectors are model-free), we rescored all 4,000 windows under eight keys, the study key first and the remainder drawn from a fixed seed. Variance inflation is key-robust: the Turkish null standard deviation stays between 1.4645 and 2.5326 across keys, English between 1.3076 and 1.4987, Wikisource between 1.4199 and 1.5757, and in no corpus under any key does it fall to the theoretical value of 1. The tail count, by contrast, is highly key-sensitive: Turkish exceedances of z = 4 range from 3 to 143 across the eight keys, with a median of 7. The study key produces the smallest tail among the eight keys we sampled, so the 63× headline is conditional on that key and sits at the low end of the sampled range; the median sampled key would give roughly 147×. We sampled eight keys and did not enumerate the key space, so this is a statement about the sample, not a bound. We report the sweep because it cuts against a convenient number, not because it flatters one.

**H2 does not survive a control we added after pre-registration, and we report it as not confirmed.** On the pre-registered comparison the English null standard deviation is 1.321 versus 1.479 for Turkish (Levene test, p = 0.00039). Two observations already qualified that result. The tail counts are identical, 3 of 1,500 windows exceeding z = 4 in each language, so at this sample size the exceedance counts cannot separate the languages and the pre-registered verdict rested on the variance test alone. And with an English null standard deviation of 1.321 the z = 4 threshold is miscalibrated in English too, so Turkish could at most worsen a failure it did not create.

The control is sequence length. Our windows were matched on word count (365 words, Section 3.4), which is the right unit for a reader but not for a detector: KGW scores tokens, and Turkish subword fertility is far higher than English. Measured on the sampled windows, the median window is 1,017 tokens in Turkish and 529 in English, so the pre-registered comparison contrasted Turkish documents with English documents roughly half their length in the unit the statistic actually consumes. We therefore rescored every window truncated to a common token budget, using the detector's own scoring path on truncated token sequences so that no re-tokenization drift enters (the path reproduces the recorded scores exactly). At matched length the difference disappears and its sign reverses: Turkish 1.1768 versus English 1.2060 at T = 300 (Levene p = 0.21), 1.2287 versus 1.2530 at T = 400 (p = 0.26), and 1.2815 versus 1.3011 at T = 500 (p = 0.61). We do not use the T = 800 cell, where only 73 English windows survive truncation and the surviving set is the longest 5% rather than a random sample.

What the length control reveals is a dose–response that both languages share (Table 9). The null standard deviation rises monotonically with the number of tokens scored, from 1.177 at T = 300 to 1.383 at T = 800 in Turkish, from 1.206 to 1.301 across the usable English range, and from 1.214 to 1.385 in the Wikisource register. Overdispersion accumulates with sequence length, and at equal length the two languages are indistinguishable. H2 as pre-registered attributed the inflation to the language; the data are instead consistent with an exposure pathway running through length, with the language entering only through how many tokens a given amount of text becomes. We keep the pre-registered result on record and mark it superseded rather than deleting it.

**H3 is confirmed.** SynthID's null is almost exactly as predicted (standard deviation 0.003 in Turkish, 0.004 in English, against the pre-registered ≈ 0.003) with no window exceeding its configuration threshold in either language. EXP likewise shows no analogue of the KGW failure, which is specific to pairing a parametric normality assumption with an inflated null; EXP ships no such nominal guarantee. We note, without attaching a hypothesis test, that the EXP Turkish null is wider and further right-shifted than its English counterpart (standard deviation 0.749 versus 0.470; mean 0.590 versus 0.452), and that this tail drives EXP's 0.9% Turkish false-positive rate at its configuration threshold; the consequence surfaces in the threshold-transfer finding below.

**Mechanism.** The dependence account is not ours and we do not claim it. KGW's variance derivation assumes each green-list indicator is an independent draw. With `prefix_length` = 1 the green/red vocabulary partition for a token is fixed by hashing the single preceding token (Kirchenbauer et al., 2023), so whenever a seeding token recurs the same partition is consulted again and successive indicators share partitions rather than being drawn independently. Document-level green counts become over-dispersed and the variance of the z-statistic exceeds its binomial value while the mean stays near zero. Fernandez et al. (2023) established this empirically before us, and at a scale ours does not approach: 100k multilingual Wikipedia texts of 256 tokens scored under ten master keys, where the empirical false-positive rate of the z-test sits far above its theoretical value. Their decomposition matters for reading ours: part of that gap is the Gaussian approximation itself, which exact tests close, and the residue is what repeated context windows contribute by reseeding the same partition. Khachaturov et al. (2025) reach a related repetition-driven failure from the mimicry side and likewise recommend longer seeding windows. Our contribution here is neither the mechanism nor its first demonstration; it is a magnitude at the shipped default configuration, on one language's human text and at native document length rather than at a fixed 256-token window, together with a measurement of what carries it.

Our own data now identify the carrier as length rather than morphology. We had proposed that Turkish suffix subtokens recur often enough to raise the repetition rate directly, which predicts a language effect at fixed length; the token-controlled comparison above rules that prediction out, since at equal token budgets Turkish and English nulls coincide. What survives is an indirect route: agglutinative morphology raises subword fertility, higher fertility turns a given amount of readable text into roughly twice as many tokens, and the inflation grows with the number of tokens scored. The language effect is real in deployment, where documents are written in words and not in tokens. The token-matched comparison is post-hoc and observational: it rules out a language effect at fixed token count, but it does not establish causal mediation by tokenization, which would require manipulating the tokenizer or the seeding window directly. We did not manipulate `prefix_length`, so the specific claim that a longer seeding window would remove the inflation remains untested here; Fernandez et al. (2023) measure the gap narrowing as the window widens, and Khachaturov et al. (2025) argue for the same remedy on independent grounds. Widening it is not free: Fernandez et al. (2023) also observe that a short window is part of what makes the watermark robust to edits, and Liu et al. (2024) frame the window length explicitly as a trade-off, where too few conditioning tokens leave the vocabulary partition easy to reverse-engineer and too many leave the seed fragile to any edit.

![Figure 3: KGW null distributions on human text](figs/fig1_null_distributions.png)

**Figure 3.** Kernel density estimates of the KGW detection statistic on unwatermarked human text: Turkish Wikipedia (n = 1,500), Turkish Wikisource (n = 1,000), and English Wikipedia (n = 1,500), against the theoretical N(0,1) null. All three empirical nulls are wider than the theory assumes; the annotated counts give the windows exceeding the default z = 4 threshold. Generated by `paper/make_figures.py` from the S1 score files.

**Second register (pre-registered extension, commit 5c4f323).** To test whether the inflation is a property of encyclopedic prose rather than of the language, we repeated the Turkish measurement on a second register: 1,000 windows of older official and literary prose from Turkish Wikisource (dump 20231201; Wikimedia Foundation, 2023b), collected under the same windowing and pre-registered before collection with the single hypothesis that H1 would hold. It does: the KGW null standard deviation is 1.420, and 4 of 1,000 windows cross z = 4 (empirical FPR 0.004, roughly 126 times nominal). The variance difference between the two Turkish registers is not significant (Levene p = 0.20). We read that as a failure to reject rather than as evidence of equivalence, since we ran no equivalence test and both registers are formal written prose; conversational or newspaper Turkish may behave differently. An earlier version of this paragraph concluded that the inflation tracks the language rather than the register. The length control reported above withdraws the language half of that conclusion: what replicates across the two registers is the inflation itself, which the token-matched comparison attributes to sequence length in both languages. The two registers are analyzed separately and never pooled.

**Exploratory observations (labeled as such; not pre-registered).** First, the English KGW null mean is shifted to +0.278, whereas the Turkish mean is −0.055; no hypothesis anticipated this shift, and we record it strictly as a replication target. Second, thresholds calibrated on model-generated negatives do not transfer to human text: the 1% model-calibrated thresholds yield 7.4% on Turkish human text for EXP and 4.1% on English human text for SynthID. The measurement column was pre-specified in the S1 protocol, but no hypothesis was attached, so we label the interpretation exploratory: model output appears to be an inadequate proxy for the human-text negative class, and operational thresholds should be calibrated on negatives drawn from the deployment distribution itself. Both observations are confined to a single register (encyclopedia text); Section 6 discusses this and the remaining limitations.

### 4.4 Utility axis (S2)

A detection drop alone does not make an attack successful (Section 3.5). The utility axis is therefore measured with pairwise LLM judgments under the protocol pre-registered at commit cbcb988: two judges from different model families (Claude Opus 5 and gpt-oss-120b), 40 unique pairs per condition presented in both orders (80 ordered presentations, 40 independent pair units per condition–judge cell), blind calibration pairs passed by both judges before any real verdict was read, and the requirement that any launder_api verdict be supported by both judges, because Opus 5 produced the launder_api texts (Section 3.5). Judged conditions are rtt, para, launder, and launder_api, with source texts drawn from the KGW-positive arm.

Table 10 reports the outcome. Meaning is preserved in every cell: for all four judged attacks and both judges, the meaning-preservation rate is 1.00. Two limits on that sentence should be read with it. All judged pairs come from the KGW arm, as pre-registered, so this is a statement about attacks applied to KGW-watermarked text and not about the EXP or SynthID arms. And only four of the ten attacks were judged; the six diacritic and morphological variants were not, so the corpus-wide claim is that no judged attack destroys what the text says.

**Table 10.** S2 pairwise judging results per condition and judge (40 unique pairs per cell, each presented in both orders; percentages are over the 80 ordered presentations).

| Condition | Judge | n | Meaning preserved | Position-flip rate |
|---|---|---|---|---|
| rtt | gpt-oss-120b | 80 | 1.00 | 25.0% |
| rtt | Opus 5 | 80 | 1.00 | 10.0% |
| para | gpt-oss-120b | 80 | 1.00 | 42.5% |
| para | Opus 5 | 80 | 1.00 | 15.0% |
| launder | gpt-oss-120b | 80 | 1.00 | 57.5% |
| launder | Opus 5 | 80 | 1.00 | 5.0% |
| launder_api | gpt-oss-120b | 80 | 1.00 | 50.0% |
| launder_api | Opus 5 | 80 | 1.00 | 0.0% |

The pre-registered decision rule declares an attack successful iff (i) ΔAUROC > 0.05 and (ii) meaning is preserved by judge majority, with (ii) required from both judges for launder_api. The pre-registration fixed the source arm for the judged texts but did not state against which scheme's AUROC clause (i) is evaluated; rather than selecting a scheme post hoc, we evaluate the rule for each scheme separately and report all three outcomes (Table 11; each ΔAUROC is computed as 1.000 (the clean AUROC of every scheme in Table 2) minus that scheme's attacked AUROC in Table 2).

**Table 11.** Decision-rule evaluation per scheme (ΔAUROC = 1.000 minus the corresponding Table 2 value).

| Scheme | Δ launder_api | Δ rtt | Δ para | Δ launder | Rule satisfied by |
|---|---|---|---|---|---|
| KGW | 0.083 | 0.046 | 0.002 | 0.001 | launder_api |
| EXP | 0.137 | 0.044 | 0.000 | 0.003 | launder_api |
| SynthID | 0.253 | 0.184 | 0.002 | 0.019 | launder_api, rtt |

Under every resolution of the ambiguity the conclusion is the same: launder_api is the only attack whose detection damage clears the threshold for all three schemes. Round-trip translation clears it only for SynthID; para and launder clear it for no scheme (largest ΔAUROC 0.019). The second clause of the rule is carried by KGW-arm judgements throughout, so the full rule is demonstrated for KGW and inferred for the other two. Section 6 records why this inference is not free.

Fluency claims require discipline. The position-flip rate (how often a judge's fluency preference reverses when the same pair is shown in the opposite order) exceeds the pre-registered 30% reliability bound for the independent judge on para (42.5%), launder (57.5%), and launder_api (50.0%): a preference that flips with presentation order at near-chance rates is position noise, and no directional fluency claim is made from it. The conflicted cell illustrates why the second judge exists: Opus 5 judging launder_api pairs never prefers the original (0.0%, with a 0.0% flip rate), which is the pattern (Panickssery et al., 2024) predicts when a model grades its own output, and we discard the verdict rather than interpret it. The independent judge fails in the other documented direction, order sensitivity (Zheng et al., 2023), at 42.5% to 57.5% across three of four conditions, which is exactly what the pre-registered 30% bound was set to catch, and it caught it. For para, launder and launder_api the independent judge exceeded the pre-registered 30% position-flip bound, so no directional fluency conclusion is supported for those conditions in either direction, including "does not degrade". Round-trip translation is the contrast case: both judges' flip rates fall within the bound (25.0% and 10.0%) and both prefer the original (85.0% and 95.0% of pairs), so rtt (NLLB-200-distilled-600M; NLLB Team et al., 2024) produces detectable fluency loss even where it fails as a detection attack.
## 5 Discussion

### 5.1 Thresholds must be calibrated per language and per negative distribution

The default KGW threshold z = 4 encodes an assumption (an approximately standard normal null) that fails on human text. On 1500 Wikipedia windows (Wikimedia Foundation, 2023a) the KGW null standard deviation is 1.479 against a theoretical 1, and 3/1500 human Turkish windows (0.2%) cross z = 4, approximately 63 times the nominal false-positive rate of 3.17 × 10⁻⁵, with an exact binomial interval of 13 to 184 times nominal (empirical estimate primary; the Gaussian parametric figure of 3.05 × 10⁻³ / 3.17 × 10⁻⁵ ≈ 96× is approximate only, since the inflation itself shows the null is not the assumed Gaussian). A Turkish deployment that ships the default threshold therefore accuses human writers at roughly 63 times the rate the scheme's theory promises (Kirchenbauer et al., 2023), and the eight-key sweep of Section 4.3 places that figure at the conservative end of a range whose median is about 147 times.

The failure is not confined to Turkish, and saying so is the honest reading of our own data. English shows the same inflated null (standard deviation 1.321) and exactly the same tail count, 3 of 1,500. At matched token length the two languages are statistically indistinguishable. What Turkish adds is exposure rather than a different mechanism: because its subword fertility is roughly twice that of English, a document of a given reading length is scored over roughly twice as many tokens, and the inflation grows with tokens scored. A deployment serving Turkish therefore sits further along the same curve, not on a different one. Nemecek et al. (2026) reach the same structural verdict from a wider grid, reporting that cross-lingual disparity in watermarking is predominantly between typological families rather than idiosyncratic to particular languages, and that every scheme they audit ships a hardcoded threshold targeting a theoretical false-positive rate under an IID-token null that multilingual generation does not satisfy. Their prescription, empirical per-deployment threshold calibration, is ours as well; what our measurement adds to it is the second axis, since calibrating on the right language but the wrong negative distribution is not enough.

Calibration must also match the negative distribution, not just the language. We record an exploratory, not pre-registered, but operationally important observation. Thresholds set to 1% FPR on the model's own unwatermarked outputs do not transfer to human text: the same thresholds yield 7.4% FPR on human Turkish for EXP and 4.1% on human English for SynthID. Model-generated negatives are an inadequate proxy for the human text a deployed detector will actually screen. The practical prescription is that deployments should calibrate on, and report, the negative distribution of their own language and register. Two remedies for the dependence itself already exist and we did not apply either: Fernandez et al. (2023) score only those tokens whose watermark context window, or context-plus-token tuple, has not already been seen in the document, and both Fernandez et al. (2023) and Khachaturov et al. (2025) recommend a wider seeding window. What we measure is the configuration as shipped (`prefix_length` = 1 with a z = 4 threshold, the MarkLLM defaults; Pan et al., 2024), which is what a deployment inherits unless it knows to change it, and our 63× figure should be read as the cost of that default rather than as a bound on what the scheme family can achieve.

### 5.2 The best-calibrated scheme is the most fragile

No scheme dominates both axes. That a watermarking design buys one property at the cost of another is a documented pattern rather than a surprise: Pang et al. (2024) show that common design choices leave the resulting systems open to attack and derive fundamental trade-offs among robustness, utility and usability. The pair we measure, attack robustness against the behaviour of the null distribution on unwatermarked text, is not among theirs, and it is the pair a deployment has to price, because one axis governs how often the watermark is missed and the other how often an innocent writer is accused. The three detectors report statistics on different scales, so their raw standard deviations are not comparable and Section 3.3 forbids comparing them; the comparable quantity is the realized false-positive rate on human text at each scheme's own shipped threshold. On that measure SynthID (Dathathri et al., 2024) is the best behaved, flagging 0 of the 1500 Turkish windows (0.00%), against KGW's 3 (0.20%) and EXP's 13 (0.87%). Yet SynthID is the most fragile under attack: all four Holm-significant prompt-level pairwise differences are against SynthID (rtt: EXP +0.479, p = 0.001 and KGW +0.281, p = 0.001; launder_api: EXP +0.240, p = 0.003 and KGW +0.177, p = 0.013), and under launder_api its AUROC falls to 0.747 with TPR 0.250 at the clean-calibrated threshold. The absolute half of that observation is not new: Han et al. (2025) report SynthID-Text degraded by meaning-preserving attacks including paraphrase and back-translation, and propose hybridizing it with a semantic scheme (Liu et al., 2024) as the remedy. What we add is the relative half, measured rather than asserted: at each scheme's own clean-calibrated threshold and with the prompt as the unit of analysis, SynthID is more fragile than both alternatives in every one of the four paired comparisons that survive Holm correction, and it is so on Turkish, where none of the three schemes had been measured. KGW is comparatively robust to attack but carries the inflated Turkish null of Section 4.3. EXP (Aaronson, 2023; Aaronson & Kirchner, 2022) sits between them (KGW–EXP differences are not significant: p = 0.104 for rtt, p = 0.513 for launder_api), with the caveat that its fixed-length generation is a structural confound noted in Section 6. Choosing a watermark for Turkish is thus a trade-off between attack robustness and null calibration, and the scheme with the most trustworthy false-positive behaviour is the easiest to wash out.

### 5.3 Laundering is cheap and effective; defense is open

Laundering through an external model is the only attack whose detection damage clears the pre-registered threshold for all three schemes, and the only one that also passes the utility clause where we measured it. Its mean AUROC drop across schemes is 0.158 (the next attack, rtt, achieves 0.091), and it pushes TPR at the clean-calibrated thresholds down to 0.427 (KGW), 0.490 (EXP), and 0.250 (SynthID) while preserving meaning in every judged pair drawn from the KGW arm, and leaving no fluency loss the independent judge can detect. This is a counterweight to the reliability result of Kirchenbauer et al. (2024), who report that after strong human paraphrase a green-list watermark remains detectable once roughly 800 tokens are observed at a nominal 10⁻⁵ false-positive rate. Our texts are longer than that budget (the median KGW text is 983.5 tokens, Table 1, and the EXP arm is fixed at 950), and detection still falls to a true-positive rate of 0.427 for KGW and 0.250 for SynthID. Two differences keep this from being a failed replication and make it a boundary condition instead: their attack paraphrases the text whereas ours rewrites it through a different and external model, and their token budget is derived from a nominal 10⁻⁵ rate that Section 4.3 measures to be wrong on human text by one to two orders of magnitude, so the length at which detection becomes trustworthy is itself understated. Nor is it covert truncation: the median attacked-to-source length ratio is 0.976. At the prompt level, launder_api is more destructive than round-trip translation for KGW (paired Wilcoxon p = 0.0053, significant after Bonferroni correction across the three schemes); the direction is the same for EXP (p = 0.037) and SynthID (p = 0.019) without surviving correction. The contrast with self-paraphrase is instructive: asking the watermarking model itself to rewrite its output barely moves detection (mean AUROC drop 0.008 for launder, 0.001 for para), so the attack's power comes from routing text through a different, external model (one outside the defender's control), not from paraphrasing as such. The attack is also cheap and requires no knowledge of the scheme or key: the entire launder_api pass over the corpus cost USD 17.704 in measured API charges (the Opus 5 judge evaluation added USD 7.021; the second judge's cost was not separately metered), and it degrades all three schemes at once. We evaluate no defenses here, and the question is not open in theory: Zhang et al. (2024) prove that no strong watermarking scheme survives an attacker holding a quality oracle and a mixing perturbation oracle, and instantiate that attack successfully against the green-list scheme (Kirchenbauer et al., 2023) that we also test and against the distortion-free family (Kuditipudi et al., 2024), of which we test the Aaronson-Kirchner variant rather than their edit-robust EXP-Edit and ITS-Edit algorithms, which MarkLLM implements separately and we did not run. Our launder_api attack is a crude, single-pass realization of that perturbation oracle. What remains open is empirical and quantitative: how much detection survives which rewrite budget, for which scheme, at which document length and in which language, and whether any deployable defense makes the attack expensive enough to matter, including whether the paraphrase-oriented schemes noted in Section 2 (Hou et al., 2024; Liu et al., 2024), which we did not evaluate, degrade more gracefully than the three context-hashed schemes measured here.

### 5.4 Exploratory observations

Two post-hoc observations are recorded as replication hypotheses, not findings. First, non-Latin script contamination concentrates in the logit-perturbing schemes: 8/96 KGW and 9/96 SynthID texts against 2/96 unwatermarked and 0/96 EXP texts. If this replicates, the logit-perturbing schemes would carry an additional Turkish-specific utility cost that the sampling-based scheme avoids. Second, the KGW null mean on human English is itself shifted positive (+0.278, against −0.055 on Turkish), suggesting that null miscalibration is not exclusively a Turkish phenomenon: Turkish is where the variance inflation is largest, not the only place the theoretical null bends.
## 6 Limitations

**Scope of generalization.** All generated text in this study comes from a single generator, Qwen3-14B (Yang et al., 2025). This was not for lack of trying: five candidate generators were run through the same pre-registered acceptance gate (Latin-script purity 16/16 mandatory; overall gate ≥ 12/16), and only Qwen3-14B passed. Qwen2.5-3B and -7B failed on foreign-script contamination across five configurations; Mistral-Nemo-12B failed on contamination and under-delivery (Latin 14/16, gate 9/16, median 315 words); and the Turkish-tuned Turkish-Llama-8b produced clean, long text (Latin 16/16, word criterion 16/16, median 808.5 words) but degenerated into repetition and failed to terminate (repetition criterion 3/16, termination 2/16, gate 0/16). Cross-model replication was therefore attempted and not achieved (the gate records are in the repository), and producing acceptable long-form Turkish appears to be a barrier in its own right. Nothing in the design licenses generalization to other model families, scales, or tokenizers; the calibration failure in particular is a property of a scheme–tokenizer–language triple and must be re-measured for any other pairing. The scheme set is bounded in the same way. All three schemes tested here perturb or couple the next-token distribution using a key seeded from surface context, and all three are configured as the toolkit ships them. Schemes designed precisely against paraphrase, namely SIR (Liu et al., 2024), which is itself token-level but seeds its watermark logits from a semantic embedding of all preceding tokens rather than from a fixed token window, and SemStamp (Hou et al., 2024), which watermarks by rejection sampling whole sentences, are both implemented in MarkLLM and therefore available to us. Neither was evaluated, so nothing here licenses a claim about watermarking in general; the laundering result is a statement about surface-context-seeded schemes at default settings. A side observation: the effective-γ deviation noted below under implementation-level caveats is Qwen-specific; both rejected candidates have tokenizers whose length equals their declared vocabulary size (deviation exactly 0). Similarly, the entire generation pipeline ran on a single machine and GPU (a Quadro RTX 8000). Reproducibility was measured within that one environment: the determinism test (T4) of the version-drift battery returned token-identical sequences across repeated generations under the pinned software stack; but this is a single-environment result, not a portability claim across hardware or library versions.

**Human-text baseline (S1).** The human corpus covers two registers (encyclopedic prose from Wikipedia (Wikimedia Foundation, 2023a) and older official/literary prose from Turkish Wikisource), and the inflation replicates across both (Section 4.3); newspaper, essayistic, or conversational Turkish may still behave differently. Detector keys are device-class-bound: we measured that a SynthID detector instantiated on CPU draws a different pseudo-random key stream than one on CUDA, so watermarked text scored on the wrong device class collapses to chance (mean g-score 0.498 vs. 0.530), while re-scoring on the generation device reproduces the shipped scores bit-exactly (maximum difference 5.55 × 10⁻¹⁷). The S1 human-text measurements are unaffected by the device class: no watermark is present, and the SynthID null standard deviation is 0.003 under either device class. We limit that exchangeability claim to what we measured, namely SynthID across two device classes; it is not a general statement about all three schemes, and the key sweep reported in Section 4.3 shows that KGW's null mean and tail are decidedly not key-invariant even though its variance inflation is. Any deployment must run detection on the same device class as generation, or serialize the key explicitly.

Sample size bounds precision: with n = 1500 windows per language, the design supports order-of-magnitude statements (the empirical rate of 3/1500 = 0.002 at z = 4 is roughly 63 times nominal, with an exact binomial interval spanning 13 to 184 times) but not claims at finer resolution, which is why we report the empirical estimate as primary and the Gaussian parametric extrapolation as approximate only. Two further bounds belong here. The key sweep covers eight keys for S1 only; extending it to the attack and AUROC axes would require regenerating the corpus under each key, which we did not do, so every robustness number in Section 4.2 is conditional on the single study key. And the length control was applied to the human-text null, not to the generated corpus, whose lengths were fixed by the generation protocol.

**The morphological attack did not fire.** The attack planned as the central typological probe produced almost no edits in this corpus: the morph variant averages 1.1 edits per text, with 60.4% of texts receiving zero edits, and the broader morph_v1 variant averages 7.5 edits per text (zero edits in 4.2% of texts). The mechanism is a register mismatch: the transforms target the progressive suffix -(I)yor via the zeyrek analyzer (Bulat, 2022), and the formal expository register the model produces rarely uses that form. The measured detection effect is accordingly null (mean AUROC drop 0.000 for both variants). Where morph did fire (the n = 38 texts with nonzero edits), the per-edit slope survives our robustness battery (0.052 z per edit, 95% CI [0.022, 0.071], Theil–Sen 0.051, Spearman ρ = 0.579 at p = 0.00014) but is practically tiny: at the observed mean of 2.9 edits it implies a shift of about 0.15 z (0.052 z per edit × 2.9 edits ≈ 0.15) against a matched clean-signal mean of 11.467, invisible at AUROC level. The morph_v1 slope is retracted after the same battery: the OLS estimate of 0.026 has a 95% CI of [−0.005, 0.034] that includes zero, Theil–Sen falls to 0.005, Spearman ρ = 0.091 is not significant (p = 0.39), and the sign flips to −0.003 when the three highest-leverage points are removed (n = 92). Whether an informal-register corpus, where -(I)yor is common, changes this verdict is an open question, not a result of this paper.

**Closed-model laundering.** The launder_api attack routes text through a closed commercial model (Claude Opus 5) whose deployed version can change without notice. The raw laundered outputs are stored in the repository, so every detection score on those texts can be recomputed exactly; the attack generation itself, however, may not be re-creatable against a future version of the model. The result should be read as an existence demonstration (one available external model suffices) rather than as a stable measurement of a fixed system.

**EXP is structurally different.** The EXP implementation generates a fixed sequence length of 950 tokens, does not consume the shared sampling arguments, and never stops at an EOS token; its token-count standard deviation is 1.5, against 178.2 for KGW, 158.4 for SynthID, and 101.0 for the unwatermarked arm, and its 96 texts are exempt from the termination criterion (leaving 288 texts in that denominator). Any cross-scheme comparison of text quality is therefore confounded with this structural difference. Detection comparisons use each scheme's own clean-calibrated threshold, which mitigates but does not remove the concern.

**The utility axis covers one arm.** Every pair judged in S2 was drawn from the KGW-watermarked arm, as the pre-registration fixed. Meaning preservation is therefore measured for attacks applied to KGW text, and carried to the EXP and SynthID rows of Table 11 by assumption rather than by measurement. The assumption is not idle: meaning preservation is a property of the (source, rewrite) pair, the sources differ by arm, and the paragraph above states that cross-scheme comparisons of text quality are confounded. It would cost roughly three US dollars of API charges to judge the other two arms, since the attacked texts already exist, and we regard that as the first extension anyone replicating this work should make. Two further bounds belong here: only four of the ten attacks were judged, and the pre-registered decision rule counts a verdict of "partially preserved" as preservation, which is the permissive reading.

**Acceptance thresholds are only partly justified.** Of the pre-fixed corpus acceptance thresholds (word count ≥ 300, compliance ≥ 0.75, termination ≥ 0.90, contamination ≤ 0.05), the compliance value is inherited from the pre-gate criterion, but the 0.90 and 0.05 values have no external justification. They were fixed before any corpus data existed, which protects against post-hoc tuning, but no sensitivity analysis was performed, and a different choice could have produced a different corpus-validity verdict.

**Implementation-level caveats.** Three smaller issues are recorded for completeness. First, KGW's effective green-list fraction deviates slightly from the configured γ = 0.5 because the implementation sizes the list from the tokenizer length rather than the declared vocabulary size; the measured effective fraction is 0.499118 (len(tokenizer) = 151,669 vs. vocabulary size 151,936; deviation -0.000882). Second, 2 of 96 KGW texts and 2 of 96 SynthID texts hit the 1800-token generation cap and are therefore truncated. Third, in the first run the attention implementation fell back to the transformers default (effectively sdpa); this was not a deliberate choice, and the provenance note is kept in `hpc/config_cuda.py`.

**Post-hoc observation on contamination.** Non-Latin-script contamination is more frequent in the two logit-perturbing arms: KGW 8/96 and SynthID 9/96, against 2/96 unwatermarked and 0/96 for EXP; in total 8 + 9 + 2 + 0 = 19 of 384 texts (4.9%), under the pre-registered 5% gate. This association was noticed after the data were collected. It is labeled exploratory and recorded as a replication hypothesis for future work, not as a finding of this study.
## 7 Reproducibility Statement

Every number reported in this paper is generated from the underlying data by code. The metrics module (`pilot/metrics.py`) produces the summary report and detection tables directly from the scored corpus, and a dedicated exporter (`pilot/make_paper_numbers.py`) emits the single JSON file (`paper/numbers.json`) from which all manuscript numbers are drawn; no number is typed by hand. A regime gate refuses to produce any report when the active configuration does not match the sealed run configuration, so numbers from mismatched settings cannot silently enter the output. Because the experiments span two environments (a local development machine and a university HPC container), the environment layer imports the scientific code rather than forking it, and a content hash over the scientific source files is recorded with each run so that the two environments can be verified to execute identical code. The upstream MarkLLM toolkit (Pan et al., 2024) is pinned to a fixed commit (c45ddc40), the prompt file is sealed by hash (SHA-256 prefix 8fcbe4074b46), and the full generation settings are recorded alongside the results. Before the main run, a version-drift battery (tests T1–T6, pre-registered in `hpc/README.md`) re-measured every environment-dependent assumption on the target machine rather than inheriting local measurements; its determinism test (T4) yielded token-identical repeated generations. All three detectors run model-free (`model=None`), verified against the implementations, so detection scores do not depend on the generator weights or on the numeric precision used for generation. Model-free is not the same as device-independent, and we state the difference because our own measurement contradicts the stronger reading: SynthID's key stream is drawn from a device-class-dependent generator, so a watermarked text scored on the wrong device class collapses to chance (Section 6). Scoring on the generation device class reproduces the shipped scores bit-exactly.

The human-text corpus of S1 is reproducible by construction: each window records its Wikipedia page identifier together with the dump version (wikimedia/wikipedia, 20231101 (Wikimedia Foundation, 2023a)), so the exact text windows can be re-fetched deterministically. The corpus acceptance thresholds were fixed in code before Phase 1 began; the S1 protocol, hypotheses, and analysis plan were sealed at commit 8f8df72 before data collection; and the S2 judging protocol, blind calibration design, and decision rule were sealed at commit cbcb988 before the judging run. Code, corpus, scores, attacked texts (including the raw closed-model laundering outputs), and the pre-registration documents reside in a single repository, so the full path from raw text to every reported statistic can be re-executed.

## Statements and Declarations

### Funding

The author declares that no funds, grants, or other support were received during
the preparation of this manuscript. The commercial API charges reported in
Sections 3.2 and 3.5 (USD 17.704 and USD 7.021) were met from the author's own
resources. Computation for text generation and detection was carried out on
hardware provided by the author's institution (Acknowledgments).

### Competing interests

The author has no competing financial interests or personal relationships that could
have appeared to influence the work reported in this paper. In particular, the author
has no employment, consultancy, equity, patent, honorarium, advisory or funding
relationship with Anthropic, Google DeepMind, Groq, Alibaba/Qwen, or with the
developers of the MarkLLM toolkit, whose schemes, models and reference
implementations are evaluated, in several cases critically, in this study.

Three facts are recorded here for transparency. They are not competing interests
under the definition above, but a reader may reasonably wish to weigh them.

1. **Purchased services, not relationships.** Two components of the experiment were
   run on metered commercial APIs at published list prices: generation of the
   external-laundering attack corpus through Anthropic's API (measured cost USD
   17.704, Section 3.2) and one of the two meaning-preservation judges (measured cost
   USD 7.021 for the Claude Opus 5 judge, Section 3.5). The second judge,
   gpt-oss-120b, was served through Groq and its cost was not separately metered.
   These are arm's-length purchases of a metered service, reported in the paper as
   measurements of attack economics because attack cost is part of the threat model.
   They establish no relationship with the vendors beyond that of a paying customer,
   and no vendor reviewed, funded, approved or was consulted about this work.

2. **A structural conflict inside the measurement, declared and mitigated.** One
   model, Claude Opus 5, occupies two roles in the design: it produces the
   `launder_api` texts and it serves as one of the two judges. This is a conflict
   internal to the protocol rather than an interest of the author, and the
   pre-registration sealed at commit `cbcb988` addresses it before any verdict was
   read: two judges drawn from different model families, agreement of both judges
   required for any `launder_api` verdict, and all fluency conclusions drawn from the
   independent judge only. Section 4.4 reports the one conflicted cell (Opus 5 never
   preferring the original on `launder_api` pairs, 0.0%, with a 0.0% position-flip
   rate) and discards rather than interprets it.

3. **Relationship to the evaluated toolkit.** This work is a research fork of the
   MarkLLM toolkit (Apache-2.0). The author is not affiliated with its developers,
   did not consult them, and they did not review the manuscript. The calibration
   findings concern that toolkit's shipped default configuration.

### Ethics approval

This study involved no human participants and no animals, and therefore did not
require review by an institutional research ethics committee. Three points support
that determination and are stated explicitly because the study's inputs and
instruments are unusual.

First, **the human-text baseline is published text, not participant data.** The 4,000
human windows of Study S1 are verbatim contiguous excerpts from public Wikimedia
projects (Turkish and English Wikipedia, dump `20231101`; Turkish Wikisource, dump
`20231201`), released by their authors under CC BY-SA 3.0 (or later) and GFDL. No
person was recruited, contacted, observed or profiled; no personal data was
collected; no attempt was made to identify article authors, and the only
author-related information retained is the page identifier that makes the
licence-required attribution link constructible (`ATTRIBUTION.md`,
`ATTRIBUTION_pages.tsv`). Named individuals occur in the excerpts only incidentally,
as public-figure mentions in already published encyclopedic and literary prose.

Second, **the LLM judges of Study S2 are measurement instruments, not participants.**
The 788 pairwise verdicts were produced by two software systems executing a fixed,
pre-registered prompt protocol. A language model has no welfare interests, cannot be
harmed, cannot give or withhold informed consent, and cannot be withdrawn from a
study; its outputs are readings of an instrument in the same sense as the output of
an automatic classifier, and they are validated the way an instrument is validated:
with blind calibration items (identical pairs and different-prompt pairs), both-order
presentation, and a pre-declared position-flip reliability bound of 30% (Sections 3.5
and 4.4). Treating these systems as human annotators would misdescribe both the
protocol and the epistemic status of the resulting numbers. Human-subjects
protections consequently do not apply, and none were needed.

Third, **on the dual-use character of the laundering result.** The paper reports a
working attack that degrades all three watermark schemes while preserving meaning.
The author judges publication to be the responsible course. The attack requires no
watermark key, no knowledge of which scheme was used and no privileged access; it
consists of asking a widely available commercial model to rewrite a text, and its
measured cost over the entire corpus was USD 17.704. It is therefore already
available to any adversary and confers no capability that publication creates. What
publication does create is a measurement that defenders can act on: the threshold
recalibration prescribed in Section 5.1 and the fragility pattern of
Section 5.2 cannot be acted upon by an operator who does not know the size of the
effect. The attacked texts are released so that detection countermeasures can be
evaluated against the same material; no defence is proposed here, and the paper says
so.

### Consent to participate

Not applicable. The study involved no human participants, so no informed consent was
sought or required. Reuse of the Wikimedia-derived text is governed by its CC BY-SA
licence and is a matter of licence compliance and attribution
(`ATTRIBUTION.md`), not of consent.

### Consent to publish

Not applicable. The manuscript contains no data, images or details relating to an
identifiable individual.

### Data, Material and/or Code availability

All code, corpora, detector scores, attacked texts and judge annotations behind this
paper are openly available in the repository
<https://github.com/alicetinkaya76/turkish-llm-watermarking> (Çetinkaya, 2026), at the
release tag `v1.2.0-paper`, which freezes the exact code, data and manuscript state
from which every reported number was produced. That release is archived at Zenodo and
is reached through the concept DOI 10.5281/zenodo.22168552
(<https://doi.org/10.5281/zenodo.22168552>), which resolves to the most recent version
and lists the version DOI of each. Readers reproducing this article should take the
version tagged `v1.2.0-paper`. An earlier release, `v1.1.0-paper`
(10.5281/zenodo.22168553), predates the corrections described in Section 3.3 and the
reference revisions, and is superseded; we record it here rather than deleting it,
because it has a DOI and a DOI should not silently change what it points to.

The release contains 4,000 human text windows (1,500 Turkish Wikipedia, 1,500
word-matched English Wikipedia, 1,000 Turkish Wikisource), 384 generated Turkish
texts across four arms, 3,840 attacked texts in 40 files, 58,161 detector scores
(including the length-controlled rescoring and the eight-key sweep), 788 pairwise
judge verdicts, and the combined score table of 6,336 rows. Reproducibility
provisions are described in Section 7: the upstream MarkLLM toolkit is pinned at
commit `c45ddc40`, the prompt file is content-addressed (SHA-256 prefix
`8fcbe4074b46`), every manuscript number is regenerated from the data into
`paper/numbers.json` by `pilot/make_paper_numbers.py`, and the three
pre-registrations are commits in the repository history, each made before the
corresponding data was collected: `8f8df72` (S1 hypotheses), `cbcb988` (S2 protocol
and decision rule), `5c4f323` (second register). We state precisely what this does and
does not guarantee. The commit hashes bind the registered content cryptographically
and fix its position in the history, so a reader can verify that no later commit
silently altered a registration. The wall-clock dates are a different matter. The
repository was first published on 2026-08-29 and archived at Zenodo on 2026-08-30,
and those are third-party timestamps; but both postdate the data collection, so
neither independently separates registration from data. The asserted dates of
2026-08-23 to 2026-08-25 rest on the author's local repository history, which an
author can in principle rewrite before first publication. We report this rather than
letting the phrase "pre-registered" carry more weight than the evidence supports, and
future registrations in this line of work will be anchored to a third-party timestamp
at the moment of registration. The known limitations of the released
resource are stated at its top level in `BENCHMARK.md`.

**The licensing of this release is deliberately not uniform, and users must consult
`DATA_LICENSE.md` before reuse.** Different components derive from sources with
different terms and are redistributed accordingly: code is Apache-2.0 (as is upstream
MarkLLM); the Wikimedia-derived human windows are CC BY-SA 3.0 (or later) and GFDL
and carry a ShareAlike obligation that propagates to any adaptation incorporating
them; the round-trip-translation outputs (`att_*_rtt.jsonl`) are labelled CC BY-NC
4.0 under a deliberately restrictive reading of an unresolved question about whether
a non-commercial model licence reaches model outputs; the generated, attacked and
externally laundered texts and the judge verdicts are CC BY 4.0; and the detector
scores and derived metrics are CC0 1.0 as facts. `DATA_LICENSE.md` gives the
per-path table, states which readings are contested and why the restrictive one was
chosen, and explains how to assemble a commercially usable subset. It is the
authoritative statement. The archive record's licence field is set to "Other (Open)"
for this reason: no single identifier describes the deposit, and that field is not a
blanket grant. Users must determine the applicable terms from the component they
actually reuse.

Because the repository is a fork of MarkLLM, the release and its archived snapshot
also carry roughly 330 MB of upstream files that this study never reads: C4 excerpts
shipped by upstream as evaluation fixtures, under ODC-BY together with the Common
Crawl terms of use, and dictionaries, cluster mappings and precomputed counts for the
XSIR, SIR and watermark-stealing components, redistributed by upstream under
Apache-2.0. These are not part of the released benchmark, we make no claim over them,
and we did not independently verify upstream's labelling of the XSIR dictionaries.
`DATA_LICENSE.md` itemises them and describes the roughly 35 MB subset that is
self-contained for every number reported here.

### Author contributions

Ali Çetinkaya is the sole author of this manuscript and contributed as follows
(CRediT): Conceptualization; Methodology; Software; Validation; Formal analysis;
Investigation; Resources; Data curation; Writing – original draft; Writing – review
and editing; Visualization; Project administration. The author read and approved the
final manuscript and takes full responsibility for its content.

### Declaration of generative AI use

Generative AI systems were used in this work in three distinct ways. They are
separated here because they carry different implications, and because the third is
the one on which readers are entitled to a clear statement.

**(a) As the object of study: the attack instrument.** Claude Opus 5, accessed
through the Anthropic API, generated the `launder_api` attack corpus (Section 3.2).
Here the model is not a tool used to produce the paper but the adversary the paper
measures: the external, closed-weight rewriter of the threat model (Section 3.2 declines to call it stronger, because no benchmark here licenses a capability ordering). The
generation settings, the measured cost (USD 17.704) and the raw laundered outputs are
all in the release, so every detection score computed on those texts can be
recomputed exactly. As Section 6 states, the attack generation itself may not be
re-creatable against a future version of a closed commercial model, and the result is
therefore reported as an existence demonstration rather than as a stable measurement
of a fixed system.

**(b) As measurement instruments: the judges.** Claude Opus 5 and gpt-oss-120b
(served via Groq) produced the 788 pairwise meaning- and fluency-preservation
verdicts of Study S2 (Sections 3.5 and 4.4), under a protocol pre-registered at
commit `cbcb988` before the run: pairwise-only judging, both presentation orders,
blind calibration items passed before any real verdict was read, a 30% position-flip
reliability bound, two model families, and a requirement that both judges agree
before any `launder_api` verdict is accepted, precisely because Opus 5 produced those
texts. The full verdict file is released. These outputs are data reported in the
paper, not text written into the paper.

Uses (a) and (b) are documented in Methods, are reported with their costs and their
failure modes, and did not draft, edit or phrase any part of this manuscript.

**(c) As a coding and drafting assistant.** Claude Opus 5 was used as an assistant
during implementation of the experimental code and analysis pipeline and during
drafting and editing of the manuscript text. This use is visible in the public
repository: of the 31 commits the author contributed to this fork, 20 carry the git
trailer `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. That trailer is a
machine-readable provenance marker emitted by the tooling to record that an AI
assistant participated in producing a commit. **It is not, and is not intended as, a
claim of authorship.** No AI system is an author of this paper, and none could be: an
AI system cannot take responsibility for the content, cannot approve a manuscript,
cannot respond to correspondence, and cannot be accountable for the accuracy and
integrity of the work, which are the conditions under which authorship is granted. The author
reviewed all generated code and all generated text, verified the behaviour of the
pipeline against the data, and is solely accountable for the design, the analysis,
the interpretation, the claims and any errors.

Two structural safeguards limit what this assistance could have introduced. First, no
scientific claim in this paper rests on unverified generated text: every reported
number is regenerated from the underlying data by code into `paper/numbers.json`
(Section 7), no number is typed by hand, and a regime gate refuses to emit a report
when the active configuration does not match the sealed run configuration. Second,
generative AI was not used to create, augment or alter the research data: the human
corpus consists of verbatim Wikimedia excerpts, the generated corpus comes from
Qwen3-14B under logged settings, and the detector scores are computed by the pinned
MarkLLM implementations. The role of the assistant was confined to writing code that
the author reviewed and to language editing of text the author wrote and approved.

---

## References

Aaronson, S. (2023, August 17). *Watermarking of large language models* [Conference presentation]. Large Language Models and Transformers Workshop, Simons Institute for the Theory of Computing, Berkeley, CA, United States. https://simons.berkeley.edu/talks/scott-aaronson-ut-austin-openai-2023-08-17

Aaronson, S., & Kirchner, H. (2022). *Watermarking GPT outputs* [Slides]. https://www.scottaaronson.com/talks/watermark.ppt

Al Ghanim, M., Xue, J., Hastuti, R. P., Zheng, M., Solihin, Y., & Lou, Q. (2025). Evaluating the robustness and accuracy of text watermarking under real-world cross-lingual manipulations. In *Findings of the Association for Computational Linguistics: EMNLP 2025* (pp. 7396–7416). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.findings-emnlp.390

Bamber, D. (1975). The area above the ordinal dominance graph and the area below the receiver operating characteristic graph. *Journal of Mathematical Psychology*, *12*(4), 387–415. https://doi.org/10.1016/0022-2496(75)90001-2

Bulat, O. (2022). *zeyrek: Python morphological analyzer and lemmatizer for Turkish* (Version 0.1.3) [Computer software]. Python Package Index. https://pypi.org/project/zeyrek/0.1.3/

Çetinkaya, A. (2026). *turkish-llm-watermarking: Code and data for TR-WM-EVAL, a Turkish watermark-evaluation benchmark* (Version 1.1.0-paper) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22168553

Dathathri, S., See, A., Ghaisas, S., Huang, P.-S., McAdam, R., Welbl, J., Bachani, V., Kaskasoli, A., Stanforth, R., Matejovicova, T., Hayes, J., Vyas, N., Al Merey, M., Brown-Cohen, J., Bunel, R., Balle, B., Cemgil, T., Ahmed, Z., Stacpoole, K., … Kohli, P. (2024). Scalable watermarking for identifying large language model outputs. *Nature*, *634*(8035), 818–823. https://doi.org/10.1038/s41586-024-08025-4

Fernandez, P., Chaffin, A., Tit, K., Chappelier, V., & Furon, T. (2023). Three bricks to consolidate watermarks for large language models. In *2023 IEEE International Workshop on Information Forensics and Security (WIFS)* (pp. 1–6). IEEE. https://doi.org/10.1109/WIFS58808.2023.10374576

Han, X., Li, Q., Ni, J., & Zulkernine, M. (2025). Robustness assessment and enhancement of text watermarking for Google's SynthID. In *2025 IEEE 24th International Conference on Trust, Security and Privacy in Computing and Communications (TrustCom)* (pp. 942–949). IEEE. https://doi.org/10.1109/TrustCom66490.2025.00109

He, Z., Zhou, B., Hao, H., Liu, A., Wang, X., Tu, Z., Zhang, Z., & Wang, R. (2024). Can watermarks survive translation? On the cross-lingual consistency of text watermark for large language models. In *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)* (pp. 4115–4129). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.acl-long.226

Hou, A., Zhang, J., He, T., Wang, Y., Chuang, Y.-S., Wang, H., Shen, L., Van Durme, B., Khashabi, D., & Tsvetkov, Y. (2024). SemStamp: A semantic watermark with paraphrastic robustness for text generation. In *Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)* (pp. 4067–4082). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.naacl-long.226

Khachaturov, D., Mullins, R., Shumailov, I., & Dathathri, S. (2025). *Watermarking needs input repetition masking* (arXiv:2504.12229). arXiv. https://doi.org/10.48550/arXiv.2504.12229

Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I., & Goldstein, T. (2023). A watermark for large language models. In *Proceedings of the 40th International Conference on Machine Learning* (Proceedings of Machine Learning Research, Vol. 202, pp. 17061–17084). PMLR. https://proceedings.mlr.press/v202/kirchenbauer23a.html

Kirchenbauer, J., Geiping, J., Wen, Y., Shu, M., Saifullah, K., Kong, K., Fernando, K., Saha, A., Goldblum, M., & Goldstein, T. (2024). On the reliability of watermarks for large language models. In *The Twelfth International Conference on Learning Representations*. https://openreview.net/forum?id=DEJIDCmWOz

Krishna, K., Song, Y., Karpinska, M., Wieting, J., & Iyyer, M. (2023). Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. In *Advances in Neural Information Processing Systems 36* (pp. 27469–27500). Neural Information Processing Systems Foundation. https://doi.org/10.52202/075280-1195

Kuditipudi, R., Thickstun, J., Hashimoto, T., & Liang, P. (2024). Robust distortion-free watermarks for language models. *Transactions on Machine Learning Research*. https://openreview.net/forum?id=FpaCL1MO2C

Liang, J., Wang, Z., Hong, S., Ji, S., & Wang, T. (2025). Watermark under fire: A robustness evaluation of LLM watermarking. In *Findings of the Association for Computational Linguistics: EMNLP 2025* (pp. 21050–21074). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.findings-emnlp.1148

Liu, A., Pan, L., Hu, X., Meng, S., & Wen, L. (2024). A semantic invariant robust watermark for large language models. In *The Twelfth International Conference on Learning Representations*. https://openreview.net/forum?id=6p8lpe4MNf

Mohamed, A., & Gubri, M. (2025). *Is multilingual LLM watermarking truly multilingual? Scaling robustness to 100+ languages via back-translation* (arXiv:2510.18019). arXiv. https://doi.org/10.48550/arXiv.2510.18019

Nemecek, A., Zafar, O., Ganguly, D., Singh, V., Chaudhary, V., & Ayday, E. (2026). *Auditing cross-lingual fairness in language model watermarking* (arXiv:2608.20047). arXiv. https://doi.org/10.48550/arXiv.2608.20047

Newcombe, R. G. (2006). Confidence intervals for an effect size measure based on the Mann–Whitney statistic. Part 2: Asymptotic methods and evaluation. *Statistics in Medicine*, *25*(4), 559–573. https://doi.org/10.1002/sim.2324

NLLB Team, Costa-jussà, M. R., Cross, J., Çelebi, O., Elbayad, M., Heafield, K., Heffernan, K., Kalbassi, E., Lam, J., Licht, D., Maillard, J., Sun, A., Wang, S., Wenzek, G., Youngblood, A., Akula, B., Barrault, L., Mejia Gonzalez, G., Hansanti, P., … Wang, J. (2024). Scaling neural machine translation to 200 languages. *Nature*, *630*(8018), 841–846. https://doi.org/10.1038/s41586-024-07335-x

Pan, L., Liu, A., He, Z., Gao, Z., Zhao, X., Lu, Y., Zhou, B., Liu, S., Hu, X., Wen, L., King, I., & Yu, P. S. (2024). MarkLLM: An open-source toolkit for LLM watermarking. In *Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing: System Demonstrations* (pp. 61–71). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.emnlp-demo.7

Pang, Q., Hu, S., Zheng, W., & Smith, V. (2024). No free lunch in LLM watermarking: Trade-offs in watermarking design choices. In *Advances in Neural Information Processing Systems 37* (pp. 138756–138788). Neural Information Processing Systems Foundation. https://doi.org/10.52202/079017-4402

Panickssery, A., Bowman, S. R., & Feng, S. (2024). LLM evaluators recognize and favor their own generations. In *Advances in Neural Information Processing Systems 37* (pp. 68772–68802). Neural Information Processing Systems Foundation. https://doi.org/10.52202/079017-2197

Park, S., Park, H., An, H., & Han, Y.-S. (2026). A linguistics-aware LLM watermarking via syntactic predictability. In *Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)* (pp. 45629–45647). Association for Computational Linguistics. https://doi.org/10.18653/v1/2026.acl-long.2115

Piet, J., Sitawarin, C., Fang, V., Mu, N., & Wagner, D. (2025). MARKMyWORDS: Analyzing and evaluating language model watermarks. In *2025 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML)* (pp. 68–91). IEEE. https://doi.org/10.1109/SaTML64287.2025.00012

Rust, P., Pfeiffer, J., Vulić, I., Ruder, S., & Gurevych, I. (2021). How good is your tokenizer? On the monolingual performance of multilingual language models. In *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)* (pp. 3118–3135). Association for Computational Linguistics. https://doi.org/10.18653/v1/2021.acl-long.243

Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., & Feizi, S. (2025). Can AI-generated text be reliably detected? Stress testing AI text detectors under various attacks. *Transactions on Machine Learning Research*. https://openreview.net/forum?id=OOgsAZdFOt

Tu, S., Sun, Y., Bai, Y., Yu, J., Hou, L., & Li, J. (2024). WaterBench: Towards holistic evaluation of watermarks for large language models. In *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)* (pp. 1517–1542). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.acl-long.83

Wang, L., Yang, N., Huang, X., Yang, L., Majumder, R., & Wei, F. (2024). *Multilingual E5 text embeddings: A technical report* (arXiv:2402.05672). arXiv. https://doi.org/10.48550/arXiv.2402.05672

Wikimedia Foundation. (2023a). *Wikipedia* (Version 20231101) [Data set]. Hugging Face. https://huggingface.co/datasets/wikimedia/wikipedia

Wikimedia Foundation. (2023b). *Wikisource* (Version 20231201) [Data set]. Hugging Face. https://huggingface.co/datasets/wikimedia/wikisource

Yang, A., Li, A., Yang, B., Zhang, B., Hui, B., Zheng, B., Yu, B., Gao, C., Huang, C., Lv, C., Zheng, C., Liu, D., Zhou, F., Huang, F., Hu, F., Ge, H., Wei, H., Lin, H., Tang, J., … Qiu, Z. (2025). *Qwen3 technical report* (arXiv:2505.09388). arXiv. https://doi.org/10.48550/arXiv.2505.09388

Zhang, H., Edelman, B. L., Francati, D., Venturi, D., Ateniese, G., & Barak, B. (2024). Watermarks in the sand: Impossibility of strong watermarking for language models. In *Proceedings of the 41st International Conference on Machine Learning* (Proceedings of Machine Learning Research, Vol. 235, pp. 58851–58880). PMLR. https://proceedings.mlr.press/v235/zhang24o.html

Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. In *Advances in Neural Information Processing Systems 36* (pp. 46595–46623). Neural Information Processing Systems Foundation. https://doi.org/10.52202/075280-2020
