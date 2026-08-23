"""FCM HTTP v1 client wrapper.

We use the firebase-admin SDK for v1 messaging. The legacy server-key API is
deprecated and being shut down.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass


class UnregisteredError(Exception):
    """FCM returned that the token is unregistered."""


@dataclass
class FCMConfig:
    service_account_json: dict

    @classmethod
    def from_env(cls) -> FCMConfig:
        encoded = os.environ["FCM_SERVICE_ACCOUNT_JSON_BASE64"]
        return cls(service_account_json=json.loads(base64.b64decode(encoded)))


class FCMClient:
    def __init__(self, config: FCMConfig):
        self.config = config
        self._initialized = False

    def _ensure(self) -> None:
        if self._initialized:
            return
        import firebase_admin  # type: ignore[import-not-found]
        from firebase_admin import credentials  # type: ignore[import-not-found]

        cred = credentials.Certificate(self.config.service_account_json)
        firebase_admin.initialize_app(cred)
        self._initialized = True

    async def send(self, token: str, message: dict) -> None:
        import asyncio

        from firebase_admin import messaging  # type: ignore[import-not-found]
        from firebase_admin.exceptions import FirebaseError  # type: ignore[import-not-found]

        self._ensure()

        def _do() -> None:
            try:
                messaging.send(messaging.Message(token=token, **message))
            except messaging.UnregisteredError as e:
                raise UnregisteredError(token) from e
            except FirebaseError as e:
                raise RuntimeError(f"FCM failed: {e}") from e

        await asyncio.to_thread(_do)
