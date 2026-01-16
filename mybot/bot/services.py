import subprocess
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_audio(url: str) -> str | None:
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--cookies", "cookies.txt",  # <<< Add this line
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

        mp3_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)),
            reverse=True,
        )
        return os.path.join(DOWNLOAD_DIR, mp3_files[0])

    except Exception as e:
        print("Error finding downloaded file:", e)
        return None

