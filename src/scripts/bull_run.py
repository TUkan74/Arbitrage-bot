import ccxt, csv, datetime

exchange   = ccxt.binance()
symbol     = 'BTC/USDT'
timeframe  = '1h'
since_ms   = exchange.parse8601('2025-07-10T00:00:00Z')
until_ms   = exchange.parse8601('2025-07-15T00:00:00Z')

rows = []
while since_ms < until_ms:
    batch = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=1000)
    if not batch:
        break
    rows.extend(batch)
    since_ms = batch[-1][0] + 1          # next candle

with open('btc_usdt_1h_20250710_0714.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['timestamp', 'close_price'])
    for ts, _o, _h, _l, c, _v in rows:
        stamp = datetime.datetime.utcfromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S')
        w.writerow([stamp, c])
print("Wrote btc_usdt_1h_20250710_0714.csv  –", len(rows), "rows")