# Nmap 7.99 scan initiated Mon Aug 10 02:01:31 2026 as: nmap -sCV -T5 --min-rate 300 --reason -o helixports.md -vvv 10.129.245.123
Increasing send delay for 10.129.245.123 from 0 to 5 due to 19 out of 47 dropped probes since last increase.
Warning: 10.129.245.123 giving up on port because retransmission cap hit (2).
Nmap scan report for 10.129.245.123
Host is up, received syn-ack (0.18s latency).
Scanned at 2026-08-10 02:01:32 -03 for 47s
Not shown: 611 closed tcp ports (conn-refused), 387 filtered tcp ports (no-response)
PORT   STATE SERVICE REASON  VERSION
22/tcp open  ssh     syn-ack OpenSSH 8.9p1 Ubuntu 3ubuntu0.15 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 60:b3:f7:6c:0b:92:ab:00:ac:e7:12:e1:d1:26:9c:1e (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBPTJ+LkpmuH2sQS9dhqnvmpl1NhudGQHvIxfw5Qrhj2MEU4J7VXSPAt/OPas+zeYGU8XOWgNtfnJjHEYe3XsLII=
|   256 c8:30:e6:cb:c6:cd:fc:0c:39:e5:34:04:20:07:b9:b3 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGYnLTVO7QjbF2nWYA4R9O3DaSGllmNuBdWKKZyZxMZS
80/tcp open  http    syn-ack nginx 1.18.0 (Ubuntu)
| http-methods: 
|_  Supported Methods: GET HEAD POST
|_http-title: Did not follow redirect to http://helix.htb/
|_http-server-header: nginx/1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Mon Aug 10 02:02:19 2026 -- 1 IP address (1 host up) scanned in 48.74 seconds
