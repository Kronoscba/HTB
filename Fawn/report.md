# HTB Fawn - Assessment Report

**Date**: 2026-06-27
**Target IP**: 10.129.134.77
**Difficulty**: Easy
**Total Time**: ~5 minutes

---

## Executive Summary

Hack The Box machine "Fawn" was compromised through anonymous FTP login. The machine exposed a single service (FTP) with anonymous access enabled, allowing direct retrieval of the user flag without authentication.

**Risk Level**: Critical (full flag compromised)
**Attack Vector**: Anonymous FTP login

---

## Methodology

### Phase 1: Reconnaissance
- **Tool**: rustscan + nmap
- **Finding**: Only port 21/tcp open (vsftpd 3.0.3)
- **Evidence**: `nmap/initial_rustscan.txt`, `nmap/full_tcp_scan.txt`

### Phase 2: Service Enumeration
- **Tool**: curl
- **Finding**: Anonymous FTP login allowed (code 230)
- **Command**: `curl -s --list-only ftp://anonymous:anonymous@10.129.134.77/`
- **Finding**: Single file `flag.txt` (32 bytes) in root directory

### Phase 3: Exploitation
- **Tool**: curl
- **Command**: `curl -s ftp://anonymous:anonymous@10.129.134.77/flag.txt > loot/flag.txt`
- **Result**: Flag retrieved successfully

---

## Findings

### [FIND-001] Anonymous FTP Login Enabled
- **Severity**: Critical
- **CVSS 3.1**: 10.0 (AV:N/AC:L/PR:N/UI:N/C:C/I:C/A:N)
- **CWE**: CWE-284 (Improper Access Control)
- **Location**: 10.129.134.77:21
- **Description**: vsftpd 3.0.3 configured with anonymous FTP login allowed. No authentication required to access files.
- **Evidence**:
  - `nmap/full_tcp_scan.txt` (line 20: ftp-anon: Anonymous FTP login allowed)
- **Impact**: Complete information disclosure. Any unauthenticated user can read all files accessible to the ftp user.
- **Remediation**: Disable anonymous FTP access in vsftpd.conf (`anonymous_enable=NO`)
- **References**: vsftpd documentation, CIS Benchmarks

### [FIND-002] Flag Exposed on Anonymous FTP
- **Severity**: Critical
- **Location**: 10.129.134.77:21/flag.txt
- **Description**: User flag stored in a world-readable location on an anonymous FTP server.
- **Evidence**: `loot/flag.txt`
- **Impact**: Direct flag compromise

---

## Evidence Inventory

| File | Type | Description |
|------|------|-------------|
| `nmap/initial_rustscan.txt` | Port scan | Initial port discovery |
| `nmap/full_tcp_scan.txt` | Port scan | Full TCP scan (65535 ports) |
| `loot/flag.txt` | Flag | User flag |
| `evidence/user_flag.txt` | Flag | User flag (copy) |

---

## Lessons Learned

1. **FTP anonymous login is a common easy-box vector** — always test it first when FTP (port 21) is discovered.
2. **Minimal attack surface**: Only one port exposed means limited enumeration needed.
3. **No privilege escalation required**: The flag was directly accessible without gaining shell access.
