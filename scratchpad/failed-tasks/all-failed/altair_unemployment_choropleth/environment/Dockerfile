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
        pytest-xprocess \
        altair \
        vega_datasets \
        pandas && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/myproject && \
    cat >/home/user/myproject/solution.py <<'EOF'
"""Initial stub for the unemployment choropleth task.

Replace the body of this script with your implementation. The script must
produce ``/home/user/myproject/chart.html`` when executed with
``python3 solution.py``.
"""


def main() -> None:
    raise NotImplementedError(
        "Implement the Altair choropleth + brushable histogram dashboard "
        "and save it to chart.html in this directory."
    )


if __name__ == "__main__":
    main()
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Vega-Altair task environment with altair + browser verification stack for the US unemployment choropleth dashboard task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - vega-altair stack (altair, vega_datasets, pandas) for solver execution
#   - browser verification dependencies: pochi-verifier, agent-browser, ffmpeg, X libraries, Node.js v24
#   - pytest-xprocess for managing optional long-running processes inside the verifier
#   - /home/user/myproject: project directory containing a minimal solution.py stub
