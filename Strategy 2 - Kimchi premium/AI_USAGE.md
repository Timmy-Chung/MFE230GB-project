# AI usage

The course allows AI. This file documents what AI produced for Strategy 2 and how the work
was kept honest.

## Tool

Claude (Anthropic), in an agentic Claude session on 7 October 2026 (configured model identifier
`claude-opus-5-5`). The session had a Python environment, web access to the public data sources
listed in README.md, and read access to the Strategy 1 materials (the "Crowded Carry" page and
slides) for consistency of style.

## Prompts

The author's requests, verbatim or as the multiple-choice answers given:

1. "complete the second trading strategy, choose crypto. the presentation should be around 8
   minutes. propose a few strategy for me to choose from."
2. From four proposals (A: Polymarket vs Deribit mispricing; B: the kimchi premium; C:
   stablecoin and exchange flows; D: crypto CIP basis against on-chain arbitrage capital), the
   author chose **B**; the 8 minutes cover the crypto part only; a separate deck and page.
3. After the pre-registered backtest showed a loss, the author chose to **present the result
   as it is** rather than add a post-hoc fix or switch strategy.
4. "report only results in the last 5 years. keep only the most useful robustness test. for the
   slides, I would like it to be more crypto style"

The fourth request changed what is reported, after the full-sample result was known. Claude
implemented it and recorded it as entry 5 of the deviations log in `DESIGN.md`: the reported
window (October 2021 – September 2026) is not an out-of-sample test, the pre-registered
2020–2026 run is still rebuilt by `run_backtest.py full` and shipped, and the slides, page and
README each say so. Claude picked the Japan placebo as the one robustness test to present because
it tests the mechanism (capital controls) directly; the rest of the pre-specified grid stays in
the full-sample folder.

## What the AI produced

* The four strategy proposals, after checking that each data source could be downloaded.
* `DESIGN.md`: hypotheses, signal, rule, robustness grid, written before any return was computed.
* All code in `src/` (downloads, panel construction, backtest, statistics, figures, page build).
* The interactive page (`output/page/kimchi_premium.html`). Its chart kit is reused from the
  Strategy 1 page, which was also built with Claude.
* The slide deck, including speaker notes, restyled in a dark "exchange terminal" look on
  request, and this documentation.

## Safeguards

* **Pre-registration first.** The hypotheses, parameters and robustness tests were written into
  `DESIGN.md` while the data downloaded and before any return or signal statistic was looked at.
  Nothing in the rule was changed afterwards; additions are listed in its deviations log.
* **One exploratory variant, disclosed.** After the main result, exactly one further rule was
  specified and run once (short-only above a 25 bp band). It lost money and is reported, not
  adopted.
* **Placebos and randomization.** The Japan placebo (no capital controls) is the robustness test
  presented; 1,000 random signal shuffles and the full grid are in the full-sample folder.
* **A window chosen after the fact, disclosed.** The five-year reporting window was requested
  after the full-sample loss was known. The results slide says so, and a backup slide, the page,
  the README and `DESIGN.md` give the full-sample numbers beside the five-year ones.
* **Traceable numbers.** The page reads every number from `output/tables` through
  `page_data.json`. Numbers on the slides come from `src/slide_numbers.py`
  (`output/tables/slide_numbers.json`), which recomputes them from the same tables.
* **Reproducibility.** One script rebuilds every output; the randomization uses a fixed seed.
* **Bugs found and fixed during the work** (before any result was reported): a duplicate-column
  error in the beta estimate, sample-end handling for 4-week horizons, and a quintile table that
  used slightly different bins from the backtest (now identical by construction).

## Responsibility

The author is responsible for the content and for checking it before submission. AI output is a
draft to be verified, not a source.
