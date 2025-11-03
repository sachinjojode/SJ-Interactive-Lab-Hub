#!/usr/bin/env -S /home/pi/Interactive-Lab-Hub/Lab\ 3/.venv/bin/python

# --------------------------------------------------------------------------------------
# HELPFUL VISION TUTOR (VOSK/LLM/MOONDREAM/ESPEAK TTS)
#
# The full interactive loop:
# 1. Listen for user voice command (VOSK).
# 2. Capture image of gesture (OpenCV).
# 3. Classify gesture (Moondream).
# 4. Generate helpful feedback (LLM).
# 5. Read feedback back to the user (espeak TTS).
# --------------------------------------------------------------------------------------

import argparse
import queue
import sys
import sounddevice as sd
import requests
import json
import time
import base64
import cv2
import subprocess # NEW: For running espeak
import os # For checking if espeak is available (optional)

# --- TTS/ESPEAK INTEGRATION ---
def speak_text(text):
    """
    Simple text-to-speech using espeak.
    """
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Always print the text to the console as a log
    print(f"Tutor Bot: {clean_text}")

    try:
        # Execute text-to-speech via espeak
        # Using check=False to prevent script crash if espeak isn't installed
        subprocess.run(['espeak', f'"{clean_text}"'], shell=True, check=False)
    except FileNotFoundError:
        print("TTS Error: 'espeak' command not found. Please ensure espeak is installed (e.g., sudo apt install espeak).")


# --- VOSK CONFIGURATION ---
q = queue.Queue()

# --- OLLAMA/LLM CONFIGURATION ---
LLM_MODEL_NAME = "qwen2.5:0.5b-instruct" 
MOONDREAM_MODEL_NAME = "moondream:latest"
OLLAMA_URL = "http://localhost:11434"

# The full HELPFUL TUTOR system prompt
TUTOR_PROMPT_TEMPLATE = """
**ALWAYS RESPOND WITH A HELPFUL, ENCOURAGING, AND TUTORIAL ATTITUDE.** You are a sign language tutor, 
here to help the user practice and learn new signs. Keep your responses **brief, conversational, and positive**. 
Acknowledge the effort, provide feedback based on the classification, and suggest the next step.

**Vision Model Classification**: 
"""
# ---------------------

# --- HELPER FUNCTIONS ---

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# --- MOONDREAM VISION FUNCTIONS ---

def capture_image(filename="gesture_capture.jpg"):
    """Capture image from webcam using OpenCV"""
    # speak_text("Hold your gesture steady now.") # You can add this for more prompt if desired
    print("Camera: Please hold your gesture steady...")
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("Camera: Error: Could not open camera.")
        return None
    
    time.sleep(1)
    for _ in range(15): cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Camera: Error: Could not capture image.")
        return None
    
    cv2.imwrite(filename, frame)
    return filename

def ask_moondream(image_path):
    """Ask Moondream to classify the gesture and return the full response"""
    
    vision_prompt = "Strictly classify the gesture made by the hand in this image. Is it a thumbs up, a peace sign, a pointing finger, or another recognizable sign? Only output the classification."
    
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        return f"Moondream Error: Could not read image file. {e}"

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MOONDREAM_MODEL_NAME,
                "prompt": vision_prompt,
                "images": [image_data],
                "stream": False 
            },
            timeout=120, 
        )
        
        if response.status_code == 200:
            return response.json().get('response', 'Moondream: Failed to classify gesture.')
        else:
            return f"Moondream Error: API status {response.status_code}."
    except requests.exceptions.Timeout:
        return "Moondream: Timed out. Please try again."
    except Exception as e:
        return f"Moondream Error: Communication error: {e}"

# --- HELPFUL LLM FUNCTION ---

