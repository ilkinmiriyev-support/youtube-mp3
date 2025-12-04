# Python image
FROM python:3.12-slim

# FFmpeg quraşdır
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# İş qovluğu
WORKDIR /app

# Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot kodu
COPY bot.py .

# Env variable üçün port (lazım deyil polling üçün, webhook üçün lazımdır)
ENV BOT_TOKEN=""

# Botu işə sal
CMD ["python", "bot.py"]
