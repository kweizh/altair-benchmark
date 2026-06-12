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

# Initial state: project directory with a minimal build_chart.py stub.
RUN mkdir -p /home/user/altair_task && \
    cat >/home/user/altair_task/build_chart.py <<'EOF'
"""Build the barley grouped-bar chart HTML.

This stub does not yet implement the task. Replace its body with code that
constructs the required Altair chart and writes it to
``/home/user/altair_task/output/chart.html``.
"""

import os


def main() -> None:
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    # TODO: build the chart with Altair and save it to output/chart.html.


if __name__ == "__main__":
    main()
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Vega-Altair task environment for the faceted, sorted, grouped barley bar chart with mean overlay; includes browser verification dependencies."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Python deps for the task: altair, vega_datasets, pandas
#   - Python deps for verification: pytest-xprocess, pochi-verifier
#   - Node.js v24 + agent-browser + Chromium libs for browser verification
#   - /home/user/altair_task/build_chart.py: minimal stub the executor must complete
