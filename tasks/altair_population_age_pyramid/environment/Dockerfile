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
        vega_datasets && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/myproject && \
    cat >/home/user/myproject/build_pyramid.py <<'EOF'
"""Stub for the altair_population_age_pyramid task.

Replace the body of this script with code that builds a back-to-back
population age pyramid using Vega-Altair and writes both
`pyramid.html` and `pyramid_spec.json` to /home/user/myproject.
"""


def main() -> None:
    raise NotImplementedError(
        "build_pyramid.py is a stub. Implement the Altair age pyramid here."
    )


if __name__ == "__main__":
    main()
EOF

LABEL Author="generate-harbor-tasks"
LABEL Description="Vega-Altair task environment with altair, vega_datasets, pochi-verifier, and a stub build_pyramid.py for the back-to-back population age pyramid task."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - vega-altair task environment: altair, vega_datasets, pytest-xprocess
#   - browser verification dependencies: pochi-verifier, agent-browser, ffmpeg and friends, Node.js v24
#   - /home/user/myproject/build_pyramid.py: initial stub script that the executor must replace
