# Auto-generated from the shared install recipe for gitleaks — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/gitleaks/ (docker-compose.yml points here).
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Pinned to a release confirmed reachable when this Dockerfile was written
# (2026-10). Bump the version if you want something newer.
RUN curl -fsSL https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz \
    | tar -xz -C /usr/local/bin gitleaks
RUN chmod +x /usr/local/bin/gitleaks

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="gitleaks"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
