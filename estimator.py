from pdf_pipeline import estimate_tts_runtime
from pathlib import Path

text_path = Path("test.txt")
if not text_path.exists():
    raise FileNotFoundError(f"File not found: {text_path}")

content = text_path.read_text(encoding="utf-8")
estimate_tts_runtime(content, wpm=120, gen_ratio=5/3.5)