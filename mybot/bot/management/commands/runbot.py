import os
import subprocess
import threading
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from http.server import HTTPServer, BaseHTTPRequestHandler

# Directory to store downloaded audio
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_audio(url: str) -> str | None:
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        url,
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Error downloading audio:", e)
        return None

    try:
        files = os.listdir(DOWNLOAD_DIR)
        mp3_files = [f for f in files if f.endswith(".mp3")]
        if not mp3_files:
            return None
        mp3_files.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
        return os.path.join(DOWNLOAD_DIR, mp3_files[0])
    except Exception as e:
        print("Error finding downloaded file:", e)
        return None

# ----- Telegram Handlers -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Send me a YouTube link and I will convert it to MP3!")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link")
        return

    status = await update.message.reply_text("⏳ Converting video to audio...")
    file_path = download_audio(url)
    if not file_path:
        await status.edit_text("❌ Failed to convert video")
        return

    try:
        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f),
                filename=os.path.basename(file_path),
                caption="🎧 Your MP3 is ready!"
            )
    except Exception as e:
        print("Error sending file:", e)
        await update.message.reply_text("❌ Failed to send MP3")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ----- Dummy HTTP server for Render -----
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

# ----- Django Command -----
class Command(BaseCommand):
    help = "Run Telegram bot"

    def handle(self, *args, **kwargs):
        # Start dummy HTTP server in background
        threading.Thread(target=run_dummy_server, daemon=True).start()

        # Start Telegram bot
        app = ApplicationBuilder().token(settings.BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

        print("🤖 Bot is running...")
        app.run_polling()
