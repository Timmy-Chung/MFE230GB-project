"""Download Binance public-archive data (data.binance.vision) for every coin that trades
on Upbit (KRW) or bitbank (JPY): spot USDT daily klines, USDT-margined perpetual daily
klines and perpetual funding settlements. Delisted Binance symbols are included.

Usage: python -I src/dl_binance.py data/raw

Writes data/raw/binance/{spot,perp,funding}/<SYMBOL>.csv
"""
import csv
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

RAW = sys.argv[1]
OUT = os.path.join(RAW, "binance")
UA = {"User-Agent": "Mozilla/5.0 (research; MFE230GB replication)"}
LAST_MONTH = "2026-09"
PERP_PREFIXES = ["", "1000", "1000000", "1M", "10000"]


def get(url, raw=True, tries=6):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1.0 * (k + 1))
        except Exception:
            time.sleep(1.0 * (k + 1))
    raise RuntimeError(url)


def s3_keys(prefix):
    keys, marker = [], ""
    while True:
        b = get(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix={prefix}&marker={marker}").decode()
        ks = re.findall(r"<Key>([^<]+)</Key>", b)
        keys += ks
        if "<IsTruncated>true</IsTruncated>" in b and ks:
            marker = ks[-1]
        else:
            return [k for k in keys if k.endswith(".zip")]


def month_of(key):
    m = re.search(r"(\d{4}-\d{2})\.zip$", key)
    return m.group(1) if m else None


def read_zip_csv(blob):
    z = zipfile.ZipFile(io.BytesIO(blob))
    with z.open(z.namelist()[0]) as f:
        return list(csv.reader(io.TextIOWrapper(f)))


def ts_to_date(ts):
    ts = int(float(ts))
    if ts > 10**14:      # spot files switched to microseconds in 2025
        ts //= 1000
    return time.strftime("%Y-%m-%d", time.gmtime(ts / 1000))


def fetch_klines(kind, sym):
    """kind: 'spot' or 'perp'"""
    base = "data/spot/monthly/klines" if kind == "spot" else "data/futures/um/monthly/klines"
    path = os.path.join(OUT, kind, f"{sym}.csv")
    if os.path.exists(path):
        return sym, "cached"
    keys = [k for k in s3_keys(f"{base}/{sym}/1d/") if month_of(k) and month_of(k) <= LAST_MONTH]
    rows = {}
    for k in sorted(keys):
        blob = get("https://data.binance.vision/" + k)
        if not blob:
            continue
        for r in read_zip_csv(blob):
            if not r or not r[0].strip().isdigit():
                continue
            d = ts_to_date(r[0])
            # open, high, low, close, volume, quote_volume, n_trades, taker_buy_base, taker_buy_quote
            rows[d] = [r[1], r[2], r[3], r[4], r[5], r[7], r[8], r[9], r[10]]
    if not rows:
        return sym, "none"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume", "quote_volume", "n_trades",
                    "taker_buy_base", "taker_buy_quote"])
        for d in sorted(rows):
            w.writerow([d] + rows[d])
    return sym, len(rows)


def fetch_funding(sym):
    path = os.path.join(OUT, "funding", f"{sym}.csv")
    if os.path.exists(path):
        return sym, "cached"
    keys = [k for k in s3_keys(f"data/futures/um/monthly/fundingRate/{sym}/") if month_of(k) and month_of(k) <= LAST_MONTH]
    out = []
    for k in sorted(keys):
        blob = get("https://data.binance.vision/" + k)
        if not blob:
            continue
        for r in read_zip_csv(blob):
            if not r or not r[0].strip().isdigit():
                continue
            t = int(r[0])
            out.append((time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t / 1000)), r[-1]))
    if not out:
        return sym, "none"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "funding_rate"])
        w.writerows(sorted(set(out)))
    return sym, len(out)


if __name__ == "__main__":
    lists = json.load(open(os.path.join(RAW, "symbol_lists.json")))
    spot_dirs, perp_dirs = set(lists["spot"]), set(lists["perp"])
    upbit = json.load(open(os.path.join(RAW, "upbit", "_markets.json")))
    bases = {m["market"].split("-", 1)[1] for m in upbit}
    try:
        bases |= {p.split("_")[0].upper() for p in json.load(open(os.path.join(RAW, "bitbank", "_pairs.json")))}
    except FileNotFoundError:
        pass
    bases |= {"BTC", "ETH", "MATIC", "RNDR", "FTM", "EOS", "MKR"}   # renamed tickers' old symbols
    spot_syms = sorted(b + "USDT" for b in bases if b + "USDT" in spot_dirs)
    perp_syms = sorted(p + b + "USDT" for b in bases for p in PERP_PREFIXES if p + b + "USDT" in perp_dirs)
    print("bases", len(bases), "spot", len(spot_syms), "perp", len(perp_syms), flush=True)
    json.dump({"spot": spot_syms, "perp": perp_syms}, open(os.path.join(OUT + "_targets.json"), "w"))
    with ThreadPoolExecutor(12) as ex:
        for s, n in ex.map(lambda s: fetch_klines("spot", s), spot_syms):
            print("spot", s, n, flush=True)
        for s, n in ex.map(lambda s: fetch_klines("perp", s), perp_syms):
            print("perp", s, n, flush=True)
        for s, n in ex.map(fetch_funding, perp_syms):
            print("funding", s, n, flush=True)
    print("done")
