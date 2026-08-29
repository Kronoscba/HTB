#!/bin/bash
source /opt/syswatch/config/syswatch.conf
source /opt/syswatch/plugins/common.sh
umask 022

LOG_FILE="$DISK_LOG"
EMAIL="$EMAIL_ADMIN"
EXCLUDE_LIST=("tmpfs" "devtmpfs" "squashfs")

[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE" && chmod 644 "$LOG_FILE"

log_message "$LOG_FILE" "Running disk space check"

ALERTS=""
while read -r line; do
    [[ "$line" =~ ^Filesystem ]] && continue

    FILESYSTEM=$(echo "$line" | awk '{print $1}')
    MOUNT=$(echo "$line" | awk '{print $NF}')
    USAGE=$(echo "$line" | awk '{print $5}' | sed 's/%//')

    SKIP=0
    for EXCL in "${EXCLUDE_LIST[@]}"; do
        [[ "$FILESYSTEM" == *"$EXCL"* ]] && SKIP=1 && break
    done

    [ "$SKIP" -eq 1 ] && continue

    if [ "$USAGE" -gt "$DISK_THRESHOLD" ]; then
        ALERTS+="  - $MOUNT (usage: ${USAGE}%)"$'\n'
    fi

done <<< "$(df -h)"

if [ ! -z "$ALERTS" ]; then
    MESSAGE="DISK SPACE ALERT: Filesystems exceeding ${DISK_THRESHOLD}%:\n$ALERTS"
    send_alert "$LOG_FILE" "$MESSAGE" "$EMAIL"
fi
exit 0
