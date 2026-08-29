#!/bin/bash
source /opt/syswatch/config/syswatch.conf
source /opt/syswatch/plugins/common.sh
umask 022

LOG_FILE="$LOG_MONITOR_LOG"
EMAIL="$EMAIL_ADMIN"
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE" && chmod 644 "$LOG_FILE"

declare -A LOG_PATTERNS=(
    ["/var/log/syslog"]="(error|critical|fatal|failed|failure)"
    ["/var/log/auth.log"]="(failed|invalid|error|authentication failure)"
    ["/var/log/apache2/error.log"]="(fatal|error|critical)"
    ["/var/log/mysql/error.log"]="(ERROR|CRITICAL)"
)

TIMESTAMP_FILE="/tmp/logmonitor_timestamp"
[ -f "$TIMESTAMP_FILE" ] && LAST_RUN=$(cat "$TIMESTAMP_FILE") || LAST_RUN=$(date -d "10 minutes ago" "+%Y-%m-%d %H:%M:%S")
date "+%Y-%m-%d %H:%M:%S" > "$TIMESTAMP_FILE"

date_to_seconds() { date -d "$1" +%s; }
LAST_RUN_SECONDS=$(date_to_seconds "$LAST_RUN")
CURRENT_SECONDS=$(date_to_seconds "$(date '+%Y-%m-%d %H:%M:%S')")

ALERTS=""
for LOG in "${!LOG_PATTERNS[@]}"; do
    [ ! -f "$LOG" ] && log_message "$LOG_FILE" "Warning: $LOG not found" && continue
    NEW_ENTRIES=$(grep -i -E "${LOG_PATTERNS[$LOG]}" "$LOG")
    [ ! -z "$NEW_ENTRIES" ] && ALERTS="$ALERTS$LOG - New critical entries:\n$(echo "$NEW_ENTRIES" | head -n 15)\n\n"
done

[ ! -z "$ALERTS" ] && send_alert "$LOG_FILE" "LOG ALERT:\n$ALERTS" "$EMAIL"
exit 0
