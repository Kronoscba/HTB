#!/bin/bash
source /opt/syswatch/config/syswatch.conf
source /opt/syswatch/plugins/common.sh
umask 022

LOG_FILE="$NETWORK_LOG"
EMAIL="$EMAIL_ADMIN"
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE" && chmod 644 "$LOG_FILE"

log_message "$LOG_FILE" "Checking network connections"

TOTAL=$(netstat -an | grep ESTABLISHED | wc -l)
log_message "$LOG_FILE" "Total active connections: $TOTAL"

[ "$TOTAL" -gt "$NET_MAX_CONNECTIONS" ] && send_alert "$LOG_FILE" "HIGH CONNECTION ALERT: $TOTAL active connections (Threshold: $NET_MAX_CONNECTIONS)" "$EMAIL"

IP_CONNECTIONS=$(netstat -an | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr)
SUSPICIOUS=""
while read -r line; do
    COUNT=$(echo "$line" | awk '{print $1}')
    IP=$(echo "$line" | awk '{print $2}')
    [ "$COUNT" -gt "$NET_MAX_PER_IP" ] && SUSPICIOUS="$SUSPICIOUS$IP - $COUNT connections\n"
done <<< "$IP_CONNECTIONS"

[ ! -z "$SUSPICIOUS" ] && send_alert "$LOG_FILE" "SUSPICIOUS CONNECTION ALERT:\n$SUSPICIOUS" "$EMAIL"
exit 0
