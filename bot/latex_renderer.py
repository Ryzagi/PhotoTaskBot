# python
# file: bot/app/latex_renderer.py
import asyncio
import hashlib
import os
import re
import tempfile
from functools import lru_cache
from typing import Dict, Any, Optional

import subprocess

# Tune these
LATEX_TIMEOUT_SEC = 15
MAX_CONCURRENT_COMPILATIONS = 2


# Keep this function but don't use it in rendering (anymore - GPT rewrites all input)
def _sanitize_user_text(text: str) -> str:
    """Remove dangerous LaTeX commands (unused - GPT rewrites all input)"""
    pattern = re.compile(
        r"""\\(input|include|write|openout|read|catcode|usepackage|def|loop|repeat|csname|newwrite|immediate|let|expandafter|makeatletter)\b""",
        re.IGNORECASE,
    )
    return pattern.sub("", text)



def _hash_solution(solution: Dict[str, Any]) -> str:
    m = hashlib.sha256()
    m.update(repr(solution).encode("utf-8"))
    return m.hexdigest()

def _strip_math_delimiters(s: str) -> str:
    s = s.strip()
    for a, b in (("$$", "$$"), ("$", "$"), ("\\[", "\\]"), ("\\(", "\\)")):
        if s.startswith(a) and s.endswith(b):
            return s[len(a): -len(b)].strip()
    return s

_LATEX_HEADER = r"""
\documentclass[preview,border=5pt]{standalone}
\usepackage{amsmath, amssymb}
\usepackage{fontspec}
\usepackage{polyglossia}
\setdefaultlanguage{russian}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}
\usepackage{enumitem}
\usepackage{geometry}
\geometry{paperwidth=25cm,paperheight=20cm}
\setlength{\parindent}{0pt}
\begin{document}
"""




_LATEX_FOOTER = r"""
\end{document}
"""

def _escape_text(text: str) -> str:
    replace = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
    }
    for k, v in replace.items():
        text = text.replace(k, v)
    return text

def _validate_text_content(content: str) -> str:
    """Warn if LaTeX commands appear outside math mode"""
    # Check for bare LaTeX operators in text
    bare_operators = re.findall(r'(?<!\$)\\(ge|le|neq|cdot|times|frac)(?!\$)', content)
    if bare_operators:
        print(f"WARNING: Bare LaTeX operators found: {bare_operators}")
        print(f"Content: {content[:100]}")
    return content


_MATH_BLOCK_RE = re.compile(
    r'(\$+[^\$]+\$+|\\\([^\)]+\\\)|\\\[[^\]]+\\\])',
    re.DOTALL
)


