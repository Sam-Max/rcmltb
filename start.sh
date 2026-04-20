#!/bin/bash

export PATH="$HOME/.deno/bin:/usr/local/bin:$PATH"

# Check for Deno (required for yt-dlp YouTube extraction)
if ! command -v deno &> /dev/null; then
    echo "⚠️  Deno not found. Installing Deno for yt-dlp..."
    curl -fsSL https://deno.land/install.sh | sh -s -- -y
    export PATH="$HOME/.deno/bin:$PATH"
fi

python3 update.py && python3 -m bot
