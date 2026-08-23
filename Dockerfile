# Lean image for the FastAPI app + arq worker (serves /v1, /internal, legacy).
# NO TeX Live here — LaTeX→PNG rendering is only used by the Telegram bot
# (bot/latex_renderer.py, imported solely by bot/app/tg_app.py). The bot builds
# from Dockerfile.bot instead. Keeping this image apt-free means the API/worker
# build never touches Debian repos (avoids mirror/signature/disk failures) and
# is a couple GB smaller.

FROM python:3.11-slim-bookworm

WORKDIR /app
COPY . /app
RUN pip install .

ENV PYTHONPATH=/app

# /v1/* (mobile) + /internal/* (bot) + legacy /tasker/api/*
CMD ["sh", "-c", "uvicorn bot.app.main:app --host 0.0.0.0 --port 8000"]
