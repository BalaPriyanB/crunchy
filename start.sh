#!/bin/bash

# Update package list and install necessary packages
apt -qq update && apt -qq install -y ffmpeg mediainfo build-essential

# Install curl and clean up
apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Download and setup Crunchy CLI
curl -O -L https://github.com/crunchy-labs/crunchy-cli/releases/download/v3.6.3/crunchy-cli-v3.6.3-linux-x86_64 \
    && chmod +x crunchy-cli-v3.6.3-linux-x86_64

# Run the Python script
python3 main.py
