from __future__ import annotations

from datetime import datetime

from assistant.brain import check_ollama, make_brain
from assistant.storage import APP_NAME, AssistantState


class PersonalAssistant:
    def __init__(self) -> None:
        self.state = AssistantState()
        self.state.load()

    @property
    def assistant_name(self) -> str:
        return self.state.data["profile"].get("assistant_name", APP_NAME)

    @property
    def user_name(self) -> str:
        return self.state.data["profile"].get("name", "Boss")

    def greet(self) -> str:
        return (
            f"{self.assistant_name}: I am here, {self.user_name}. "
            "Type /help to see what I can do."
        )

    def handle(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Say something and I will work with it."

        if text.startswith("/"):
            return self.handle_command(text)

        return self.chat(text)

    def chat(self, text: str) -> str:
        brain = make_brain(self.state.data)
        reply = brain.reply(text, self.state.data)
        self.state.data["conversation"].append(
            {"user": text, "assistant": reply, "created_at": timestamp()}
        )
        self.state.save()
        return reply

    def handle_command(self, text: str) -> str:
        command, _, payload = text.partition(" ")
        command = command.lower()
        payload = payload.strip()

        if command in {"/help", "/?"}:
            return help_text()
        if command in {"/quit", "/exit"}:
            raise KeyboardInterrupt
        if command == "/name":
            return self.set_user_name(payload)
        if command == "/assistant-name":
            return self.set_assistant_name(payload)
        if command == "/brain":
            return self.set_brain(payload)
        if command == "/model":
            return self.set_ollama_model(payload)
        if command == "/doctor":
            return self.doctor()
        if command == "/remember":
            return self.remember(payload)
        if command == "/memories":
            return self.list_memories()
        if command == "/forget":
            return self.forget(payload)
        if command == "/task":
            return self.add_task(payload)
        if command == "/tasks":
            return self.list_tasks()
        if command == "/done":
            return self.complete_task(payload)
        if command == "/journal":
            return self.add_journal(payload)
        if command == "/profile":
            return self.profile()

        return f"I do not know `{command}` yet. Type /help."

    def set_user_name(self, name: str) -> str:
        if not name:
            return "Use it like this: /name Your Name"
        self.state.data["profile"]["name"] = name
        self.state.save()
        return f"Good. I will call you {name}."

    def set_assistant_name(self, name: str) -> str:
        if not name:
            return "Use it like this: /assistant-name Name"
        self.state.data["profile"]["assistant_name"] = name
        self.state.save()
        return f"Done. My name is now {name}."

    def set_brain(self, brain: str) -> str:
        if brain not in {"rules", "ollama"}:
            return "Use it like this: /brain rules or /brain ollama"
        self.state.data["settings"]["brain"] = brain
        self.state.save()
        if brain == "ollama":
            return "Offline Ollama brain selected. Make sure Ollama is running locally."
        return "Rules brain selected. This works fully offline with no model installed."

    def set_ollama_model(self, model: str) -> str:
        if not model:
            return "Use it like this: /model llama3.2"
        self.state.data["settings"]["ollama_model"] = model
        self.state.save()
        return f"Ollama model set to {model}."

    def doctor(self) -> str:
        return check_ollama(self.state.data)

    def remember(self, memory: str) -> str:
        if not memory:
            return "Use it like this: /remember I prefer direct advice."
        self.state.data["memories"].append({"text": memory, "created_at": timestamp()})
        self.state.save()
        return "I have saved that in local memory."

    def list_memories(self) -> str:
        memories = self.state.data["memories"]
        if not memories:
            return "No memories saved yet."
        lines = ["Local memories:"]
        lines.extend(f"{index + 1}. {item['text']}" for index, item in enumerate(memories))
        return "\n".join(lines)

    def forget(self, payload: str) -> str:
        if not payload.isdigit():
            return "Use it like this: /forget 2"

        index = int(payload) - 1
        memories = self.state.data["memories"]
        if index < 0 or index >= len(memories):
            return "That memory number does not exist."

        removed = memories.pop(index)
        self.state.save()
        return f"Forgot: {removed['text']}"

    def add_task(self, task: str) -> str:
        if not task:
            return "Use it like this: /task Study Python for 30 minutes"
        self.state.data["tasks"].append(
            {"text": task, "done": False, "created_at": timestamp(), "done_at": None}
        )
        self.state.save()
        return "Task added. I will keep it on the list."

    def list_tasks(self) -> str:
        tasks = self.state.data["tasks"]
        if not tasks:
            return "No tasks yet."
        lines = ["Tasks:"]
        for index, task in enumerate(tasks):
            mark = "x" if task["done"] else " "
            lines.append(f"{index + 1}. [{mark}] {task['text']}")
        return "\n".join(lines)

    def complete_task(self, payload: str) -> str:
        if not payload.isdigit():
            return "Use it like this: /done 1"

        index = int(payload) - 1
        tasks = self.state.data["tasks"]
        if index < 0 or index >= len(tasks):
            return "That task number does not exist."

        tasks[index]["done"] = True
        tasks[index]["done_at"] = timestamp()
        self.state.save()
        return f"Marked done: {tasks[index]['text']}"

    def add_journal(self, entry: str) -> str:
        if not entry:
            return "Use it like this: /journal Today I learned..."
        self.state.data["journal"].append({"text": entry, "created_at": timestamp()})
        self.state.save()
        return "Journal saved."

    def profile(self) -> str:
        profile = self.state.data["profile"]
        settings = self.state.data["settings"]
        return "\n".join(
            [
                f"User: {profile.get('name', 'Boss')}",
                f"Assistant: {profile.get('assistant_name', APP_NAME)}",
                f"Style: {profile.get('style')}",
                f"Brain: {settings.get('brain', 'rules')}",
                f"Ollama model: {settings.get('ollama_model', 'qwen2.5:0.5b')}",
                f"Memories: {len(self.state.data['memories'])}",
                f"Tasks: {len(self.state.data['tasks'])}",
                f"Journal entries: {len(self.state.data['journal'])}",
                f"Conversation turns: {len(self.state.data['conversation'])}",
            ]
        )


def help_text() -> str:
    return """Commands:
/help                 Show this help
/name NAME            Set what I call you
/assistant-name NAME  Rename the assistant
/brain rules          Use built-in offline rules brain
/brain ollama         Use local Ollama offline model
/model MODEL          Set Ollama model name
/doctor               Check local Ollama connection
/remember TEXT        Save a local memory
/memories             Show saved memories
/forget NUMBER        Delete a memory
/task TEXT            Add a task
/tasks                Show tasks
/done NUMBER          Mark a task done
/journal TEXT         Save a journal entry
/profile              Show profile and counts
/quit                 Exit
"""


def timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")
