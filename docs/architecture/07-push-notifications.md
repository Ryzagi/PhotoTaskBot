# 07 — Push Notifications

We use Apple Push Notification service (APNs) directly for iOS and Firebase Cloud Messaging HTTP v1 for Android. We do **not** use Firebase as an APNs proxy.

## Why direct APNs, not Firebase-as-proxy

Many tutorials show FCM → APNs. It works, and it's one API to integrate. The downsides:

- Two systems can drop a delivery; debugging "did Google fail or did Apple fail?" is painful.
- Firebase adds a Google dependency (and a Firebase project, billing, etc.) to the iOS path for no benefit.
- APNs HTTP/2 with a `.p8` token is ~150 lines via `aioapns`.

So: `aioapns` for iOS, `firebase-admin` for Android. Backend wraps both behind a `PushService.send(user_id, topic, payload)` API.

## Token lifecycle

```
Client                                Server
───────                               ───────
App launches → grant permission → token T  ──►  POST /v1/devices
                                                  ├─ upsert user_devices(user_id, platform, T)
                                                  └─ 200

User backgrounds the app

Notification sent to T              <── PushService.send

Token T invalidated by Apple/Google (user uninstalls)
                                  Push send returns 410 Unregistered  ──► DELETE user_devices WHERE token = T

App reopens, OS rotates token to T'  ──►  POST /v1/devices  (new row; the dead T' is cleaned up by 410 next attempt)

User signs out  ──►  DELETE /v1/devices/{T}
```

Critical: a user can have **multiple devices** — phone + tablet, or an old phone they forgot about. Send to all rows for the user, not just the latest. The 410 handler cleans up the dead ones.

## Wire format

### APNs payload (iOS)

```json
{
  "aps": {
    "alert": {
      "title": "Solution ready",
      "body": "Найди производную f(x) = ..."
    },
    "sound": "default",
    "badge": 1,
    "mutable-content": 1,
    "thread-id": "task.completed"
  },
  "task_id": "0e7c…",
  "thumbnail_url": "https://…signed…"
}
```

`mutable-content: 1` enables the `NotificationServiceExtension` on iOS to download the thumbnail and attach it (rich push). `thread-id` groups notifications.

### FCM payload (Android)

```json
{
  "message": {
    "token": "<device token>",
    "notification": {
      "title": "Solution ready",
      "body": "Найди производную f(x) = ..."
    },
    "data": {
      "task_id": "0e7c…",
      "thumbnail_url": "https://…signed…",
      "topic": "task.completed"
    },
    "android": {
      "priority": "high",
      "notification": {
        "channel_id": "task_updates",
        "image": "https://…signed…"
      }
    }
  }
}
```

Android puts the image right in the notification — no extension needed.

## Topics

| Topic | When | Payload extra |
|---|---|---|
| `task.completed` | Worker finishes successfully | `task_id`, `thumbnail_url`, problem preview |
| `task.failed` | Both solvers failed | `task_id`, `error_code` |
| `daily.reset` | Daily limit just reset (optional, opt-in) | `daily_limit` |
| `balance.added` | Telegram payment recorded | `added`, `total` |
| `app.broadcast` | Admin broadcast | `text`, `cta_url?` |

## User-controlled muting

Settings → Notifications:

- [ ] Solutions ready (`task.completed`, `task.failed`)
- [ ] Daily limit refilled (`daily.reset`)
- [ ] Promotions and product news (`app.broadcast`)

Stored as bit-flags on `user_devices.notification_prefs SMALLINT` (or a separate `user_notification_prefs` table). Backend checks before sending. Apple/Google do the per-system mute on top.

## Localization

The notification body is localized server-side, using the `locale` we stored on the `user_devices` row at registration. The same string table is shared with the apps (`strings.xml` / `Localizable.strings`).

```python
title = i18n.t("push.task_completed.title", locale=device.locale)
body = i18n.t("push.task_completed.body", locale=device.locale, problem=preview)
```

Fall back to Russian if locale missing or unsupported.

## Implementation sketch

```python
# bot/push/service.py
class PushService:
    def __init__(self, apns: APNs, fcm: FCMClient, db: DB):
        self.apns, self.fcm, self.db = apns, fcm, db

    async def send(self, user_id: UUID, topic: str, payload: dict):
        devices = await self.db.user_devices.list_for_user(user_id)
        await asyncio.gather(*[self._send_one(d, topic, payload) for d in devices])

    async def _send_one(self, device, topic, payload):
        try:
            if device.platform == "ios":
                await self.apns.send(device.token, build_apns(topic, payload, device.locale))
            else:
                await self.fcm.send(device.token, build_fcm(topic, payload, device.locale))
        except UnregisteredError:
            await self.db.user_devices.delete_by_token(device.token)
```

## Secrets

- **APNs**: `.p8` key file, key ID, team ID, bundle ID. All in env vars (`APNS_AUTH_KEY_BASE64`, `APNS_KEY_ID`, `APNS_TEAM_ID`, `APNS_BUNDLE_ID`). Use the JWT-token-based auth, not the legacy certificate.
- **FCM**: service account JSON. `FCM_SERVICE_ACCOUNT_JSON_BASE64`.

Rotation: documented in [`../runbooks/rotate-supabase-keys.md`](../runbooks/rotate-supabase-keys.md) (with sections for APNs/FCM too).

## Observability

Every push send gets logged with `{user_id, device_id, topic, platform, status, latency_ms, apns_id_or_fcm_id}`. Dashboard panels:

- Send success rate per platform (target >99%).
- 410 cleanup rate (informational; spikes = mass uninstalls).
- P95 send latency (target <500ms).

## What not to do

- **Don't send raw solution JSON in the push payload.** It's >4KB easily, exceeding APNs/FCM limits. Send `task_id` and let the client fetch.
- **Don't store the user's image bytes in the push.** Same reason, plus privacy.
- **Don't use silent pushes to drive UI state.** They're best-effort; the foreground polling loop is the source of truth.
- **Don't share device tokens across users.** Even if Apple/Google would technically deliver, you'd be leaking notifications to whoever signed in last.
