"""Parameters fixed in DESIGN.md (pre-registration). Change nothing here without logging it."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
TABLES = os.path.join(ROOT, "output", "tables")
FIGS = os.path.join(ROOT, "output", "figures")
PAGE = os.path.join(ROOT, "output", "page")
for _d in (PROC, TABLES, FIGS, PAGE):
    os.makedirs(_d, exist_ok=True)

# ---- sample
FIRST_FORMATION = "2020-01-06"     # first Monday of 2020 (pre-registered full sample)
LAST_FORMATION = "2026-09-21"      # holding week ends Monday 28 September 2026
SPLIT_DATE = "2023-01-01"          # sub-periods 2020-22 vs 2023-26 (full-sample appendix)
# Reported window: the last five years, October 2021 to September 2026 (deviations log, entry 5)
REPORT_START = "2021-10-04"        # first Monday of October 2021
REPORT_DAILY_START = "2021-10-01"
REPORT_DAILY_END = "2026-09-30"

# ---- universe
EXCLUDE = {
    # fiat- and commodity-pegged tokens
    "USDT", "USDC", "USD1", "USDE", "USDG", "USDS", "PYUSD", "RLUSD", "EURC", "JPYC", "DAI",
    "TUSD", "BUSD", "FDUSD", "USDP", "XAUT", "PAXG",
    # wrapped or staked derivatives
    "WBTC", "WETH", "STETH", "WSTETH", "CBBTC", "WBETH", "BETH", "CBETH",
}
MIN_UPBIT_DAYS = 28               # closes in the past 35 days
MIN_PERP_AGE_DAYS = 28
MIN_UPBIT_TURNOVER_KRW = 500e6    # 7-day average, per day
MIN_PERP_VOLUME_USD = 5e6         # 7-day average, per day
STRICT_UPBIT_TURNOVER_KRW = 2e9
STRICT_PERP_VOLUME_USD = 20e6
SAME_ASSET_MAX_MEDIAN_DEV = 0.15  # median |p_i - kappa|
SAME_ASSET_MIN_CORR = 0.5         # daily return correlation Upbit vs Binance
BLOCKED_CHANNEL = 0.10            # drop coin-week if |pi_bar| > 10%
MIN_COINS = 20

# ---- signal and portfolio
SIGNAL_DAYS = 7
MIN_SIGNAL_DAYS = 5
QUANTILE = 0.2                    # quintiles
COST_BP = 10.0                    # per unit of notional traded
BETA_WINDOW = 90

# ---- overlay
FROTH_WINDOW = 365
FROTH_PCTL = 0.90

# Binance perpetual symbol prefixes that scale the contract (1000SHIBUSDT = 1,000 SHIB)
PERP_MULT = {"": 1, "1000": 1000, "10000": 10000, "1000000": 1000000, "1M": 1000000}

# Ticker renames: Upbit base -> older Binance bases of the same token (1:1 swaps). The new
# symbol's data are used wherever they exist, the old symbol's before that.
RENAMES = {
    "POL": ["MATIC"],      # Polygon MATIC -> POL (2024)
    "RENDER": ["RNDR"],    # Render RNDR -> RENDER (2024)
    "A": ["EOS"],          # EOS -> Vaulta A (2025)
}
# bitbank tickers that differ from Binance
BITBANK_MAP = {"BCC": "BCH"}

EPISODES = {
    "LUNA collapse": ("2022-05-09", "2022-05-15"),
    "FTX collapse": ("2022-11-07", "2022-11-13"),
    "Yen carry unwind": ("2024-08-05", "2024-08-11"),
    "Korean martial-law night": ("2024-12-02", "2024-12-08"),
    "10 Oct 2025 liquidations": ("2025-10-06", "2025-10-12"),
}
