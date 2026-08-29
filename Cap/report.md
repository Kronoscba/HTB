# Penetration Testing Report — Cap (Hack The Box)

**Date:** 2026-06-28
**Target:** 10.129.41.19
**Assessment Type:** CTF — Hack The Box Machine (Easy)
**Tester:** Gabi
**Duration:** ~15 minutes

---

## 1. Executive Summary

An external penetration test was conducted against the Hack The Box machine "Cap" (10.129.41.19). The assessment identified **two critical vulnerabilities** that allowed full compromise of the system:

1. **Cleartext FTP credentials exposed in downloadable PCAP captures** — the web application's Security Dashboard feature allows any unauthenticated user to download packet capture files containing sensitive data, including valid FTP credentials for user `nathan`.
2. **Misconfigured Linux capabilities on Python 3.8** (`cap_setuid`) — once initial access was obtained via SSH, the `cap_setuid` capability on `/usr/bin/python3.8` allowed trivial privilege escalation to root without requiring sudo or any additional exploits.

**Risk Level: Critical** — Full system compromise achieved starting from zero authentication.

---

## 2. Methodology

The assessment followed the **PTES (Penetration Testing Execution Standard)** framework:

| Phase | Actions Performed | Tools |
|-------|-------------------|-------|
| **Pre-engagement** | Scope defined via `.target` file; target IP: 10.129.41.19 | — |
| **Intelligence Gathering** | Port scanning, service enumeration, web technology fingerprinting | rustscan, nmap, httpx, katana |
| **Threat Modeling** | Identified attack surface: FTP (vsftpd 3.0.3), SSH (OpenSSH 8.2), HTTP (Gunicorn/Python) | — |
| **Vulnerability Analysis** | Manual web endpoint analysis, PCAP file analysis, Linux capabilities audit | curl, tshark, getcap |
| **Exploitation** | Credential extraction from PCAP, SSH login, privilege escalation via cap_setuid | sshpass, scp, python3.8 |
| **Post-Exploitation** | Root shell obtained, flags captured | python3.8 (cap_setuid) |
| **Reporting** | This document | — |

---

## 3. Findings

### FIND-001: Cleartext Credentials Exposed in Downloadable PCAP Files

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **CVSS 3.1 Score** | 9.8 (Critical) |
| **CWE** | CWE-312 (Cleartext Storage of Sensitive Information), CWE-200 (Exposure of Sensitive Information) |
| **CVE** | N/A (Application logic flaw) |
| **Location** | `http://10.129.41.19/download/0` |

**Description:**
The Security Dashboard web application at `http://10.129.41.19` exposes unauthenticated endpoints `/download/{id}` that serve raw PCAP (packet capture) files. These captures contain cleartext FTP traffic including valid authentication credentials.

**Evidence:**
- File: `content/capture_0.pcap` — Downloaded via `curl -s -L http://10.129.41.19/download/0 -o content/capture_0.pcap`
- File: `web/pcap0_ftp.txt` — tshark extraction showing FTP USER/PASS commands:
  ```
  USER  nathan
  PASS  Buck3tH4TF0RM3!
  230   Login successful.
  ```

**Impact:**
- Full authentication bypass for FTP service (port 21) and SSH service (port 22)
- Lateral movement: user `nathan` has interactive shell access
- Combined with FIND-002, leads to complete system compromise

**Remediation:**
1. Restrict access to `/download/` endpoints behind authentication
2. Implement access controls on PCAP file downloads
3. Avoid capturing or storing cleartext credentials in diagnostic captures
4. Disable FTP and use SFTP exclusively

---

### FIND-002: Linux Capability Misconfiguration — cap_setuid on Python 3.8

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **CVSS 3.1 Score** | 9.8 (Critical) |
| **CWE** | CWE-269 (Improper Privilege Management) |
| **CVE** | N/A (Configuration issue) |
| **Location** | `/usr/bin/python3.8` — `cap_setuid,cap_net_bind_service+eip` |

