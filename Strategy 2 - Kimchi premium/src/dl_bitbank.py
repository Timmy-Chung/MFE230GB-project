"""Download bitbank (Japan) JPY-market daily candles, used for the Japan placebo.

Usage: python -I src/dl_bitbank.py data/raw/bitbank

bitbank's 1-day candles are stamped at 00:00 UTC, the same day boundary as Binance and Upbit.
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research; MFE230GB replication)"}


def get(url, tries=5):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1.0 * (k + 1))
        except Exception:
            time.sleep(1.0 * (k + 1))
    return None


pairs = [p["name"] for p in get("https://api.bitbank.cc/v1/spot/pairs")["data"]["pairs"] if p["name"].endswith("_jpy")]
json.dump(pairs, open(os.path.join(OUT, "_pairs.json"), "w"))
for p in pairs:
    path = os.path.join(OUT, f"{p}.csv")
    if os.path.exists(path):
        continue
    rows = []
    for yr in range(2017, 2027):
        d = get(f"https://public.bitbank.cc/{p}/candlestick/1day/{yr}")
        time.sleep(0.15)
        if not d or d.get("success") != 1:
            continue
        for c in d["data"]["candlestick"][0]["ohlcv"]:
            o, h, l, cl, v, ts = c
            rows.append((time.strftime("%Y-%m-%d", time.gmtime(ts / 1000)), o, h, l, cl, v))
    rows = sorted(set(rows))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        w.writerows(rows)
    print(p, len(rows), rows[0][0] if rows else "-", flush=True)
print("done")
