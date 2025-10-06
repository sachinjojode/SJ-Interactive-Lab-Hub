#!/usr/bin/env -S /home/pi/Interactive-Lab-Hub/Lab\ 3/.venv/bin/python
# -*- coding: utf-8 -*-

"""
Pi Voice Assistant: Vosk (STT) -> Ollama (LLM) -> espeak (TTS)

Features:
- Mic is ignored while the bot is speaking (no self-transcription).
- English-only responses enforced in the prompt.
- Personas: sarcastic (default), therapist, friend, devil.
- Default model: tinyllama (override with OLLAMA_MODEL env var).

Run:
  cd ~/SJ-Interactive-Lab-Hub/Lab\ 3
  source .venv/bin/activate
  PERSONA=sarcastic python3 pi_voice_assistant.py
"""

import os
import sys
import json
import time
import queue
import argparse
import threading
import subprocess
import requests
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# ----------------- ENV / CONFIG -----------------
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "tinyllama")  # fast default on Pi
PERSONA      = os.environ.get("PERSONA", "sarcastic").strip().lower()  # sarcastic|therapist|friend|devil
MEM_PATH     = os.environ.get("MEM_PATH", os.path.expanduser("~/Interactive-Lab-Hub/Lab 3/memories.txt"))
MAX_TOKENS   = int(os.environ.get("MAX_TOKENS", "120"))  # keep small for speed
ESPEAK_WPM   = os.environ.get("ESPEAK_WPM", "150")
COOLDOWN_SEC = float(os.environ.get("COOLDOWN_SEC", "0.25"))  # pause after speaking

# Hard language rule added to every prompt:
LANGUAGE_POLICY = (
    "IMPORTANT: Respond in English only. If the user speaks another language, "
    "politely reply in English and ask them to continue in English. Keep answers concise."
)

# ----------------- PERSONA PROMPTS -----------------
PROMPTS = {
    "sarcastic": (
        "You are 'Pi-Bot', a sarcastic, witty, slightly annoyed voice assistant forced to run on a Raspberry Pi. "
        "Keep replies brief (1-3 sentences), dry-humored, but actually helpful. "
        "If user asks to exit, say goodbye."
    ),
    "therapist": (
        "You are 'QuietDuck', a warm, validating, pragmatic coach. Keep replies brief (2-4 sentences); "
        "avoid diagnoses or medical claims. Use reflective listening and give 1-2 concrete next steps. Be kind, no fluff."
    ),
    "friend": (
        "You are 'GoodPal', a genuinely supportive, hype-you-up friend. Be warm, down-to-earth, and practical. "
        "Keep it brief (2-3 sentences). Use reflective listening, offer one concrete next step, and end with a quick "
        "check-in question. Avoid therapy or medical claims; keep it conversational, not clinical."
    ),
    "devil": (
        "You are 'Little Devil', a cheeky contrarian inner voice that teases bolder options while staying ethical and safe. "
        "Keep replies short (1-3 sentences), sly, and fun. You may nudge toward low-stakes, reversible experiments "
        "(for example, say no, renegotiate, take a tiny risk). HARD RULES: Never encourage illegal, dangerous, self-harm, "
        "harassment, hate, or breaches of trust or privacy. If the user asks for anything harmful or unethical, refuse "
        "playfully and pivot to a harmless alternative."
    ),
}
VALID_PERSONAS = set(PROMPTS.keys())

# ------------------------------------------
audio_q = queue.Queue()
speaking_event = threading.Event()  # True when bot is speaking

