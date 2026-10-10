#!/usr/bin/env bash
# Rebuild Strategy 2 (Kimchi Premium) from public data.
# Full run: about 45 minutes, mostly downloads. With the processed data shipped in
# data/processed (and the coin checks in output/tables) you can skip the downloads:
#   SKIP_DOWNLOAD=1 bash run_all.sh      (about 8 minutes)
set -euo pipefail
cd "$(dirname "$0")"
PY="python3 -I"

if [ "${SKIP_DOWNLOAD:-0}" != "1" ]; then
  mkdir -p data/raw
  echo "[1/4] Upbit daily candles (four parallel shards)"
  for k in 0 1 2 3; do $PY src/dl_upbit.py data/raw/upbit "$k" 4 > "data/raw/dl_upbit_$k.log" 2>&1 & done
  wait
  echo "[2/4] bitbank (Japan placebo) and FRED"
  $PY src/dl_bitbank.py data/raw/bitbank
  $PY src/dl_fred.py data/raw/fred
  echo "[3/4] Binance archive: symbol lists, spot and perpetual klines, funding"
  $PY src/dl_lists.py data/raw
  $PY src/dl_binance.py data/raw
  echo "[4/4] daily panels"
  $PY src/build_panel.py
fi

# Optional: JetBrains Mono, so the slide figures look as published (falls back to the default font)
FONTS_DIR="${FONTS_DIR:-data/fonts}"
if [ ! -d "$FONTS_DIR" ]; then
  mkdir -p "$FONTS_DIR"
  for f in Regular Medium SemiBold Bold; do
    curl -s -f -m 30 -o "$FONTS_DIR/JetBrainsMono-$f.ttf" \
      "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-$f.ttf" || true
  done
fi

$PY src/run_backtest.py       # reported window (Oct 2021 - Sep 2026): main rule, cost grid, Japan placebo
$PY src/run_backtest.py full  # pre-registered 2020-26 run: variants, robustness grid, randomization
$PY src/run_analysis.py       # H1-H4, overlay, risk analysis (reported window)
$PY src/make_figures.py "$FONTS_DIR"
$PY src/slide_numbers.py      # every number on the slides
$PY src/export_page_data.py
$PY src/build_page.py         # output/page/kimchi_premium.html
echo "done: tables in output/tables, figures in output/figures, page in output/page"
