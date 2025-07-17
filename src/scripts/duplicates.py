"""
dedupe_opportunities.py  —  collapses repeated rows that have identical
symbol + (buy_ex, sell_ex) + minute(timestamp) and ranks symbols by
unique-hit frequency.
"""

import pandas as pd
from pathlib import Path

FILES = [
    "logs/arbitrage/arbitrage.opps.csv",
    "logs/arbitrage/arbitrage_1.opps.csv",
    "logs/arbitrage/arbitrage_48.opps.csv",
]

frames = []
for fn in FILES:
    df = pd.read_csv(fn, parse_dates=["timestamp"])
    df["minute"] = df["timestamp"].dt.floor("min")
    frames.append(df)

raw = pd.concat(frames, ignore_index=True)

# collapse duplicates
deduped = (
    raw.drop_duplicates(subset=["sym", "buy_ex", "sell_ex", "minute"])
        .copy()
)

print(f"Raw rows: {len(raw):,}  →  Unique rows: {len(deduped):,}")

# frequency table
freq = (
    deduped.groupby("sym")
           .size()
           .sort_values(ascending=False)
           .rename("unique_hits")
)

freq.to_csv("tables/symbol_frequency.csv")
print("Wrote tables/symbol_frequency.csv")
