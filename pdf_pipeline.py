from __future__ import annotations



import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Sequence
import time
import logging
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union
from tts import chatterbox_tts
# --- PDF TEXT EXTRACTION ------------------------------------------------------

def _import_pypdf_reader():
    """
    Try importing a PDF reader from pypdf (preferred) or PyPDF2 (fallback).
    Returns: (PdfReader, ImportError|None)
    """
    try:
        from pypdf import PdfReader  # type: ignore
        return PdfReader, None
    except Exception as e1:
        try:
            from PyPDF2 import PdfReader  # type: ignore
            return PdfReader, None
        except Exception as e2:
            return None, ImportError(
                "Neither 'pypdf' nor 'PyPDF2' is installed. "
                "Install one: pip install pypdf   (or)   pip install PyPDF2"
            )

def parse_pages_spec(pages: Optional[Union[str, Sequence[int]]], total_pages: Optional[int] = None) -> List[int]:
    """
    Parse pages specification into 0-based page indices.

    Accepts:
      - None (means all pages if total_pages is provided)
      - "1,3-5,8"  (human 1-based ranges)
      - [1, 3, 4, 5] (human 1-based list)

    Returns 0-based sorted unique indices.
    """
    if pages is None:
        if total_pages is None:
            raise ValueError("total_pages must be provided when pages=None.")
        return list(range(total_pages))

    if isinstance(pages, (list, tuple)):
        idxs = set(int(p) - 1 for p in pages)
        return sorted(i for i in idxs if i >= 0 and (total_pages is None or i < total_pages))

    # string like "1,3-5,8"
    pages = pages.strip()
    if not pages:
        raise ValueError("Empty pages spec.")
    idxs = set()
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a)
            end = int(b)
            if start > end:
                start, end = end, start
            for p in range(start, end + 1):
                idxs.add(p - 1)
        else:
            idxs.add(int(part) - 1)
    return sorted(i for i in idxs if i >= 0 and (total_pages is None or i < total_pages))

def pdf_to_string(
    pdf_path: Union[str, Path],
    pages: Optional[Union[str, Sequence[int]]] = None,
    save: bool = False,
    out_txt_path: Optional[Union[str, Path]] = None,
    normalize_whitespace: bool = True,
    dehyphenate: bool = True,
) -> str:
    """
    Extract text from specific pages of a PDF into a single string.

    Args:
        pdf_path: path to PDF.
        pages: None for all; or "1,3-5"; or list of human 1-based page numbers.
        save: if True, save the resulting string to a .txt file.
        out_txt_path: where to save if save=True. Defaults to <pdf_basename>.txt.
        normalize_whitespace: collapse excessive whitespace.
        dehyphenate: join words split across line breaks with hyphens.

    Returns:
        Extracted text (str).
    """
    PdfReader, err = _import_pypdf_reader()
    if err:
        raise err

    pdf_path = Path(pdf_path)
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)

    page_indices = parse_pages_spec(pages, total_pages=total)  # 0-based

    chunks: List[str] = []
    for i in page_indices:
        text = reader.pages[i].extract_text() or ""
        chunks.append(text)

    text = "\n".join(chunks)

    if dehyphenate:
        # join hyphenated line breaks: e.g., "inter-\nnational" -> "international"
        text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Normalize Windows-style line breaks first
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if normalize_whitespace:
        # Remove trailing spaces on lines, collapse multiple blank lines
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse excessive internal spaces
        text = re.sub(r"[ \t]{2,}", " ", text)

    if save:
        out_txt_path = Path(out_txt_path) if out_txt_path else pdf_path.with_suffix(".txt")
        Path(out_txt_path).write_text(text, encoding="utf-8")

    return text



# ------------------ 1) Sentence splitter ------------------

# Improved sentence splitter: URL-safe + whitespace normalization
_ABBREV = r"(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|e\.g|i\.e|Hon|Ltd|Inc|Co|U\.S|U\.K)"
_TERMINATOR = r"[.!?]"

