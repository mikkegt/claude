# Speak text with a voice designed in Google AI Studio (Gemini TTS).
#
# The API key comes from $GEMINI_API_KEY, or else from MulmoCast's settings.json.
# It is never printed.
#
# usage:
#   tts.py voices
#   tts.py speak --voice voice_xxx [--style "..."] [--atempo 1.05] --out DIR --text "..."
#   tts.py speak --voice voice_xxx [--style "..."] [--atempo 1.05] --out DIR --texts beats.json [N ...]
#
# beats.json is a JSON array of strings, one per beat. N is a 1-based beat number;
# with no N, every beat is spoken. Output files are DIR/beat-NN.wav.

import argparse
import base64
import json
import os
import subprocess
import sys

from google import genai

MODEL = "gemini-3.8-flash-tts"
MULMOCAST_SETTINGS = os.path.expanduser("~/Library/Application Support/MulmoCast/settings.json")


def load_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    with open(MULMOCAST_SETTINGS) as f:
        return json.load(f)["APIKEY"]["GEMINI_API_KEY"]


def list_voices(client):
    token = None
    while True:
        page = client.voices.list(page_token=token) if token else client.voices.list()
        for v in page.voices:
            if v.type != "prebuilt":
                print(v.id, v.type, v.display_name, v.expire_time, sep="\t")
        token = page.next_page_token
        if not token:
            break


def speak(client, text, voice, style):
    content = {"type": "text", "text": text}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    # Designed voices (voice_...) are only accepted by the Interactions API.
    interaction = client.interactions.create(
        model=MODEL,
        input=[{"type": "user_input", "content": [content]}],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voice}]},
    )
    audio = interaction.output_audio
    if audio.mime_type != "audio/wav":
        sys.exit(f"unexpected audio type: {audio.mime_type}")
    return base64.b64decode(audio.data)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("voices")
    sp = sub.add_parser("speak")
    sp.add_argument("--voice", required=True)
    sp.add_argument("--style")
    sp.add_argument("--out", required=True)
    sp.add_argument("--atempo", type=float, help="speed up with ffmpeg, e.g. 1.05")
    group = sp.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--texts")
    sp.add_argument("beats", nargs="*", type=int)
    args = parser.parse_args()

    client = genai.Client(api_key=load_key())
    if args.command == "voices":
        list_voices(client)
        return

    if args.text is not None:
        jobs = [(1, args.text)]
    else:
        with open(args.texts) as f:
            texts = json.load(f)
        numbers = args.beats or range(1, len(texts) + 1)
        jobs = [(n, texts[n - 1]) for n in numbers]

    os.makedirs(args.out, exist_ok=True)
    for n, text in jobs:
        path = os.path.join(args.out, f"beat-{n:02d}.wav")
        if os.path.exists(path):
            sys.exit(f"already exists, not overwriting: {path}")
        audio = speak(client, text, args.voice, args.style)
        if args.atempo:
            raw = path + ".raw.wav"
            with open(raw, "wb") as f:
                f.write(audio)
            subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-n", "-i", raw, "-filter:a", f"atempo={args.atempo}", path],
                check=True,
            )
            os.remove(raw)
        else:
            with open(path, "wb") as f:
                f.write(audio)
        print(path)


if __name__ == "__main__":
    main()
