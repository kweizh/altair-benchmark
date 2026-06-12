FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep \
        ffmpeg libxcb-shm0 libx11-xcb1 libx11-6 libxcb1 libxext6 libxrandr2 libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 libgtk-3-0t64 libpangocairo-1.0-0 libpango-1.0-0 libatk1.0-0t64 libcairo-gobject2 libcairo2 libgdk-pixbuf-2.0-0 libxrender1 libasound2t64 libfreetype6 libfontconfig1 libdbus-1-3 libnss3 libnspr4 libatk-bridge2.0-0t64 libdrm2 libxkbcommon0 libatspi2.0-0t64 libcups2t64 libxshmfence1 libgbm1 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm i -g agent-browser && \
    agent-browser install && \
    pip3 install --break-system-packages \
        pytest-json-ctrf \
        pytest-xprocess \
        pochi-verifier \
        altair \
        pandas \
        numpy && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /home/user/altair_stocks_candlestick

# Generate a deterministic synthetic OHLCV CSV with >= 60 trading days.
RUN python3 - <<'PY'
import csv
import math
import os
import random
from datetime import date, timedelta

random.seed(20240115)
out_path = "/home/user/altair_stocks_candlestick/ohlcv.csv"

rows = []
price = 100.0
current = date(2024, 1, 2)
n_days = 90  # > 60 trading rows
written = 0
while written < n_days:
    # Skip Saturdays (5) and Sundays (6) so the dates look like trading days.
    if current.weekday() < 5:
        # Random walk with mild drift.
        drift = random.uniform(-1.8, 1.9)
        open_p = price
        close_p = max(1.0, open_p + drift)
        high_p = max(open_p, close_p) + abs(random.uniform(0.1, 1.5))
        low_p = min(open_p, close_p) - abs(random.uniform(0.1, 1.5))
        low_p = max(0.5, low_p)
        volume = int(random.uniform(800_000, 5_000_000))
        rows.append({
            "date": current.isoformat(),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": volume,
        })
        price = close_p
        written += 1
    current += timedelta(days=1)

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["date", "open", "high", "low", "close", "volume"]
    )
    writer.writeheader()
    writer.writerows(rows)
PY

LABEL Author="generate-harbor-tasks"
LABEL Description="Vega-Altair task environment with browser verification and a synthetic OHLCV CSV for the candlestick + volume dashboard."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - browser verification dependencies: pochi-verifier, agent-browser, ffmpeg, and supporting libs
#   - Python data stack for Altair: altair, pandas, numpy, pytest-xprocess
#   - /home/user/altair_stocks_candlestick: project directory
#   - /home/user/altair_stocks_candlestick/ohlcv.csv: synthetic OHLCV initial state (>=60 daily rows)
