import subprocess
import json
import tempfile
import numpy as np
from pathlib import Path

class MontiWhisper:
    def __init__(self, model_path="whisper.cpp/models/ggml-base.en.bin"):
        self.whisper_bin = Path("whisper.cpp/main")
        self.model_path = Path(model_path)
        assert self.whisper_bin.exists(), "Compile whisper.cpp first"
        assert self.model_path.exists(), f"Model not found: {model_path}"

    def detect_language(self, audio_path, initial_prompt=None):
        """Return detected language code (e.g., 'en') using whisper.cpp."""
        cmd = [
            str(self.whisper_bin),
            "-m", str(self.model_path),
            "-f", audio_path,
            "--print-progress", "false",
            "--print-colors", "false",
            "--output-json", "true",
            "--language", "auto",
        ]
        if initial_prompt:
            cmd += ["--prompt", initial_prompt]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # whisper.cpp outputs JSON to stderr? Actually to stdout with --output-json
        try:
            data = json.loads(result.stdout)
            lang = data.get("language", "unknown")
            return lang
        except:
            # fallback: parse stderr for language detection line
            for line in result.stderr.split("\n"):
                if "Detected language" in line:
                    return line.split()[-1]
        return "en"

    def transcribe(self, audio_path, language=None):
        cmd = [
            str(self.whisper_bin),
            "-m", str(self.model_path),
            "-f", audio_path,
            "--output-txt", "true",
            "--output-json", "true",
        ]
        if language:
            cmd += ["-l", language]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return data.get("text", "")

# Example usage (if run directly)
if __name__ == "__main__":
    import sys
    w = MontiWhisper()
    if len(sys.argv) > 1:
        lang = w.detect_language(sys.argv[1])
        print(f"Detected language: {lang}")
        text = w.transcribe(sys.argv[1], language=lang)
        print(f"Transcription: {text}")
