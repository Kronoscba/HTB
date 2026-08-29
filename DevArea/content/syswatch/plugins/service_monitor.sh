#!/bin/bash
source /opt/syswatch/config/syswatch.conf
source /opt/syswatch/plugins/common.sh
umask 022

LOG_FILE="$SERVICE_LOG"
EMAIL="$EMAIL_ADMIN"
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE" && chmod 644 "$LOG_FILE"

log_message "$LOG_FILE" "Checking service status"

FAILED=""
RESTARTED=""

for SVC in "${SERVICES[@]}"; do
    NAME=$(echo "$SVC" | cut -d: -f1)
    FLAG=$(echo "$SVC" | cut -d: -f2)
    if systemctl is-active --quiet "$NAME"; then
        log_message "$LOG_FILE" "$NAME running"
    else
        log_message "$LOG_FILE" "$NAME not running"
        FAILED="$FAILED$NAME "
        [ "$FLAG" -eq 1 ] && systemctl restart "$NAME" && sleep 2 && systemctl is-active --quiet "$NAME" && RESTARTED="$RESTARTED$NAME "
    fi
done

[ ! -z "$FAILED" ] && send_alert "$LOG_FILE" "SERVICE ALERT: Failed services: $FAILED\nRestarted: $RESTARTED" "$EMAIL"
exit 0
