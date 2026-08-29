#!/bin/bash
source /opt/syswatch/config/syswatch.conf

mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

for script in /opt/syswatch/plugins/*.sh; do
    # Skip common.sh
    if [[ "$script" == *"common.sh" ]]; then
        continue
    fi

    bash "$script" &
done

wait
