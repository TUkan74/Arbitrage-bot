#!/usr/bin/env python3
"""
Extract arbitrage opportunities from console logs such as:

    [2025-07-10 21:13:52] [INFO] Opportunity: HFT/USDT - Buy: BINANCE @ 0.0881, Sell: BITGET @ 0.0891, Profit: 0.93%

For each opportunity we capture:
  timestamp | symbol | buy_ex | buy_px | sell_ex | sell_px | profit_pct

Usage
------
$ poetry run python scripts/summarise_console_log.py  logs/runtime.txt
"""

import re, sys, csv, pathlib, datetime as dt, os
from statistics import median, mean

# Maximum profit percentage considered valid. Opportunities above this value
# are treated as false positives and excluded from summary statistics. This
# mirrors the safeguard in `ArbitrageEngine`.
MAX_PROFIT_THRESHOLD: float = float(os.getenv("ARBITRAGE_MAX_PROFIT", "100"))

PATTERN = re.compile(
    r"\[(?P<ts>[\d\-: ]+)\] .*?"
    r"Opportunity:\s+(?P<sym>[A-Z0-9]+/USDT)\s+-\s+"
    r"Buy:\s+(?P<buy_ex>[A-Z0-9]+)\s+@\s+(?P<buy_px>[0-9.]+),\s+"
    r"Sell:\s+(?P<sell_ex>[A-Z0-9]+)\s+@\s+(?P<sell_px>[0-9.]+),\s+"
    r"Profit:\s+(?P<pct>[0-9.]+)%"
)

def parse_line(line: str):
    m = PATTERN.search(line)
    if not m:
        return None
    d = m.groupdict()
    d["timestamp"] = dt.datetime.strptime(d.pop("ts"), "%Y-%m-%d %H:%M:%S")
    d["buy_px"]   = float(d["buy_px"])
    d["sell_px"]  = float(d["sell_px"])
    d["profit_pct"] = float(d.pop("pct"))
    return d

def main(path: pathlib.Path):
    rows = [parse_line(l) for l in path.open(encoding="utf-8") if "Opportunity:" in l]
    # Drop unparsable lines and suppress rows whose profit_pct indicates an
    # unrealistic (likely false-positive) opportunity.
    rows = [r for r in rows if r and r["profit_pct"] < MAX_PROFIT_THRESHOLD]

    if not rows:
        print("No opportunities found in log.")
        return

    # write raw CSV
    out_csv = path.with_suffix(".opps.csv")
    with out_csv.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    # aggregate
    profits = [r["profit_pct"] for r in rows]
    summary = {
        "window_start": min(r["timestamp"] for r in rows),
        "window_end":   max(r["timestamp"] for r in rows),
        "num_opportunities": len(rows),
        "median_profit_pct": round(median(profits), 3),
        "mean_profit_pct":   round(mean(profits), 3),
        "max_profit_pct":    round(max(profits), 3),
    }

    # print pretty report
    print("\n=== Case-study summary ===")
    for k, v in summary.items():
        print(f"{k.replace('_',' ').title():<22} {v}")

    # save for LaTeX
    summary_csv = path.with_suffix(".summary.csv")
    with summary_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerows(summary.items())

    print(f"\nRaw opportunities -> {out_csv}")
    print(f"Summary CSV       -> {summary_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: summarise_console_log.py path/to/runtime.log")
    main(pathlib.Path(sys.argv[1]))