**Description:**
The binary `/usr/bin/python3.8` has the `cap_setuid` Linux capability set. This allows any user (including `nathan`) to execute Python as root by calling `os.setuid(0)` before spawning a shell. No sudo password or special permissions required.

**Evidence:**
- File: `ad/capabilities.txt` — Output of `getcap -r /`:
  ```
  /usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip
  ```
- File: `scripts/privesc.py` — Exploitation script:
  ```python
  import os
  os.setuid(0)
  os.system("cat /root/root.txt")
  ```
- File: `loot/root_flag.txt` — Root flag captured: `a32fe3a5829337f7ce90f5ffd730e92d`

**Impact:**
- Complete system compromise — any authenticated user can escalate to root
- Full control over the server: data exfiltration, persistence, lateral movement

**Remediation:**
1. Remove `cap_setuid` from Python3.8: `sudo setcap -r /usr/bin/python3.8`
2. Audit all binaries for unnecessary capabilities: `getcap -r /`
3. Apply principle of least privilege — only grant capabilities when strictly required

---

## 4. Evidence Inventory

| File | Type | Finding | Description |
|------|------|---------|-------------|
| `nmap/initial_rustscan.txt` | Port scan | Recon | Initial rustscan attempt (filtered) |
| `nmap/full_scan.txt` | Port scan | Recon | Full port scan — 3 ports open (21, 22, 80) |
| `nmap/detailed_scan.txt` | Service scan | Recon | Detailed nmap with scripts on ports 21/22/80 |
| `web/httpx_probe.txt` | Web probe | Recon | Technology fingerprinting (Gunicorn, Python, jQuery 2.2.4) |
| `web/katana_crawl.txt` | Web crawl | Recon | Endpoint discovery: /ip, /netstat, /capture, /data/1 |
| `content/capture_0.pcap` | PCAP capture | FIND-001 | Contains cleartext FTP credentials |
| `content/capture_1.pcap` | PCAP capture | FIND-001 | Secondary capture |
| `web/pcap0_ftp.txt` | Analysis | FIND-001 | Extracted FTP USER/PASS from capture_0 |
| `loot/creds.txt` | Credentials | FIND-001 | nathan:Buck3tH4TF0RM3! |
| `ad/users.txt` | User list | FIND-001 | nathan |
| `ad/capabilities.txt` | Capabilities | FIND-002 | cap_setuid on python3.8 |
| `scripts/privesc.py` | Exploit | FIND-002 | Python privilege escalation script |
| `loot/user_flag.txt` | Flag | — | `6861d9372bfb8cc5a5cfb2e65858b1e0` |
| `loot/root_flag.txt` | Flag | — | `a32fe3a5829337f7ce90f5ffd730e92d` |

---

## 5. Remediation Summary

| Priority | Finding | Remediation | Effort |
|----------|---------|-------------|--------|
| **P1 — Immediate** | FIND-001 | Restrict `/download/` behind authentication; disable FTP; rotate credentials | Quick win |
| **P1 — Immediate** | FIND-002 | Remove `cap_setuid` from Python3.8; audit all capabilities | Quick win |
| **P2 — Short term** | General | Implement network segmentation; add WAF; enable HTTPS | Short term |
| **P3 — Long term** | General | Deploy EDR; implement credential rotation policy; security training | Long term |

---

## 6. Lessons Learned & Deviations

- **Rustscan limitation**: Initial rustscan failed due to batch size and firewall filtering. Nmap with `-Pn` was required — note for future VM scans.
- **No authentication required**: The web application serves sensitive data (PCAP files, system commands) without any authentication, making it the primary attack vector.
- **Capabilities overlooked**: Linux capabilities (`getcap`) are often overlooked in privilege escalation checks — always verify them after obtaining initial access.
- **PCAP files as credential source**: Packet captures are a common source of credential leakage in CTF environments — always download and analyze available captures.
