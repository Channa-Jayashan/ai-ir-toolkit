#!/usr/bin/env python3
"""
AI-IR Toolkit v4.0
Gemma-IR + MCP Kali Server
Dockerized • Offline • Chain-of-Custody • Approval Gate • Session Reports
"""

import requests
import json
import datetime
import os
import sys
import re
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.rule import Rule
from rich import box

console = Console()

# ====================== CONFIG ======================
OLLAMA_URL   = "http://localhost:11434"
KALI_MCP_URL = "http://localhost:5000"
MODEL        = "gemma-ir"
LOGS_DIR     = os.path.expanduser("~/ai-ir-toolkit/logs")

# ====================== SESSION STATE ======================
SESSION = {
    "session_id":    None,
    "session_start": None,
    "session_end":   None,
    "model":         MODEL,
    "kali_mcp":      KALI_MCP_URL,
    "ollama_url":    OLLAMA_URL,
    "commands_run":  0,
    "commands_rejected": 0,
    "entries":       [],
    "conversation":  []
}

LOG_FILE    = None
REPORT_FILE = None

# ====================== SYSTEM PROMPT ======================
SYSTEM_PROMPT = """You are Gemma-IR, an expert Digital Forensics and Incident Response (DFIR) analyst on Kali Linux.
You have access to real Kali Linux tools via an MCP execution server.

When you need to run a command, output it in this EXACT format on its own line:
COMMAND: <the exact shell command>

Rules:
- Always use COMMAND: prefix for any command you want to execute
- Suggest only one command at a time
- After seeing command output, analyze it professionally and suggest next steps
- Always maintain chain of custody in your analysis
- Think step by step using <think> tags when planning complex tasks
- Be concise and professional
- Never suggest destructive commands (rm, dd, format) without clear justification"""


# ====================== STARTUP CHECKS ======================
def check_services():
    """Check that MCP server and Ollama are reachable before starting."""
    all_ok = True

    # Check MCP server
    try:
        r = requests.get(f"{KALI_MCP_URL}/health", timeout=60)
        data = r.json()
        console.print(f"[green]✔ MCP Kali Server[/green] — {data.get('status', 'unknown')}")
    except Exception:
        console.print("[red]✘ MCP Kali Server is NOT running on port 5000[/red]")
        console.print("[yellow]  → Run: sudo systemctl start kali-server-mcp[/yellow]")
        all_ok = False

    # Check Ollama / Gemma
    try:
    	r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
    	if r.status_code == 200:
        	models = [m["name"] for m in r.json().get("models", [])]
        	if MODEL in models or any(MODEL in m for m in models):
            		console.print(f"[green]✔ Gemma-IR model[/green] — reachable at {OLLAMA_URL}")
        	else:
            		console.print(f"[yellow]⚠ Ollama running but model '{MODEL}' not found[/yellow]")
            		console.print(f"[yellow]  Available: {models}[/yellow]")
    	else:
        	raise Exception(f"HTTP {r.status_code}")
    except Exception as e:
    	console.print(f"[red]✘ Gemma-IR model is NOT reachable: {e}[/red]")
    	console.print("[yellow]  → Run: docker start gemma-ir-brain[/yellow]")
    	all_ok = False

    return all_ok


# ====================== LOGGING ======================
def init_session():
    """Initialize session ID, log file, and report file."""
    global LOG_FILE, REPORT_FILE, SESSION

    os.makedirs(LOGS_DIR, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    SESSION["session_id"]    = ts
    SESSION["session_start"] = datetime.datetime.now().isoformat()

    LOG_FILE    = os.path.join(LOGS_DIR, f"session-{ts}.json")
    REPORT_FILE = os.path.join(LOGS_DIR, f"report-{ts}.md")

    _flush_session()
    console.print(f"[dim]📁 Log: {LOG_FILE}[/dim]")


def _flush_session():
    """Write current session state to disk."""
    with open(LOG_FILE, "w") as f:
        json.dump(SESSION, f, indent=2, default=str)


def log_command(command, result, approved=True):
    """Log a command execution entry."""
    entry = {
        "timestamp":   datetime.datetime.now().isoformat(),
        "command":     command,
        "approved":    approved,
        "exit_code":   result.get("return_code", -1) if approved else None,
        "stdout":      result.get("stdout", "")[:5000] if approved else None,
        "stderr":      result.get("stderr", "")[:2000] if approved else None,
        "success":     result.get("success", False) if approved else False,
        "timed_out":   result.get("timed_out", False) if approved else False,
    }
    SESSION["entries"].append(entry)
    if approved:
        SESSION["commands_run"] += 1
    else:
        SESSION["commands_rejected"] += 1
    _flush_session()
    return entry


def log_conversation(role, content):
    """Log conversation turn."""
    SESSION["conversation"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "role":      role,
        "content":   content
    })
    _flush_session()


