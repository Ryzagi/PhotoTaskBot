import asyncio
import json
import logging
import os
import re
import sys
import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.types import Message, BufferedInputFile
from aiohttp import ClientTimeout
from dotenv import load_dotenv

import routers
from bot.constants import DOWNLOAD_ENDPOINT, SOLVE_ENDPOINT, GET_EXIST_SOLUTION_ENDPOINT, LOADING_MESSAGE, NETWORK, \
    DAILY_LIMIT_EXCEEDED_MESSAGE
from bot.fluent_loader import get_fluent_localization
from bot.localization import L10nMiddleware

load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_TG_ID = os.environ.get("ADMIN_TG_ID")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# Function to escape special Markdown characters
def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)


async def save_image(path, photo_io, user_id):
    # photo_io.seek(0)  # Ensure file pointer is at the beginning of the file
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('image_path', path)
        data.add_field('file', photo_io, filename='image.jpg', content_type='image/jpeg')
        data.add_field('user_id', user_id)

        async with session.post(
                f"http://{NETWORK}:8000{DOWNLOAD_ENDPOINT}",
                data=data
        ) as response:
            answer = await response.json()
            print("Answer", answer)
            if "error" in answer:
                # Step 2: Replace single quotes with double quotes for valid JSON format
                status_code_str = answer['error'].replace("'", "\"")
                print("Status code str", status_code_str)
                status_code = json.loads(status_code_str)
                print("Status code", status_code)
                if status_code["statusCode"] != 200:
                    print("Response", response), print("Answer", answer)
                    if status_code["error"] == "Duplicate":
                        return answer["message"], answer["status_code"], answer["error"]
                    if status_code["error"] == "Daily limit exceeded":
                        return answer["message"], answer["status_code"], answer["error"]

    return answer["message"], answer["status_code"], False


async def get_solution(path, photo_io, user_id):
    # photo_io.seek(0)  # Ensure file pointer is at the beginning of the file

    async with aiohttp.ClientSession(timeout=ClientTimeout(5 * 60)) as session:
        data = aiohttp.FormData()
        data.add_field('image_path', path)
        data.add_field('file', photo_io, filename='image.jpg', content_type='image/jpeg')
        data.add_field('user_id', user_id)

        async with session.post(
                f"http://{NETWORK}:8000{SOLVE_ENDPOINT}",
                data=data
        ) as response:
            answer = await response.json()
            if response.status != 200:
                raise Exception(f"Failed to get solution. Status code: {response.status}")
    print('Image sent to OpenAI')
    print(answer["answer"])
    return answer["answer"]


async def get_exist_solution(path, user_id):
    # photo_io.seek(0)  # Ensure file pointer is at the beginning of the file

    async with aiohttp.ClientSession(timeout=ClientTimeout(5 * 60)) as session:
        data = aiohttp.FormData()
        data.add_field('image_path', path)
        data.add_field('user_id', user_id)

        async with session.post(
                f"http://{NETWORK}:8000{GET_EXIST_SOLUTION_ENDPOINT}",
                data=data
        ) as response:
            answer = await response.json()
            print("Answer", answer)
            if response.status != 200:
                raise Exception(f"Failed to get solution. Status code: {response.status}")
    print("Got existing solution")
    print("Answer:", answer["answer"])
    return answer["answer"]["message"][0]["solution"]

def _prepare_latex_document(solution):
    # LaTeX document header and footer with XeLaTeX support
    latex_header = r'''
\documentclass[preview]{standalone}
\usepackage{fontspec}
\usepackage{amsmath, amssymb}
\usepackage{polyglossia}
\setdefaultlanguage{russian}
\setmainfont{Times New Roman} % Use a font that is installed
\newfontfamily\cyrillicfont{Times New Roman}
\newfontfamily\cyrillicfontsf{Arial}
\newfontfamily\cyrillicfonttt{Courier New}
\begin{document}
'''

    latex_footer = r'''
\end{document}
'''

    # Function to escape LaTeX special characters
    def escape_latex(s):
        return re.sub(r'([%$&#_^{}~^\\])', r'\\\1', s)

    # Combine steps into LaTeX code
    content = ""

    # Add problem statement
    problem_text = escape_latex(solution["problem"])
    content += r"\textbf{Problem:}\\ " + problem_text + r"\\[10pt]"

    # Add steps
    content += r"\textbf{Solution Steps:}\\"
    for step in solution["steps"]:
        step_text = escape_latex(step)
        content += step_text + r"\\[5pt]"

    # Add final solution
    content += r"\textbf{Final Solution:}\\"

    if isinstance(solution["solution"], dict):
        content += r"\begin{align*}"
        for key, value in solution["solution"].items():
            key_escaped = escape_latex(str(key))
            value_escaped = escape_latex(str(value))
            # Wrap the key with \text{} to ensure it's treated as text
            content += f"\\text{{{key_escaped}}} &= {value_escaped} \\\\"
        content += r"\end{align*}"
    else:
        solution_text = escape_latex(solution["solution"])
        content += r"\[" + solution_text + r"\]"

    # Combine all parts
    full_latex = latex_header + content + latex_footer
    return full_latex