def _validate_solution(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean GPT output"""
    # Clean all content fields
    for section in ["steps", "solution"]:
        for item in solution.get(section, []):
            if "content" in item:
                # Remove control characters
                item["content"] = re.sub(r'[\x00-\x1F\x7F]', '', item["content"])

                # Fix common GPT errors
                content = item["content"]
                # Fix \x0c + char → \char
                content = re.sub(r'\x0c([a-z])', r'\\\1', content)
                item["content"] = content

    return solution


def _adjust_table_width(text: str) -> str:
    """Reduce table column widths if total exceeds safe limits"""
    # Match tabular column specs like {|l|p{6cm}|p{6cm}|}
    match = re.search(r'\\begin\{tabular\}\{([^}]+)\}', text)
    if not match:
        return text

    cols = match.group(1)
    # Count p{Xcm} columns
    p_cols = re.findall(r'p\{(\d+(?:\.\d+)?)cm\}', cols)

    if len(p_cols) >= 2:
        total_width = sum(float(w) for w in p_cols)
        if total_width > 10:  # Too wide for A4-like preview
            # Scale down to fit
            scale = 10 / total_width
            for old_width in p_cols:
                new_width = float(old_width) * scale
                cols = cols.replace(f'p{{{old_width}cm}}', f'p{{{new_width:.1f}cm}}', 1)
            text = text.replace(match.group(1), cols)

    return text


def _process_mixed(text: str) -> str:
    """Split text into math and non-math parts, escape only non-math and non-table content"""
    # Remove control characters (including \x0c form feed)
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)

    # Check if this is table content
    if r'\begin{tabular}' in text:
        text = _adjust_table_width(text)
        return text

    # Regular text processing...
    parts = _MATH_BLOCK_RE.split(text)
    out = []
    for p in parts:
        if _MATH_BLOCK_RE.fullmatch(p):
            out.append(p)
        else:
            out.append(_escape_text(p))
    return "".join(out)


def build_latex(solution: Dict[str, Any]) -> str:
    problem = _process_mixed(solution["problem"])
    lines = [r"\textbf{Задание:}\\", problem, r"\\[6pt]"]

    lines.append(r"\textbf{Решение:}\\[-2pt]")
    _append_items(lines, solution["steps"])

    # Check if solution contains table
    has_table_in_solution = any(
        r'\begin{tabular}' in item.get("content", "")
        for item in solution["solution"]
    )

    if not has_table_in_solution:
        # Only add "Ответ:" header for non-table solutions
        lines.append(r"\textbf{Ответ:}\\[-2pt]")

    _append_items(lines, solution["solution"])

    return _LATEX_HEADER + "\n".join(lines) + _LATEX_FOOTER


def _append_items(lines: list, items: list) -> None:
    """
    Append items with smart handling:
    - Tables: rendered directly without enumerate
    - Headers (\textbf): outside enumerate with spacing
    - Math items: display math (no enumerate)
    - Text items: inside enumerate with \item
    """
    # Check if any item is a table
    has_table = any(r'\begin{tabular}' in item.get("content", "") for item in items)

    if has_table:
        # Table mode: render all content directly without enumerate
        for item in items:
            content = item["content"]
            lines.append(_process_mixed(content))
        return

    # Regular mode: smart enumerate handling
    in_enumerate = False

    for item in items:
        content = item["content"]

        # Check if this is a section header
        is_header = content.strip().startswith(r'\textbf')

        if is_header:
            # Close enumerate before header (only if open)
            if in_enumerate:
                lines.append(r"\end{enumerate}")
                in_enumerate = False

            # Add spacing before header
            lines.append(r"\vspace{6pt}")
            lines.append(content)

        elif item["type"] == "math":
            # Close enumerate before math (only if open)
            if in_enumerate:
                lines.append(r"\end{enumerate}")
                in_enumerate = False

            # Render as display math
            content = _strip_math_delimiters(content)
            lines.append(r"\[" + content + r"\]")

        else:
            # Text content - use enumerate
            if not in_enumerate:
                lines.append(r"\begin{enumerate}[leftmargin=*,nosep]")
                in_enumerate = True

            lines.append(r"\item " + _process_mixed(content))

    # Close enumerate only if it's currently open
    if in_enumerate:
        lines.append(r"\end{enumerate}")





class LatexCompilationError(Exception):
    def __init__(self, message: str, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr

class LatexRenderer:
    def __init__(self):
        self._sem = asyncio.Semaphore(MAX_CONCURRENT_COMPILATIONS)

    async def render_solution(self, solution: Dict[str, Any]) -> bytes:
        # Validate and clean GPT output
        solution = _validate_solution(solution)

        # Cache per-solution content
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
        with tempfile.TemporaryDirectory() as tmp:
            tex_path = os.path.join(tmp, "doc.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_code)

            cmd = ["xelatex", "-no-shell-escape", "-interaction=nonstopmode", "doc.tex"]
            env = {
                **os.environ,
                "HOME": "/tmp",
                "TEXMFVAR": "/tmp/texmf-var",
                "TEXMFCONFIG": "/tmp/texmf-config"
            }

            try:
                result = subprocess.run(
                    cmd,
                    cwd=tmp,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    timeout=LATEX_TIMEOUT_SEC,
                )
            except subprocess.TimeoutExpired as e:
                raise LatexCompilationError("LaTeX timeout", "", "") from e
            except subprocess.CalledProcessError as e:
                stdout = e.stdout.decode("utf-8", "ignore")
                stderr = e.stderr.decode("utf-8", "ignore")

                # Log the full error for debugging
                print(f"XeLaTeX failed with exit code {e.returncode}")
                print(f"STDOUT:\n{stdout}")
                print(f"STDERR:\n{stderr}")

                # Also log the generated LaTeX code
                print(f"Generated LaTeX:\n{latex_code[:1000]}")

                raise LatexCompilationError("LaTeX failed", stdout, stderr) from e

            pdf_path = os.path.join(tmp, "doc.pdf")
            if not os.path.exists(pdf_path):
                raise LatexCompilationError("PDF not produced")

            # Convert PDF → PNG
            png_path = os.path.join(tmp, "out.png")
            try:
                subprocess.run(
                    ["pdftoppm", "-png", "-singlefile", pdf_path, "out"],
                    cwd=tmp,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    timeout=5,
                )
            except subprocess.CalledProcessError as e:
                raise LatexCompilationError(
                    "PDF->PNG failed",
                    e.stdout.decode("utf-8", "ignore"),
                    e.stderr.decode("utf-8", "ignore"),
                ) from e
            with open(png_path, "rb") as f:
                return f.read()

# Simple in‑process cache
@lru_cache(maxsize=256)
def _get_cache(key: str) -> Optional[bytes]:
    return None  # lru_cache wrapper placeholder

_cache_store: Dict[str, bytes] = {}

def _store_cache(key: str, data: bytes) -> None:
    _cache_store[key] = data

def _get_cache(key: str) -> Optional[bytes]:  # override helper
    return _cache_store.get(key)

# Singleton instance
latex_renderer = LatexRenderer()