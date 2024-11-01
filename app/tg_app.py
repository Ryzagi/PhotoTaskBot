import asyncio
import json
import logging
import os
import re
import sys
from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiohttp import ClientTimeout
from dotenv import load_dotenv

import routers
from constants import ADD_NEW_USER_ENDPOINT, DOWNLOAD_ENDPOINT, SOLVE_ENDPOINT
from fluent_loader import get_fluent_localization
from localization import L10nMiddleware

load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# Function to escape special Markdown characters
def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)


async def save_image(path, photo_io):
    # photo_io.seek(0)  # Ensure file pointer is at the beginning of the file
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('image_path', path)
        data.add_field('file', photo_io, filename='image.jpg', content_type='image/jpeg')

        async with session.post(
                f"http://localhost:8000{DOWNLOAD_ENDPOINT}",
                data=data
        ) as response:
            path = await response.json()
            if response.status != 200:
                raise Exception(f"Failed to save image. Status code: {response.status}")
    return path["message"], path["status_code"]


async def get_solution(path, photo_io, user_id):
    # photo_io.seek(0)  # Ensure file pointer is at the beginning of the file

    async with aiohttp.ClientSession(timeout=ClientTimeout(5 * 60)) as session:
        data = aiohttp.FormData()
        data.add_field('image_path', path)
        data.add_field('file', photo_io, filename='image.jpg', content_type='image/jpeg')
        data.add_field('user_id', user_id)

        async with session.post(
                f"http://localhost:8000{SOLVE_ENDPOINT}",
                data=data
        ) as response:
            answer = await response.json()
            if response.status != 200:
                raise Exception(f"Failed to get solution. Status code: {response.status}")
    print('Image sent to OpenAI')
    print(answer["answer"])
    return answer["answer"]


async def send_solution_to_user(message, answer):
    print(answer)
    if answer:
        answer = json.loads(answer)
        for solution in answer["solutions"]:
            problem = escape_markdown(solution["problem"])
            solution_text = escape_markdown(solution["solution"])
            steps = "\n".join([escape_markdown(step) for step in solution["steps"]])
            message_to_send = f"*Problem:* {problem}\n*Solution:* {solution_text}\n*Steps:*\n{steps}"

            await message.answer(message_to_send, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await message.answer("Daily limit exceeded. Please try again tomorrow.")


async def process_photo_message(message: Message):
    user_id = message.from_user.id
    # TODO: Add .file_id or unique identifier to the file name
    file_name = f"{message.photo[-1].file_id}.png"
    path = f"{user_id}/{file_name}"
    # -1 (last image) is the largest photo, 0 is the smallest, downloaded into memory
    photo_to_save = await bot.download(message.photo[-1])
    print(f"Photo saved in memory")
    message_text, status_code = await save_image(path=path, photo_io=photo_to_save)
    print(f"Message: {message_text}, Status code: {status_code}")
    if status_code != 200:
        raise Exception(f"Failed to save image. Status code: {status_code}")
    # This is a shitty way to do it, but I don't have time to fix it
    photo_to_answer = await bot.download(message.photo[-1])
    answer = await get_solution(path=path, photo_io=photo_to_answer, user_id=str(user_id))
    await send_solution_to_user(message, answer)


async def main() -> None:
    locale = get_fluent_localization()

    dp = Dispatcher()

    dp.message.outer_middleware(L10nMiddleware(locale))
    dp.pre_checkout_query.outer_middleware(L10nMiddleware(locale))
    dp.include_router(routers.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