def split_into_sentences(text: str, min_len: int = 2) -> List[str]:
    """
    URL-safe, lightweight splitter.
    - Protects URLs so domain dots don't split sentences
    - Handles common abbreviations
    - Normalizes tabs/extra spaces, keeps paragraph breaks (double newlines)
    """
    # Normalize newlines and collapse tabs/spaces (but preserve double newlines as paragraph breaks)
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)            # collapse runs of spaces/tabs
    t = re.sub(r"\n{3,}", "\n\n", t)         # cap blank lines at 2

    # Protect URLs and abbreviations by replacing dots with a sentinel
    def protect_dots(s: str) -> str:
        # Protect URLs: http(s)://... or www....
        def _url_sub(m):
            return m.group(0).replace(".", "§")
        s = re.sub(r"(https?://\S+|www\.\S+)", _url_sub, s)
        # Protect abbrev trailing dots
        s = re.sub(rf"\b{_ABBREV}\.", lambda m: m.group(0).replace(".", "§"), s)
        return s

    def restore_dots(s: str) -> str:
        return s.replace("§", ".")

    protected = protect_dots(t)

    # Split on sentence terminators followed by whitespace + (optional quote/bracket) + capital/number
    parts = re.split(rf"({_TERMINATOR})(?=\s+['\"(\[]?[A-Z0-9])", protected)

    candidates: List[str] = []
    for i in range(0, len(parts), 2):
        base = parts[i]
        term = parts[i + 1] if i + 1 < len(parts) else ""
        s = restore_dots((base + term)).strip()
        if len(s) >= min_len:
            candidates.append(s)

    # Further split on paragraph breaks while keeping content intact
    sentences: List[str] = []
    for seg in candidates:
        sentences.extend([p.strip() for p in re.split(r"\n{2,}", seg) if p.strip()])

    return sentences


# ------------------ 2) WAV -> OPUS ------------------

def _ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH. Install it first.")

