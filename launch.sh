#!/bin/bash

# Path to the app directory
APP_DIR="$HOME/projects/music-sync"

# Activate virtual environment
source "$APP_DIR/venv/bin/activate"

# Run the Python script
exec python "$APP_DIR/music_sync.py"