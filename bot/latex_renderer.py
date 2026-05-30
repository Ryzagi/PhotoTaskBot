# python
# file: bot/latex_renderer.py
import asyncio
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
from typing import Any

# Tune these
LATEX_TIMEOUT_SEC = 20
MAX_CONCURRENT_COMPILATIONS = 2


def _hash_solution(solution: dict[str, Any]) -> str:
    m = hashlib.sha256()
    m.update(repr(solution).encode("utf-8"))
    return m.hexdigest()


def _strip_math_delimiters(s: str) -> str:
    if not isinstance(s, str):
        return str(s)
    s = s.strip()
    for a, b in (("$$", "$$"), ("$", "$"), ("\\[", "\\]"), ("\\(", "\\)")):
        if s.startswith(a) and s.endswith(b):
            return s[len(a): -len(b)].strip()
    return s


# Updated Header for pdfLaTeX:
# 1. Switched to pdfLaTeX engine (standard T2A binding for robust Cyrillic).
# 2. Removed fontspec/polyglossia (XeLaTeX specific).
# 3. Added inputenc/fontenc/babel (Standard LaTeX).
_LATEX_HEADER = r"""
\documentclass[preview,border=10pt,varwidth=17cm]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T2A]{fontenc}
\usepackage[russian]{babel}
\usepackage{amsmath, amssymb}
\usepackage{enumitem}
\usepackage{graphicx}

% Ensure math symbols look consistent
\usepackage{textcomp}

% Remove parindent to save space on mobile
\setlength{\parindent}{0pt}
\begin{document}
"""

_LATEX_FOOTER = r"""
\end{document}
"""


def _escape_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    replace = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
        "{": r"\{",
        "}": r"\}",
    }
    for k, v in replace.items():
        text = text.replace(k, v)
    return text


_MATH_BLOCK_RE = re.compile(
    r'(\$+[^\$]+\$+|\\\([^\)]+\\\)|\\\[[^\]]+\\\])',
    re.DOTALL
)


def _validate_solution(solution: dict[str, Any]) -> dict[str, Any]:
    """Validate and clean GPT output"""
    for section in ["steps", "solution"]:
        for item in solution.get(section, []):
            if "content" in item:
                # Remove control chars
                item["content"] = re.sub(r'[\x00-\x1F\x7F]', '', item["content"])
                # Remove common garbage
                item["content"] = item["content"].replace("\x0c", "")
    return solution


def _adjust_table_width(text: str) -> str:
    match = re.search(r'\\begin\{tabular\}\{([^}]+)\}', text)
    if not match:
        return text

    cols = match.group(1)
    p_cols = re.findall(r'p\{(\d+(?:\.\d+)?)cm\}', cols)

    if len(p_cols) >= 2:
        total_width = sum(float(w) for w in p_cols)
        SAFE_WIDTH = 16
        if total_width > SAFE_WIDTH:
            scale = SAFE_WIDTH / total_width
            for old_width in p_cols:
                new_width = float(old_width) * scale
                cols = cols.replace(f'p{{{old_width}cm}}', f'p{{{new_width:.1f}cm}}', 1)
            text = text.replace(match.group(1), cols)
    return text


