#!/usr/bin/env python3
"""Generate EN TTS using qwen3tts API - WAV chunk method with local ffmpeg"""
import os
import re
import sys
import json
import requests
import subprocess
import tempfile

TTS_URL = "http://192.168.0.151:9000/synthesize"
PROJECT_DIR = "/home/jsong/dev/jsong1230-github/booksummary"

# Try to find ffmpeg
FFMPEG_PATHS = [
    "/usr/bin/ffmpeg",
    "/usr/local/bin/ffmpeg",
]
FFMPEG = None
for p in FFMPEG_PATHS:
    if os.path.exists(p):
        FFMPEG = p
        break
if not FFMPEG:
    # Try which
    try:
        FFMPEG = subprocess.check_output(["which", "ffmpeg"]).decode().strip()
    except:
        pass

if not FFMPEG:
    print("ERROR: ffmpeg not found!")
    sys.exit(1)
print(f"Using ffmpeg: {FFMPEG}")

BOOKS = [
    {
        "summary": "Mindset_summary_en.md",
        "output": "Mindset_longform_en.mp3",
    },
    {
        "summary": "Outlive_summary_en.md",
        "output": "Outlive_longform_en.mp3",
    },
    {
        "summary": "Lessons_in_Chemistry_summary_en.md",
        "output": "Lessons_in_Chemistry_longform_en.mp3",
    },
    {
        "summary": "Same_as_Ever_summary_en.md",
        "output": "Same_as_Ever_longform_en.mp3",
    },
]

def chunk_text(text, max_chars=800):
    """Split text into chunks at sentence boundaries"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) + 1 <= max_chars:
            current = current + " " + sent if current else sent
        else:
            if current:
                chunks.append(current.strip())
            current = sent
    if current:
        chunks.append(current.strip())
    return chunks

def synthesize_book(book):
    summary_path = os.path.join(PROJECT_DIR, "assets/summaries", book["summary"])
    output_path = os.path.join(PROJECT_DIR, "assets/audio", book["output"])

    print(f"\n=== Processing {book['summary']} ===")

    with open(summary_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Clean text
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'\[HOOK[^\]]*\]|\[BODY[^\]]*\]|\[BRIDGE[^\]]*\]', '', text)
    text = text.strip()

    chunks = chunk_text(text)
    print(f"Chunks: {len(chunks)}")

    wav_files = []
    tmpdir = tempfile.mkdtemp()

    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)}: {len(chunk)} chars", end="\r")
        resp = requests.post(TTS_URL, json={
            "text": chunk,
            "model": "qwen3tts",
            "voice": "default",
            "speed": 1.0
        }, timeout=300)
        resp.raise_for_status()

        wav_path = os.path.join(tmpdir, f"chunk_{i:03d}.wav")
        with open(wav_path, 'wb') as f:
            f.write(resp.content)
        wav_files.append(wav_path)

    print(f"\n  Concatenating {len(wav_files)} WAV files...")
    list_file = os.path.join(tmpdir, "list.txt")
    with open(list_file, 'w') as f:
        for w in wav_files:
            f.write(f"file '{w}'\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run([
        FFMPEG, '-y', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-ab', '192k', output_path
    ], check=True, capture_output=True)

    # Cleanup
    for w in wav_files:
        os.remove(w)
    os.remove(list_file)
    os.rmdir(tmpdir)

    size = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Saved: {output_path} ({size:.1f}MB)")

for book in BOOKS:
    output_path = os.path.join(PROJECT_DIR, "assets/audio", book["output"])
    if os.path.exists(output_path):
        size = os.path.getsize(output_path) / 1024 / 1024
        print(f"Skipping {book['output']} (already exists, {size:.1f}MB)")
        continue
    synthesize_book(book)

print("\n=== All EN TTS done ===")
