# Auto-generated from the shared install recipe for whatweb — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/whatweb/ (docker-compose.yml points here).
FROM ruby:3.3-slim
RUN apt-get update && apt-get install -y --no-install-recommends git python3 build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/urbanadventurer/WhatWeb.git /opt/whatweb \
    && cd /opt/whatweb && bundle install
RUN printf '#!/bin/sh\nexec ruby /opt/whatweb/whatweb "$@"\n' > /usr/local/bin/whatweb \
    && chmod +x /usr/local/bin/whatweb

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="whatweb"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
