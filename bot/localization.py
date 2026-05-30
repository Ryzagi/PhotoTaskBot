from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from fluent.runtime import FluentLocalization


# Middleware to add localization to the data dictionary
class L10nMiddleware(BaseMiddleware):
    def __init__(self, locale: FluentLocalization):
        self.locale = locale

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        data["l10n"] = self.locale
        return await handler(event, data)
