from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session, flash
from collections import deque
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import re
import shutil
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SYSWATCH_SECRET_KEY", "change-me")
LOG_DIR = os.environ.get("SYSWATCH_LOG_DIR", "/opt/syswatch/logs")
DB_PATH = os.environ.get("SYSWATCH_DB_PATH", os.path.join(os.path.dirname(__file__), "syswatch.db"))
PLUGIN_DIR = os.environ.get("SYSWATCH_PLUGIN_DIR", "/opt/syswatch/plugins")
BACKUP_DIR = os.environ.get("SYSWATCH_BACKUP_DIR", "/opt/syswatch/backup")
APP_VERSION = os.environ.get("SYSWATCH_VERSION", "1.0.0")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)"
    )
    conn.commit()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()[0] == 0:
        pwd = os.environ.get("SYSWATCH_ADMIN_PASSWORD")
        if pwd:
            cur.execute("INSERT INTO users(username, password_hash) VALUES(?, ?)", ("admin", generate_password_hash(pwd)))
            conn.commit()
    conn.close()

init_db()

LOG_FILES = {
    "CPU & Memory": "cpu-mem.log",
    "Disk Usage": "disk.log",
    "Network Traffic": "network.log",
    "Log Alerts": "log-alerts.log",
    "Service Status": "service.log"
}

PLUGIN_SCRIPTS = {
    "CPU & Memory": "cpu_mem_monitor.sh",
    "Disk Usage": "disk_monitor.sh",
    "Network Traffic": "network_monitor.sh",
    "Log Alerts": "log_monitor.sh",
    "Service Status": "service_monitor.sh",
}


def read_log_file(filename, max_lines=200):
    path = os.path.join(LOG_DIR, filename)

    # File does not exist
    if not os.path.isfile(path):
        return ["[Log file not found]"]

    try:
        with open(path, "r", errors="ignore") as f:
            return list(deque(f, maxlen=max_lines))

    except PermissionError:
        return [f"[Permission denied]: {filename}"]

    except Exception as e:
        return [f"[Error reading file {filename}]: {e}"]



def require_login():
    if not session.get("user_id"):
        return redirect(url_for("login"))

@app.route("/")
def index():
    r = require_login()
    if r:
        return r
    structured_logs = {name: {"filename": fname, "lines": read_log_file(fname)}
                       for name, fname in LOG_FILES.items()}
    return render_template("index.html", logs=structured_logs, version=APP_VERSION)

ALLOWED = set(LOG_FILES.values())

@app.route("/download/<filename>")
def download(filename):
    r = require_login()
    if r:
        return r
    if filename not in ALLOWED:
        return "Forbidden", 403
    return send_from_directory(LOG_DIR, filename, as_attachment=True)

@app.route("/service-status", methods=["GET", "POST"])
@app.route("/service-status/", methods=["GET", "POST"])

SAFE_SERVICE = re.compile(r"^[^;/\&.<>\rA-Z]*$")

def service_status():
    r = require_login()
    if r:
        return r
    output = None
    error = None
    service = ""
    if request.method == "POST":
        service = request.form.get("service", "").strip()
        if not service or not SAFE_SERVICE.match(service):
            error = "Invalid service name"
        else:
            try:
                res = subprocess.run([f"systemctl status --no-pager {service}"], shell=True,capture_output=True, text=True, timeout=10)
                output = res.stdout if res.stdout else res.stderr
            except Exception as e:
                error = str(e)
    return render_template("service_status.html", output=output, error=error, service=service)

def safe_join(dirpath, filename):
    if not re.match(r"^[A-Za-z0-9_.-]+$", filename):
        return None
    full = os.path.abspath(os.path.join(dirpath, filename))
    base = os.path.abspath(dirpath)
    return full if full.startswith(base + os.sep) or full == base else None

@app.route("/refresh/<key>", methods=["POST"])
def refresh_log(key):
    r = require_login()
    if r:
        return r
    name = None
    for k in LOG_FILES.keys():
        if k.replace(" ", "_").lower() == key.lower():
            name = k
            break
    if not name or name not in PLUGIN_SCRIPTS:
        flash("Unknown log key")
        return redirect(url_for("index"))
    script = PLUGIN_SCRIPTS[name]
    script_path = safe_join(PLUGIN_DIR, script)
    if not script_path or not os.path.isfile(script_path):
        flash("Plugin script not found or invalid")
        return redirect(url_for("index"))
    try:
        res = subprocess.run(["bash", script_path], capture_output=True, text=True, timeout=20)
        if res.returncode == 0:
            flash(f"Refreshed: {name}")
        else:
            msg = res.stderr.strip() or "Plugin error"
            flash(f"Failed to refresh {name}: {msg}")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for("index"))

@app.route("/backup-logs", methods=["POST"])
def backup_logs():
    r = require_login()
    if r:
        return r
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = os.path.join(BACKUP_DIR, ts)
        os.makedirs(target, exist_ok=True)
        copied = []
        for fname in LOG_FILES.values():
            src_path = safe_join(LOG_DIR, fname)
            if not src_path:
                continue
            if os.path.exists(src_path):
                if os.path.isfile(src_path) or os.path.islink(src_path):
                    shutil.copy2(src_path, os.path.join(target, fname))
                    try:
                        if os.path.islink(src_path):
                            os.unlink(src_path)
                        else:
                            os.remove(src_path)
                    except Exception:
                        pass
                    with open(src_path, "w"):
                        pass
                    try:
                        os.chmod(src_path, 0o644)
                    except Exception:
                        pass
                    copied.append(fname)
        flash(f"Backed up and cleaned: {', '.join(copied)}" if copied else "No logs to backup")
    except Exception as e:
        flash(f"Backup error: {e}")
    return redirect(url_for("index"))

@app.route("/docs")
def docs():
    r = require_login()
    if r:
        return r
    return render_template("docs.html", version=APP_VERSION)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
            session["username"] = username
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid credentials", version=APP_VERSION)
    if session.get("user_id"):
        return redirect(url_for("index"))
    return render_template("login.html", version=APP_VERSION)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7777, debug=False)
