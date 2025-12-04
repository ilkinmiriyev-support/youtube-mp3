import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp
import tempfile
from pydub import AudioSegment
import re

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
executor = ThreadPoolExecutor(max_workers=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salam! YouTube linkini göndər və MP3 çıxarılsın.")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url_message_id = update.message.message_id
    chat_id = update.message.chat_id
    url = update.message.text

    if not url.startswith("http"):
        await update.message.reply_text("Send valid url")
        return

    msg = await update.message.reply_text("▰▱▱▱▱")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Sinkron yükləmə funksiyası
            def download_video():
                ydl_opts = {
                    'format': 'bestaudio/best[ext=webm]/bestaudio/best[ext=m4a]/ba',
                    'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    },
                    'extractor_args': {'youtube': {'player_client': ['web']}},
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    webm_file = ydl.prepare_filename(info)
                    return webm_file, info

            # Animasiya funksiyası
            async def animate_download(task):
                frames = [
                    "▰▱▱▱▱",
                    "▰▰▱▱▱",
                    "▰▰▰▱▱",
                    "▰▰▰▰▱",
                    "▰▰▰▰▰",
                ]
                i = 0
                while not task.done():
                    try:
                        text = f"{''.join([frames[(i+j) % len(frames)] for j in range(5)])}"
                        await msg.edit_text(text)
                        i += 1
                    except Exception as e:
                        logging.debug(f"Animation error: {e}")
                    await asyncio.sleep(0.15)

            # Thread-də yükləmə işlət
            loop = asyncio.get_event_loop()
            download_task = loop.run_in_executor(executor, download_video)

            # Animasiyanı çalıştır
            animation_task = asyncio.create_task(animate_download(download_task))

            # Yükləmənin bitməsini gözlə
            webm_file, info = await download_task
            animation_task.cancel()

            # Safe title
            safe_title = re.sub(r'[\\/*?:"<>|]', "_", info['title'])
            mp3_file = os.path.join(tmpdir, f"{safe_title}.mp3")

            # Dönüştürmə - 320kbps maksimum keyfiyyət
            def convert_to_mp3():
                audio = AudioSegment.from_file(webm_file, format="webm")
                audio.export(mp3_file, format="mp3", bitrate="320k")

            await loop.run_in_executor(executor, convert_to_mp3)

            # Göndər
            await msg.edit_text("Uploading: 📤")
            with open(mp3_file, 'rb') as f:
                await update.message.reply_audio(audio=f, title=safe_title)

            await msg.delete()

            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=url_message_id)
            except:
                pass

    except Exception as e:
        error_msg = str(e)[:100]
        await msg.edit_text(f"Xəta baş verdi:\n{error_msg}")
        logging.error(f"Download error: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download))
    app.run_polling()