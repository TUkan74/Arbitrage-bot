import pandas as pd

freq = pd.read_csv("tables/symbol_frequency.csv")
freq = freq.sort_values("unique_hits", ascending=False)

k = 7                                      # choose any k
top_k = freq.head(k)

share = top_k["unique_hits"].sum() / freq["unique_hits"].sum() * 100
symbol_list = ", ".join(top_k["sym"].tolist())

print(f"Top {k} symbols: {symbol_list}")
print(f"Share of unique opportunities: {share:.1f} %")
