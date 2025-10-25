import asyncio
import json
import logging
import os
import re
import sys

import routers
import subprocess
import tempfile
import shutil

from aiogram import Bot, Dispatcher, exceptions
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.types import Message, BufferedInputFile, InputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import ClientTimeout
from bot.constants import (
    DOWNLOAD_ENDPOINT,
    SOLVE_ENDPOINT,
    GET_EXIST_SOLUTION_ENDPOINT,
    LOADING_MESSAGE,
    NETWORK,
    DAILY_LIMIT_EXCEEDED_MESSAGE,
    TEXT_SOLVE_ENDPOINT,
    LATEX_TO_TEXT_SOLVE_ENDPOINT,
    GET_ALL_USER_IDS,
    ADD_SUBSCRIPTION_LIMITS_FOR_ALL_USERS,
)
from bot.fluent_loader import get_fluent_localization
from bot.latex_renderer import latex_renderer
from bot.localization import L10nMiddleware
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_TG_ID = os.environ.get("ADMIN_TG_ID")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

LATEX_ENGINE_ENV = os.getenv("LATEX_ENGINE", "").strip().lower()

MD_V2_SPECIALS = r"_*[]()~`>#+-=|{}.!\\"

_MD_V2_REGEX = re.compile(r"([_*[\]()~`>#+\-=|{}.!\\])")


def pick_latex_engine():
    """
    Determine which LaTeX engine is available.
    Priority: explicit env -> xelatex -> lualatex -> pdflatex.
    """
    candidates = []
    if LATEX_ENGINE_ENV:
        candidates.append(LATEX_ENGINE_ENV)
    candidates += ["xelatex", "xelatex", "lualatex", "pdflatex"]
    for eng in candidates:
        if shutil.which(eng):
            return eng
    return None


def build_latex_header(engine: str, minimal: bool = False) -> str:
    """
    Build a header appropriate for the chosen engine.
    For XeLaTeX/LuaLaTeX: use fontspec + polyglossia with Liberation fonts (Cyrillic capable).
    For pdfLaTeX: use T2A + babel (requires texlive-lang-cyrillic + cm-super installed).
    """
    if engine in ("xelatex", "lualatex"):
        main_font = "Liberation Serif"
        sans_font = "Liberation Sans"
        mono_font = "Liberation Mono"
        return (
            "\\documentclass[preview]{standalone}\n"
            "\\usepackage{amsmath,amssymb}\n"
            "\\usepackage{polyglossia}\n"
            "\\setdefaultlanguage{russian}\n"
            "\\setotherlanguage{english}\n"
            "\\usepackage{fontspec}\n"
            "\\defaultfontfeatures{Ligatures=TeX}\n"
            f"\\setmainfont{{{main_font}}}\n"
            f"\\setsansfont{{{sans_font}}}\n"
            f"\\setmonofont{{{mono_font}}}\n"
            f"\\newfontfamily\\russianfont{{{main_font}}}\n"
            f"\\newfontfamily\\russianfontsf{{{sans_font}}}\n"
            f"\\newfontfamily\\russianfonttt{{{mono_font}}}\n"
            "\\begin{document}\n"
        )
    else:
        extra = "" if minimal else "\n\\usepackage{icomma}"
        return (
                "\\documentclass[preview]{standalone}\n"
                "\\usepackage[T2A]{fontenc}\n"
                "\\usepackage[utf8]{inputenc}\n"
                "\\usepackage[russian,english]{babel}\n"
                "\\usepackage{amsmath,amssymb}" + extra + "\n"
                                                          "\\begin{document}\n"
        )


LATEX_FOOTER = "\\end{document}\n"


def make_solution_body(solution) -> str:
    lines = []
    lines.append(r"\textbf{Задание:}\\ " + process_text_with_math(solution["problem"]) + r"\\[8pt]")
    lines.append(r"\textbf{Решение:}\\[-2pt]")
    lines.append(r"\begin{enumerate}")
    for step in solution["steps"]:
        if step["type"] == "math":
            lines.append(r"\item $" + strip_math_delimiters(step["content"]) + r"$")
        else:
            lines.append(r"\item " + process_text_with_math(step["content"]))
    lines.append(r"\end{enumerate}")
    lines.append(r"\textbf{Ответ:}\\[-2pt]")
    lines.append(r"\begin{enumerate}")
    for sol in solution["solution"]:
        if sol["type"] == "math":
            lines.append(r"\item $" + strip_math_delimiters(sol["content"]) + r"$")
        else:
            lines.append(r"\item " + process_text_with_math(sol["content"]))
    lines.append(r"\end{enumerate}")
    return "\n".join(lines)


