import os
import zipfile

from aiogram import types
from yt_dlp import YoutubeDL
from celery import Celery

from celery import Celery
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/1')

download_dir = 'downloads/musiqalarim'
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

@app.task
def download_audio_task(search_query):
    """YouTube musiqa yuklash Celery vazifasi."""
    ydl_opts = {
        'format': 'bestaudio[ext=mp3]/bestaudio/best',
        'noplaylist': True,
        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'merge_output_format': 'mp3',
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=True)
            filename = ydl.prepare_filename(info['entries'][0])
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            if os.path.exists(mp3_filename):
                return mp3_filename
        except Exception as e:
            return f"Xato: {e}"
    return None

@app.task
def create_zip_task(files):
    """ZIP fayl yaratish Celery vazifasi."""
    zip_files = []
    current_zip_size = 0
    current_zip_name = None
    current_zip = None

    for file_path in files:
        # Fayl mavjudligini tekshirish
        if not os.path.exists(file_path):
            print(f"Fayl topilmadi: {file_path}")
            continue

        file_size = os.path.getsize(file_path)
        if not current_zip or current_zip_size + file_size > 50 * 1024 * 1024:  # 50 MB
            if current_zip:
                current_zip.close()
                zip_files.append(current_zip_name)

            current_zip_name = os.path.join(download_dir, f"archive_{len(zip_files) + 1}.zip")
            current_zip = zipfile.ZipFile(current_zip_name, 'w')
            current_zip_size = 0

        current_zip.write(file_path, os.path.basename(file_path))
        current_zip_size += file_size

    if current_zip:
        current_zip.close()
        zip_files.append(current_zip_name)

    # Fayllarni o'chirish
    for file_path in files:
        if os.path.exists(file_path):
            os.remove(file_path)  # Faylni o'chirish

    return zip_files

async def send_music(message: types.Message):
    downloaded_files = [...]  # Yuklab olingan fayllarning yo'llari
    zip_task = create_zip_task.delay(downloaded_files)  # Fayllarni ZIPga joylash

    await message.reply("ZIP fayl yaratilmoqda, iltimos kuting...")

    # ZIP faylni yaratish tugallangandan keyin
    zip_files = zip_task.get()  # Bu yerda zip_task get() yordamida natijani olish

    # ZIP faylni foydalanuvchiga yuborish
    for zip_file in zip_files:
        await message.answer_document(open(zip_file, 'rb'))

        # ZIP faylni yuborganidan keyin uni o'chirish
        os.remove(zip_file)
