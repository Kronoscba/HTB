#!/bin/bash
# Common functions for all monitoring scripts

log_message() {
    local logfile="$1"
    local msg="$2"
    if [ -L "$logfile" ]; then
        rm -f -- "$logfile"
        : > "$logfile"
        chmod 644 "$logfile"
    elif [ ! -f "$logfile" ]; then
        : > "$logfile"
        chmod 644 "$logfile"
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $msg" >> "$logfile"
}

send_alert() {
    local logfile="$1"
    local msg="$2"
    local email="$3"
    log_message "$logfile" "$msg"
    echo "$msg" | mail -s "Server Alert: $(hostname)" "$email"
}
