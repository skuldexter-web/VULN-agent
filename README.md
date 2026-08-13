markdown
# VULN Agent - Automated Vulnerability Scanner & Penetration Tool

**VULN** is a command-line tool designed for authorized digital forensics and penetrati
on testing. It automates vulnerability discovery using Nmap and SearchSploit, then leve
rages Metasploit to exploit known CVEs, establish a reverse shell, and generate Remote 
Access Trojan (RAT) payloads.

> **⚠️ Legal Disclaimer:** This tool is intended for **educational purposes** and **aut
horized security audits only**. Unauthorized use against systems you do not own or have
 written permission to test is illegal. The developers are not responsible for any misu
se.

## Features

- 🔍 **Automatic Vulnerability Scan** – Uses Nmap `vulners` script and SearchSploit to e
numerate CVEs.
- ⚡ **Metasploit Integration** – Maps CVEs to exploit modules and runs them automatical
ly.
- 📡 **Reverse Shell** – Starts a Metasploit `multi/handler` for incoming connections.
- 🕹️ **RAT Generation** – Creates custom meterpreter payloads (Windows/Linux) with `msf
venom`.
- 📺 **Live Output Feed** – Explains each action in real-time with color-coded status me
ssages.
- 🗂️ **Submenus & Modular Architecture** – Beginner-friendly interactive menu.

## Requirements

- **Kali Linux** (or a Debian-based distro with security tools)
- **Installed tools**:
  - `nmap`
  - `searchsploit`
  - `metasploit-framework` (`msfconsole`, `msfvenom`)
- Python 3.x (no extra libraries required)

Install missing tools:

```bash
sudo apt update && sudo apt install nmap exploitdb metasploit-framework


## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/skuldexter-web/vuln-agent.git
cd vuln-agent


2. Make the script executable:

```bash
chmod +x vuln_agent.py


3. Run the tool:

```bash
sudo python3 vuln_agent.py


4. Follow the interactive prompts:
   - Enter target IP address
   - Enter your LHOST (your IP for reverse connections, e.g., `tun0` if using VPN)
   - Choose a menu option (e.g., `1` for Full Auto-Scan & Exploit)

## Usage Example

```text
=================================================================
   VULN - Vulnerability Scanner & Penetration Tool  v1.0
=================================================================
[10:00:01] [OK] All required tools found.
[?] Enter target IP address: 192.168.1.10
[?] Enter your LHOST (listener IP): 192.168.1.5

VULN Agent - Main Menu
==================================================
1) Full Auto-Scan & Exploit
2) Vulnerability Scan Only
3) Generate RAT Payload
4) Start Reverse Shell Listener
5) Exit
[?] Select an option: 1


## Architecture

```
vuln_agent.py               # Main script
├── Utils                    # Utility functions (tool check, live output, formatting)
├── VulnerabilityScanner     # Nmap + SearchSploit scanning functions
├── ExploitManager           # Metasploit exploit mapping & execution
├── RATGenerator             # msfvenom payload generation
└── VulnAgent                # Main controller/menu system


## How It Works

1. **Scan** – Nmap with `--script vulners` extracts CVE information from services.
2. **Mapping** – CVEs are matched against a small embedded database of Metasploit modul
es (extendable).
3. **Exploit** – The selected Metasploit module runs automatically and attempts to gain
 a session.
4. **Reverse Shell** – The module uses `windows/x64/meterpreter/reverse_tcp` pointing t
o your `LHOST:LPORT`.
5. **RAT** – After a session is established, you can generate a persistent payload and 
deploy it manually.

## Extending the Tool

- Add more CVE → Metasploit module mappings in the `cve_db` dictionary inside `ExploitM
anager`.
- Integrate with Metasploit's `msfrpc` for dynamic exploit selection.
- Implement automatic RAT deployment via the meterpreter session (e.g., `upload` comman
d).
- Add OS detection and tailored payloads.

## Directory Structure

```
vuln-agent/
├── README.md
├── requirements.txt   (empty, no dependencies)
└── vuln_agent.py


## Notes

- Always run with `sudo` for full network scanning capabilities.
- Results are stored in a `vuln_agent_results/` folder.
- The `searchsploit` step in the demo is simplified – in production, parse Nmap service
 versions and search with that.
