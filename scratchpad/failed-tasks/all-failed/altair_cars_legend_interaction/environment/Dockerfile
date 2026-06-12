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
        vega_datasets \
        pandas && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/myproject && \
    cat >/home/user/myproject/solution.py <<'EOF'
"""Starter stub for the altair_cars_legend_interaction task.

Replace this file with a full implementation that:
  - Loads the `cars` dataset (e.g. via `vega_datasets.data.cars`).
  - Builds a (scatter | stacked_bar) & binned_histogram dashboard.
  - Wires a single shared `selection_point(fields=['Origin'], bind='legend')`
    to drive an opacity condition across all three sub-views.
  - Saves the composed chart to `/home/user/myproject/chart.html` with
    `chart.save(...)`.
"""

if __name__ == "__main__":
    raise NotImplementedError(
        "altair_cars_legend_interaction: implement the dashboard and "
        "save it to /home/user/myproject/chart.html"
    )
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Vega-Altair environment for the cars legend-interaction dashboard task, including browser verification deps."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Vega-Altair stack: altair, vega_datasets, pandas
#   - pytest-xprocess for the local HTTP server fixture
#   - Browser verification: pochi-verifier, agent-browser (Node.js v24), ffmpeg, and headless browser libs
#   - /home/user/myproject: project directory with a starter solution.py stub
