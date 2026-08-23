"""Business-logic service layer.

The HTTP routers (bot/api/v1, bot/api/internal) and queue workers (bot/tasks)
call into these. Services depend on the DB adapter (bot/supabase_service)
and on third-party clients (solvers, push). They never know about FastAPI
request objects or HTTP status codes.

Wire-up happens in bot/app/main.py.
"""
