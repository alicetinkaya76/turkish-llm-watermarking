# Attribution for the Wikimedia-derived text in this repository

The human-text windows in `results_insan/insan_*.jsonl` are excerpts from
Wikimedia projects and are licensed **CC BY-SA 3.0 (or later) and GFDL**.
Wikimedia's Terms of Use accept attribution via a hyperlink or URL to the
article; every record in our files carries the `pageid` that makes such a link
constructible, and the full list is in `ATTRIBUTION_pages.tsv`.

## Sources

| Collection | Project | Dump | Windows | File |
|---|---|---|---|---|
| Turkish Wikipedia | `tr.wikipedia.org` | `20231101.tr` | 1,500 | `results_insan/insan_tr.jsonl` |
| English Wikipedia | `en.wikipedia.org` | `20231101.en` | 1,500 | `results_insan/insan_en.jsonl` |
| Turkish Wikisource | `tr.wikisource.org` | `wikisource 20231201.tr` | 1,000 | `results_insan/insan_tr_wikisource.jsonl` |

## How to attribute an individual window

For a record with `pageid` P from domain D, the canonical link is:

```
https://D/?curid=P
```

For example, `pageid` 10 from `tr.wikipedia.org` resolves to
<https://tr.wikipedia.org/?curid=10>. The article's authors are listed in its
revision history, which is the attribution the licence requires and which the
link reaches.

## Extraction method

Windows were drawn from the Hugging Face `wikimedia/wikipedia` and
`wikimedia/wikisource` dumps named above. Each window is a contiguous,
sentence-boundary-respecting excerpt targeting 365 words, selected with a fixed
seed; articles shorter than 250 words were skipped. The extraction code is
`pilot/dev_insan_fpr.py`. No text was altered: windows are verbatim excerpts.

## ShareAlike

Adaptations that incorporate this text must be released under CC BY-SA. See
`DATA_LICENSE.md` for how this interacts with the other components.
