import asyncio
import logging
import os
import zipfile
import time
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InputFile
from aiogram.utils import executor
from yt_dlp import YoutubeDL

API_TOKEN = '7320164836:AAHEsvKlt040Sq0kRyRJWbAuk6jfNMoh3KI'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

download_dir = 'downloads/musiqalarim'
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# YouTube'dan MP3 formatida audio yuklash funksiyasi
async def download_audio(search_query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': '/usr/bin/ffmpeg',  # Linux uchun yo'l
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=True)
            filename = ydl.prepare_filename(info['entries'][0])
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            title = info['entries'][0]['title']
            return mp3_filename, title if os.path.exists(mp3_filename) else (None, None)
        except Exception as e:
            print(f"Yuklashda xatolik: {e}")
            return None, None

# Asynchronous download handler
async def download_multiple_tracks(search_queries):
    tasks = [download_audio(query) for query in search_queries]
    results = await asyncio.gather(*tasks)  # Parallel download
    return results

# ZIP fayl yaratish va 50 MB cheklov
def create_zip_files(files):
    zip_files = []
    current_zip_size = 0
    current_zip_name = None
    current_zip = None

    for file_path in files:
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

    return zip_files


@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    await message.reply("Salom! Ashulalar ro'yxatini vergul bilan ajratib yozing va men ularni yuklab beraman.\n\nMasalan:\nshakira waka waka, michael jackson beat it", parse_mode='Markdown')


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def send_music(message: Message):
    search_queries = message.text.split(',')
    search_queries = [query.strip() for query in search_queries if query.strip()]

    if not search_queries:
        await message.reply("Iltimos, ashulalar ro'yxatini kiriting.")
        return

    await message.reply("Ashulalar yuklanmoqda, biroz kuting...")

    # Asynchronous MP3 download
    downloaded_files = []
    results = await download_multiple_tracks(search_queries)

    for mp3_file_path, title in results:
        if mp3_file_path:
            downloaded_files.append(mp3_file_path)

    if downloaded_files:
        zip_files = create_zip_files(downloaded_files)
        for zip_file in zip_files:
            await bot.send_document(message.chat.id, InputFile(zip_file))
        await message.reply("Ashulalar ZIP faylda yuborildi!")
        clear_downloaded_files()
    else:
        await message.reply("Ashulalarni yuklashda xatolik yuz berdi.")


# Yuklangan fayllarni tozalash funksiyasi
def clear_downloaded_files():
    for root, dirs, files in os.walk(download_dir):
        for file in files:
            os.remove(os.path.join(root, file))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
