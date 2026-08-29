# Hidden Deep Into My Heart — HackTheBox Web Challenge

**Category:** Web · **Difficulty:** Easy · **Points:** 100
**Target:** `http://10.67.183.32:5000` · **Date:** 2026-06-29

## Flag

```
THM{l0v3_is_in_th3_r0b0ts_txt}
```

## TL;DR

Information disclosure in `robots.txt` leaks a hidden path and a credential hint. The credential works on a hidden admin login form found by directory fuzzing under that path. No exploit, no injection — pure recon.

## Recon

Initial request to `/` returned a 200 with a static "Love Letters Anonymous" landing page (Flask / Werkzeug 3.1.5, Python 3.10.12). No forms, no JS, no API. Manual checks on common paths (`/admin`, `/login`, `/api`, `/flag`, `/vault`, `/secret`, `/backup`, `/sitemap.xml`, `/.git/HEAD`) all returned 404.

**Two hits out of the obvious path list:**
- `GET /robots.txt` → 200
- `GET /console` → 400 (Werkzeug debug console path; not relevant to the challenge)

## Vulnerability 1 — Information disclosure in `robots.txt`

```
$ curl -s http://10.67.183.32:5000/robots.txt
User-agent: *
Disallow: /cupids_secret_vault/*

# cupid_arrow_2026!!!
```

Two leaks in one file:
1. A hidden path: `/cupids_secret_vault/*`.
2. A credential hint left as a comment: `cupid_arrow_2026!!!`.

The "comment" is clearly a password — same shape as a Cupid-themed secret, with `!!!` and a year pattern. At this point I had one path and one candidate password.

## Vulnerability 2 — Hidden admin endpoint

`/cupids_secret_vault/` returned a static page ("You've found the secret vault, but there's more to discover…"). Querying it with `?password=…` and similar produced 200, but the response body never changed — pure static HTML, no handler logic.

Ad-hoc guessing of subpaths (`/deep`, `/heart`, `/inside_my_heart`, etc.) returned 404. Switched to `ffuf` with `seclists/Discovery/Web-Content/common.txt`:

```
$ ffuf -u http://10.67.183.32:5000/cupids_secret_vault/FUZZ \
       -w /usr/share/seclists/Discovery/Web-Content/common.txt \
       -mc 200,301,302,403 -t 30 -s
administrator
```

Only one hit: `/cupids_secret_vault/administrator`, a real admin login form (`username` + `password`, POST).

## Exploit

The leak in `robots.txt` was the full credential. Tested `admin` as username (typical for "administrator" routes):

```
$ curl -s -X POST -d "username=admin&password=cupid_arrow_2026%21%21%21" \
       http://10.67.183.32:5000/cupids_secret_vault/administrator
...
<h1>Welcome, Cupid!</h1>
<p class="message">
  Congratulations! You've discovered Cupid's secret vault
  and found the hidden treasure of love!
</p>
<div class="flag-box">
  THM{l0v3_is_in_th3_r0b0ts_txt}
</div>
```

Other usernames (`administrator`, `cupid`, `root`, `love`, `valentine`) all returned "Invalid credentials!" — only `admin` matched.

## Result

- **Flag:** `THM{l0v3_is_in_th3_r0b0ts_txt}`
- **Submission:** paste flag into HTB challenge page to mark complete.

## Lessons / takeaways

- **Always read `robots.txt`** — it is public by design and commonly leaks paths and developer comments that should never have shipped.
- **Comments in config files are not secrets.** A password left as a `# comment` in robots is the same as no password.
- **Directory fuzzing beats guessing** when a static page hints "there's more to discover". One `ffuf` run with the small SecLists wordlist is cheaper than typing subpaths by hand.
- **Hidden ≠ protected.** Obfuscating a route via `robots.txt` Disallow is not access control; it is an index for anyone who reads it.
- **The flag itself is the lesson**: `l0v3_is_in_th3_r0b0ts_txt` — the entire challenge is a riff on this mistake.

## Attack chain summary

```
GET /robots.txt
  → leaks /cupids_secret_vault/*  +  password "cupid_arrow_2026!!!"
GET /cupids_secret_vault/administrator  (found via ffuf on the vault subtree)
  → admin login form
POST username=admin & password=cupid_arrow_2026!!!
  → THM{l0v3_is_in_th3_r0b0ts_txt}
```