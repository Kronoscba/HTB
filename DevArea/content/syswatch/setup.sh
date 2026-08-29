#!/bin/bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then echo "Require root"; exit 1; fi
echo "[*] SysWatch setup starting"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPT_DIR="/opt/syswatch"
id -u syswatch >/dev/null 2>&1 || useradd --system --create-home -d "$OPT_DIR" --shell /usr/sbin/nologin syswatch
install -d -m 0755 "$OPT_DIR/plugins" "$OPT_DIR/config" "$OPT_DIR/logs" "$OPT_DIR/backup" "$OPT_DIR/syswatch_gui"
install -m 0644 "$SRC_DIR/config/syswatch.conf" "$OPT_DIR/config/syswatch.conf"
cp -r "$SRC_DIR/plugins/." "$OPT_DIR/plugins/"
install -m 0755 "$SRC_DIR/monitor.sh" "$OPT_DIR/monitor.sh"
install -m 0755 "$SRC_DIR/syswatch.sh" "$OPT_DIR/syswatch.sh"
cp -r "$SRC_DIR/syswatch_gui/." "$OPT_DIR/syswatch_gui/"
chown -R root:root "$OPT_DIR"
chown -R syswatch:syswatch "$OPT_DIR/logs"
chown -R syswatch:syswatch "$OPT_DIR/backup"

chmod 755 "$OPT_DIR" "$OPT_DIR/plugins" "$OPT_DIR/config" "$OPT_DIR/syswatch_gui"
if command -v apt-get >/dev/null 2>&1; then
  echo "[*] Installing packages via apt"
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip net-tools mailutils
elif command -v dnf >/dev/null 2>&1; then
  echo "[*] Installing packages via dnf"
  dnf install -y python3 python3-venv python3-pip net-tools mailx
elif command -v yum >/dev/null 2>&1; then
  echo "[*] Installing packages via yum"
  yum install -y python3 python3-venv python3-pip net-tools mailx
else
  echo "Package manager not detected"; exit 1
fi
python3 -m venv "$OPT_DIR/venv"
"$OPT_DIR/venv/bin/pip" install --upgrade pip
"$OPT_DIR/venv/bin/pip" install -r "$OPT_DIR/syswatch_gui/requirements.txt"
ENV_FILE="/etc/syswatch.env"
SECRET="${SYSWATCH_SECRET_KEY:-}"
ADMIN="${SYSWATCH_ADMIN_PASSWORD:-}"
if [ -z "$SECRET" ]; then
  if command -v openssl >/dev/null 2>&1; then
    SECRET="$(openssl rand -hex 32)"
  else
    SECRET="$(head -c 32 /dev/urandom | xxd -p)"
  fi
fi
[ -z "$ADMIN" ] && ADMIN="SyswatchAdmin2026"
cat > "$ENV_FILE" <<EOF
SYSWATCH_SECRET_KEY=$SECRET
SYSWATCH_ADMIN_PASSWORD=$ADMIN
SYSWATCH_LOG_DIR=$OPT_DIR/logs
SYSWATCH_DB_PATH=$OPT_DIR/syswatch_gui/syswatch.db
SYSWATCH_PLUGIN_DIR=$OPT_DIR/plugins
SYSWATCH_BACKUP_DIR=$OPT_DIR/backup
SYSWATCH_VERSION=1.0.0
EOF
chmod 755 "$ENV_FILE"
WEB_UNIT="/etc/systemd/system/syswatch-web.service"
cat > "$WEB_UNIT" <<EOF
[Unit]
Description=SysWatch Web GUI
After=network.target

[Service]
Type=simple
User=syswatch
Group=syswatch
EnvironmentFile=$ENV_FILE
WorkingDirectory=$OPT_DIR/syswatch_gui
ExecStart=$OPT_DIR/venv/bin/python $OPT_DIR/syswatch_gui/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
MON_SVC="/etc/systemd/system/syswatch-monitor.service"
cat > "$MON_SVC" <<EOF
[Unit]
Description=SysWatch Monitor Runner

[Service]
Type=oneshot
User=root
Group=root
EnvironmentFile=$ENV_FILE
ExecStart=/bin/bash $OPT_DIR/monitor.sh
EOF
MON_TIMER="/etc/systemd/system/syswatch-monitor.timer"
cat > "$MON_TIMER" <<EOF
[Unit]
Description=Run SysWatch Monitor every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Unit=syswatch-monitor.service

[Install]
WantedBy=timers.target
EOF
install -m 0755 "$OPT_DIR/syswatch.sh" /usr/local/bin/syswatch
systemctl daemon-reload
systemctl enable --now syswatch-web.service
systemctl enable --now syswatch-monitor.timer
#if command -v ufw >/dev/null 2>&1; then ufw allow 7777/tcp || true; fi
echo "[+] SysWatch setup complete"
