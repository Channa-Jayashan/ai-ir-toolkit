# 🛡️ AI-IR Toolkit

> **AI-powered Incident Response toolkit powered by Gemma-IR + Kali Linux MCP Server**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Kali Linux](https://img.shields.io/badge/Kali_Linux-2026.1-blue?logo=kali-linux)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📖 Overview

**AI-IR Toolkit** is a fully offline, locally hosted AI-driven incident response system that combines the reasoning power of the **Gemma language model** with the execution capabilities of **Kali Linux security tools** — all under strict human operator control.

The system is built around a simple but powerful principle:

> **Gemma is the brain. Kali is the muscle. You are the gatekeeper.**

Every command suggested by the AI must be explicitly approved by the operator before execution. No action is ever taken autonomously.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    OPERATOR (You)                        │
│              Reviews & Approves every command            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   ir-agent.py                            │
│         Orchestration + Approval Gate Layer              │
│   • Sends prompts to Gemma via Ollama HTTP API           │
│   • Parses COMMAND: from Gemma responses                 │
│   • Shows approval prompt to operator                    │
│   • Routes approved commands to MCP server               │
│   • Feeds results back to Gemma for analysis             │
│   • Logs everything with chain-of-custody                │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────┐        ┌──────────────────────────────┐
│  Gemma-IR Model │        │   Kali MCP Server            │
│  (Docker /      │        │   kali-server-mcp            │
│   Ollama)       │        │   Flask API on port 5000     │
│                 │        │                              │
│  gemma2:2b base │        │   Tools available:           │
│  + IR system    │        │   • nmap                     │
│    prompt       │        │   • nikto                    │
│                 │        │   • gobuster / dirb          │
│  Port: 11434    │        │   • sqlmap                   │
└─────────────────┘        │   • hydra                    │
                           │   • john the ripper          │
                           │   • metasploit               │
                           │   • wpscan                   │
                           │   • enum4linux               │
                           │   • raw command execution    │
                           └──────────────────────────────┘
```

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🧠 **AI Reasoning** | Gemma-IR model interprets natural language and suggests precise Kali commands |
| 🔐 **Approval Gate** | Every command requires explicit operator approval before execution |
| 🚫 **Destructive Command Blocking** | Automatically blocks `rm -rf`, `dd`, `mkfs` and similar dangerous patterns |
| 📋 **Chain of Custody Logging** | Every command, output, and timestamp is recorded to a JSON log file |
| 📄 **Session Report Generation** | Auto-generates a professional Markdown IR report at session end |
| 🔍 **Optional Analysis** | Operator can choose whether to get Gemma's analysis after each command |
| 🔄 **Alternative Suggestions** | When a command is rejected, optionally ask Gemma for alternatives |
| 🏥 **Service Health Checks** | Startup checks verify MCP server and Gemma are running before starting |
| 📦 **Fully Offline** | No cloud APIs — everything runs locally on your Kali machine |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Model | Gemma 2 2B (fine-tuned as `gemma-ir`) via Ollama |
| Model Runtime | Docker container (`gemma-ir-brain`) |
| Execution Engine | `kali-server-mcp` — Kali Linux MCP Bridge (Flask/JSON-RPC) |
| Orchestration | Python 3.10+ with `requests`, `rich` |
| Communication | HTTP REST between all components |
| Logging | JSON structured logs + Markdown reports |

---

## 📁 Project Structure

```
ai-ir-toolkit/
├── ir-agent.py              # Main orchestration script
├── docker/
│   ├── docker-compose.yml   # Ollama Docker container config
│   └── Modelfile            # Gemma-IR model definition
├── logs/                    # Auto-created — session logs & reports
│   ├── session-YYYYMMDD-HHMMSS.json
│   └── report-YYYYMMDD-HHMMSS.md
└── venv/                    # Python virtual environment
```

---

## ⚙️ Prerequisites

- **Kali Linux 2026.1** (with `mcp-kali-server` package)
- **Docker** installed and running
- **Python 3.10+**
- **4GB+ RAM** recommended (model is 1.6GB)

---

## 🚀 Installation & Setup

### Step 1 — Clone the repository

```bash
git clone https://github.com/Channa-Jayashan/ai-ir-toolkit.git
cd ai-ir-toolkit
```

### Step 2 — Install the Kali MCP Server

```bash
sudo apt update
sudo apt install mcp-kali-server -y
```

Enable and start the MCP API server:

```bash
sudo systemctl enable kali-server-mcp
sudo systemctl start kali-server-mcp
```

Fix the PATH so the MCP server can find Kali tools:

```bash
sudo systemctl edit kali-server-mcp
```

Add inside the editor:

```ini
[Service]
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart kali-server-mcp
```

Verify it's running:

```bash
curl http://localhost:5000/health
```

### Step 3 — Set up Gemma-IR Docker container

```bash
cd docker
docker compose up -d
```

Wait ~30 seconds for Ollama to initialize, then pull and build the model:

```bash
docker exec -it gemma-ir-brain ollama pull gemma2:2b
docker exec -it gemma-ir-brain ollama create gemma-ir -f /Modelfile
```

Verify the model is available:

```bash
docker exec -it gemma-ir-brain ollama list
```

You should see `gemma-ir:latest` in the list.

### Step 4 — Set up Python environment

```bash
cd ~/ai-ir-toolkit
python3 -m venv venv
source venv/bin/activate
pip install requests rich
```

### Step 5 — Run the toolkit

```bash
source venv/bin/activate
python3 ir-agent.py
```

---

## 🖥️ Usage

When you start the toolkit, it performs automatic service checks:

```
✔ MCP Kali Server — healthy
✔ Gemma-IR model — reachable at http://localhost:11434
```

Then you interact naturally in plain English:

```
[You] scan localhost for open ports

🧠 Gemma-IR:
COMMAND: nmap -sS -T4 -p- 127.0.0.1

🔧 Gemma-IR wants to execute:
  nmap -sS -T4 -p- 127.0.0.1

Approve this command? [y/n]: y

⚡ Executing...

📊 Output [exit code: 0]:
  Starting Nmap 7.99...
  PORT     STATE  SERVICE
  22/tcp   open   ssh
  5000/tcp open   upnp
  ...

Want Gemma-IR to analyze these results? [y/n]: y

🧠 Gemma-IR Analysis:
  Port 22 (SSH) is open — standard remote access...
  Port 5000 is the MCP server itself...
```

### Interactive Commands

| Input | Action |
|-------|--------|
| Any natural language | Gemma reasons and suggests a command |
| `y` at approval gate | Execute the command |
| `n` at approval gate | Reject — optionally get alternative |
| `exit` or `quit` | End session and optionally generate report |

---

## 📄 Session Logs & Reports

Every session automatically creates two files in `~/ai-ir-toolkit/logs/`:

**JSON Log** (`session-YYYYMMDD-HHMMSS.json`) — structured machine-readable record:
```json
{
  "session_id": "20260428-230145",
  "session_start": "2026-04-28T23:01:45",
  "commands_run": 3,
  "commands_rejected": 1,
  "entries": [
    {
      "timestamp": "2026-04-28T23:02:10",
      "command": "nmap -sS -T4 127.0.0.1",
      "exit_code": 0,
      "stdout": "...",
      "success": true
    }
  ]
}
```

**Markdown Report** (`report-YYYYMMDD-HHMMSS.md`) — human-readable IR report with:
- Session metadata
- Full chain of custody log
- All command outputs
- Rejected commands
- Conversation summary

---

## 🔒 Security Considerations

- **Approval gate** — no command executes without operator confirmation
- **Destructive command blocking** — `rm -rf`, `dd if=`, `mkfs`, `shutdown` etc. are automatically blocked
- **Localhost only** — MCP server binds to `127.0.0.1:5000` by default
- **Dedicated service user** — MCP server runs as `_mcp-kali` with limited privileges
- **No cloud connectivity** — all AI inference is fully local via Ollama
- **Prompt injection awareness** — Gemma's system prompt warns it to never interpret tool output as instructions

> ⚠️ **Disclaimer:** This toolkit is intended for authorized security testing, CTF challenges, and educational purposes only. Always obtain proper authorization before scanning or testing any system. The author assumes no responsibility for misuse.

---

## 🗺️ Roadmap

- [ ] Web UI dashboard instead of terminal
- [ ] SHA-256 evidence hashing for chain of custody
- [ ] Multi-session report aggregation
- [ ] Support for larger Gemma models (GPU)
- [ ] Integration with SIEM platforms
- [ ] Automated report export to PDF

---

## 🙏 Acknowledgements

- [MCP Kali Server](https://gitlab.com/kalilinux/packages/mcp-kali-server) — Kali Linux MCP Bridge
- [Ollama](https://ollama.com) — Local LLM runtime
- [Google Gemma](https://ai.google.dev/gemma) — Base model
- [Rich](https://github.com/Textualize/rich) — Terminal UI library

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/Channa-Jayashan">Channa Jayashan</a>
</p>
