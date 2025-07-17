"""
Usage:
    poetry run python scripts/fig_profit_vs_btc.py
Assumes:
    - opportunity CSV files live in project root or ./data
    - BTC price CSV: btc_usdt_1h_20250710_0714.csv
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATADIR = Path(".")            # adjust if your CSVs live elsewhere
OUTDIR  = Path("figs"); OUTDIR.mkdir(exist_ok=True)
TABLEDIR = Path("tables"); TABLEDIR.mkdir(exist_ok=True)

OPP_FILES = [
    "logs/arbitrage/arbitrage_48.opps.csv",
    "logs/arbitrage/arbitrage_1.opps.csv",
    "logs/arbitrage/arbitrage.opps.csv",
]

# ---------- load opportunity data -------------------------------------
frames = []
for fn in OPP_FILES:
    df = pd.read_csv(DATADIR / fn, parse_dates=["timestamp"])
    df["hour"] = df["timestamp"].dt.floor("H")
    df = df.rename(columns={"profit_pct": "profit_pct_rel"})
    df["profit_usdt"] = df["profit_pct_rel"] * 10  # notional $1 000 ⇒ 0.01 → $10
    frames.append(df[["hour", "profit_usdt"]])

hourly = (
    pd.concat(frames)
      .groupby("hour")
      .agg(count=("profit_usdt", "size"),
           avg_profit_usdt=("profit_usdt", "mean"))
      .reset_index()
)

# ---------- load BTC hourly close -------------------------------------
btc = (
    pd.read_csv(DATADIR / "btc_usdt_1h_20250710_0714.csv",
                parse_dates=["timestamp"])
      .rename(columns={"timestamp": "hour"})
      .loc[:, ["hour", "close_price"]]
)
btc["abs_ret"] = btc["close_price"].pct_change().abs()

merged = hourly.merge(btc[["hour", "abs_ret"]], on="hour", how="inner")

# ---------- correlation for the write-up ------------------------------
rho = merged["count"].corr(merged["abs_ret"])
print(f"Pearson ρ(count, |BTC ret|) = {rho:.2f}")

# ---------- export LaTeX table ----------------------------------------
(
    hourly.set_index("hour")
          .tail(24)                 # last 24 h for brevity
          .to_latex(TABLEDIR / "hourly_summary.tex",
                    float_format="%.2f")
)

# ---------- dual-axis plot --------------------------------------------
fig, ax1 = plt.subplots(figsize=(7.2, 4.0))
ax2 = ax1.twinx()

ax1.plot(merged["hour"], merged["count"], label="# opportunities", lw=1.4)
ax2.plot(merged["hour"], merged["abs_ret"], label="|BTC return|", ls="--", lw=1.2, color='tab:orange')

ax1.set_xlabel("Hour (UTC)")
ax1.set_ylabel("Opportunity count")
ax2.set_ylabel("Absolute BTC hourly return")

fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.92))
fig.tight_layout()
plt.savefig(OUTDIR / "opps_vs_btc_return.pdf", dpi=300)
plt.close()
print("Saved figs/opps_vs_btc_return.pdf and tables/hourly_summary.tex")