def wavs_to_opus(
    wav_paths: Sequence[Path | str],
    out_dir: Path | str,
    bitrate: str = "96k",
    sr: int = 48000,
    channels: int = 1,
) -> List[Path]:
    """
    Convert a list of WAV files to OPUS (Ogg container) with identical params.
    Returns list of output .opus paths in the same order as wav_paths.
    """
    _ensure_ffmpeg()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    opus_paths: List[Path] = []
    for in_path in map(Path, wav_paths):
        out_path = out_dir / (in_path.stem + ".opus")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(in_path),
            "-c:a", "libopus",
            "-b:a", str(bitrate),
            "-ar", str(sr),
            "-ac", str(channels),
            str(out_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        opus_paths.append(out_path)
    return opus_paths

# ------------------ 3) Concatenate OPUS ------------------

def concat_opus(opus_paths: Sequence[Path | str], output_path: Path | str) -> Path:
    """
    Concatenate OPUS (Ogg) files into a single .opus without re-encoding.
    All inputs MUST have identical codec params (we ensure that in wavs_to_opus).
    """
    _ensure_ffmpeg()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg concat demuxer needs a file list
    filelist = output_path.with_suffix(".txt")
    with filelist.open("w", encoding="utf-8") as f:
        for p in map(Path, opus_paths):
            f.write(f"file '{p.as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(filelist),
        "-c", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        filelist.unlink()
    except Exception:
        pass
    return output_path

# ------------------ 4) One-shot pipeline using YOUR chatterbox_tts ------------------

def tts_text_to_single_opus(
    text: str,
    out_dir: Path | str,
    chatterbox_tts,  # <-- your function exactly as provided
    voice_sample_path: str,
    chapter_name: str = "chapter",
    from_voice: bool = False,
    cfg_weight: float = 0.5,
    exaggeration: float = 0.5,
    sentence_min_len: int = 2,
    bitrate: str = "96k",
    sr: int = 48000,
    channels: int = 1,
) -> Path:
    """
    Splits text into sentences -> calls your chatterbox_tts per sentence to produce WAVs ->
    converts all WAVs to OPUS -> concatenates into one <chapter_name>.opus file.

    Returns the final .opus path.
    """
    out_dir = Path(out_dir)
    wav_dir = out_dir / "wav"
    opus_dir = out_dir / "opus"
    wav_dir.mkdir(parents=True, exist_ok=True)
    opus_dir.mkdir(parents=True, exist_ok=True)

    sentences = split_into_sentences(text, min_len=sentence_min_len)

    wav_dir = Path("C:/Users/Ruslan/Downloads/corporate finance/chapter_audio/wav")  # change to your actual wav folder
    wav_paths: List[Path] = []
    for i, sent in enumerate(sentences, start=420):
        out_wav = wav_dir / f"{chapter_name}_{i:05d}.wav"
        # call YOUR function
        chatterbox_tts(
            text=sent,
            output_path=str(out_wav),
            voice_sample_path=voice_sample_path,
            from_voice=from_voice,
            cfg_weight=cfg_weight,
            exaggeration=exaggeration,
        )
        wav_paths.append(out_wav)

    opus_paths = wavs_to_opus(wav_paths, out_dir=opus_dir, bitrate=bitrate, sr=sr, channels=channels)
    final_path = out_dir / f"{chapter_name}.opus"
    return concat_opus(opus_paths, final_path)

import re

def estimate_tts_runtime(text: str, wpm: int = 120, gen_ratio: float = 5/3.5) -> float:
    """
    Estimate wall-clock runtime for generating TTS locally.

    Args:
        text: The full text you plan to synthesize.
        wpm: Assumed speaking rate in words per minute (default 120).
        gen_ratio: Generation-time multiplier relative to audio length.
                   Example: 3.5 min audio takes 5 min => gen_ratio = 5 / 3.5.

    Returns:
        Estimated wall-clock time in minutes (also prints a summary).
    """
    words = re.findall(r"[A-Za-z0-9']+", text)
    n_words = len(words)

    audio_minutes = n_words / max(int(wpm), 1)
    runtime_minutes = audio_minutes * float(gen_ratio)

    print(f"[TTS Runtime Estimate]")
    print(f"  Words: {n_words}")
    print(f"  Assumed speech rate: {wpm} wpm")
    print(f"  Estimated audio length: {audio_minutes:.2f} min")
    print(f"  Generation ratio (real/audio): {gen_ratio:.4f}x")
    print(f"  Estimated wall-clock time: {runtime_minutes:.2f} min")

    return runtime_minutes



if __name__ == "__main__":
    # Your existing variables
    dir = "C:/Users/Ruslan/Downloads/corporate finance/"
    pdf_path = dir + "Fundamentals of Corporate Finance ( PDFDrive.com ).pdf"
    voice_path = dir + "Audiobook voice sample.wav"
    pages = "1532-1581"  # can also be list like [1532, 1533, ...]
    chapter_name = "chapter_corp_fin"
    out_dir = Path(dir) / "chapter_audio"

    # 1. Extract text from the specified pages
    text = pdf_to_string(pdf_path, pages=pages, save=True, out_txt_path="test.txt")
    text_path = Path("test1.txt")
    content = text_path.read_text(encoding="utf-8")
    print(content[:100])
    # 2. Generate the OPUS audiobook for the chapter
    final_opus = tts_text_to_single_opus(
        text=content,
        out_dir=Path(dir) / "chapter_audio",
        chatterbox_tts=chatterbox_tts,      # <-- your existing function
        voice_sample_path=voice_path,
        chapter_name="chapter_corp_fin",
        from_voice=True,                    
        cfg_weight=0.5,
        exaggeration=0.5,
        sentence_min_len=2,
        bitrate="96k",
        sr=48000,
        channels=1
    )

    print(f"Audiobook chapter saved to: {final_opus}")
