#!/bin/bash

# Simple number input script
# Usage: ./numerical_input.sh

echo "What's your phone number?"
espeak -ven+f2 -k5 -s150 --stdout "What's your phone number?" | aplay

echo "Recording for 5 seconds..."
arecord -f cd -t wav -d 5 -r 16000 -c 1 answer.wav

echo "Transcribing with Whisper..."
whisper answer.wav --model tiny --output_format txt --output_dir .

echo "Your answer:"
cat answer.txt