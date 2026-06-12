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
        pochi-verifier \
        altair \
        vega_datasets \
        pandas \
        vl-convert-python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/iris_chart && \
    cat > /home/user/iris_chart/chart.py <<'EOF'
"""Initial stub: replace this file with a script that builds the layered
Altair chart described in instruction.md and saves both chart.json and
chart.html under /home/user/iris_chart/."""

if __name__ == "__main__":
    raise SystemExit(
        "chart.py is a stub. Implement the layered Altair visualization and save "
        "chart.json and chart.html under /home/user/iris_chart/."
    )
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Vega-Altair task environment for the iris regression + LOESS + errorband layered chart, including browser verification."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Vega-Altair stack: altair, vega_datasets, pandas, vl-convert-python (for chart.save HTML/JSON export)
#   - browser verification dependencies: pochi-verifier, agent-browser, Node.js v24, ffmpeg, and X libs
#   - /home/user/iris_chart: project directory with a chart.py stub the executor must replace
