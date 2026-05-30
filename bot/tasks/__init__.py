"""Async solver workers (arq).

Run with:
    arq bot.tasks.worker.WorkerSettings

The HTTP layer enqueues; workers run on the same Redis instance used for rate
limiting and idempotency keys.
"""
