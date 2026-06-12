"""Generate a synthetic OHLCV CSV for 252 trading days (≈ 1 year)."""
import csv
import random
from datetime import date, timedelta

random.seed(42)

ROWS = 252
START_DATE = date(2025, 1, 2)
START_PRICE = 150.0

rows = []
price = START_PRICE
# Skip weekends when advancing dates
current_date = START_DATE
trading_days = 0

while trading_days < ROWS:
    if current_date.weekday() < 5:  # Mon–Fri
        # Simulate daily OHLCV
        open_ = round(price * (1 + random.gauss(0, 0.005)), 2)
        close = round(open_ * (1 + random.gauss(0, 0.012)), 2)
        high = round(max(open_, close) * (1 + abs(random.gauss(0, 0.006))), 2)
        low = round(min(open_, close) * (1 - abs(random.gauss(0, 0.006))), 2)
        volume = int(random.gauss(5_000_000, 1_200_000))
        volume = max(volume, 500_000)
        rows.append({
            "date": current_date.isoformat(),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
        price = close
        trading_days += 1
    current_date += timedelta(days=1)

with open("ohlcv.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Written {len(rows)} rows to ohlcv.csv")
