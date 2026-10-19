#!/usr/bin/env bash
# Reference install commands for every tool Cyron can orchestrate.
#
# NOT the default path anymore: the provided docker-compose.yml already
# runs every tool as its own container under /tool-services/, and
# ToolRunner.run() (backend/app/recon/base.py) calls those containers over
# HTTP. This script is for the alternative — installing tools straight onto
# the backend's own host/image and pointing ToolRunner.run() back at a
# local subprocess call instead. Not run automatically either way.
set -euo pipefail

# --- Go-based (ProjectDiscovery and friends) ---
go install -v github.com/owasp-amass/amass/v4/...@master
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest
go install -v github.com/tomnomnom/waybackurls@latest
go install -v github.com/ffuf/ffuf/v2@latest
go install -v github.com/OJ/gobuster/v3@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# --- Rust ---
cargo install feroxbuster

# --- Python ---
pip install dnsrecon
pip install scoutsuite

# --- Ruby ---
gem install whatweb

# --- apt / system packages ---
apt-get install -y nmap masscan

# --- Download-and-place binaries (check each project's releases page) ---
#   linkfinder, secretfinder : github.com/GerbenJavado/LinkFinder, github.com/m4ll0k/SecretFinder
#   gitleaks                 : github.com/gitleaks/gitleaks/releases
#   trufflehog                : github.com/trufflesecurity/trufflehog/releases
#   kiterunner                : github.com/assetnote/kiterunner/releases
#   kube-hunter               : pip install kube-hunter
#   kube-bench                : github.com/aquasecurity/kube-bench/releases
#   vulnx                     : github.com/anouarbensaad/vulnx

# --- Containers (run alongside Cyron rather than inside the backend image) ---
#   OWASP ZAP : docker run -d -p 8080:8080 zaproxy/zap-stable zap.sh -daemon \
#               -host 0.0.0.0 -port 8080 -config api.disablekey=false
#   Prowler   : docker run --rm -v ~/.aws:/root/.aws toniblyx/prowler:latest

# --- API-only (no binary, just a key in .env) ---
#   Shodan, Censys, FOFA, NVD — see .env.example
