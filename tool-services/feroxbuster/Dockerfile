# Auto-generated from the shared install recipe for feroxbuster — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/feroxbuster/ (docker-compose.yml points here).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L \
    https://github.com/epi052/feroxbuster/releases/download/v2.13.1/x86_64-linux-feroxbuster.zip \
    -o /tmp/feroxbuster.zip \
    && unzip /tmp/feroxbuster.zip -d /tmp/feroxbuster \
    && find /tmp/feroxbuster -type f -name feroxbuster -exec cp {} /usr/local/bin/feroxbuster \; \
    && chmod +x /usr/local/bin/feroxbuster \
    && rm -rf /tmp/feroxbuster /tmp/feroxbuster.zip

COPY _shim/shim.py /shim/shim.py

ENV CYRON_TOOL_NAME="feroxbuster"

EXPOSE 8080

CMD ["python3", "/shim/shim.py"]