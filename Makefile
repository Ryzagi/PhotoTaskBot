.PHONY: install test lint openapi migrate run worker bot

install:
	pip install -e .
	pip install pytest ruff mypy

test:
	PYTHONPATH=. pytest tests/unit -v

lint:
	ruff check bot tests scripts --exclude bot/app/tg_app__.py

openapi:
	PYTHONPATH=. python -m scripts.gen_openapi

migrate:
	PYTHONPATH=. python -m bot.migrate up

run:
	uvicorn bot.app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	arq bot.tasks.worker.WorkerSettings

bot:
	python bot/app/tg_app.py
