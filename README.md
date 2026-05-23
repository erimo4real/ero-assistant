# Personal Assistant CLI

This is step 1 of your personal assistant: a local command-line helper that can work offline.
The code is now structured so we can later add desktop, web, mobile, voice, and online tools.

## What it can do now

- Chat with a calm mentor/helper style
- Save local memories
- Track tasks
- Save journal notes
- Save conversation history
- Switch between the built-in offline rules brain and an optional local Ollama model
- Store everything locally in `data/assistant_state.json`

## Run it

Recommended on Windows:

```powershell
.\run.bat
```

PowerShell script option:

```powershell
.\run.ps1
```

If PowerShell blocks `run.ps1`, use `run.bat`. That is normal on some Windows systems.

From Command Prompt:

```cmd
run.bat
```

After activating the virtual environment, you can also run:

```powershell
python personal_assistant.py
```

Activate the virtual environment in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Useful commands

```text
/help
/name Your Name
/assistant-name Brother
/brain rules
/brain ollama
/model qwen2.5:0.5b
/doctor
/remember I want direct and practical advice
/memories
/task Learn Python for 30 minutes
/tasks
/done 1
/journal Today I started building my assistant
/profile
/quit
```

## Growth plan

1. Terminal CLI with local memory and tasks
2. Offline AI model connection with Ollama
3. Online AI/search mode when allowed
4. Background jobs and reminders
5. Voice input/output
6. Desktop app
7. Web app
8. Mobile app

## Connect the offline AI brain

This project is prepared for Ollama, a local AI model runner.

1. Install Ollama from `https://ollama.com/download`
2. Open a terminal and run:

```powershell
ollama pull qwen2.5:0.5b
```

3. Launch the assistant:

```powershell
.\run.bat
```

4. Inside the assistant, run:

```text
/doctor
/brain ollama
/model qwen2.5:0.5b
```

After that, normal chat messages will use the local offline model.

If you prefer the bigger model and `/doctor` shows it as `llama3.2:latest`, use:

```text
/model llama3.2:latest
```

## Project structure

```text
personal_assistant.py   CLI launcher
assistant/core.py       Commands and assistant behavior
assistant/brain.py      Brain providers: rules now, Ollama later
assistant/storage.py    Local JSON storage
data/                   Your private local assistant data
```
