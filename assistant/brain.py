from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any


class Brain:
    def reply(self, text: str, state: dict[str, Any]) -> str:
        raise NotImplementedError


class RulesBrain(Brain):
    def reply(self, text: str, state: dict[str, Any]) -> str:
        lower = text.lower()

        if any(word in lower for word in ["sad", "tired", "stressed", "confused"]):
            return (
                "I hear you. First, slow down and breathe. "
                "Tell me the one thing pressing you most right now, and we will break it into a small next step."
            )

        if any(word in lower for word in ["learn", "study", "teach"]):
            return (
                "Good. We will learn it step by step: first understand the idea, "
                "then practice one small example, then build something real with it."
            )

        if any(word in lower for word in ["plan", "goal", "project"]):
            return (
                "Let us make it concrete. What is the outcome, the deadline, "
                "and the smallest action you can take today?"
            )

        memory_hint = memory_summary(state)
        if memory_hint:
            return (
                f"I am with you. I also remember: {memory_hint}. "
                "Tell me the outcome you want, and I will help you shape the next step."
            )

        return (
            "I am with you. For this first version I can remember things, track tasks, "
            "save journal notes, and help you think through your next step. "
            "Use /remember, /task, or just keep talking."
        )


class OllamaBrain(Brain):
    def reply(self, text: str, state: dict[str, Any]) -> str:
        settings = state.get("settings", {})
        url = settings.get("ollama_url", "http://localhost:11434/api/generate")
        model = settings.get("ollama_model", "qwen2.5:0.5b")
        timeout = int(settings.get("ollama_timeout_seconds", 180))
        prompt = build_prompt(text, state)
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            return (
                "I tried to use the offline Ollama brain, but I could not reach it. "
                f"Reason: {error}. Use /brain rules for now, or start Ollama."
            )
        except socket.timeout:
            return (
                "The offline model is taking too long to answer. "
                "It may still be loading into memory. Try the same message again, or use /brain rules."
            )

        return data.get("response", "").strip() or "The offline brain returned an empty answer."


def make_brain(state: dict[str, Any]) -> Brain:
    if state.get("settings", {}).get("brain") == "ollama":
        return OllamaBrain()
    return RulesBrain()


def check_ollama(state: dict[str, Any]) -> str:
    settings = state.get("settings", {})
    generate_url = settings.get("ollama_url", "http://localhost:11434/api/generate")
    tags_url = generate_url.replace("/api/generate", "/api/tags")

    try:
        with urllib.request.urlopen(tags_url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        return (
            "Ollama is not reachable yet.\n"
            f"URL checked: {tags_url}\n"
            f"Reason: {error}\n"
            "Start Ollama, then run: /doctor"
        )

    models = [model.get("name", "") for model in data.get("models", [])]
    if not models:
        return (
            "Ollama is running, but no models are installed yet.\n"
            "Install one with: ollama pull llama3.2"
        )

    selected = settings.get("ollama_model", "qwen2.5:0.5b")
    model_lines = "\n".join(f"- {model}" for model in models)
    if selected not in models:
        selected_latest = f"{selected}:latest"
        if selected_latest in models:
            state["settings"]["ollama_model"] = selected_latest
            selected = selected_latest
        else:
            return (
                "Ollama is running.\n"
                f"Selected model: {selected}\n"
                f"Installed models:\n{model_lines}\n"
                "Use /model MODEL_NAME to choose one of the installed models."
            )

    return (
        "Ollama is connected and ready.\n"
        f"Selected model: {selected}\n"
        f"Installed models:\n{model_lines}"
    )


def build_prompt(text: str, state: dict[str, Any]) -> str:
    profile = state.get("profile", {})
    memories = "\n".join(f"- {item['text']}" for item in state.get("memories", [])[-8:])
    tasks = "\n".join(
        f"- [{'x' if task.get('done') else ' '}] {task['text']}"
        for task in state.get("tasks", [])[-8:]
    )
    return f"""You are {profile.get('assistant_name', 'Brother')}, a personal assistant.
Style: {profile.get('style')}
User name: {profile.get('name', 'Boss')}

Known memories:
{memories or '- none'}

Recent tasks:
{tasks or '- none'}

User said:
{text}

Reply like a practical mentor and helper. Be direct, warm, and step by step.
"""


def memory_summary(state: dict[str, Any]) -> str:
    memories = state.get("memories", [])
    if not memories:
        return ""
    return "; ".join(item["text"] for item in memories[-2:])
