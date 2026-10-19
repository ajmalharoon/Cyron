# Auto-generated from the shared install recipe for linkfinder — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/linkfinder/ (docker-compose.yml points here).
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/GerbenJavado/LinkFinder.git /opt/linkfinder \
    && pip install --no-cache-dir -r /opt/linkfinder/requirements.txt
RUN printf '#!/bin/sh\nexec python3 /opt/linkfinder/linkfinder.py "$@"\n' > /usr/local/bin/linkfinder \
    && chmod +x /usr/local/bin/linkfinder

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="linkfinder"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
