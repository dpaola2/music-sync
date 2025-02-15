#!/bin/bash

# Get the directory where the script is located
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Ensure we're using the right Ruby version
eval "$(rbenv init -)"

# Change to app directory
cd "$APP_DIR"

# Run the app with bundler
exec bundle exec ruby music_sync.rb