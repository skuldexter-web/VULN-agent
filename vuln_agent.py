import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from typing import List, Optional

BANNER = r"""
  V   V  U   U  L      N   N
  V   V  U   U  L      NN  N
  V   V  U   U  L      N N N
   V V   U   U  L      N  NN
    V     UUU   LLLLL  N   N
==================================
 VULN - Vulnerability Assessment
 Digital Forensics Edition
==================================
"""


class Logger:
    """Live output + log file writer."""

    def __init__(self, log_file="vulnscan.log"):
        self.log_file = log_file
        self.RESET = "\033[0m"
        self.COLORS = {
            "INFO": "\033[96m",
            "OK": "\033[92m",
            "WARN": "\033[93m",
            "ERR": "\033[91m",
        }
        open(self.log_file, "a").close()

    def log(self, level, module, action, reason):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] [{module}] {action} | reason: {reason}"
        color = self.COLORS.get(level, self.COLORS["INFO"])
        print(f"{color}{line}{self.RESET}")
        self.write_file(line)

    def write_file(self, line):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def raw(self, text):
        """Write raw command output to the log file."""
        self.write_file(text)


class PortScanner:
    """Wraps Nmap with service version detection and vulners script."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def run(self, target: str, ports: str = "--top-ports 1000") -> Optional[str]:
        if not shutil.which("nmap"):
            self.logger.log("ERR", "PortScanner", "nmap not found", "Install with: sudo
 apt install nmap")
            return None

        os.makedirs("reports", exist_ok=True)
        xml_path = os.path.join("reports", f"nmap_{self._safe(target)}.xml")
        cmd = ["nmap", "-Pn", "-sV", ports, "--script=vulners", "-oX", xml_path, target
]

        self.logger.log("INFO", "PortScanner", "Running Nmap vulnerability scan", f"Com
mand: {' '.join(cmd)}")
        self.logger.log("INFO", "PortScanner", "Streaming Nmap live output", "Live outp
ut shows open ports, versions, and CVE references")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in proc.stdout:
                print(line, end="")
                self.logger.raw(line.rstrip())

            proc.wait()

            if proc.returncode == 0 or os.path.exists(xml_path):
                return xml_path
            return None

        except FileNotFoundError:
            self.logger.log("ERR", "PortScanner", "nmap not found", "Install nmap and t
ry again")
            return None

    @staticmethod
    def _safe(text: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]", "_", text)


def extract_cves_from_nmap(xml_path: str, logger: Logger) -> List[str]:
    """Pull CVE IDs out of Nmap XML output."""
    cves = set()

    try:
        root = ET.parse(xml_path).getroot()
        for script in root.iter("script"):
            output = script.get("output", "")
            for match in re.findall(r"CVE-\d{4}-\d{4,}", output):
                cves.add(match.upper())
    except Exception as e:
        logger.log("ERR", "CveExtractor", "Failed to parse Nmap XML", str(e))

    return sorted(cves)


class CVEChecker:
    """Looks up CVE details from public CIRCL API and local files."""

    def __init__(self, logger: Logger):
        self.logger = logger

    @staticmethod
    def is_valid(cve_id: str) -> bool:
        return bool(re.match(r"CVE-\d{4}-\d{4,}$", cve_id.strip().upper()))

    def lookup(self, cve_id: str) -> Optional[dict]:
        cve_id = cve_id.strip().upper()

        if not self.is_valid(cve_id):
            self.logger.log("WARN", "CVEChecker", f"Ignoring malformed CVE: {cve_id}", 
"CVE IDs must be like CVE-2021-44228")
            return None

        url = f"https://cve.circl.lu/api/cve/{cve_id}"
        self.logger.log("INFO", "CVEChecker", f"Querying {cve_id}", f"GET {url}")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VULN-Scanner/1.0"
})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.load(resp)

            info = {
                "id": cve_id,
                "summary": data.get("summary", "No summary"),
                "cvss": data.get("cvss", "N/A"),
                "published": data.get("Published", "Unknown"),
                "references": data.get("references", []),
            }

            self.logger.log("OK", "CVEChecker", f"Found {cve_id}", f"CVSS={info['cvss']
}, published={info['published']}")
            return info

        except urllib.error.HTTPError as e:
            self.logger.log("ERR", "CVEChecker", f"{cve_id} lookup failed", f"HTTP {e.c
ode}")
        except Exception as e:
            self.logger.log("ERR", "CVEChecker", f"{cve_id} lookup failed", str(e))

        return None

    def lookup_file(self, path: str) -> List[dict]:
        if not os.path.isfile(path):
            self.logger.log("ERR", "CVEChecker", f"File not found: {path}", "Check the 
path and try again")
            return []

        results = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                cve_id = line.strip()
                if not cve_id or cve_id.startswith("#"):
                    continue
                result = self.lookup(cve_id)
                if result:
                    results.append(result)

        return results


class MetasploitSearcher:
    """Searches SearchSploit and Metasploit module database for CVEs."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def search_searchsploit(self, cve_id: str) -> str:
        if not shutil.which("searchsploit"):
            self.logger.log("WARN", "MetasploitSearcher", "searchsploit not found", "In
stall with: sudo apt install exploitdb")
            return ""

        self.logger.log("INFO", "MetasploitSearcher", f"Running searchsploit {cve_id}",
 "Searching local Exploit-DB for public exploit code")

        try:
            proc = subprocess.Popen(
                ["searchsploit", cve_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            output = []
            for line in proc.stdout:
                print(line, end="")
                self.logger.raw(line.rstrip())
                output.append(line)

            proc.wait()
            return "".join(output)

        except Exception as e:
            self.logger.log("ERR", "MetasploitSearcher", "searchsploit failed", str(e))
            return ""

    def search_msf(self, cve_id: str) -> str:
        if not shutil.which("msfconsole"):
            self.logger.log("WARN", "MetasploitSearcher", "msfconsole not found", "Inst
all with: sudo apt install metasploit-framework")
            return ""

        msf_cve = cve_id.replace("CVE-", "")
        cmd = ["msfconsole", "-q", "-x", f"search cve:{msf_cve}; exit"]

        self.logger.log("INFO", "MetasploitSearcher", f"Searching Metasploit for {cve_i
d}", "Metasploit module database may contain matching exploit modules")

        env = os.environ.copy()
        env["PAGER"] = "cat"

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )

            output = []
            for line in proc.stdout:
                print(line, end="")
                self.logger.raw(line.rstrip())
                output.append(line)

            proc.wait()
            return "".join(output)

        except Exception as e:
            self.logger.log("ERR", "MetasploitSearcher", "msfconsole search failed", st
r(e))
            return ""


class ReportGenerator:
    """Creates a timestamped Markdown report with evidence hash."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def generate(self, target: str, cves: List[str], msf_outputs: dict = None) -> str:
        os.makedirs("reports", exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = re.sub(r"[^A-Za-z0-9._-]", "_", target)
        filename = os.path.join("reports", f"report_{safe_target}_{ts}.md")

        lines = []
        lines.append("# VULN Assessment Report\n")
        lines.append(f"**Target:** `{target}`  \n")
        lines.append(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}\n")
        lines.append("## CVEs Found\n")

        if cves:
            for cve in cves:
                lines.append(f"- {cve}\n")
        else:
            lines.append("No CVEs were extracted from Nmap output.\n")

        if msf_outputs:
            lines.append("## Exploit Search Results\n")
            for cve, output in msf_outputs.items():
                lines.append(f"### {cve}\n")
                lines.append("```\n")
                lines.append(output)
                lines.append("\n```\n")

        content = "".join(lines)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        sha = hashlib.sha256(content.encode()).hexdigest()

        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"\n## Report Integrity\nSHA256: `{sha}`\n")

        self.logger.log("OK", "ReportGenerator", f"Report saved: {filename}", "Markdown
 report with CVE and exploit search data for evidence preservation")

        return filename


class AssessmentEngine:
    """CLI controller for VULN."""

    def __init__(self):
        self.logger = Logger()
        self.check_environment()

    @staticmethod
    def check_environment():
        print("\nChecking required tools...")
        for tool in ["nmap", "searchsploit", "msfconsole"]:
            if shutil.which(tool):
                print(f"  [OK] {tool}")
            else:
                print(f"  [--] {tool} not found (optional)")
        print()

    def run(self):
        print(BANNER)
        self.main_menu()

    def main_menu(self):
        while True:
            print("=" * 50)
            print("VULN Main Menu")
            print("=" * 50)
            print("1. Quick CVE lookup")
            print("2. Nmap vulnerability scan")
            print("3. Search Metasploit/SearchSploit for a CVE")
            print("4. Full assessment (scan + exploit search + report)")
            print("5. Read CVE list from file")
            print("0. Exit")
            print("=" * 50)

            choice = input("Select option: ").strip()

            if choice == "1":
                self.quick_cve_lookup()
            elif choice == "2":
                self.scan_target()
            elif choice == "3":
                self.search_metasploit()
            elif choice == "4":
                self.run_full_assessment()
            elif choice == "5":
                self.check_cve_list()
            elif choice == "0":
                print("Exiting. Logs saved to vulnscan.log")
                break
            else:
                print("Invalid option. Try again.")

    def quick_cve_lookup(self):
        cve_id = input("Enter CVE ID (e.g., CVE-2021-44228): ").strip()
        if not cve_id:
            return

        checker = CVEChecker(self.logger)
        result = checker.lookup(cve_id)

        if result:
            self._print_cve(result)

    def scan_target(self):
        target = input("Enter target IP or hostname: ").strip()
        if not target:
            self.logger.log("WARN", "AssessmentEngine", "Empty target", "You must enter
 an IP or hostname")
            return

        scanner = PortScanner(self.logger)
        xml_path = scanner.run(target)

        if not xml_path:
            return

        cves = extract_cves_from_nmap(xml_path, self.logger)

        print(f"\n[VULN] Extracted {len(cves)} CVE references from Nmap output.\n")
        for cve in cves:
            print(f"  - {cve}")

        if cves:
            answer = input("\nSearch Exploit-DB/Metasploit for these CVEs now? [y/N]: "
).strip().lower()
            if answer.startswith("y"):
                self._search_all(cves)

    def search_metasploit(self):
        cve_id = input("Enter CVE ID (e.g., CVE-2021-44228): ").strip()
        if not cve_id:
            return

        searcher = MetasploitSearcher(self.logger)
        searcher.search_searchsploit(cve_id)
        searcher.search_msf(cve_id)

    def run_full_assessment(self):
        target = input("Enter target IP or hostname: ").strip()
        if not target:
            return

        self.logger.log("INFO", "AssessmentEngine", f"Starting full assessment on {targ
et}", "Pipeline: Nmap -> CVE extraction -> exploit search -> report")

        scanner = PortScanner(self.logger)
        xml_path = scanner.run(target)

        if not xml_path:
            return

        cves = extract_cves_from_nmap(xml_path, self.logger)

        print(f"\n[VULN] Extracted {len(cves)} CVE references.\n")

        searcher = MetasploitSearcher(self.logger)
        outputs = {}

        for cve in cves:
            self.logger.log("INFO", "AssessmentEngine", f"Processing {cve}", "Searching
 for known public exploits and Metasploit module matches")
            searchsploit_out = searcher.search_searchsploit(cve)
            msf_out = searcher.search_msf(cve)
            outputs[cve] = searchsploit_out + "\n" + msf_out

        report = ReportGenerator(self.logger)
        path = report.generate(target, cves, outputs)

        print(f"\n[VULN] Report ready: {path}\n")

    def check_cve_list(self):
        path = input("Path to CVE list file (default cve_list.txt): ").strip() or "cve_
list.txt"

        checker = CVEChecker(self.logger)
        results = checker.lookup_file(path)

        print(f"\n[VULN] Processed {len(results)} CVEs from {path}\n")
        for result in results:
            self._print_cve(result)

    def _search_all(self, cves):
        searcher = MetasploitSearcher(self.logger)
        for cve in cves:
            self.logger.log("INFO", "AssessmentEngine", f"Searching exploits for {cve}"
, "CVE references map to public or Metasploit modules")
            searcher.search_searchsploit(cve)
            searcher.search_msf(cve)

    @staticmethod
    def _print_cve(info):
        print("\nCVE Details")
        print(f"  ID        : {info['id']}")
        print(f"  Published : {info['published']}")
        print(f"  CVSS      : {info['cvss']}")
        print(f"  Summary   : {info['summary']}")

        if info.get("references"):
            print("  References:")
            for ref in info["references"][:5]:
                print(f"    - {ref}")

        print()


if __name__ == "__main__":
    try:
        AssessmentEngine().run()
    except KeyboardInterrupt:
        print("\n[!] Interrupted. Logs preserved in vulnscan.log")
        raise SystemExit(0)