def build_full_latex(solution, engine: str, minimal: bool = False) -> str:
    return build_latex_header(engine, minimal=minimal) + make_solution_body(solution) + LATEX_FOOTER


def compile_latex(latex_code: str, engine: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "doc.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)

        cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", "-output-directory", temp_dir, tex_path]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise RuntimeError(f"{engine} failed: {proc.stderr.decode('utf-8', 'ignore')[:500]}")

        pdf_path = os.path.join(temp_dir, "doc.pdf")
        if not os.path.exists(pdf_path):
            raise RuntimeError("PDF not produced")

        png_base = os.path.join(temp_dir, "out")
        conv = subprocess.run(["pdftoppm", "-png", "-singlefile", "-r", "200", pdf_path, png_base],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if conv.returncode != 0:
            raise RuntimeError(f"pdftoppm failed: {conv.stderr.decode('utf-8', 'ignore')[:400]}")
        with open(png_base + ".png", "rb") as img:
            return img.read()


def render_solution_to_png(solution):
    engine = pick_latex_engine()
    if not engine:
        raise RuntimeError("No LaTeX engine found (install xelatex or pdflatex).")
    errors = []
    tries = [
        dict(minimal=False),
        dict(minimal=True)
    ]
    for t in tries:
        try:
            code = build_full_latex(solution, engine, minimal=t["minimal"])
            return compile_latex(code, engine)
        except Exception as e:
            errors.append(str(e))
            continue
    if engine != "pdflatex" and shutil.which("pdflatex"):
        try:
            code = build_full_latex(solution, "pdflatex", minimal=True)
            return compile_latex(code, "pdflatex")
        except Exception as e:
            errors.append(str(e))
    raise RuntimeError("All LaTeX render attempts failed:\n" + "\n---\n".join(errors))


async def save_image(path, photo_io, user_id):
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("image_path", path)
        data.add_field(
            "file", photo_io, filename="image.jpg", content_type="image/jpeg"
        )
        data.add_field("user_id", user_id)

        async with session.post(
                f"http://{NETWORK}:8000{DOWNLOAD_ENDPOINT}", data=data
        ) as response:
            answer = await response.json()
            print("Answer", answer)
            if "error" in answer:
                status_code_str = answer["error"].replace("'", '"')
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


async def text_solution(text, user_id):
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("text", text)
        data.add_field("user_id", user_id)

        async with session.post(
                f"http://{NETWORK}:8000{TEXT_SOLVE_ENDPOINT}", data=data
        ) as response:
            answer = await response.json()
            print("Answer", answer)
            if response.status != 200:
                raise Exception(
                    f"Failed to get solution. Status code: {response.status}"
                )
            if answer["answer"] == 429:
                return None
    print("Text sent to Gemini")
    print(answer["answer"])
    return answer["answer"]


async def latex_to_text_solution(latex, user_id):
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("text", latex)
        data.add_field("user_id", user_id)

        async with session.post(
                f"http://{NETWORK}:8000{LATEX_TO_TEXT_SOLVE_ENDPOINT}", data=data
        ) as response:
            answer = await response.json()
            if response.status != 200:
                raise Exception(
                    f"Failed to get solution. Status code: {response.status}"
                )
    print("Text sent to Gemini")
    print(answer["answer"])
    return answer["answer"]


async def get_solution(path, photo_io, user_id):
    async with aiohttp.ClientSession(timeout=ClientTimeout(5 * 60)) as session:
        data = aiohttp.FormData()
        data.add_field("image_path", path)
        data.add_field(
            "file", photo_io, filename="image.jpg", content_type="image/jpeg"
        )
        data.add_field("user_id", user_id)

        async with session.post(
                f"http://{NETWORK}:8000{SOLVE_ENDPOINT}", data=data
        ) as response:
            answer = await response.json()
            if response.status != 200:
                raise Exception(
                    f"Failed to get solution. Status code: {response.status}"
                )
    print("Image sent to OpenAI")
    print(answer["answer"])
    return answer["answer"]


async def get_exist_solution(path, user_id):
    async with aiohttp.ClientSession(timeout=ClientTimeout(5 * 60)) as session:
        data = aiohttp.FormData()
        data.add_field("image_path", path)
        data.add_field("user_id", user_id)

        async with session.post(
                f"http://{NETWORK}:8000{GET_EXIST_SOLUTION_ENDPOINT}", data=data
        ) as response:
            answer = await response.json()
            print("Answer", answer)
            if response.status != 200:
                raise Exception(
                    f"Failed to get solution. Status code: {response.status}"
                )
    print("Got existing solution")
    print("Answer:", answer["answer"])
    return answer["answer"]["message"][0]["solution"]


def _prepare_latex_document(solution):
    latex_header = r"""
\documentclass[preview]{standalone}
\usepackage{fontspec}
\usepackage{amsmath, amssymb}
\usepackage{polyglossia}
\setdefaultlanguage{russian}
\setmainfont{Times New Roman}
\newfontfamily\cyrillicfont{Times New Roman}
\newfontfamily\cyrillicfontsf{Arial}
\newfontfamily\cyrillicfonttt{Courier New}
\begin{document}
"""

    latex_footer = r"""
\end{document}
"""

    def escape_latex(s):
        return re.sub(r"([%$&#_^{}~^\\])", r"\\\1", s)

    content = ""

    problem_text = escape_latex(solution["problem"])
    content += r"\textbf{Problem:}\\ " + problem_text + r"\\[10pt]"

    content += r"\textbf{Solution Steps:}\\"
    for step in solution["steps"]:
        step_text = escape_latex(step)
        content += step_text + r"\\[5pt]"

    content += r"\textbf{Final Solution:}\\"

    if isinstance(solution["solution"], dict):
        content += r"\begin{align*}"
        for key, value in solution["solution"].items():
            key_escaped = escape_latex(str(key))
            value_escaped = escape_latex(str(value))
            content += f"\\text{{{key_escaped}}} &= {value_escaped} \\\\"
        content += r"\end{align*}"
    else:
        solution_text = escape_latex(solution["solution"])
        content += r"\[" + solution_text + r"\]"

    full_latex = latex_header + content + latex_footer
    return full_latex


def escape_latex_special_chars(text: str) -> str:
    special = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
    }
    for k, v in special.items():
        text = text.replace(k, v)
    return text


_MATH_BLOCK_RE = re.compile(r"(\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\))", re.DOTALL)


def normalize_display_math(text: str) -> str:
    return re.sub(r"\$\$(.*?)\$\$", r"\\[\1\\]", text, flags=re.DOTALL)


def process_text_with_math(text: str) -> str:
    """
    Split text into math / non-math fragments.
    Never escape inside math fragments.
    """
    text = normalize_display_math(text)
    parts = _MATH_BLOCK_RE.split(text)
    out = []
    for part in parts:
        if not part:
            continue
        if _MATH_BLOCK_RE.fullmatch(part):
            out.append(part)
        else:
            out.append(escape_latex_special_chars(part))
    return "".join(out)


def strip_math_delimiters(s: str) -> str:
    s = s.strip()
    for a, b in (("$$", "$$"), ("\\[", "\\]"), ("\\(", "\\)"), ("$", "$")):
        if s.startswith(a) and s.endswith(b):
            return s[len(a):-len(b)].strip()
    return s


def prepare_latex_document(solution):
    """Prepare the full LaTeX document for a solution."""
    latex_header = r"""
        \documentclass[preview]{standalone}
        \usepackage{fontspec}
        \usepackage{amsmath, amssymb}
        \usepackage{polyglossia}
        \usepackage{icomma}
        \setdefaultlanguage{russian}
        \setmainfont{Liberation Serif}
        \newfontfamily\cyrillicfont{Liberation Serif}
        \newfontfamily\cyrillicfontsf{Liberation Sans}
        \newfontfamily\cyrillicfonttt{Liberation Mono}

        \begin{document}
        """
    latex_footer = r"""
        \end{document}
        """

    content = ""

    problem_text = process_text_with_math(solution["problem"])
    content += r"\textbf{Задание:}\\ " + problem_text + r"\\[10pt]" + "\n"

    content += r"\textbf{Решение:}\\[5pt]" + "\n"
    content += r"\begin{enumerate}" + "\n"
    for step in solution["steps"]:
        if step["type"] == "math":
            step_content = strip_math_delimiters(step["content"])
            content += r"\item $" + step_content + r"$" + "\n"
        else:
            step_content = process_text_with_math(step["content"])
            content += r"\item " + step_content + "\n"
    content += r"\end{enumerate}" + "\n"

    content += r"\textbf{Ответ:}\\[5pt]" + "\n"
    content += r"\begin{enumerate}" + "\n"
    for sol in solution["solution"]:
        if sol["type"] == "math":
            sol_content = strip_math_delimiters(sol["content"])
            content += r"\item $" + sol_content + r"$" + "\n"
        else:
            sol_content = process_text_with_math(sol["content"])
            content += r"\item " + sol_content + "\n"
    content += r"\end{enumerate}" + "\n"

    full_latex = latex_header + content + latex_footer
    return full_latex


def render_latex_to_image(latex_code):
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = os.path.join(temp_dir, "document.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_code)

        process = subprocess.Popen(
            [
                "xelatex",
                "-interaction=nonstopmode",
                "-output-directory",
                temp_dir,
                "document.tex",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"LaTeX compilation failed")
            print(f"Return code: {process.returncode}")
            print(f"stdout: {stdout.decode('utf-8')}")
            print(f"stderr: {stderr.decode('utf-8')}")
            print("LaTeX code:")
            print(latex_code)
            raise Exception("LaTeX compilation failed")

        pdf_file = os.path.join(temp_dir, "document.pdf")
        process = subprocess.Popen(
            [
                "pdftoppm",
                "-png",
                "-singlefile",
                pdf_file,
                os.path.join(temp_dir, "image"),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"PDF to image conversion failed")
            print(f"Return code: {process.returncode}")
            print(f"stdout: {stdout.decode('utf-8')}")
            print(f"stderr: {stderr.decode('utf-8')}")
            raise Exception("PDF to image conversion failed")

        image_file = os.path.join(temp_dir, "image.png")
        with open(image_file, "rb") as f:
            image_bytes = f.read()

    return image_bytes


def regenerate_latex(solution):
    header = r"""
\documentclass[preview]{standalone}
\usepackage{amsmath,amssymb}
\usepackage[T2A]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[russian]{babel}
\begin{document}
"""
    footer = r"\end{document}"
    body = []
    body.append(r"\textbf{Задание:}\\ " + process_text_with_math(solution["problem"]) + r"\\[6pt]")
    body.append(r"\textbf{Решение:}\\[-2pt]")
    body.append(r"\begin{enumerate}")
    for step in solution["steps"]:
        if step["type"] == "math":
            body.append(r"\item $" + strip_math_delimiters(step["content"]) + r"$")
        else:
            body.append(r"\item " + process_text_with_math(step["content"]))
    body.append(r"\end{enumerate}")
    body.append(r"\textbf{Ответ:}\\[-2pt]")
    body.append(r"\begin{enumerate}")
    for sol in solution["solution"]:
        if sol["type"] == "math":
            body.append(r"\item $" + strip_math_delimiters(sol["content"]) + r"$")
        else:
            body.append(r"\item " + process_text_with_math(sol["content"]))
    body.append(r"\end{enumerate}")
    return header + "\n".join(body) + footer


from bot.latex_renderer import latex_renderer, LatexCompilationError


async def send_solution_to_user(message, answer):
    if not answer:
        await message.answer(DAILY_LIMIT_EXCEEDED_MESSAGE)
        return

    if isinstance(answer, str):
        answer = json.loads(answer)

    for idx, solution in enumerate(answer.get("solutions", []), start=1):
        try:
            # Use latex_renderer instead of local functions
            img = await latex_renderer.render_solution(solution)
            file = BufferedInputFile(img, filename=f"solution_{idx}.png")
            await message.answer_photo(file, caption=f"Решение {idx}")
            await bot.send_photo(
                chat_id=ADMIN_TG_ID,
                photo=file,
                caption=f"Solution for user: {message.from_user.id}, @{message.from_user.username}",
            )
        except LatexCompilationError as e:
            print(f"LaTeX error: {str(e)}\nSTDOUT: {e.stdout[:500]}\nSTDERR: {e.stderr[:500]}")
            await message.answer(f"Проблема с LaTeX. Отправляю текст:")
            await send_text_solution_to_user(message, json.dumps({"solutions": [solution]}))
        except Exception as e:
            logging.exception(f"Unexpected rendering error: {e}")
            await send_text_solution_to_user(message, json.dumps({"solutions": [solution]}))


def prepare_plain_text_document(solution):
    """Plain text fallback reflecting new data shape."""
    out = []
    out.append("Задание:\n" + _extract_item_content(solution.get("problem", "")) + "\n")
    out.append("Решение:")
    for idx, step in enumerate(solution.get("steps", []), start=1):
        out.append(f"{idx}. {_extract_item_content(step)}")
    out.append("\nОтвет:")
    final_seq = solution.get("solution", [])
    if isinstance(final_seq, (str, dict)):
        final_seq = [final_seq]
    for item in final_seq:
        out.append(f"{_extract_item_content(item)}")
    return "\n".join(out) + "\n"


async def process_photo_message(message: Message):
    """Process photo message with parallel execution support."""
    try:
        user_id = message.from_user.id
        time = message.date
        file_name = f"{message.photo[-1].file_id}_{time}.png"
        print(f"File name: {file_name}")
        path = f"{user_id}/{file_name}"
        photo_to_save = await bot.download(message.photo[-1])
        print(f"Photo saved in memory")
        message_text, status_code, error = await save_image(
            path=path, photo_io=photo_to_save, user_id=str(user_id)
        )
        print(f"Message: {message_text}, Status code: {status_code}")
        print(f"Error: {error}")

        if status_code == 429:
            await message.answer(DAILY_LIMIT_EXCEEDED_MESSAGE)
            return None

        print(f"Status code: {status_code}")

        photo_to_answer = await bot.download(message.photo[-1])
        await message.answer(LOADING_MESSAGE)
        answer = await get_solution(
            path=path, photo_io=photo_to_answer, user_id=str(user_id)
        )
        await send_solution_to_user(message, answer)
    except Exception as e:
        logging.exception(f"Error processing photo message: {e}")
        await message.answer("Произошла ошибка при обработке фото. Попробуйте позже.")


def escape_markdown_v2(text: str) -> str:
    """
    Escape Telegram Markdown V2 characters per spec.
    """
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\r\n", "\n")
    return _MD_V2_REGEX.sub(r"\\\1", text)


def escape_markdown(text):
    """
    Escape Telegram Markdown V2 special chars.
    Accepts any type; converts to str first.
    """
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(r"([{}])".format(re.escape(escape_chars)), r"\\\1", text)


def _extract_item_content(item):
    """
    Convert a step / solution item (dict or str) to raw text for display.
    Math items: keep content as-is (Telegram will show inline).
    """
    if isinstance(item, dict):
        return item.get("content", "")
    return str(item)


async def send_text_solution_to_user(message, answer):
    MAX_MESSAGE_LENGTH = 4096

    if not answer:
        await message.answer(DAILY_LIMIT_EXCEEDED_MESSAGE)
        return
    if isinstance(answer, str):
        answer = json.loads(answer)

    solutions = answer.get("solutions", [])
    for sol in solutions:
        problem_raw = sol.get("problem", "")
        problem = escape_markdown_v2(_extract_item_content(problem_raw))

        steps_seq = sol.get("steps", [])
        step_lines = []
        for step in steps_seq:
            raw = _extract_item_content(step)
            step_lines.append(escape_markdown_v2(raw))

        final_seq = sol.get("solution", [])
        if isinstance(final_seq, (str, dict)):
            final_seq = [final_seq]

        final_lines = []
        for item in final_seq:
            raw = _extract_item_content(item)
            if "|" in raw and "\n" in raw:
                safe_table = raw.replace("`", "\\`")
                final_lines.append("```\n" + safe_table + "\n```")
            else:
                final_lines.append(escape_markdown_v2(f"{raw}"))

        message_to_send = (
                f"*Задание:* {problem}\n\n"
                f"*Решение:*\n" + "\n\n".join(step_lines) + "\n\n"
                                                            f"*Ответ:*\n" + "\n".join(final_lines)
        )

        if len(message_to_send) <= MAX_MESSAGE_LENGTH:
            await message.answer(message_to_send, parse_mode=ParseMode.MARKDOWN_V2)
            if ADMIN_TG_ID and ADMIN_TG_ID.isdigit():
                try:
                    await bot.send_message(
                        ADMIN_TG_ID,
                        f"Text solution for user {message.from_user.id} (@{message.from_user.username}):",
                    )
                    await bot.send_message(
                        chat_id=ADMIN_TG_ID,
                        text=message_to_send,
                        parse_mode=ParseMode.MARKDOWN_V2,
                    )
                except exceptions.TelegramAPIError:
                    pass
        else:
            chunks = []
            current_chunk = ""

            for line in message_to_send.split("\n"):
                if len(current_chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += ("\n" if current_chunk else "") + line

            if current_chunk:
                chunks.append(current_chunk)

            for idx, chunk in enumerate(chunks, start=1):
                header = f"*Часть {idx}/{len(chunks)}*\n\n" if len(chunks) > 1 else ""
                await message.answer(header + chunk, parse_mode=ParseMode.MARKDOWN_V2)

            if ADMIN_TG_ID and ADMIN_TG_ID.isdigit():
                try:
                    await bot.send_message(
                        ADMIN_TG_ID,
                        f"Text solution for user {message.from_user.id} (@{message.from_user.username}):",
                    )
                    for chunk in chunks:
                        await bot.send_message(
                            chat_id=ADMIN_TG_ID,
                            text=chunk,
                            parse_mode=ParseMode.MARKDOWN_V2,
                        )
                except exceptions.TelegramAPIError:
                    pass


async def process_text_message(message: Message):
    """Process text message with parallel execution support."""
    try:
        user_id = message.from_user.id
        message_text = message.text
        print(f"Message text: {message_text}")
        await message.answer(LOADING_MESSAGE)
        answer = await text_solution(message_text, user_id)
        await send_text_solution_to_user(message, answer)
    except Exception as e:
        logging.exception(f"Error processing text message: {e}")
        await message.answer("Произошла ошибка при обработке текста. Попробуйте позже.")


async def notify_all_users(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://{NETWORK}:8000{GET_ALL_USER_IDS}",
                json={"user_id": str(message.from_user.id)},
        ) as response:
            answer = await response.json()
            print(answer)
            text_message = message.text.split(" = ")[1]
            print(text_message)
            if response.status != 200:
                raise Exception(
                    f"Failed to get balance. Status code: {response.status}"
                )
            await bot.send_message(ADMIN_TG_ID, text_message)
            for user in answer["message"]:
                try:
                    await bot.send_message(user["user_id"], text_message)
                    await bot.send_message(
                        ADMIN_TG_ID, f"Message sent to user {user['user_id']}"
                    )
                except exceptions.TelegramForbiddenError:
                    print(f"User {user['user_id']} has blocked the bot. Skipping.")
                except exceptions.TelegramAPIError as e:
                    print(
                        f"Failed to send message to {user['user_id']} due to Telegram API error: {e}"
                    )
                await asyncio.sleep(0.2)


async def notify_user(message: Message):
    if message.photo:
        print("Message", message)
        text = message.caption.split("/notify_user")[1]
        user_id = text.split(" ")[1]
        text_message = message.caption.split(" = ")[1]
        await bot.send_photo(
            chat_id=user_id, photo=message.photo[-1].file_id, caption=text_message
        )
    else:
        user_id = message.text.split(" ")[1]
        text_message = message.text.split(" = ")[1]
        await bot.send_message(user_id, text_message)


async def add_subscription_limits_for_all_users(limit):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://{NETWORK}:8000{ADD_SUBSCRIPTION_LIMITS_FOR_ALL_USERS}",
                json={"user_id": ADMIN_TG_ID, "limit": limit},
        ) as response:
            answer = await response.json()
            print(answer)
            if response.status != 200:
                raise Exception(
                    f"Failed to get balance. Status code: {response.status}"
                )
            for user in answer["message"]:
                try:
                    await bot.send_message(
                        user["user_id"],
                        "Бесплатно добавлены донатные решения! Проверь свой баланс /balance",
                    )
                    await bot.send_message(
                        ADMIN_TG_ID,
                        f"Лимит решений для пользователя {user['user_id']} увеличен!",
                    )
                except exceptions.TelegramForbiddenError:
                    print(f"User {user['user_id']} has blocked the bot. Skipping.")
                except exceptions.TelegramAPIError as e:
                    print(
                        f"Failed to send message to {user['user_id']} due to Telegram API error: {e}"
                    )
                await asyncio.sleep(0.2)


async def main() -> None:
    locale = get_fluent_localization()

    # Use MemoryStorage for state management
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.outer_middleware(L10nMiddleware(locale))
    dp.pre_checkout_query.outer_middleware(L10nMiddleware(locale))
    dp.include_router(routers.router)

    # Start polling with parallel processing enabled
    await dp.start_polling(
        bot,
        polling_timeout=30,
        handle_signals=True,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
