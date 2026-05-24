from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any


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

APP_PRESETS = {
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "cmd": "cmd.exe",
    "explorer": "explorer.exe",
    "notepad": "notepad.exe",
    "powershell": "powershell.exe",
    "pwsh": "powershell.exe",
}

SKIP_SEARCH_DIRS = {".git", ".venv", "__pycache__", "node_modules"}


def handle_pc_command(payload: str, state: dict[str, Any]) -> str:
    action, _, rest = payload.strip().partition(" ")
    action = action.lower()
    rest = rest.strip()

    if not action or action in {"help", "?"}:
        return pc_help()
    if action == "system":
        return system_info()
    if action == "open":
        return open_target(rest)
    if action == "app":
        return open_app(rest)
    if action == "web":
        return open_web(rest)
    if action == "search":
        return search_files(rest)
    if action == "run":
        return run_read_only(rest)
    if action == "pending":
        return describe_pending(state.get("pending_action"))
    if action == "mkdir":
        return queue_mkdir(rest, state)
    if action == "copy":
        return queue_file_action("copy", rest, state)
    if action == "move":
        return queue_file_action("move", rest, state)

    return "Unknown /pc action. Use /pc help."


def pc_help() -> str:
    return """PC commands:
/pc system                 Show basic system info
/pc open PATH_OR_APP        Open a file, folder, or app
/pc app NAME                Open an approved app preset
/pc web URL                 Open a website
/pc search ROOT PATTERN     Search files by name
/pc run READ_ONLY_COMMAND   Run a safe read-only command
/pc mkdir PATH              Prepare to create a folder
/pc copy SOURCE DEST        Prepare to copy a file or folder
/pc move SOURCE DEST        Prepare to move a file or folder
/pc pending                 Show pending action
/yes                        Approve pending action
/no                         Cancel pending action

Allowed /pc run commands:
cd, dir, echo, hostname, ipconfig, systeminfo, tree, type, ver, where

App presets:
calc, calculator, cmd, explorer, notepad, powershell, pwsh
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


def open_app(app_name: str) -> str:
    if not app_name:
        return "Use it like this: /pc app notepad"

    key = app_name.strip().lower()
    command = APP_PRESETS.get(key)
    if not command:
        presets = ", ".join(sorted(APP_PRESETS))
        return f"Unknown app preset: {app_name}. Available presets: {presets}"

    try:
        subprocess.Popen([command], shell=False)
    except OSError as error:
        return f"I could not open {app_name}. Reason: {error}"

    return f"Opened app: {app_name}"


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


def search_files(payload: str) -> str:
    try:
        parts = shlex.split(payload, posix=False)
    except ValueError as error:
        return f"I could not parse the search. Reason: {error}"

    if len(parts) != 2:
        return "Use it like this: /pc search ROOT PATTERN"

    root = Path(parts[0]).expanduser()
    pattern = parts[1]
    if not root.exists():
        return f"I could not find the root folder: {root}"
    if not root.is_dir():
        return f"Search root is not a folder: {root}"

    matches: list[str] = []
    try:
        for path in search_paths(root, pattern):
            matches.append(str(path))
            if len(matches) >= 25:
                break
    except OSError as error:
        return f"I could not complete the search. Reason: {error}"

    if not matches:
        return f"No files found for pattern `{pattern}` under {root}."

    lines = [f"Found {len(matches)} result(s). Showing up to 25:"]
    lines.extend(f"{index + 1}. {match}" for index, match in enumerate(matches))
    return "\n".join(lines)


def search_paths(root: Path, pattern: str):
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [directory for directory in dirs if directory not in SKIP_SEARCH_DIRS]
        current_path = Path(current_root)
        for filename in files:
            path = current_path / filename
            if path.match(pattern):
                yield path


def queue_mkdir(path_text: str, state: dict[str, Any]) -> str:
    if not path_text:
        return "Use it like this: /pc mkdir C:\\Users\\erimo\\Documents\\NewFolder"

    target = str(Path(path_text).expanduser())
    state["pending_action"] = {
        "type": "mkdir",
        "target": target,
    }
    return confirmation_message(
        "Create folder",
        [f"Target: {target}"],
    )


def queue_file_action(action: str, payload: str, state: dict[str, Any]) -> str:
    try:
        parts = shlex.split(payload, posix=False)
    except ValueError as error:
        return f"I could not parse the paths. Reason: {error}"

    if len(parts) != 2:
        return f"Use it like this: /pc {action} SOURCE DEST"

    source = str(Path(parts[0]).expanduser())
    destination = str(Path(parts[1]).expanduser())
    if not Path(source).exists():
        return f"I could not find the source: {source}"

    state["pending_action"] = {
        "type": action,
        "source": source,
        "destination": destination,
    }
    return confirmation_message(
        f"{action.title()} file/folder",
        [f"Source: {source}", f"Destination: {destination}"],
    )


def confirmation_message(title: str, lines: list[str]) -> str:
    details = "\n".join(lines)
    return (
        f"Pending PC action: {title}\n"
        f"{details}\n"
        "Type /yes to approve, or /no to cancel."
    )


def describe_pending(action: dict[str, Any] | None) -> str:
    if not action:
        return "No pending PC action."
    action_type = action.get("type")
    if action_type == "mkdir":
        return confirmation_message("Create folder", [f"Target: {action.get('target')}"])
    if action_type in {"copy", "move"}:
        return confirmation_message(
            f"{action_type.title()} file/folder",
            [
                f"Source: {action.get('source')}",
                f"Destination: {action.get('destination')}",
            ],
        )
    return "There is a pending action, but I do not know how to describe it."


def execute_pending(state: dict[str, Any]) -> str:
    action = state.get("pending_action")
    if not action:
        return "No pending PC action to approve."

    try:
        result = execute_action(action)
    except OSError as error:
        result = f"I could not complete the action. Reason: {error}"
    finally:
        state["pending_action"] = None

    return result


def cancel_pending(state: dict[str, Any]) -> str:
    if not state.get("pending_action"):
        return "No pending PC action to cancel."
    state["pending_action"] = None
    return "Pending PC action cancelled."


def execute_action(action: dict[str, Any]) -> str:
    action_type = action.get("type")

    if action_type == "mkdir":
        target = Path(action["target"])
        target.mkdir(parents=True, exist_ok=True)
        return f"Created folder: {target}"

    if action_type in {"copy", "move"}:
        source = Path(action["source"])
        destination = Path(action["destination"])
        if not source.exists():
            return f"I could not find the source: {source}"
        if destination.exists():
            return f"Destination already exists, so I stopped: {destination}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if action_type == "copy":
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            return f"Copied: {source} -> {destination}"
        shutil.move(str(source), str(destination))
        return f"Moved: {source} -> {destination}"

    return "I do not know how to execute that pending action."
