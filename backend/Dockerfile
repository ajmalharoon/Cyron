FROM python:3.12-slim

# nmap is installed here as a baseline example. See tools/install.sh for the
# full tool list — most ProjectDiscovery / Go-based tools are easiest to add
# with a multi-stage `golang` build stage, and heavier tools (OWASP ZAP,
# Prowler, ScoutSuite, kube-hunter, kube-bench) are usually run as their own
# sidecar containers rather than baked into this image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