def strip_math_delimiters(s):
    """Remove math delimiters from a string."""
    s = s.strip()
    if s.startswith('$$') and s.endswith('$$'):
        return s[2:-2].strip()
    elif s.startswith('$') and s.endswith('$'):
        return s[1:-1].strip()
    elif s.startswith('\\[') and s.endswith('\\]'):
        return s[2:-2].strip()
    elif s.startswith('\\(') and s.endswith('\\)'):
        return s[2:-2].strip()
    else:
        return s


def escape_latex_special_chars(text):
    """Escape special LaTeX characters in text."""
    special_chars = {
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',           # Escape underscores
        # '{':  r'\{',          # Do not escape '{' and '}'
        # '}':  r'\}',
        '~':  r'\textasciitilde{}',
        '^':  r'\^{}',
        # Backslashes are not escaped here
    }
    for char, escape_seq in special_chars.items():
        text = text.replace(char, escape_seq)
    return text



def process_text_with_math(text):
    """Process text content with embedded math expressions."""
    # Regular expression to find math expressions within \( ... \) or $ ... $
    pattern = r'(\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\])'

    # Split the text into math and non-math parts
    parts = re.split(pattern, text, flags=re.DOTALL)

    processed_parts = []
    for part in parts:
        if re.match(pattern, part, flags=re.DOTALL):
            # It's a math expression, leave it as is
            processed_parts.append(part)
        else:
            # It's normal text, escape special characters
            processed_parts.append(escape_latex_special_chars(part))
    return ''.join(processed_parts)


def prepare_latex_document(solution):
    """Prepare the full LaTeX document for a solution."""
    # LaTeX document header and footer with XeLaTeX support
    latex_header = r'''
        \documentclass[preview]{standalone}
        \usepackage{fontspec}
        \usepackage{amsmath, amssymb}
        \usepackage{polyglossia}
        \setdefaultlanguage{russian}
        \setmainfont{Liberation Serif} % Use Liberation fonts
        \newfontfamily\cyrillicfont{Liberation Serif}
        \newfontfamily\cyrillicfontsf{Liberation Sans}
        \newfontfamily\cyrillicfonttt{Liberation Mono}

        \begin{document}
        '''
    latex_footer = r'''
        \end{document}
        '''

    content = ""

    # Add problem statement
    problem_text = process_text_with_math(solution["problem"])
    content += r"\textbf{Problem:}\\ " + problem_text + r"\\[10pt]" + "\n"

    # Add steps
    content += r"\textbf{Solution Steps:}\\[5pt]" + "\n"
    content += r"\begin{enumerate}" + "\n"
    for step in solution["steps"]:
        if step["type"] == "math":
            step_content = strip_math_delimiters(step["content"])
            content += r"\item $" + step_content + r"$" + "\n"
        else:
            # Include text content as-is
            step_content = step["content"]
            content += r"\item " + step_content + "\n"
    content += r"\end{enumerate}" + "\n"

    # Add final solution
    content += r"\textbf{Final Solution:}\\[5pt]" + "\n"
    content += r"\begin{enumerate}" + "\n"
    for sol in solution["solution"]:
        if sol["type"] == "math":
            sol_content = strip_math_delimiters(sol["content"])
            content += r"\item $" + sol_content + r"$" + "\n"
        else:
            sol_content = process_text_with_math(sol["content"])
            content += r"\item " + sol_content + "\n"
    content += r"\end{enumerate}" + "\n"

    # Combine all parts
    full_latex = latex_header + content + latex_footer
    return full_latex


