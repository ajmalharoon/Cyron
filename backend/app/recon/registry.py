"""The single source of truth for Cyron's 18 recon phases. The API serves
this to the frontend (GET /api/phases) so the UI never hardcodes phase or
tool names, and the job runner (recon/runner.py) reads it to know which
ToolRunner instances to execute for a given phase."""
from dataclasses import dataclass, field

from app.recon.tools.amass import AmassRunner
from app.recon.tools.censys_tool import CensysRunner
from app.recon.tools.cve_intel import CveIntelRunner
from app.recon.tools.dnsrecon import DnsReconRunner
from app.recon.tools.dnsx import DnsxRunner
from app.recon.tools.feroxbuster import FeroxbusterRunner
from app.recon.tools.ffuf import FfufRunner
from app.recon.tools.fofa_tool import FofaRunner
from app.recon.tools.gau import GauRunner
from app.recon.tools.getallurls import GetAllUrlsRunner
from app.recon.tools.gitleaks import GitleaksRunner
from app.recon.tools.gobuster import GobusterRunner
from app.recon.tools.httpx_tool import HttpxRunner
from app.recon.tools.katana import KatanaRunner
from app.recon.tools.kiterunner import KiterunnerRunner
from app.recon.tools.kube_bench import KubeBenchRunner
from app.recon.tools.kube_hunter import KubeHunterRunner
from app.recon.tools.linkfinder import LinkFinderRunner
from app.recon.tools.masscan import MasscanRunner
from app.recon.tools.naabu import NaabuRunner
from app.recon.tools.nmap import NmapRunner
from app.recon.tools.nuclei import NucleiRunner
from app.recon.tools.prowler import ProwlerRunner
from app.recon.tools.scoutsuite import ScoutSuiteRunner
from app.recon.tools.secretfinder import SecretFinderRunner
from app.recon.tools.shodan_tool import ShodanRunner
from app.recon.tools.shuffledns import ShuffleDnsRunner
from app.recon.tools.subfinder import SubfinderRunner
from app.recon.tools.tls_recon import TlsReconRunner
from app.recon.tools.trufflehog import TruffleHogRunner
from app.recon.tools.web_crawler import WebCrawlerRunner
from app.recon.tools.whatweb import WhatWebRunner
from app.recon.tools.zap import ZapRunner


@dataclass
class Phase:
    id: str
    name: str
    mode: str  # "active" | "passive"
    description: str
    recommendation: str
    tools: list = field(default_factory=list)  # list of (label, factory)


PHASES: list[Phase] = [
    Phase("asset", "Asset and subdomain discovery", "active",
          "Finds hosts and subdomains the organisation owns, so nothing is tested blind.",
          "Retire unused subdomains and keep an inventory of owned assets.",
          [("OWASP Amass", AmassRunner), ("subfinder", SubfinderRunner), ("dnsx", DnsxRunner)]),
    Phase("dns", "DNS reconnaissance", "active",
          "Reads records, mail policy and zone settings that reveal hosting and trust.",
          "Publish a DMARC policy, restrict zone transfers and remove stale records.",
          [("dnsx", DnsxRunner), ("shuffleDNS", ShuffleDnsRunner), ("DNSRecon", DnsReconRunner)]),
    Phase("net", "IP and network reconnaissance", "active",
          "Maps open ports and the services behind them.",
          "Close ports that have no owner and filter management ports.",
          [("Nmap", NmapRunner), ("Naabu", NaabuRunner), ("Masscan", MasscanRunner)]),
    Phase("http", "HTTP/HTTPS reconnaissance", "active",
          "Checks web responses, redirects and certificate health.",
          "Enforce HTTPS and renew certificates ahead of expiry.",
          [("httpx", HttpxRunner), ("TLS reconnaissance", TlsReconRunner), ("Web crawler", WebCrawlerRunner)]),
    Phase("hist", "Historical URL discovery", "active",
          "Looks in web archives for pages that no longer appear on the site.",
          "Remove old admin and backup files, and block them at the server.",
          [("GAU", GauRunner), ("GetAllUrls", GetAllUrlsRunner)]),
    Phase("content", "Web content discovery", "active",
          "Probes for hidden paths and files.",
          "Restrict admin paths by IP or login and remove unused folders.",
          [("ffuf", FfufRunner), ("Feroxbuster", FeroxbusterRunner), ("Gobuster", GobusterRunner)]),
    Phase("tech", "Technology fingerprinting", "active",
          "Identifies server, framework and library versions.",
          "Patch outdated components and hide version banners.",
          [("WhatWeb", WhatWebRunner)]),
    Phase("js", "JavaScript reconnaissance", "active",
          "Mines scripts for endpoints and secrets.",
          "Rotate any exposed key and keep source maps out of production.",
          [("LinkFinder", LinkFinderRunner), ("SecretFinder", SecretFinderRunner), ("Gitleaks", GitleaksRunner)]),
    Phase("api", "API reconnaissance", "active",
          "Lists API routes and their documentation.",
          "Require authentication on every route and hide API docs.",
          [("Katana", KatanaRunner), ("kiterunner", KiterunnerRunner),
           ("OWASP ZAP", lambda: ZapRunner(active_scan=False))]),
    Phase("web", "Web security analysis", "active",
          "Reviews headers, cookies and browser protections.",
          "Add a CSP and set HttpOnly and SameSite on cookies.",
          [("OWASP ZAP", lambda: ZapRunner(active_scan=True))]),
    Phase("vuln", "Vulnerability discovery", "active",
          "Runs template checks for known weaknesses.",
          "Remove exposed repository data and update vulnerable libraries.",
          [("Nuclei", NucleiRunner)]),
    Phase("svc", "Protocol and service enumeration", "active",
          "Pulls protocol detail from open services.",
          "Disable risky methods and legacy TLS versions.",
          [("Nmap NSE", lambda: NmapRunner(nse=True))]),
    Phase("cve", "CVE and vulnerability intelligence", "passive",
          "Matches detected versions against NVD and CVE records.",
          "Patch in order of severity and exploit availability.",
          [("NVD / CVE database", CveIntelRunner)]),
    Phase("exp", "Internal exposure discovery", "passive",
          "Checks what internet-wide search engines already know about the target.",
          "Take unlisted assets down or add them to the inventory.",
          [("Shodan", ShodanRunner), ("Censys", CensysRunner), ("FOFA", FofaRunner)]),
    Phase("aws", "Cloud: AWS", "passive",
          "Audits AWS configuration against best practice.",
          "Block public access on storage, enforce MFA and remove unused keys.",
          [("Prowler", ProwlerRunner), ("ScoutSuite", lambda: ScoutSuiteRunner(provider="aws"))]),
    Phase("multi", "Cloud: multi-cloud", "passive",
          "Audits other cloud providers with one tool.",
          "Fix public storage first, then review IAM.",
          [("ScoutSuite", lambda: ScoutSuiteRunner(provider="azure"))]),
    Phase("k8s", "Kubernetes", "passive",
          "Checks cluster exposure and CIS benchmark results.",
          "Fix failed CIS checks and close open kubelet ports.",
          [("kube-hunter", KubeHunterRunner), ("kube-bench", KubeBenchRunner)]),
    Phase("src", "Source code and repositories", "passive",
          "Scans repositories and history for secrets.",
          "Rotate leaked secrets, then purge them from history.",
          [("Gitleaks", lambda: GitleaksRunner(repo_path=".")), ("TruffleHog", lambda: TruffleHogRunner(repo_path="."))]),
]

PHASES_BY_ID = {p.id: p for p in PHASES}
