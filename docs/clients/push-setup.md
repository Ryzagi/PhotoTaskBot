# Push notifications setup (FCM + APNs)

The push code path is complete on both the backend and the Android client. It is
**inert until you supply provider credentials** — the app degrades safely
(`SignInViewModel.registerFcm()` is wrapped in `runCatching`, so a missing
Firebase config just means no token is registered and no pushes arrive).

## How it works (already wired)

- **Backend.** `POST /v1/tasks` enqueues an arq job when `REDIS_URL` is set
  (otherwise it solves inline and no push is needed). On completion/failure the
  worker (`bot/tasks/jobs.py`) calls `PushService.send(user_id, topic, payload)`
  (`bot/push/service.py`), which fans out to APNs (iOS) and FCM (Android) for
  every row in `user_devices`, and deletes tokens that come back `Unregistered`/410.
- **Android.** `FcmService` registers the token on refresh and shows the
  notification; `SignInViewModel` registers the current token after sign-in and on
  cold start; channels are created in `App.kt`; the manifest declares the service,
  `POST_NOTIFICATIONS`, and the `pandasolve://` deep-link filter; `MainActivity`
  requests the notification permission on Android 13+; and the nav graph maps
  `pandasolve://task/{id}` to the task screen, so tapping a notification opens it.

## Android: enable FCM

1. Firebase console → create/choose a project → add an Android app for **each**
   applicationId: `com.pandasolve.app.dev` (debug) and `com.pandasolve.app` (release).
2. Download `google-services.json` into `clients/android/app/` (already gitignored).
3. Uncomment the `google-services` plugin in **both** Gradle files (alias is already
   declared in `gradle/libs.versions.toml`):
   - `build.gradle.kts` → `alias(libs.plugins.google.services) apply false`
   - `app/build.gradle.kts` → `alias(libs.plugins.google.services)`
4. Rebuild. `FirebaseMessaging.getInstance().token` now resolves and the token is
   POSTed to `/v1/devices` on sign-in.

## Backend: FCM HTTP v1 credentials

`FCMClient`/`FCMConfig.from_env()` need a Google service account with the
**Firebase Cloud Messaging API** enabled. Set the env vars referenced by
`bot/push/fcm.py` (service-account JSON path or inline creds + project id). Without
them `FCMConfig.from_env()` raises at worker startup, so only configure once the
project exists.

## iOS: APNs

`APNsClient`/`APNsConfig.from_env()` use an APNs **`.p8`** token key. Provide the
key file, key id, team id, and bundle id via env (see `bot/push/apns.py`). `.p8`
files are gitignored.

## Verify end to end

1. Run the backend with `REDIS_URL` set and `make worker` running.
2. Sign in on a device with `google-services.json` in place; confirm a row appears
   in `user_devices`.
3. Submit a task; when the worker finishes, a "Решение готово" notification should
   arrive and tapping it should open the task detail.
