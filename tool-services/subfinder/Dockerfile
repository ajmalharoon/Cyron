# Auto-generated from the shared install recipe for subfinder — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/subfinder/ (docker-compose.yml points here).
FROM golang:1.27-alpine AS build
RUN apk add --no-cache git
ENV GOPATH=/go
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

FROM python:3.12-alpine
RUN apk add --no-cache ca-certificates
COPY --from=build /go/bin/subfinder /usr/local/bin/subfinder

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="subfinder"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
