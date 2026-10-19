# Auto-generated from the shared install recipe for kube-hunter — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/kube-hunter/ (docker-compose.yml points here).
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir kube-hunter

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="kube-hunter"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
