import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InputFile
from aiogram.utils import executor
from celery.result import AsyncResult
from tasks import download_audio_task, create_zip_task

API_TOKEN = '6583880436:AAEWxOdUYbuj4bwe7gbvw9-b-kfW8m7pwaU'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)


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

    # Celery bilan yuklash
    task_ids = [download_audio_task.delay(query) for query in search_queries]

    # Vazifalar natijasini kutish
    downloaded_files = []
    for task_id in task_ids:
        result = AsyncResult(task_id.id)
        while not result.ready():
            await asyncio.sleep(1)
        downloaded_files.append(result.result)

    if downloaded_files:
        zip_task = create_zip_task.delay(downloaded_files)
        while not zip_task.ready():
            await asyncio.sleep(1)

        zip_files = zip_task.result
        for zip_file in zip_files:
            await bot.send_document(message.chat.id, InputFile(zip_file))
        await message.reply("Ashulalar ZIP faylda yuborildi!")
    else:
        await message.reply("Ashulalarni yuklashda xatolik yuz berdi.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