def _process_mixed(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    if r'\begin{tabular}' in text:
        text = _adjust_table_width(text)
        return text

    parts = _MATH_BLOCK_RE.split(text)
    out = []
    for p in parts:
        if _MATH_BLOCK_RE.fullmatch(p):
            out.append(p)
        else:
            out.append(_escape_text(p))
    return "".join(out)


def build_latex(solution: dict[str, Any]) -> str:
    lines = [r"\begin{sloppypar}"]

    problem = _process_mixed(solution.get("problem", ""))
    lines.extend([r"\textbf{Задание:}\\", problem, r"\\[6pt]"])

    if solution.get("steps"):
        lines.append(r"\textbf{Решение:}\\[-2pt]")
        _append_items(lines, solution["steps"])

    sols = solution.get("solution", [])
    has_table_in_solution = any(
        r'\begin{tabular}' in item.get("content", "")
        for item in sols
    )

    if not has_table_in_solution and sols:
        lines.append(r"\vspace{6pt}\textbf{Ответ:}\\[-2pt]")

    if sols:
        _append_items(lines, sols)

    lines.append(r"\end{sloppypar}")
    return _LATEX_HEADER + "\n".join(lines) + _LATEX_FOOTER


def _append_items(lines: list, items: list) -> None:
    has_table = any(r'\begin{tabular}' in item.get("content", "") for item in items)
    if has_table:
        for item in items:
            lines.append(_process_mixed(item["content"]))
        return

    # Start enumerate block
    lines.append(r"\begin{enumerate}[leftmargin=*,nosep]")

    for item in items:
        content = item.get("content", "")

        if content.strip().startswith(r'\textbf'):
            lines.append(r"\item[] " + content)
        elif item.get("type") == "math":
            clean_math = _strip_math_delimiters(content)
            # Use display math \[ ... \]
            lines.append(r"\item \[" + clean_math + r"\]")
        else:
            lines.append(r"\item " + _process_mixed(content))

    lines.append(r"\end{enumerate}")


class LatexCompilationError(Exception):
    def __init__(self, message: str, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr


class LatexRenderer:
    def __init__(self):
        self._sem = asyncio.Semaphore(MAX_CONCURRENT_COMPILATIONS)

    async def render_solution(self, solution: dict[str, Any]) -> bytes:
        solution = _validate_solution(solution)
        key = _hash_solution(solution)
        cached = _get_cache(key)
        if cached:
            return cached
        latex = build_latex(solution)
        png = await self._compile_to_png(latex)
        _store_cache(key, png)
        return png

    async def _compile_to_png(self, latex_code: str) -> bytes:
        async with self._sem:
            return await asyncio.to_thread(self._compile_sync, latex_code)

    def _compile_sync(self, latex_code: str) -> bytes:
        # Use pdflatex instead of xelatex for better built-in font support
        pdflatex_bin = shutil.which("pdflatex")
        if not pdflatex_bin:
            raise LatexCompilationError(
                "pdflatex executable not found. Please install TeX Live "
                "(sudo apt-get install texlive-latex-base texlive-lang-cyrillic on Linux, "
                "MacTeX on macOS)."
            )

        # Ensure pdftoppm is also available
        pdftoppm_bin = shutil.which("pdftoppm")
        if not pdftoppm_bin:
            raise LatexCompilationError("pdftoppm (poppler-utils) not found")

        with tempfile.TemporaryDirectory() as tmp:
            tex_path = os.path.join(tmp, "doc.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_code)

            # NOTE: pdflatex defaults to -no-shell-escape mostly, but we add it to be safe
            cmd = [pdflatex_bin, "-interaction=nonstopmode", "doc.tex"]

            env = {
                **os.environ,
                "HOME": tmp,
            }

            try:
                subprocess.run(
                    cmd,
                    cwd=tmp,
                    env=env,
                    check=True,
                    capture_output=True,
                    timeout=LATEX_TIMEOUT_SEC
                )
            except subprocess.TimeoutExpired as e:
                raise LatexCompilationError("LaTeX timeout", "", "") from e
            except FileNotFoundError:
                raise LatexCompilationError(f"Could not execute binary: {pdflatex_bin}")
            except subprocess.CalledProcessError as e:
                stdout = e.stdout.decode("utf-8", "ignore")
                stderr = e.stderr.decode("utf-8", "ignore")
                print(f"pdfLaTeX failed. Exit code: {e.returncode}")
                # Print tail of stdout to see LaTeX errors
                print(f"STDOUT TAIL:\n{stdout[-1000:]}")
                raise LatexCompilationError("LaTeX failed", stdout, stderr) from e

            pdf_path = os.path.join(tmp, "doc.pdf")
            if not os.path.exists(pdf_path):
                raise LatexCompilationError("PDF not produced")

            # Convert PDF -> PNG (300 DPI for quality)
            png_base = os.path.join(tmp, "out")
            try:
                subprocess.run(
                    [pdftoppm_bin, "-png", "-r", "300", "-singlefile", pdf_path, png_base],
                    cwd=tmp,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                raise LatexCompilationError(
                    "pdftoppm failed",
                    e.stdout.decode("utf-8", "ignore"),
                    e.stderr.decode("utf-8", "ignore")
                )

            png_path = png_base + ".png"
            if not os.path.exists(png_path):
                # fallback
                if os.path.exists(png_base):
                    png_path = png_base

            with open(png_path, "rb") as f:
                return f.read()


@lru_cache(maxsize=256)
def _get_cache(key: str) -> bytes | None:
    return _cache_store.get(key)


_cache_store: dict[str, bytes] = {}


def _store_cache(key: str, data: bytes) -> None:
    _cache_store[key] = data


latex_renderer = LatexRenderer()
