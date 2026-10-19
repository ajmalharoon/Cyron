# Auto-generated from the shared install recipe for shuffledns — see
# tool-services/_shim/shim.py for what every one of these images runs.
# Build context is tool-services/shuffledns/ (docker-compose.yml points here).
FROM golang:1.27-alpine AS build
RUN apk add --no-cache git
ENV GOPATH=/go
RUN go install -v github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest

FROM python:3.12-alpine
RUN apk add --no-cache ca-certificates
COPY --from=build /go/bin/shuffledns /usr/local/bin/shuffledns

# shuffleDNS drives massdns under the hood.
RUN apk add --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/edge/testing massdns || \
    echo "massdns not in this Alpine repo snapshot — install it manually if resolution fails"

# --- shared shim, identical in every tool image ---
COPY _shim/shim.py /shim/shim.py
ENV CYRON_TOOL_NAME="shuffledns"
EXPOSE 8080
CMD ["python3", "/shim/shim.py"]
