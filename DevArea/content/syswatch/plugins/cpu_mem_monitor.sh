#!/bin/bash
source /opt/syswatch/config/syswatch.conf
source /opt/syswatch/plugins/common.sh
umask 022

LOG_FILE="$CPU_MEM_LOG"
EMAIL="$EMAIL_ADMIN"

# Create log file if it doesn't exist
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE" && chmod 644 "$LOG_FILE"

CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print 100-$8}' | cut -d. -f1)
MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}' | cut -d. -f1)

log_message "$LOG_FILE" "CPU: ${CPU_USAGE}%, Memory: ${MEM_USAGE}%"

[ "$CPU_USAGE" -gt "$CPU_THRESHOLD" ] && send_alert "$LOG_FILE" "HIGH CPU ALERT: ${CPU_USAGE}% (Threshold: $CPU_THRESHOLD%)" "$EMAIL"
[ "$MEM_USAGE" -gt "$MEM_THRESHOLD" ] && send_alert "$LOG_FILE" "HIGH MEMORY ALERT: ${MEM_USAGE}% (Threshold: $MEM_THRESHOLD%)" "$EMAIL"
exit 0