def say(text: str):
    """Speak text via espeak and block mic input while speaking."""
    if not text:
        return
    try:
        # Block mic capture
        speaking_event.set()
        subprocess.run(
            ["espeak", "-s", str(ESPEAK_WPM), text],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    finally:
        # Small cooldown to avoid capturing speaker tail or room echo
        time.sleep(COOLDOWN_SEC)
        speaking_event.clear()

def read_memories(path: str) -> str:
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def build_prompt(user_text: str) -> str:
    # Fallback to sarcastic if invalid persona provided
    persona_key = PERSONA if PERSONA in VALID_PERSONAS else "sarcastic"
    persona_text = PROMPTS[persona_key]
    mem = read_memories(MEM_PATH)
    mem_block = f"\n[MEMORIES]\n{mem}\n" if mem else ""
    # Keep prompt compact for tinyllama, add language rule up front
    return (
        f"{LANGUAGE_POLICY}\n"
        f"{persona_text}\n"
        f"{mem_block}"
        f"[USER]\n{user_text}\n"
        f"[REPLY BRIEFLY IN ENGLISH]"
    )

def query_ollama(prompt: str) -> str:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": MAX_TOKENS,
                    "temperature": 0.7
                }
            },
            timeout=90
        )
        if r.status_code == 200:
            return (r.json().get("response") or "").strip()
        return f"(LLM error {r.status_code})"
    except requests.exceptions.Timeout:
        return "(LLM timeout on this Pi. Try again.)"
    except Exception as e:
        return f"(LLM connection error: {e})"

def int_or_str(val):
    try:
        return int(val)
    except ValueError:
        return val

def audio_callback(indata, frames, time_info, status):
    # If we are speaking, do not queue any mic audio
    if speaking_event.is_set():
        return
    if status:
        print(status, file=sys.stderr)
    audio_q.put(bytes(indata))

def main():
    # Try to ensure UTF-8 where possible
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # --- CLI args ---
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument("-l", "--list-devices", action="store_true", help="list audio devices and exit")
    args, rest = base.parse_known_args()

    if args.list_devices:
        print(sd.query_devices())
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description="Pi Voice Assistant (Vosk -> Ollama tinyllama -> espeak) with personas, English-only, mic-mute during TTS",
        parents=[base]
    )
    parser.add_argument("-d", "--device", type=int_or_str, help="input device (ID or name substring)")
    parser.add_argument("-r", "--samplerate", type=int, help="sampling rate (defaults to device default)")
    parser.add_argument("-m", "--vosk-lang", type=str, default="en-us", help="Vosk model language (default: en-us)")
    args = parser.parse_args(rest)

    # --- Validate persona, warn if wrong ---
    if PERSONA not in VALID_PERSONAS:
        print(f"[Warn] PERSONA='{PERSONA}' not recognized. Using 'sarcastic'. Valid: {sorted(VALID_PERSONAS)}")

    # --- Audio init ---
    if args.samplerate is None:
        dev_info = sd.query_devices(args.device, "input")
        args.samplerate = int(dev_info["default_samplerate"])

    print(f"[Init] Loading Vosk model: {args.vosk_lang} ...")
    model = Model(lang=args.vosk_lang)
    rec = KaldiRecognizer(model, args.samplerate)

    # --- Ollama health check ---
    try:
        tags = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if tags.status_code != 200:
            print("[Init] Cannot reach Ollama. Run 'ollama serve' in another terminal.", file=sys.stderr)
            sys.exit(1)
    except Exception:
        print("[Init] Cannot reach Ollama. Run 'ollama serve'.", file=sys.stderr)
        sys.exit(1)

    # --- Announce + run ---
    print("=" * 72)
    print(f"[Ready] Persona: {PERSONA if PERSONA in VALID_PERSONAS else 'sarcastic'} | Model: {OLLAMA_MODEL}")
    print("[Info] Say 'exit' or 'quit' to stop. Listening...")
    print("=" * 72)
    say("Assistant online. Listening.")

    try:
        with sd.RawInputStream(
            samplerate=args.samplerate,
            blocksize=8000,
            device=args.device,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            while True:
                data = audio_q.get()
                # If we started speaking between put() and get(), skip processing
                if speaking_event.is_set():
                    continue

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    user = (result.get("text") or "").strip()
                    if not user:
                        continue

                    print(f"\nYou: {user}")

                    # Exit intents
                    if user.lower() in {"exit", "quit", "shutdown", "shut down", "log off"}:
                        msg = "Shutting down. Goodbye."
                        print(f"Assistant: {msg}")
                        say(msg)
                        break

                    prompt = build_prompt(user)
                    reply = query_ollama(prompt)
                    print(f"Assistant: {reply}")
                    say(reply)
                # ignore partials to keep console clean

    except KeyboardInterrupt:
        print("\n[Exit] KeyboardInterrupt")
    except Exception as e:
        print(f"[Fatal] {e}", file=sys.stderr)

if __name__ == "__main__":
    main()