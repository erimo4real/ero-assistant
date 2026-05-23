@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo Virtual environment not found. Creating .venv...
  py -3 -m venv "%PROJECT_ROOT%.venv" 2>nul || python -m venv "%PROJECT_ROOT%.venv"
  "%PYTHON%" -m pip install -r "%PROJECT_ROOT%requirements.txt"
)

"%PYTHON%" "%PROJECT_ROOT%personal_assistant.py"
