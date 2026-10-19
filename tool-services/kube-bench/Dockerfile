# Auto-generated from the shared install recipe for kube-bench — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/kube-bench/ (docker-compose.yml points here).
#
# kube-bench's release tarball ships more than the binary: a cfg/ tree of
# CIS benchmark policy YAML files it reads at runtime (by default, relative
# to its own working directory). This extracts the whole tarball rather
# than just the binary, and sets WORKDIR so that lookup resolves.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Pinned to a release confirmed reachable when this Dockerfile was written
# (2026-10). Bump the version if you want something newer.
RUN mkdir -p /opt/kube-bench \
    && curl -fsSL https://github.com/aquasecurity/kube-bench/releases/download/v0.16.0/kube-bench_0.16.0_linux_amd64.tar.gz \
       | tar -xz -C /opt/kube-bench \
    && chmod +x /opt/kube-bench/kube-bench \
    && ln -s /opt/kube-bench/kube-bench /usr/local/bin/kube-bench
WORKDIR /opt/kube-bench

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="kube-bench"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