def render_latex_to_image(latex_code):
    import subprocess
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = os.path.join(temp_dir, 'document.tex')
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_code)

        # Compile LaTeX document using xelatex
        process = subprocess.Popen(
            ['xelatex', '-interaction=nonstopmode', '-output-directory', temp_dir, 'document.tex'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"LaTeX compilation failed")
            print(f"Return code: {process.returncode}")
            print(f"stdout: {stdout.decode('utf-8')}")
            print(f"stderr: {stderr.decode('utf-8')}")
            # Print the LaTeX code for debugging
            print("LaTeX code:")
            print(latex_code)
            raise Exception("LaTeX compilation failed")

        pdf_file = os.path.join(temp_dir, 'document.pdf')
        # Convert PDF to PNG using ImageMagick's `convert` or `pdftoppm`
        # Here's an example using `pdftoppm`:
        process = subprocess.Popen(
            ['pdftoppm', '-png', '-singlefile', pdf_file, os.path.join(temp_dir, 'image')],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"PDF to image conversion failed")
            print(f"Return code: {process.returncode}")
            print(f"stdout: {stdout.decode('utf-8')}")
            print(f"stderr: {stderr.decode('utf-8')}")
            raise Exception("PDF to image conversion failed")

        image_file = os.path.join(temp_dir, 'image.png')
        with open(image_file, 'rb') as f:
            image_bytes = f.read()

    return image_bytes

def regenerate_latex(solution):
    """Simplify LaTeX content to reduce compilation errors."""
    latex_code = prepare_latex_document(solution)
    # Optionally, strip problematic sections or simplify the content here.
    # Example: Removing custom fonts or specific packages
    simplified_latex_code = latex_code.replace(r'\usepackage{fontspec}', '').replace(r'\setmainfont{Liberation Serif}', '')
    return simplified_latex_code

def prepare_plain_text_document(solution):
    """Prepare a plain-text version of the solution."""
    content = "Problem:\n" + solution["problem"] + "\n\n"
    content += "Solution Steps:\n"
    for idx, step in enumerate(solution["steps"], start=1):
        if step["type"] == "math":
            step_content = strip_math_delimiters(step["content"])
            content += f"{idx}. {step_content}\n"
        else:
            content += f"{idx}. {step['content']}\n"
    content += "\nFinal Solution:\n"
    for sol in solution["solution"]:
        if sol["type"] == "math":
            sol_content = strip_math_delimiters(sol["content"])
            content += f"- {sol_content}\n"
        else:
            content += f"- {sol['content']}\n"
    return content


async def send_solution_to_user(message, answer):
    """Send the solution to the user as an image."""
    if answer:
        if isinstance(answer, str):
            # Parse the JSON string into a Python dictionary
            answer = json.loads(answer)
        # Do not escape backslashes in the JSON data
        print("Answer:", answer)
        for solution in answer["solutions"]:
            # Prepare LaTeX document using the adjusted function
            latex_code = prepare_latex_document(solution)
            # Render LaTeX to image
            try:
                image_bytes = render_latex_to_image(latex_code)
            except Exception as e:
                print(f"Initial LaTeX compilation failed: {e}")
                latex_code = regenerate_latex(solution)
                try:
                    image_bytes = render_latex_to_image(latex_code)
                except Exception as e:
                    # Handle LaTeX compilation errors
                    print(f"LaTeX compilation error: {e}")
                    plain_text = prepare_plain_text_document(solution)
                    await message.answer(
                        f"Ошибка при создании изображения. Вот текстовое решение:\n\n{plain_text}")
                    await bot.send_message(
                        ADMIN_TG_ID,
                        f"Ошибка при создании изображения. Вот текстовое решение:\n\n{plain_text}. User ID: {message.from_user.id}, nickname: {message.from_user.username}")
                    continue  # Skip to the next solution

            # Send image via bot
            input_file = BufferedInputFile(image_bytes, filename='solution.png')
            await message.answer_photo(input_file)
            # Send to the admin
            await bot.send_photo(chat_id=ADMIN_TG_ID, photo=input_file, caption=f"Solution image for the user: {message.from_user.id}, nickname: {message.from_user.username}")
    else:
        await message.answer(DAILY_LIMIT_EXCEEDED_MESSAGE)


async def process_photo_message(message: Message):
    user_id = message.from_user.id
    file_name = f"{message.photo[-1].file_unique_id}.png"
    print(f"File name: {file_name}")
    path = f"{user_id}/{file_name}"
    # -1 (last image) is the largest photo, 0 is the smallest, downloaded into memory
    photo_to_save = await bot.download(message.photo[-1])
    print(f"Photo saved in memory")
    message_text, status_code, error = await save_image(path=path, photo_io=photo_to_save, user_id=str(user_id))
    print(f"Message: {message_text}, Status code: {status_code}")
    print(f"Error: {error}")
    if status_code == 400:
        await message.answer("Вы уже решали это задание. Вот решение:")
        message_text = await get_exist_solution(path=path, user_id=str(user_id))
        print(f"Message text: {message_text}")
        await send_solution_to_user(message, message_text)
        return None
    if status_code == 429:
        await message.answer(DAILY_LIMIT_EXCEEDED_MESSAGE)
        return None

    print(f"Status code: {status_code}")

    # Check the actual status code value
    if status_code != 200:
        raise Exception(f"Failed to save image. Status code: {status_code}")
    # This is a shitty way to do it, but I don't have time to fix it
    photo_to_answer = await bot.download(message.photo[-1])
    await message.answer(
        LOADING_MESSAGE
    )
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
