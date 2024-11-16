import logging
import aiohttp
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor
from aiogram.utils.exceptions import InvalidQueryID
from yt_dlp import YoutubeDL
import asyncio

API_TOKEN = '7320164836:AAH1oe-8f_BxCX73ivtm6wDGng0vC8It_LY'

logging.basicConfig(level=logging.INFO)

if not os.path.exists('downloads'):
    os.makedirs('downloads')

# YouTube'dan MP3 formatida audio yuklash funksiyasi
def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
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
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            return mp3_filename if os.path.exists(mp3_filename) else None
        except Exception as e:
            logging.error(f"Yuklashda xatolik: {e}")
            return None

# Qo'shiqchi nomiga asoslangan 10 ta qo'shiq qidirish
def search_top_songs(search_query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            search_result = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
            entries = search_result.get('entries', [])
            return [{"title": entry["title"], "url": entry["webpage_url"]} for entry in entries]
        except Exception as e:
            logging.error(f"Qidiruvda xatolik: {e}")
            return []

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot)

    @dp.message_handler(commands=['start'])
    async def start_command(message: Message):
        await message.reply("Salom! Qo'shiqchi nomini yozing va men uning eng mashhur 10 ta qo'shig'ini ko'rsataman.")

    @dp.message_handler(content_types=types.ContentTypes.TEXT)
    async def send_music_list(message: Message):
        search_query = message.text
        await message.reply("Qidirilmoqda, biroz kuting...")

        # 10 ta qo'shiq qidirish
        songs = search_top_songs(search_query)

        if songs:
            keyboard = InlineKeyboardMarkup(row_width=2)
            for idx, song in enumerate(songs, start=1):
                button = InlineKeyboardButton(
                    text=f"{idx}. {song['title'][:30]}",
                    callback_data=f"download_{idx}"
                )
                keyboard.add(button)

            await message.reply(
                "Quyidagi qo'shiqlardan birini tanlang:",
                reply_markup=keyboard
            )
            dp.current_songs = songs
        else:
            await message.reply("Qo'shiq topilmadi yoki xatolik yuz berdi.")

    @dp.callback_query_handler(lambda c: c.data and c.data.startswith('download_'))
    async def process_callback_download(callback_query: CallbackQuery):
        index = int(callback_query.data.split('_')[1]) - 1
        song = dp.current_songs[index]

        try:
            await bot.answer_callback_query(
                callback_query.id,
                text="Musiqa yuklanmoqda, biroz kuting...",
                show_alert=False
            )
        except InvalidQueryID:
            await bot.send_message(
                callback_query.from_user.id,
                "Musiqa yuklashda xatolik yuz berdi: so'rov muddati tugadi."
            )
            return

        await bot.send_message(callback_query.from_user.id, f"{song['title']} yuklanmoqda, biroz kuting...")

        # Audio yuklash
        file_path = download_audio(song["url"])

        if file_path:
            with open(file_path, 'rb') as audio:
                await bot.send_audio(
                    chat_id=callback_query.from_user.id,
                    audio=audio,
                    title=os.path.basename(file_path)
                )
            os.remove(file_path)
        else:
            await bot.send_message(
                callback_query.from_user.id,
                "Musiqa yuklashda xatolik yuz berdi."
            )

    dp.current_songs = []
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
