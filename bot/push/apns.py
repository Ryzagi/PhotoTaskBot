"""APNs HTTP/2 client wrapper.

We use aioapns with a .p8 token (not legacy certificates). Production endpoint
is api.push.apple.com; sandbox endpoint is api.sandbox.push.apple.com.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass


class UnregisteredError(Exception):
    """APNs returned 410: device token is no longer valid."""


@dataclass
class APNsConfig:
    key_base64: str
    key_id: str
    team_id: str
    bundle_id: str
    use_sandbox: bool = False

    @classmethod
    def from_env(cls) -> APNsConfig:
        return cls(
            key_base64=os.environ["APNS_AUTH_KEY_BASE64"],
            key_id=os.environ["APNS_KEY_ID"],
            team_id=os.environ["APNS_TEAM_ID"],
            bundle_id=os.environ["APNS_BUNDLE_ID"],
            use_sandbox=os.environ.get("APNS_SANDBOX", "false").lower() == "true",
        )


class APNsClient:
    def __init__(self, config: APNsConfig):
        self.config = config
        self._client = None

    async def _client_or_init(self):
        if self._client is None:
            from aioapns import APNs  # type: ignore[import-not-found]

            key_bytes = base64.b64decode(self.config.key_base64)
            self._client = APNs(
                key=key_bytes,
                key_id=self.config.key_id,
                team_id=self.config.team_id,
                topic=self.config.bundle_id,
                use_sandbox=self.config.use_sandbox,
            )
        return self._client

    async def send(self, token: str, payload: dict) -> None:
        from aioapns import NotificationRequest  # type: ignore[import-not-found]

        client = await self._client_or_init()
        req = NotificationRequest(device_token=token, message=payload)
        result = await client.send_notification(req)
        if result.status == "410":
            raise UnregisteredError(token)
        if not result.is_successful:
            raise RuntimeError(f"APNs failed: {result.status} {result.description}")
