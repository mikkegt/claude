#!/usr/bin/env python3
"""Gemini TTS (Kore) で テキストファイル → mp3 を生成する。

長文は段落単位でチャンク分割し、各チャンクの PCM を WAV に結合してから
ffmpeg で mp3 に変換する。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

SKILL_DIR = Path(__file__).resolve().parent
ENV_PATH = SKILL_DIR.parent.parent / ".env"
MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Kore"
SAMPLE_RATE = 24000
CHUNK_MAX_CHARS = 1500


def chunk_text(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) + 2 > max_chars and buf:
            chunks.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        chunks.append(buf)
    return chunks


def synthesize(client: genai.Client, text: str) -> bytes:
    resp = client.models.generate_content(
        model=MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
                )
            ),
        ),
    )
    return resp.candidates[0].content.parts[0].inline_data.data


def write_wav(path: Path, pcm_chunks: list[bytes]) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        for pcm in pcm_chunks:
            w.writeframes(pcm)


def wav_to_mp3(
    wav: Path,
    mp3: Path,
    title: str | None = None,
    album: str | None = None,
    artist: str | None = None,
    track: str | None = None,
) -> None:
    mp3.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav)]
    for key, val in (("title", title), ("album", album), ("artist", artist), ("track", track)):
        if val:
            cmd += ["-metadata", f"{key}={val}"]
    cmd += ["-codec:a", "libmp3lame", "-qscale:a", "4", str(mp3)]
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="整形済みテキストファイル")
    ap.add_argument("--output", required=True, type=Path, help="出力mp3パス")
    ap.add_argument("--title", help="ID3 タイトルタグ")
    ap.add_argument("--album", help="ID3 アルバムタグ")
    ap.add_argument("--artist", default="JARVIS", help="ID3 アーティストタグ (デフォルト: JARVIS)")
    ap.add_argument("--track", help="ID3 トラック番号")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 1
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found in PATH", file=sys.stderr)
        return 1

    load_dotenv(ENV_PATH)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"GEMINI_API_KEY not set (checked {ENV_PATH})", file=sys.stderr)
        return 1

    text = args.input.read_text(encoding="utf-8").strip()
    chunks = chunk_text(text)
    print(f"chunks={len(chunks)} chars={len(text)}")

    client = genai.Client(api_key=api_key)
    pcm_chunks: list[bytes] = []
    for i, c in enumerate(chunks, 1):
        print(f"  [{i}/{len(chunks)}] {len(c)} chars ...")
        pcm_chunks.append(synthesize(client, c))

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = Path(tmp.name)
    try:
        write_wav(wav_path, pcm_chunks)
        wav_to_mp3(
            wav_path, args.output,
            title=args.title, album=args.album,
            artist=args.artist, track=args.track,
        )
    finally:
        wav_path.unlink(missing_ok=True)

    size_kb = args.output.stat().st_size / 1024
    print(f"saved: {args.output} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
