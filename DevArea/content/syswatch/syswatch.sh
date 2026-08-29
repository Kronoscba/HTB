#!/bin/bash
set -euo pipefail

CONFIG_FILE="/opt/syswatch/config/syswatch.conf"
SYSWATCH_USER="syswatch"
PLUGIN_DIR="/opt/syswatch/plugins"
LOG_DIR="/opt/syswatch/logs"
SAFE_PLUGIN_REGEX='^[a-zA-Z0-9_.\-$]+$'
SAFE_LOG_REGEX='^[A-Za-z0-9_.-]+$'
VERSION="1.0.0"
source "$CONFIG_FILE"
RUN_AS_ROOT_PLUGINS=("log_monitor.sh")
LIST_EXCLUDE=("common.sh")

log_message() {
    local msg="$1"
    echo "$(date '+%F %T') - $msg" >> "$LOG_DIR/system.log"
    logger -t syswatch "$msg"
}


start_web() {
    # Reload systemd in case service was just added
    systemctl daemon-reload

    # Check if the service is already active
    if systemctl is-active --quiet syswatch-web.service; then
        echo "[*] SysWatch Web GUI is already running."
        return
    fi

    echo "[*] Starting SysWatch Web GUI service..."
    systemctl enable syswatch-web.service >/dev/null 2>&1
    systemctl start syswatch-web.service

    # Give a small delay for startup
    sleep 2

    if systemctl is-active --quiet syswatch-web.service; then
        echo "[+] SysWatch Web GUI started successfully!"
    else
        echo "[-] Failed to start SysWatch Web GUI."
    fi
}

# Function: stop web GUI
stop_web() {
    if ! systemctl is-active --quiet syswatch-web.service; then
        echo "[*] SysWatch Web GUI is not running."
        return
    fi

    echo "[*] Stopping SysWatch Web GUI service..."
    systemctl stop syswatch-web.service
    echo "[+] SysWatch Web GUI stopped."
}

# Function: restart/reload web GUI
reload_web() {
    if ! systemctl is-active --quiet syswatch-web.service; then
        echo "[*] SysWatch Web GUI is not running. Starting it..."
        start_web
        return
    fi

    echo "[*] Reloading SysWatch Web GUI service..."
    systemctl restart syswatch-web.service
    echo "[+] SysWatch Web GUI reloaded successfully!"
}

# Function: show status
status_web() {
    systemctl status syswatch-web.service --no-pager  --lines=0
}



execute_plugin() {
    local plugin="$1"; shift
    if [[ ! $plugin =~ $SAFE_PLUGIN_REGEX ]]; then
        echo "Invalid plugin name" >&2
        return 1
    fi
    local fullpath="$PLUGIN_DIR/$plugin"
    [ ! -f "$fullpath" ] && echo "Plugin not found: $plugin" >&2 && return 1
    log_message "Executing plugin: $plugin $*"
    local run_root=0
    for p in "${RUN_AS_ROOT_PLUGINS[@]}"; do
        if [ "$plugin" = "$p" ]; then
            run_root=1
            break
        fi
    done
    if [ "$run_root" -eq 1 ]; then
        bash "$fullpath" "$@"
    else
        runuser -u "$SYSWATCH_USER" -- bash "$fullpath" "$@"
    fi
}

list_plugins() {
    local files
    files=$(ls -1 "$PLUGIN_DIR" 2>/dev/null | grep -E '^.+\.sh$' || true)
    [ -z "${files:-}" ] && return
    while IFS= read -r f; do
        [ -z "$f" ] && continue
        local skip=0
        for ex in "${LIST_EXCLUDE[@]}"; do
            if [ "$f" = "$ex" ]; then
                skip=1
                break
            fi
        done
        [ "$skip" -eq 1 ] && continue
        echo " - $f"
    done <<< "$files"
}

view_logs() {
    local arg="${1:-}"

    # ---- LIST MODE ----
    if [ "$arg" = "--list" ] || [ "$arg" = "list" ]; then
        local found=0
        for p in "$LOG_DIR"/*.log; do
            [ -e "$p" ] || continue
            [ -L "$p" ] && continue       # skip symlinks in list
            [ -f "$p" ] || continue
            echo " - $(basename "$p")"
            found=1
        done
        [ "$found" -eq 0 ] && echo "[No logs found]"
        return
    fi

    # FILE NAME VALIDATION
    local file="${arg:-system.log}"
    if [[ ! "$file" =~ $SAFE_LOG_REGEX ]]; then
        echo "[Invalid log filename]: $file"
        return 1
    fi

    local path="$LOG_DIR/$file"
    if [ -L "$path" ]; then
        local target
        target=$(ls -l "$path" | awk '{print $NF}')

        if [[ "$target" == *"/"* || "$target" == *".."* || "$target" == *"\\"* ]]; then
            echo "[Blocked unsafe symlink target]: $file -> $target"
            return 1
        fi

        if [[ "$target" =~ ^[A-Za-z0-9_.-]+$ ]]; then
            local resolved="$LOG_DIR/$target"
            if [ -f "$resolved" ]; then
                cat "$resolved"
                return
            else
                echo "[Symlink target not found]: $file -> $target"
                return 1
            fi
        fi

        if [[ "$target" == /var/log/* ]]; then
            [ -f "$target" ] && cat "$target" && return
            echo "[Symlink target not regular file]: $file -> $target"
            return 1
        fi

        echo "[Refusing unsafe symlink]: $file -> $target"
        return 1
    fi

    if [[ "$file" == */* || "$file" == *".."* ]]; then
        echo "[Blocked unsafe filename]: $file"
        return 1
    fi
    
    if [ -f "$path" ]; then
        cat "$path"
    else
        echo "[Log file not found]: $file"
    fi
}


usage() {
    echo "SysWatch $VERSION"
    echo "Usage: $0 <command> [args]"
    echo "Commands:"
    echo "  web                 Start web GUI"
    echo "  web-stop            Stop web GUI"
    echo "  web-restart         Restart web GUI"
    echo "  web-status          Show web GUI status"
    echo "  plugin <name> [args] Execute plugin"
    echo "  plugins             List available plugins"
    echo "  logs <file>         View log file"
    echo "  logs --list         List available log files"
    echo "  --version           Show version"
    echo "  --help|-h|help      Show this help"
}

main() {
    case "${1:-}" in
        web) start_web ;;
        web-stop) stop_web ;;
        web-restart|web-reload) reload_web ;;
        web-status) status_web ;;
        plugin) shift; execute_plugin "$@" ;;
        plugins) list_plugins ;;
        logs) shift; view_logs "$@" ;;
        --version) echo "$VERSION" ;;
        help|--help|-h) usage ;;
        *)
            usage
            ;;
    esac
}


if [ "$(id -u)" -eq 0 ]; then
    main "$@"
else
    if [[ "${1:-}" == "logs" ]]; then
        main "$@"
    else
        echo "Access denied. Root required for this action." >&2
        exit 1
    fi
fi