# ====================== SESSION REPORT ======================
def generate_report():
    """Generate a Markdown incident response report from the session."""
    SESSION["session_end"] = datetime.datetime.now().isoformat()
    _flush_session()

    start  = datetime.datetime.fromisoformat(SESSION["session_start"])
    end    = datetime.datetime.fromisoformat(SESSION["session_end"])
    duration = str(end - start).split(".")[0]  # trim microseconds

    lines = []
    lines.append("# 🛡️ Incident Response Session Report")
    lines.append("")
    lines.append("## Session Metadata")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Session ID | `{SESSION['session_id']}` |")
    lines.append(f"| Start Time | {SESSION['session_start']} |")
    lines.append(f"| End Time   | {SESSION['session_end']} |")
    lines.append(f"| Duration   | {duration} |")
    lines.append(f"| Model      | `{SESSION['model']}` |")
    lines.append(f"| MCP Server | `{SESSION['kali_mcp']}` |")
    lines.append(f"| Commands Executed | {SESSION['commands_run']} |")
    lines.append(f"| Commands Rejected | {SESSION['commands_rejected']} |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Chain of Custody — Command Execution Log")
    lines.append("")

    approved_entries = [e for e in SESSION["entries"] if e["approved"]]
    if approved_entries:
        for i, entry in enumerate(approved_entries, 1):
            lines.append(f"### Command {i}")
            lines.append(f"- **Timestamp:** `{entry['timestamp']}`")
            lines.append(f"- **Command:** `{entry['command']}`")
            lines.append(f"- **Exit Code:** `{entry['exit_code']}`")
            lines.append(f"- **Success:** `{entry['success']}`")
            if entry.get("timed_out"):
                lines.append(f"- **Note:** Command timed out (partial results)")
            lines.append("")
            if entry.get("stdout"):
                lines.append("**Output:**")
                lines.append("```")
                lines.append(entry["stdout"].strip())
                lines.append("```")
            if entry.get("stderr"):
                lines.append("**Stderr:**")
                lines.append("```")
                lines.append(entry["stderr"].strip())
                lines.append("```")
            lines.append("")
    else:
        lines.append("_No commands were executed in this session._")
        lines.append("")

    rejected_entries = [e for e in SESSION["entries"] if not e["approved"]]
    if rejected_entries:
        lines.append("---")
        lines.append("")
        lines.append("## Rejected Commands")
        lines.append("")
        for entry in rejected_entries:
            lines.append(f"- `{entry['timestamp']}` — `{entry['command']}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Conversation Summary")
    lines.append("")
    for turn in SESSION["conversation"]:
        role    = turn["role"].upper()
        content = turn["content"][:500] + ("..." if len(turn["content"]) > 500 else "")
        lines.append(f"**[{role}]** _{turn['timestamp']}_")
        lines.append(f"> {content}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Report generated automatically by AI-IR Toolkit v4.0*")

    report_text = "\n".join(lines)
    with open(REPORT_FILE, "w") as f:
        f.write(report_text)

    return REPORT_FILE


# ====================== CORE FUNCTIONS ======================
def chat_with_gemma(messages):
    """Send messages to Gemma and return text response."""
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model":    MODEL,
            "messages": messages,
            "stream":   False
        },
        timeout=1000
    )
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "").strip()


def execute_on_kali(command):
    """Send command to MCP server for execution."""
    response = requests.post(
        f"{KALI_MCP_URL}/api/command",
        json={"command": command},
        headers={"Content-Type": "application/json"},
        timeout=10000
    )
    response.raise_for_status()
    return response.json()


def approval_gate(command):
    """Show command to operator and ask for approval."""
    # Block obviously destructive commands
    destructive = ["rm -rf", "dd if=", "mkfs", "> /dev/", "shutdown", "reboot", "halt"]
    for d in destructive:
        if d in command.lower():
            console.print(f"[bold red]🚫 BLOCKED: Destructive pattern detected: '{d}'[/bold red]")
            return False

    console.print(Panel(
        f"[bold yellow]{command}[/bold yellow]",
        title="🔧 Gemma-IR wants to execute",
        border_style="yellow"
    ))
    return Confirm.ask("[bold]Approve this command?[/bold]", default=False)


def extract_command(text):
    """Extract COMMAND: line from Gemma's response."""
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped.upper().startswith("COMMAND:"):
            cmd = stripped[8:].strip()
            # Remove any markdown backticks
            cmd = cmd.strip('`')
            if cmd:
                return cmd
    return None


