from __future__ import annotations

import base64
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Callable

import numpy as np
import sounddevice as sd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WHISPER_EXE = PROJECT_ROOT / "tools" / "whisper.cpp" / "whisper-cli.exe"
WHISPER_MODEL = PROJECT_ROOT / "models" / "whisper" / "ggml-small.en.bin"
SAMPLE_RATE = 16000


class VoiceSetupError(RuntimeError):
    pass


def run_voice_loop(respond: Callable[[str], str]) -> str:
    ensure_voice_ready()
    print("Voice mode ready. Press Enter to start recording, Enter again to stop, or type q to quit.")

    while True:
        command = input("voice> ")
        if command.strip().lower() in {"q", "quit", "exit"}:
            return "Voice mode closed."

        audio_path = record_push_to_talk()
        text = transcribe(audio_path)
        if not text:
            print("I did not catch anything. Try again.")
            continue

        print(f"You said: {text}")
        reply = respond(text)
        print(reply)
        speak(reply)


def ensure_voice_ready() -> None:
    missing = []
    if not WHISPER_EXE.exists():
        missing.append(str(WHISPER_EXE))
    if not WHISPER_MODEL.exists():
        missing.append(str(WHISPER_MODEL))
    if missing:
        raise VoiceSetupError(
            "Voice setup is incomplete. Run this first:\n"
            ".\\.venv\\Scripts\\python.exe scripts\\setup_voice.py\n\n"
            "Missing:\n- " + "\n- ".join(missing)
        )


def record_push_to_talk() -> Path:
    frames: list[np.ndarray] = []

    def callback(indata, _frames, _time, status) -> None:
        if status:
            print(f"Audio status: {status}")
        frames.append(indata.copy())

    print("Recording... press Enter to stop.")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback):
        input()

    if not frames:
        raise VoiceSetupError("No microphone audio was recorded.")

    audio = np.concatenate(frames, axis=0)
    output_dir = PROJECT_ROOT / "recordings"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "voice-command.wav"

    with wave.open(str(output_path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(audio.tobytes())

    return output_path


def transcribe(audio_path: Path) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_prefix = Path(temp_dir) / "transcript"
        command = [
            str(WHISPER_EXE),
            "-m",
            str(WHISPER_MODEL),
            "-f",
            str(audio_path),
            "-nt",
            "-otxt",
            "-of",
            str(output_prefix),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
        if completed.returncode != 0:
            raise VoiceSetupError(
                "Whisper transcription failed.\n"
                f"{completed.stderr or completed.stdout}"
            )

        transcript_path = output_prefix.with_suffix(".txt")
        if not transcript_path.exists():
            return ""
        return transcript_path.read_text(encoding="utf-8").strip()


def speak(text: str) -> None:
    if not text.strip():
        return

    text_payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
    script = (
        "Add-Type -AssemblyName System.Speech; "
        f"$bytes = [Convert]::FromBase64String('{text_payload}'); "
        "$text = [Text.Encoding]::UTF8.GetString($bytes); "
        "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$speaker.Rate = 0; "
        "$speaker.Speak($text);"
    )
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    subprocess.run(
        ["powershell", "-NoProfile", "-EncodedCommand", encoded],
        capture_output=True,
        text=True,
        timeout=120,
    )
