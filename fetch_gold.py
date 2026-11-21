#!/usr/bin/env python3
"""Fetch gold price (SGD/g) + SGD->INR and append one row to data/prices.csv."""
import csv, os, re, sys, urllib.request
from datetime import datetime, timezone

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "prices.csv")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def gold():
    html = get("https://mustafajewellery.com/", {"Referer": "https://www.google.com/",
                                                  "Accept-Language": "en-US,en;q=0.9"})
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    found = {k.lower(): float(v) for k, v in
             re.findall(r"(22k-916|24k-999) Jewellery\s*([0-9]+\.[0-9]+)", text, re.I)}
    if "22k-916" not in found or "24k-999" not in found:
        raise RuntimeError("Could not find 22k/24k prices - site layout may have changed")
    return found["22k-916"], found["24k-999"]

def fx(last):
    try:
        import json
        return float(json.loads(get("https://api.frankfurter.dev/v1/latest?base=SGD&symbols=INR"))["rates"]["INR"])
    except Exception as e:
        print(f"FX fetch failed ({e}); reusing last known rate", file=sys.stderr)
        if last: return last
        raise

def last_fx():
    try:
        with open(CSV_PATH) as f:
            rows = list(csv.reader(f))
        return float(rows[-1][3]) if len(rows) > 1 else None
    except Exception:
        return None

def main():
    p22, p24 = gold()
    rate = fx(last_fx())
    if not (50 < p22 < 1000 and 50 < p24 < 1000):
        raise RuntimeError(f"Implausible prices: {p22}, {p24}")
    row = [datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), p22, p24, rate]
    new = not os.path.exists(CSV_PATH)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["timestamp_utc", "sgd_22k_per_g", "sgd_24k_per_g", "sgd_inr"])
        w.writerow(row)
    print("Saved:", row)

if __name__ == "__main__":
    main()
