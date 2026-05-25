from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools" / "whisper.cpp"
MODELS_DIR = PROJECT_ROOT / "models" / "whisper"
WHISPER_ZIP = PROJECT_ROOT / "tools" / "whisper-bin-x64.zip"
WHISPER_URL = "https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.4/whisper-bin-x64.zip"
MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"
MODEL_PATH = MODELS_DIR / "ggml-small.en.bin"


def main() -> int:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if not (TOOLS_DIR / "whisper-cli.exe").exists():
        download(WHISPER_URL, WHISPER_ZIP)
        with zipfile.ZipFile(WHISPER_ZIP, "r") as archive:
            archive.extractall(TOOLS_DIR)
        WHISPER_ZIP.unlink(missing_ok=True)
        flatten_whisper_folder()
    else:
        print("whisper.cpp binary already installed.")

    if not MODEL_PATH.exists():
        download(MODEL_URL, MODEL_PATH)
    else:
        print("Whisper small.en model already installed.")

    print("Voice setup complete.")
    print(f"Whisper binary: {TOOLS_DIR / 'whisper-cli.exe'}")
    print(f"Model: {MODEL_PATH}")
    return 0


def download(url: str, destination: Path) -> None:
    print(f"Downloading {url}")
    print(f"To {destination}")
    with urllib.request.urlopen(url) as response:
        total = int(response.headers.get("Content-Length", "0"))
        downloaded = 0
        with destination.open("wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)
                downloaded += len(chunk)
                if total:
                    percent = downloaded * 100 / total
                    print(f"\r{downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB ({percent:.1f}%)", end="")
    print()


def flatten_whisper_folder() -> None:
    matches = list(TOOLS_DIR.rglob("whisper-cli.exe"))
    if not matches:
        raise RuntimeError("Downloaded whisper.cpp zip did not contain whisper-cli.exe")

    exe_path = matches[0]
    if exe_path.parent == TOOLS_DIR:
        return

    source_dir = exe_path.parent
    for item in source_dir.iterdir():
        target = TOOLS_DIR / item.name
        if target.exists():
            continue
        shutil.move(str(item), str(target))


if __name__ == "__main__":
    raise SystemExit(main())
