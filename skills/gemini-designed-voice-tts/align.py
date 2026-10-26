# Pad caption sentences with zero-width spaces so that MulmoCast's
# length-ratio caption timing matches the real speech timing.
#
# usage: align.py <whisper -ojf json> <script.json> <beat index (0-based)> <beat duration sec>
# prints the padded texts array (JSON) on stdout and a timing table on stderr.

import difflib
import json
import sys

ZWSP = "​"
SKIP = set(" \t\n、。，．,.！!？?；;「」")


def split_like_mulmocast(text, delimiters):
    segments, current = [], ""
    for ch in text:
        current += ch
        if ch in delimiters:
            if current.strip():
                segments.append(current.strip())
            current = ""
    if current.strip():
        segments.append(current.strip())
    return segments


def recognized_chars(whisper):
    chars = []  # (char, from_sec, to_sec)
    for seg in whisper["transcription"]:
        for tok in seg["tokens"]:
            if tok["text"].startswith("[_"):
                continue
            for ch in tok["text"]:
                if ch not in SKIP and ch != "�":
                    chars.append((ch.lower(), tok["offsets"]["from"] / 1000, tok["offsets"]["to"] / 1000))
    return chars


def main():
    whisper_path, script_path, index, duration = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
    with open(whisper_path) as f:
        whisper = json.load(f)
    with open(script_path) as f:
        script = json.load(f)
    delimiters = script["captionParams"]["textSplit"]["delimiters"]
    sentences = split_like_mulmocast(script["beats"][index]["text"], delimiters)

    # normalized script chars, remembering which sentence each came from
    s_chars, s_owner = [], []
    for i, sentence in enumerate(sentences):
        for ch in sentence:
            if ch not in SKIP:
                s_chars.append(ch.lower())
                s_owner.append(i)
    r = recognized_chars(whisper)
    matcher = difflib.SequenceMatcher(None, "".join(s_chars), "".join(c for c, _, _ in r), autojunk=False)
    s_to_r = {}
    for a, b, size in matcher.get_matching_blocks():
        for k in range(size):
            s_to_r[a + k] = b + k

    # first and last matched recognized char of each sentence
    starts, ends = [None] * len(sentences), [None] * len(sentences)
    for si, owner in enumerate(s_owner):
        if si in s_to_r:
            ri = s_to_r[si]
            if starts[owner] is None:
                starts[owner] = r[ri][1]
            ends[owner] = r[ri][2]
    if None in starts:
        sys.exit(f"could not place sentences: {[i + 1 for i, s in enumerate(starts) if s is None]}")

    # switch captions halfway through the pause between sentences
    bounds = [0.0] + [(ends[i - 1] + starts[i]) / 2 for i in range(1, len(sentences))] + [duration]
    ratios = [(bounds[i + 1] - bounds[i]) / duration for i in range(len(sentences))]
    scale = max(len(s) / ratio for s, ratio in zip(sentences, ratios))
    padded = [s + ZWSP * (round(scale * ratio) - len(s)) for s, ratio in zip(sentences, ratios)]

    total_old = sum(len(s) for s in sentences)
    total_new = sum(len(p) for p in padded)
    old_at = new_at = 0.0
    print("文  今の表示開始  直した表示開始  話し始め  文", file=sys.stderr)
    for i, s in enumerate(sentences):
        print(f"{i + 1:2d}  {old_at:6.2f}  {new_at:6.2f}  {starts[i]:6.2f}  {s}", file=sys.stderr)
        old_at += duration * len(s) / total_old
        new_at += duration * len(padded[i]) / total_new
    json.dump(padded, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
