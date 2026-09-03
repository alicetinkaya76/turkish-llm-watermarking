# Pilot cohort (August 2026): audit evidence for the selection of the two focused attacks

These three files are the summary report, detection table and environment record of an
earlier pilot run that **failed the corpus acceptance gate** and is not part of the study
(generator Qwen2.5-3B-Instruct on Apple MPS, 320-token budget, foreign-script contamination
and short texts; see `summary.md`). The pilot corpus itself is not released.

They are released for one purpose: they document that the two attack conditions carried
into the focused comparisons of the paper (Tables 5 and 6), `rtt` and `launder_api`, were
already the two most destructive attacks on this earlier, independent cohort, and were
designated as such in writing before the study corpus was generated. `summary.md` states,
in its narrowed claim after its own audit: "the major directions (rtt/launder_api most
destructive, morph ineffective, clean at ceiling) hold". The study corpus was generated on
the university HPC on 20-21 August 2026 (`results/env.json`, `results/scores.csv`), and the
analysis code that fixes the pair (`pilot/metrics.py`, commit 4c597d0) was written on
23 August.

What this record shows and does not show is stated in the paper (Section 3.3): the
designation of the pair preceded the study data; the record cannot show that the study's
own aggregate ranking (Table 4), which reproduced the pilot ordering, played no part in
confirming it. File timestamps are local (`stat`): `scores.csv` 2026-08-15,
`detection_metrics.csv` and `summary.md` 2026-08-18.

| file | what |
|---|---|
| `summary.md` | pilot report, including the narrowed-claim audit paragraph |
| `detection_metrics.csv` | per scheme x condition AUROC/TPR on the pilot cohort |
| `env.json` | generator, device and sampling settings of the pilot |

## What the report says about ordering (English gloss)

`summary.md` is in Turkish. Two passages matter for the paper's use of this record.

Section **D3**, headed "'launder_api en yıkıcı saldırı' iddiası GERİ ÇEKİLDİ"
("the claim that launder_api is the most destructive attack is WITHDRAWN"), reports
paired McNemar tests that separate `launder_api` from `rtt` in no scheme (EXP 0.000,
p = 1.000; KGW −0.052, p = 0.522; SynthID −0.125, p = 0.050) and attributes the earlier
headline to a selected minimum point estimate and a winner's-curse effect. Its narrowed
claim is that API laundering produced more detector erosion than local laundering in all
three schemes, while its advantage over round-trip translation is scheme-dependent and
not established.

The **audit paragraph** near the end gives the report's overall narrowed claim: "the major
directions (rtt/launder_api most destructive, morph ineffective, clean at ceiling) hold,
while some sub-orderings change."

Together these fix *which two* conditions are the destructive pair without ordering them.
That is the sense in which the paper (Section 3.3) treats the pair as designated by this
record: the pilot selects the pair and does not anticipate the direction Table 5 estimates.
