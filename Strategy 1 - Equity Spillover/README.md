# MFE 230GB Final Project — Equity Spillover into FX

Replication package for *Designing and Testing Global Trading Strategies* (Currency Markets, Fall 2026). Presented 8 October 2026.

**Strategy.** When a country's stock market beats the US, investors buy its assets and must buy its currency first (Topics 4–5: flows set prices, demand is inelastic; Topics 1, 3: the dollar is the other side of the trade). Each month end, for each currency: if its local-currency share-price index beat the US index over the past six months, go long the currency against USD for the next month; otherwise go short. Equal weight (1/9 each), gross 100%, no leverage, no vol targeting. Nine G10 currencies at a 2 bp half-spread; nine floating EM currencies at 15 bp. The rule and the lookback were chosen on 2000–2015 and reported on 2016–2026 untouched.

**Headline, monthly, after costs, Jan 2000 – Oct 2026.**

| | 2000–15 (selection) | 2016–26 (validation) | Full | Vol | Max DD |
|---|---|---|---|---|---|
| G10 book | 0.46 | 0.38 | 0.41 | 4.5% | −9% |
| EM floats book | 0.42 | 0.24 | 0.36 | 5.3% | −10% |
| Best cross-sectional construction of 64 (G10, chosen in sample) | 0.70 | 0.07 | 0.46 | | |

G10 is country selection: with the dollar as one of ten legs, the USD leg is 0.78% of 1.92% gross a year and seven of the other nine currencies add. EM is a dollar trade: the USD leg is 2.08% of 2.38% gross, the dollar component alone earns Sharpe 0.38 and the book with it removed earns −0.17.

## What to open

- `index.html` — self-contained interactive page (Plotly from CDN; all data inlined): constructions scatter, cumulative returns, positions by year, attribution by currency, EM floats, risk table.
- `MFE230GB_EquitySpillover_Deck.pdf` — the 11-slide class deck. `MFE230GB_EquitySpillover_Script.pdf` / `presentation_script.md` — the six-minute script with the Q&A answers.
- `output/equity_results.json` — every number for all 70 constructions, both universes, with the placebo and robustness checks.

## Reproduce

```bash
python3 -m pip install -r requirements.txt
python3 equity_spillover.py            # both books, all 70 constructions, decomposition, placebo, checks -> output/equity_results.json, output/equity_monthly_{DM,EM}.csv
python3 equity_spillover_floats.py     # the nine floating EM currencies (slide 8)                       -> output/equity_floats.json
python3 equity_spillover_slides.py     # positions by year, 10-leg attribution, risk table (slides 7, 9, 10) -> output/equity_slides.json
python3 code/build_equity_html.py      # index.html
```

Each script runs from `data/` only (no network). `python3 equity_spillover.py --fetch` re-downloads the non-FRED inputs from DBnomics, the ECB and the IMF. Python 3.10+, pandas, numpy.

## Method

**Signal.** `sig_c,t = log E_c,t − log E_c,t−6 − (log E_US,t − log E_US,t−6)` using OECD monthly share-price indices in local currency, so no exchange-rate move enters the signal. Position for month t+1: `w_c = sign(sig_c,t) / N`. Excess return: spot change plus the 3-month rate differential where a rate series exists (spot-only for BRL, COP, INR, CNY). Cost: half-spread × turnover (sum of absolute weight changes).

**Construction search (slides 3–4).** Two families, all with month-end rebalancing. *Cross-sectional:* rank currencies against each other; measure ∈ {local return, USD return, return over cash, vol-adjusted} × lookback ∈ {1, 3, 6, 12} × weighting ∈ {tercile long 3 / short 3, rank-proportional} × holding ∈ {1, 3 months} = 64. Longs equal shorts, so no net dollar position. *Dollar-relative:* no ranking; measure ∈ {relative to US, own return} × lookback ∈ {3, 6, 12} = 6. Selection on 2000–2015, validation 2016–2026. The four named constructions in the deck are A (local 6m tercile), B (vol-adjusted 6m rank, the in-sample best), C (relative-to-US 6m, the book) and D (own-return 6m).

**EM universe (slide 8).** Floating currencies per Topic 2 / IMF AREAER: BRL MXN ZAR CLP COP PLN HUF CZK KRW. Managed currencies (INR CNY IDR TRY: daily fixing or heavy intervention) are excluded because reserves absorb the flow; for reference the rule on them earns −0.38 out of sample, and `equity_spillover.py` reports the 13-currency book and the float/managed split. CNH is tradable offshore but tracks the fixed-and-banded onshore CNY (spot vol ≈ 3% a year vs 10–16% for the floats).

**Dollar component.** Because every currency is judged against the US, the book is net long or net short dollars. "Alone" = long USD vs the equal-weight basket when the US index beat the average foreign index over six months, else the reverse. "Removed" = the book minus net position × basket return. G10: removed 0.42, alone 0.13. EM floats: alone 0.38, removed −0.17.

