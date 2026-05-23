from __future__ import annotations

import os
import platform
import shlex
import subprocess
import webbrowser
from pathlib import Path


READ_ONLY_COMMANDS = {
    "cd",
    "dir",
    "echo",
    "hostname",
    "ipconfig",
    "systeminfo",
    "tree",
    "type",
    "ver",
    "where",
}


def handle_pc_command(payload: str) -> str:
    action, _, rest = payload.strip().partition(" ")
    action = action.lower()
    rest = rest.strip()

    if not action or action in {"help", "?"}:
        return pc_help()
    if action == "system":
        return system_info()
    if action == "open":
        return open_target(rest)
    if action == "web":
        return open_web(rest)
    if action == "run":
        return run_read_only(rest)

    return "Unknown /pc action. Use /pc help."


def pc_help() -> str:
    return """PC commands:
/pc system                 Show basic system info
/pc open PATH_OR_APP        Open a file, folder, or app
/pc web URL                 Open a website
/pc run READ_ONLY_COMMAND   Run a safe read-only command

Allowed /pc run commands:
cd, dir, echo, hostname, ipconfig, systeminfo, tree, type, ver, where
"""


def system_info() -> str:
    return "\n".join(
        [
            f"OS: {platform.platform()}",
            f"Machine: {platform.machine()}",
            f"Processor: {platform.processor() or 'Unknown'}",
            f"Python: {platform.python_version()}",
            f"User: {os.environ.get('USERNAME') or os.environ.get('USER') or 'Unknown'}",
            f"Current folder: {Path.cwd()}",
        ]
    )


def open_target(target: str) -> str:
    if not target:
        return "Use it like this: /pc open C:\\Users\\erimo\\Documents"

    try:
        os.startfile(target)
    except FileNotFoundError:
        return f"I could not find: {target}"
    except OSError as error:
        return f"I could not open that target. Reason: {error}"

    return f"Opened: {target}"


def open_web(url: str) -> str:
    if not url:
        return "Use it like this: /pc web https://github.com"
    if "://" not in url:
        url = f"https://{url}"

    opened = webbrowser.open(url)
    if not opened:
        return f"I could not open the website: {url}"
    return f"Opened website: {url}"


def run_read_only(command_text: str) -> str:
    if not command_text:
        return "Use it like this: /pc run dir"

    try:
        parts = shlex.split(command_text, posix=False)
    except ValueError as error:
        return f"I could not parse that command. Reason: {error}"

    if not parts:
        return "Use it like this: /pc run dir"

    command = Path(parts[0]).name.lower()
    if command.endswith(".exe"):
        command = command[:-4]

    if command not in READ_ONLY_COMMANDS:
        return (
            f"`{parts[0]}` is not approved for /pc run yet. "
            "Use /pc help to see safe commands."
        )

    command_line = subprocess.list2cmdline(parts)

    try:
        completed = subprocess.run(
            ["cmd", "/c", command_line],
            capture_output=True,
            text=True,
            shell=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return "That command took too long, so I stopped waiting."
    except OSError as error:
        return f"I could not run that command. Reason: {error}"

    output = (completed.stdout or completed.stderr or "").strip()
    if not output:
        output = f"Command finished with exit code {completed.returncode}."

    if len(output) > 4000:
        output = output[:4000] + "\n...output truncated..."

    return output
