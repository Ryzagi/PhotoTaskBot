import asyncio
import json
import logging
import os
import re
import sys
from io import BytesIO
import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.types import Message, InputFile, BufferedInputFile
from aiohttp import ClientTimeout
from dotenv import load_dotenv
from fluent.runtime import FluentLocalization

import routers
from bot.constants import DOWNLOAD_ENDPOINT, SOLVE_ENDPOINT, GET_EXIST_SOLUTION_ENDPOINT
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


async def save_image(path, photo_io):
    # photo_io.seek(0)  # Ensure file pointer is at the beginning of the file
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('image_path', path)
        data.add_field('file', photo_io, filename='image.jpg', content_type='image/jpeg')

        async with session.post(
                f"http://app:8000{DOWNLOAD_ENDPOINT}",
                data=data
        ) as response:
            answer = await response.json()
            print("Answer", answer)
            if "error" in answer:
                # Step 2: Replace single quotes with double quotes for valid JSON format
                status_code_str = answer['error'].replace("'", "\"")
                status_code = json.loads(status_code_str)
                print("Status code", status_code)
                if status_code["statusCode"] != 200:
                    print("Response", response), print("Answer", answer)
                    if status_code["error"] == "Duplicate":
                        return answer["message"], answer["status_code"], answer["error"]
                    raise Exception(f"Failed to save image. Status code: {response.status}")
    return answer["message"], answer["status_code"], False


async def get_solution(path, photo_io, user_id):
    # photo_io.seek(0)  # Ensure file pointer is at the beginning of the file

    async with aiohttp.ClientSession(timeout=ClientTimeout(5 * 60)) as session:
        data = aiohttp.FormData()
        data.add_field('image_path', path)
        data.add_field('file', photo_io, filename='image.jpg', content_type='image/jpeg')
        data.add_field('user_id', user_id)

        async with session.post(
                f"http://app:8000{SOLVE_ENDPOINT}",
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
                f"http://app:8000{GET_EXIST_SOLUTION_ENDPOINT}",
                data=data
        ) as response:
            answer = await response.json()
            print("Answer", answer)
            if response.status != 200:
                raise Exception(f"Failed to get solution. Status code: {response.status}")
    print("Got existing solution")
    print("Answer:", answer["answer"])
    return answer["answer"]["message"][0]["solution"]


def get_latex_image_url(latex_expression):
    # Use an external service like QuickLaTeX or CodeCogs
    base_url = 'https://latex.codecogs.com/png.latex?'
    encoded_expression = requests.utils.quote(latex_expression)
    url = base_url + encoded_expression
    return url  # Returns the URL of the image


# Function to process and send messages
async def image_send_solution_to_user(message, answer):
    if answer:
        if isinstance(answer, str):
            answer = json.loads(answer)
            print("Answer:", answer)
        for solution in answer["solutions"]:
            problem = solution["problem"]
            solution_text = solution["solution"]
            steps = solution["steps"]

            # Send problem
            await message.answer(f"<b>Problem:</b>\n{problem}", parse_mode=ParseMode.HTML)

            # Send steps with LaTeX rendered images
            for step in steps:
                # Find LaTeX expressions in the step
                latex_expressions = re.findall(r'\$(.*?)\$', step)
                text_parts = re.split(r'\$.*?\$', step)

                # Prepare message parts
                for i, text_part in enumerate(text_parts):
                    if text_part.strip():
                        await message.answer(text_part, parse_mode=ParseMode.HTML)
                    if i < len(latex_expressions):
                        # Get LaTeX image URL
                        image_url = get_latex_image_url(latex_expressions[i])
                        await message.answer_photo(image_url)

            # Send final solution
            await message.answer(f"<b>Solution:</b>\n{solution_text}", parse_mode=ParseMode.HTML)
    else:
        await message.answer("Daily limit exceeded. Please try again tomorrow.")


import subprocess
import os
from io import BytesIO
from PIL import Image

import json


def render_latex_online(latex_code):
    url = "https://quicklatex.com/latex3.f"
    data = {
        'formula': latex_code,
        'fsize': 12,
        'fcolor': '000000',
        'mode': 0,
        'out': 1,
        'remhost': 'quicklatex.com',
        'preamble': r'\usepackage{amsmath, amssymb}',
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        content = response.text
        # Extract the image URL
        match = re.search(r'url\:(.*?)\n', content)
        if match:
            image_url = match.group(1)
            # Download the image
            image_response = requests.get(image_url)
            return image_response.content
        else:
            print("Error rendering LaTeX:", content)
            return None
    else:
        print("HTTP Error:", response.status_code)
        return None


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



def replace_unicode_symbols(text):
    """Replace unicode symbols with LaTeX commands."""
    replacements = {
        '∬': r'\iint',
        '∫': r'\int',
        '∑': r'\sum',
        '√': r'\sqrt',
        '∞': r'\infty',
        'θ': r'\theta',
        'π': r'\pi',
        '≤': r'\leq',
        '≥': r'\geq',
        '≠': r'\neq',
        # Add more replacements as needed
    }
    for unicode_char, latex_cmd in replacements.items():
        text = text.replace(unicode_char, latex_cmd)
    return text


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
                # Handle LaTeX compilation errors
                await message.answer("An error occurred while generating the solution image.")
                print(f"LaTeX compilation error: {e}")
                continue  # Skip to the next solution

            # Send image via bot
            input_file = BufferedInputFile(image_bytes, filename='solution.png')
            await message.answer_photo(input_file)
            # Send to the admin
            await bot.send_photo(chat_id=ADMIN_TG_ID, photo=input_file, caption=f"Solution image for the user: {message.from_user.id}, nickname: {message.from_user.username}")
    else:
        await message.answer("Daily limit exceeded. Please try again tomorrow.")


async def process_photo_message(message: Message, l10n: FluentLocalization):
    user_id = message.from_user.id
    await message.answer(
        l10n.format_value("loading-message")
    )

    file_name = f"{message.photo[-1].file_unique_id}.png"
    print(f"File name: {file_name}")
    path = f"{user_id}/{file_name}"
    # -1 (last image) is the largest photo, 0 is the smallest, downloaded into memory
    photo_to_save = await bot.download(message.photo[-1])
    print(f"Photo saved in memory")
    message_text, status_code, error = await save_image(path=path, photo_io=photo_to_save)
    print(f"Message: {message_text}, Status code: {status_code}")
    print(f"Error: {error}")
    if error:
        await message.answer("This task has already been solved. Here is the solution:")
        message_text = await get_exist_solution(path=path, user_id=str(user_id))
        print(f"Message text: {message_text}")
        await send_solution_to_user(message, message_text)
        return None

    print(f"Status code: {status_code}")

    # Check the actual status code value
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
