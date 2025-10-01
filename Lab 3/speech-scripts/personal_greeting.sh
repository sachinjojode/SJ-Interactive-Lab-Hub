#!/bin/bash

# Personal TTS Greeting Script
# This script uses espeak to have the Pi greet you by name
# Usage: ./personal_greeting.sh [your_name]

# Set default name if none provided
NAME=${1:-"friend"}

# Create a personalized greeting message
GREETING="Hello $NAME! Welcome back! I hope you're having a wonderful day. Your Raspberry Pi is ready to assist you."

echo "Playing personalized greeting for: $NAME"
echo "Message: $GREETING"

# Use espeak with enhanced voice settings for a friendly greeting
# -ven+f2: English voice with female pitch
# -k5: Speech emphasis
# -s150: Speaking speed (words per minute)
# --stdout: Output to stdout so we can pipe to aplay
espeak -ven+f2 -k5 -s150 --stdout "$GREETING" | aplay

echo "Greeting complete!"