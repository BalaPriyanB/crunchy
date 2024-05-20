# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies and FFmpeg
RUN apt -qq update && apt -qq install -y ffmpeg mediainfo build-essential

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download and install crunchy-cli
RUN curl -O -L https://github.com/crunchy-labs/crunchy-cli/releases/download/v3.6.3/crunchy-cli-v3.6.3-linux-x86_64 \
    && chmod +x crunchy-cli-v3.6.3-linux-x86_64
  
# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files into the container
COPY . .

# Run the bot
CMD ["python", "bot.py"]