**Attribution (slides 7, 9).** Ten legs, USD included. Each currency's net exposure (USD = minus the net position) times its return against the equal-weight basket of all ten; the ten sum exactly to the book before costs. G10: USD 0.78%, other nine 1.14% (seven positive), costs 0.07%, book 1.85% a year. EM floats: USD 2.08%, other nine 0.30% (four negative), costs 0.49%, book 1.89%.

**Checks.** Placebo: the whole signal matrix shifted forward in time by a random 12–200 months, 200 draws, p = 0.03 for both books. Spot-only (no carry): G10 0.45, EM 0.29. Signal used one month late: G10 0.12, EM 0.40. FX momentum with the same rule in G10: −0.30. G10 at a 10 bp half-spread: 0.34; EM at 2 bp: 0.44. Correlation with the broad dollar index: 0.03 and 0.01. Longest drawdown 36 months (G10) and 63 months (EM); skew 0.0 and 0.4; monthly 95% VaR −1.8% and −2.1%.

## Data (all in `data/`)

| Series | Files | Source |
|---|---|---|
| Share-price indices, monthly, local currency, to May 2026 | `EQ_<CCY>.csv` (incl. `EQ_USD.csv`) | OECD `DSD_STES@DF_FINMARK` via DBnomics |
| Spot rates, daily | `DEX*.csv` | FRED H.10 (G10, BRL, MXN, ZAR, INR, KRW, CNY) |
| Spot rates, monthly, via EUR/USD | `ECBFX_<CCY>.csv`, `ECBFX_USD.csv` | ECB reference rates (PLN HUF CZK TRY IDR and cross-checks) |
| Spot rates, monthly | `IMFFX_CLP.csv`, `IMFFX_COP.csv` | IMF IFS end-of-period |
| 3-month rates, monthly | `IR3TIB01*.csv` | OECD via FRED |
| Broad dollar index | `DTWEXBGS.csv` | FRED |
| VIX (used only in the risk-on split reported in the results file) | `VIXCLS.csv` | FRED |

The remaining files in `data/` (CPI, Big Mac, Brent, yields, Polymarket, Lustig portfolios) belong to the earlier work described below and are kept so that those scripts also run.

## Earlier work in this package (superseded, kept for the record)

- `code/run_value.py` — a G10 FX value book (CPI real exchange rate + Big Mac, with a funding-currency filter), Sharpe 0.37 after costs, `output/value_results.json`.
- `code/run_strategies.py` and `archive/index_policy_path.html` — the first proposal (Policy Path carry-to-vol with a VIX filter and a Polymarket overlay; EM Terms of Trade), `output/results.json`. This was dropped because the carry-to-vol / VIX construction is the one presented in lecture. A forward-fill bug in its carry signal was found and fixed on 7 Oct 2026; the archived numbers are from the corrected run.
- `code/run_equity.py` is the same code as `equity_spillover.py`.

## AI documentation

Use of AI is allowed; material contributions are listed here.

- **Tools.** Claude Code (Claude Fable 5.1), 7–9 October 2026, in this project folder. Cursor agent (Grok 4.6), 7 October 2026, for the first draft of the earlier proposal.
- **What the AI produced.** The code (`equity_spillover.py`, `equity_spillover_floats.py`, `equity_spillover_slides.py`, `code/build_equity_html.py`), the deck, the presentation script and this README, all from prompts that specified the strategy, the construction families, the universe decisions and the diagnostics to run. It also fetched the OECD, ECB and IMF series through their public APIs (FRED files were downloaded directly).
- **What it did not decide.** The idea itself (equity spillover, with a DM and an EM version), the choice to test many constructions and pick the simplest one that survives out of sample, restricting EM to floating currencies, treating the dollar as one of ten legs in the attribution, and dropping the dollar-hedge discussion because the strategy takes FX risk by design. Those were the student's calls, made in conversation, and are recorded in the script.
- **Audit trail.** Every performance number in the deck, the script and `index.html` is computed by the scripts above from `data/`; the results files are in `output/`. Two earlier drafts were abandoned: a carry-based proposal (lecture material) and an FX value book (`code/run_value.py`).

## Layout

```
project/
  README.md
  requirements.txt
  index.html                          # interactive page (open this)
  MFE230GB_EquitySpillover_Deck.pdf   # class deck, 11 slides
  MFE230GB_EquitySpillover_Script.pdf # six-minute script + Q&A
  presentation_script.md
  equity_spillover.py                 # both books, all 70 constructions, checks
  equity_spillover_floats.py          # nine floating EM currencies
  equity_spillover_slides.py          # positions, attribution, risk
  code/build_equity_html.py           # builds index.html
  code/run_equity.py                  # same as equity_spillover.py
  code/run_value.py, code/run_strategies.py, code/build_html.py   # earlier work
  data/                               # all inputs (see table)
  output/                             # results files
  archive/                            # earlier proposal deck and page
```
