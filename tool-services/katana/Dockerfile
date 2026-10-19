# Auto-generated from the shared install recipe for katana — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/katana/ (docker-compose.yml points here).
FROM golang:1.27-alpine AS build
RUN apk add --no-cache git
ENV GOPATH=/go
RUN go install -v github.com/projectdiscovery/katana/cmd/katana@latest

FROM python:3.12-alpine
RUN apk add --no-cache ca-certificates
COPY --from=build /go/bin/katana /usr/local/bin/katana

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="katana"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
