import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

data_dir = Path(".")

opps = []
for fn in ["logs/arbitrage/arbitrage.opps.csv",
           "logs/arbitrage/arbitrage_1.opps.csv",
           "logs/arbitrage/arbitrage_48.opps.csv"]:
    df = pd.read_csv(data_dir / fn)
    opps.extend(df["profit_pct"].values)

plt.figure(figsize=(6,4))
plt.hist(opps, bins=50, edgecolor="black")
plt.axvline(0.5, color="red", ls="--", lw=1, label="0.5 % threshold")
plt.xlabel("Net profit [%]")
plt.ylabel("Frequency")
plt.title("Histogram of net profit percentages (all runs)")
plt.legend()
plt.tight_layout()
Path("figs").mkdir(exist_ok=True)
plt.savefig("figs/profit_hist.pdf", dpi=300)
plt.close()
print("Saved figs/profit_hist.pdf")
