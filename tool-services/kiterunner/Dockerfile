# Auto-generated from the shared install recipe for kiterunner — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/kiterunner/ (docker-compose.yml points here).
# Note: the binary this release ships is named "kr" (matching
# KiterunnerRunner.binary in the backend) — the compose service for this
# image must be named "kr" too, not "kiterunner", so the backend's lookup
# of http://kr:8080/run resolves. See docker-compose.yml.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Pinned to a release confirmed reachable when this Dockerfile was written
# (2026-10). Bump the version if you want something newer.
RUN curl -fsSL https://github.com/assetnote/kiterunner/releases/download/v1.0.2/kiterunner_1.0.2_linux_amd64.tar.gz \
    | tar -xz -C /usr/local/bin kr
RUN chmod +x /usr/local/bin/kr

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="kiterunner"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