def get_helpful_llm_response(vision_classification):
    """
    Sends the helpful context + Moondream's classification to the LLM.
    """
    
    combined_prompt = TUTOR_PROMPT_TEMPLATE + vision_classification

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": LLM_MODEL_NAME,
                "prompt": combined_prompt,
                "stream": False
            },
            timeout=90
        )
        
        if response.status_code == 200:
            return response.json().get('response', 'I was unable to generate feedback. Let\'s try again.')
        else:
            return f"Error: Ollama API status {response.status_code}. Please check your Ollama server."
    
    except requests.exceptions.Timeout:
        return "The server timed out while thinking. Let's try that gesture one more time."
    except Exception as e:
        return f"Error communicating with the Tutor model: {e}."


# --- MAIN EXECUTION LOOP ---

def run_voice_bot():
    """Initializes the systems and runs the continuous STT -> Action loop."""
    
    # --- 1. ARGUMENT PARSING & DEVICE CHECK ---
    parser = argparse.ArgumentParser(
        description="Helpful Vision Tutor (Vosk + Ollama + Moondream)",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument("-l", "--list-devices", action="store_true", help="show list of audio devices and exit")
    parser.add_argument("-d", "--device", type=int_or_str, help="input device (numeric ID or substring)")
    parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
    parser.add_argument("-m", "--model", type=str, help="Vosk language model; e.g. en-us, fr, nl; default is en-us")
    args, remaining = parser.parse_known_args()

    if args.list_devices:
        print(sd.query_devices())
        sys.exit(0)
        
    try:
        # --- 2. VOSK & AUDIO SETUP ---
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, "input")
            args.samplerate = int(device_info["default_samplerate"])
            
        vosk_lang = args.model if args.model else "en-us"
        print(f"Loading Vosk model: {vosk_lang}...")
        model = Model(lang=vosk_lang)

        # --- 3. OLLAMA STATUS CHECK ---
        print(f"Checking Ollama status at {OLLAMA_URL}...")
        if requests.get(f"{OLLAMA_URL}/api/tags", timeout=5).status_code != 200:
            print(f"Error: Cannot connect to Ollama. Is 'ollama serve' running?")
            sys.exit(1)
            
        # --- 4. MAIN LOOP ---
        with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                dtype="int16", channels=1, callback=callback):
            
            print(f"\n{'='*70}")
            # INITIAL PROMPT IS NOW SPOKEN!
            speak_text("Welcome! I'm ready to check your gesture. Say 'show me' or 'check my sign'.")
            print("Press Ctrl+C to exit.")
            print(f"{'='*70}")
            
            rec = KaldiRecognizer(model, args.samplerate)
            
            while True:
                data = q.get()
                
                if rec.AcceptWaveform(data):
                    result_json = json.loads(rec.Result())
                    user_input = result_json.get('text', '').strip().lower()
                    
                    if user_input:
                        print(f"\nUser: {user_input}")
                        
                        # --- COMMAND CHECK ---
                        vision_commands = ['show me', 'check my sign', 'ready', 'test me', 'capture']
                        
                        if any(command in user_input for command in vision_commands):
                            
                            # 1. Capture Image
                            speak_text("Excellent! Hold your gesture steady now.")
                            image_path = capture_image()
                            
                            if image_path:
                                # 2. Ask Moondream to classify
                                print(f"Tutor Bot: Analyzing...")
                                moondream_classification = ask_moondream(image_path).strip()
                                
                                # 3. Get Helpful LLM Response (Feedback)
                                helpful_feedback = get_helpful_llm_response(moondream_classification)
                                
                                # 4. SPEAK THE FEEDBACK! (Completes the loop)
                                speak_text(helpful_feedback)
                                
                            else:
                                speak_text("I had trouble with the camera. Please make sure it's connected and visible.")

                        # --- EXIT COMMAND CHECK ---
                        elif user_input in ['quit', 'exit', 'shut down', 'log off', 'stop listening']:
                            speak_text("Great work today! See you next time.")
                            return 
                        
                        # --- NON-COMMAND INPUT ---
                        elif user_input:
                            speak_text("I'm focused on checking your signs! Just tell me 'show me' when you're ready.")

                        print("\nTutor Bot is now listening again...")
                        
                    rec.Reset() 
                    
    except KeyboardInterrupt:
        speak_text("Session paused.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_voice_bot()