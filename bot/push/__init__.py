"""Push notification delivery.

Two transports, both spoken directly:
- APNs HTTP/2 with a .p8 token (iOS)
- FCM HTTP v1 (Android)

The shared API is PushService.send(user_id, topic, payload). It fans out to
every device row for the user, cleans up 410/Unregistered tokens, and logs
delivery outcomes.
"""

from bot.push.service import PushService  # noqa: F401
