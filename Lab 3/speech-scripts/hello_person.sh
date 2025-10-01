#!/bin/bash

# Simple Pi greeting script
# Usage: ./hello.sh

read -p "What's your name? " name
espeak -ven+f2 -k5 -s150 --stdout "Hello $name, I am at your service. Please ask me anything you desire." | aplay