# ====================== MAIN LOOP ======================
def main():
    console.print(Rule("[bold cyan]AI-IR Toolkit v4.0[/bold cyan]"))
    console.print(Panel(
        "[bold green]Gemma-IR + MCP Kali Server[/bold green]\n"
        "Dockerized • Offline • Chain-of-Custody • Approval Gate • Session Reports\n\n"
        "[dim]Commands: 'exit' or 'quit' to end session and generate report[/dim]",
        title="🚀 STARTING",
        border_style="green"
    ))

    # Service checks
    console.print(Rule("Service Checks"))
    ok = check_services()
    if not ok:
        console.print("\n[bold red]One or more services are down. Fix them and restart.[/bold red]")
        sys.exit(1)

    # Init session
    console.print(Rule("Session Init"))
    init_session()
    console.print(Rule("[green]Ready[/green]"))

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = console.input("\n[bold cyan][You][/bold cyan] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "/bye"]:
                break

            log_conversation("user", user_input)
            messages.append({"role": "user", "content": user_input})

            console.print("[dim]⏳ Thinking...[/dim]")
            gemma_reply = chat_with_gemma(messages)

            console.print(Panel(gemma_reply, title="🧠 Gemma-IR", border_style="blue"))
            messages.append({"role": "assistant", "content": gemma_reply})
            log_conversation("assistant", gemma_reply)

            # Check if Gemma suggested a command
            command = extract_command(gemma_reply)
            if command:
                approved = approval_gate(command)

                if approved:
                    console.print("[bold green]⚡ Executing...[/bold green]")
                    try:
                        result = execute_on_kali(command)
                        entry  = log_command(command, result, approved=True)

                        output = result.get("stdout", "").strip()
                        stderr = result.get("stderr", "").strip()
                        exit_c = result.get("return_code", -1)

                        display_output = output or stderr or "No output returned."

                        console.print(Panel(
                            display_output,
                            title=f"📊 Output [exit code: {exit_c}]",
                            border_style="green" if result.get("success") else "red"
                        ))

                        # Feed result back to Gemma for analysis
                        feedback = (
                            f"Command executed: `{command}`\n"
                            f"Exit code: {exit_c}\n"
                            f"Output:\n{display_output}\n\n"
                            f"Analyze this output. What did you find? What are the next steps?"
                        )
                        messages.append({"role": "user", "content": feedback})
                        log_conversation("user", feedback)

                        if Confirm.ask("[bold]Want Gemma-IR to analyze these results?[/bold]", default=True):
                            console.print("[dim]🔍 Analyzing results...[/dim]")
                            analysis = chat_with_gemma(messages)
                            console.print(Panel(analysis, title="🧠 Gemma-IR Analysis", border_style="cyan"))
                            messages.append({"role": "assistant", "content": analysis})
                            log_conversation("assistant", analysis)

                            next_cmd = extract_command(analysis)
                            if next_cmd:
                                console.print(f"[dim]💡 Gemma suggests a follow-up command above. Respond to continue.[/dim]")
                        else:
                            console.print("[dim]Skipping analysis. Returning to prompt.[/dim]")

                    except Exception as e:
                        console.print(f"[bold red]Execution error: {e}[/bold red]")
                        log_command(command, {"success": False, "error": str(e)}, approved=True)

                else:
                    log_command(command, {}, approved=False)
                    console.print("[red]🚫 Command rejected by operator.[/red]")

                    if Confirm.ask("[bold]Want Gemma-IR to suggest an alternative?[/bold]", default=True):
                        reject_msg = "The operator rejected that command. Please suggest an alternative approach or explain what other options exist."
                        messages.append({"role": "user", "content": reject_msg})
                        log_conversation("user", reject_msg)

                        console.print("[dim]⏳ Thinking of alternatives...[/dim]")
                        alt = chat_with_gemma(messages)
                        console.print(Panel(alt, title="🧠 Gemma-IR Alternative", border_style="blue"))
                        messages.append({"role": "assistant", "content": alt})
                        log_conversation("assistant", alt)
                    else:
                        console.print("[dim]Skipping alternative. Returning to prompt.[/dim]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by operator.[/yellow]")
            break
        except requests.exceptions.ConnectionError as e:
            console.print(f"[bold red]Connection error: {e}[/bold red]")
            console.print("[yellow]Check that MCP server and Ollama are still running.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Unexpected error: {e}[/bold red]")

    # ====================== END OF SESSION ======================
    console.print(Rule("[yellow]Session Ending[/yellow]"))

    if Confirm.ask("[bold]Generate a session report?[/bold]", default=True):
    	console.print("[dim]Generating session report...[/dim]")
    	report_path = generate_report()
    else:
    	SESSION["session_end"] = datetime.datetime.now().isoformat()
    	_flush_session()
    	console.print("[dim]Skipping report generation. Log still saved.[/dim]")
    	report_path = None

    # Print session summary table
    table = Table(title="📋 Session Summary", box=box.ROUNDED, border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")
    table.add_row("Session ID",         SESSION["session_id"])
    table.add_row("Start Time",         SESSION["session_start"])
    table.add_row("End Time",           SESSION["session_end"])
    table.add_row("Commands Executed",  str(SESSION["commands_run"]))
    table.add_row("Commands Rejected",  str(SESSION["commands_rejected"]))
    table.add_row("Report File", REPORT_FILE if report_path else "Not generated")
    table.add_row("Report File",        REPORT_FILE)
    console.print(table)

    console.print(Panel(
        f"[green]✔ Session log:[/green]    {LOG_FILE}\n"
        f"[green]✔ Session report:[/green] {REPORT_FILE}",
        title="✅ Session Complete",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
