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

_SANITIZE_PATTERN = re.compile(
    r"""\\(input|include|write|openout|read|catcode|usepackage|def|loop|repeat|csname|newwrite|immediate)""",
    re.IGNORECASE,
)

def _sanitize_user_text(text: str) -> str:
    # Remove dangerous control sequences
    return _SANITIZE_PATTERN.sub("", text)

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
\documentclass[preview]{standalone}
\usepackage{amsmath, amssymb}
\usepackage{fontspec}
\usepackage{polyglossia}
\setdefaultlanguage{russian}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}
\usepackage{enumitem}
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
def _process_mixed(text: str) -> str:
    """Split text into math and non-math parts, escape only non-math"""
    parts = _MATH_BLOCK_RE.split(text)
    out = []
    for p in parts:
        # Check if this part is a math delimiter
        if _MATH_BLOCK_RE.fullmatch(p):
            out.append(p)  # keep math as-is
        else:
            out.append(_escape_text(p))  # escape special chars
    return "".join(out)

def build_latex(solution: Dict[str, Any]) -> str:
    problem = _process_mixed(_sanitize_user_text(solution["problem"]))
    lines = [r"\textbf{Задание:}\\", problem, r"\\[6pt]"]
    lines.append(r"\textbf{Решение:}\\[-2pt]")
    lines.append(r"\begin{enumerate}[leftmargin=*,nosep]")
    for step in solution["steps"]:
        if step["type"] == "math":
            content = _strip_math_delimiters(step["content"])
            lines.append(r"\item $" + content + r"$")
        else:
            validated = _validate_text_content(step["content"])
            lines.append(r"\item " + _process_mixed(_sanitize_user_text(validated)))
    lines.append(r"\end{enumerate}")
    lines.append(r"\textbf{Ответ:}\\[-2pt]")
    lines.append(r"\begin{enumerate}[leftmargin=*,nosep]")
    for sol in solution["solution"]:
        if sol["type"] == "math":
            content = _strip_math_delimiters(sol["content"])
            lines.append(r"\item $" + content + r"$")
        else:
            lines.append(r"\item " + _process_mixed(_sanitize_user_text(sol["content"])))
    lines.append(r"\end{enumerate}")
    return _LATEX_HEADER + "\n".join(lines) + _LATEX_FOOTER

class LatexCompilationError(Exception):
    def __init__(self, message: str, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr

class LatexRenderer:
    def __init__(self):
        self._sem = asyncio.Semaphore(MAX_CONCURRENT_COMPILATIONS)

    async def render_solution(self, solution: Dict[str, Any]) -> bytes:
        # Cache per-solution content (structure hash)
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