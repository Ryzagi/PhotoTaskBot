import inspect
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from functools import wraps
from typing import Any, Literal
from uuid import UUID

from supabase import Client, create_client

from bot.constants import DEFAULT_DAILY_LIMIT, SUB_FOLDER
from bot.schemas.user import User


def _utcnow() -> datetime:
    return datetime.now(UTC)

def _is_auth_error(exc: Exception) -> bool:
    s = str(exc)
    return (
        "JWT expired" in s
        or "PGRST301" in s
        or "Invalid JWT" in s
        or "JWSError" in s
        or "Token expired" in s
    )

def auth_retry(max_retries: int = 1):
    """
    Decorator for SupabaseService methods.
    - Ensures session.
    - Retries on auth/JWT errors (re-login before retry).
    - On final failure returns standardized dict (never raises to caller).
    """
    def outer(func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                for attempt in range(max_retries + 1):
                    self._ensure_session()
                    try:
                        return await func(self, *args, **kwargs)
                    except Exception as e:
                        if attempt < max_retries and _is_auth_error(e):
                            self._login()
                            continue
                        return {
                            "message": f"{func.__name__} failed",
                            "status_code": 400,
                            "error": str(e),
                        }
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                for attempt in range(max_retries + 1):
                    self._ensure_session()
                    try:
                        return func(self, *args, **kwargs)
                    except Exception as e:
                        if attempt < max_retries and _is_auth_error(e):
                            self._login()
                            continue
                        return {
                            "message": f"{func.__name__} failed",
                            "status_code": 400,
                            "error": str(e),
                        }
            return sync_wrapper
    return outer

class SupabaseService:
    def __init__(
        self, supabase_url: str, supabase_key: str, user_email: str, user_password: str
    ):
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name: str = "tasks"
        self._users_table = "users"
        self._users_status_table = "users_status"
        self._task_table = "tasks"
        self._email = user_email
        self._password = user_password
        self._session_expiry: datetime | None = None
        self._login()

    def _login(self):
        auth_resp = self.supabase_client.auth.sign_in_with_password(
            {"email": self._email, "password": self._password}
        )
        try:
            expires_in = auth_resp.session.expires_in
            self._session_expiry = _utcnow() + timedelta(seconds=expires_in - 30)
        except Exception:
            self._session_expiry = None

    def _ensure_session(self):
        if self._session_expiry and _utcnow() < self._session_expiry:
            return
        try:
            self.supabase_client.auth.refresh_session()
            self._session_expiry = _utcnow() + timedelta(minutes=5)
        except Exception:
            self._login()

    # TODO: Implement the async upload_file method
    @auth_retry()
    async def upload_file(self, file_path: str, file_bytes: bytes) -> dict[str, str | int]:
        supabase_path = f"{SUB_FOLDER}{file_path}"
        self.supabase_client.storage.from_(self.bucket_name).upload(
            path=supabase_path, file=file_bytes
        )
        return {"message": "File uploaded successfully", "status_code": 200}

    @auth_retry()
    async def add_new_user(self, user_data: dict) -> dict[str, str | int]:
        user_id = user_data.get("user_id")
        if await self.is_exist(user_id):
            return {"message": "User already exists", "status_code": 200}
        self.supabase_client.table(self._users_table).insert(user_data).execute()
        self.supabase_client.table(self._users_status_table).insert(
            {
                "user_id": user_id,
                "last_processing_date": None,
                "daily_limit": DEFAULT_DAILY_LIMIT,
                "subscription_limit": 0,
            }
        ).execute()
        return {"message": "User added successfully", "status_code": 200}

    @auth_retry()
    async def is_exist(self, user_id: str) -> bool:
        # Check if the user with the given user_id exists in the Supabase table
        data = (
            self.supabase_client.table(self._users_table)
            .select("user_id")
            .eq("user_id", user_id)
            .execute()
        )
        print(data)
        print(data.data)
        return len(data.data) > 0

    @auth_retry()
    async def _get_last_processing_date(self, user_id: str) -> dict[str, str | int]:
        response = (
            self.supabase_client.table(self._users_status_table)
            .select("last_processing_date")
            .eq("user_id", user_id)
            .execute()
        )
        val = response.data[0]["last_processing_date"] if response.data else None
        return {"last_processing_date": val, "status_code": 200}

    @auth_retry()
    async def proceed_processing(
        self, user_id: str
    ) -> bool | dict[str, str | int]:
        # Update the last processing date for the user with the given user_id
        try:
            balance = await self.get_current_balance(user_id)
            user_limits = balance["message"][0]
            print("User limits", user_limits)
            if user_limits["daily_limit"] == 0:
                print("Daily limit is exceeded")
                if user_limits["subscription_limit"] > 0:
                    await self._decrease_subscription_limit(
                        user_id=user_id,
                        subscription_limit=user_limits["subscription_limit"],
                    )
                    return True
                else:
                    last_processing_date = await self._get_last_processing_date(user_id)
                    if (
                        last_processing_date["last_processing_date"]
                        == date.today().isoformat()
                    ):
                        print("Last processing date is today. Daily limit is exceeded")
                        return False
                    else:
                        print("Daily limit is not exceeded")
                        await self._decrease_daily_limit(user_id)
                        return True
            else:
                print("Daily limit is not exceeded")
                # TODO Uncomment the line below
                await self._decrease_daily_limit(user_id)
                return True
        except Exception as e:
            print("Failed to proceed processing", str(e))
            return False

    @auth_retry()
    async def get_current_balance(self, user_id: str) -> dict[str, Any]:
        response = (
            self.supabase_client.table(self._users_status_table)
            .select("daily_limit", "subscription_limit", "last_processing_date")
            .eq("user_id", user_id)
            .execute()
        )
        if not response.data:
            return {"message": "User not found", "status_code": 404}
        row = response.data[0]
        if row.get("last_processing_date") != date.today().isoformat():
            row["daily_limit"] = DEFAULT_DAILY_LIMIT
        return {
            "message": [
                {
                    "daily_limit": row["daily_limit"],
                    "subscription_limit": row["subscription_limit"],
                }
            ],
            "status_code": 200,
        }

    @auth_retry()
    async def _decrease_daily_limit(self, user_id: str) -> dict[str, str | int]:
        balance = await self.get_current_balance(user_id)
        if balance.get("status_code") != 200:
            return {"message": "Balance fetch failed", "status_code": 400}
        data_list = balance.get("message")
        if not isinstance(data_list, list) or not data_list:
            return {"message": "Malformed balance data", "status_code": 400}
        current = data_list[0].get("daily_limit")
        if current is None:
            return {"message": "daily_limit missing", "status_code": 400}
        new_limit = max(0, current - 1)
        today = date.today().isoformat()
        self.supabase_client.table(self._users_status_table).update(
            {"daily_limit": new_limit, "last_processing_date": today}
        ).eq("user_id", user_id).execute()
        return {"message": "Daily limit decreased", "status_code": 200}

    @auth_retry()
    async def _decrease_subscription_limit(self, user_id: str, subscription_limit: int) -> dict[str, str | int]:
        new_limit = max(0, subscription_limit - 1)
        self.supabase_client.table(self._users_status_table).update(
            {"subscription_limit": new_limit}
        ).eq("user_id", user_id).execute()
        return {"message": "Subscription limit decreased", "status_code": 200}

    @auth_retry()
    async def update_last_processing_image_path(self, user_id: str, image_path: str) -> dict[str, str | int]:
        self.supabase_client.table(self._users_status_table).update(
            {"last_processing_image_path": image_path}
        ).eq("user_id", user_id).execute()
        return {"message": "Last processing image path updated", "status_code": 200}


    @auth_retry()
    async def insert_solution(self, user_id: str, file_path: str, solution: dict) -> dict[str, str | int]:
        self.supabase_client.table(self._task_table).insert(
            {"user_id": user_id, "file_path": file_path, "solution": solution}
        ).execute()
        return {"message": "Solution inserted successfully", "status_code": 200}


    @auth_retry()
    async def get_exist_solution(self, user_id: str, file_path: str) -> dict[str, str | int]:
        response = (
            self.supabase_client.table(self._task_table)
            .select("solution")
            .eq("user_id", user_id)
            .eq("file_path", file_path)
            .execute()
        )
        return {"message": response.data, "status_code": 200}

    @auth_retry()
    async def add_subscription_limit(self, user_id: str, subscription_limit: int = 1) -> dict[str, str | int]:
        current = (
            self.supabase_client.table(self._users_status_table)
            .select("subscription_limit")
            .eq("user_id", user_id)
            .execute()
        )
        if not current.data:
            return {"message": "User not found", "status_code": 404}
        new_limit = current.data[0]["subscription_limit"] + subscription_limit
        self.supabase_client.table(self._users_status_table).update(
            {"subscription_limit": new_limit}
        ).eq("user_id", user_id).execute()
        return {"message": "Subscription updated successfully", "status_code": 200}


    @auth_retry()
    async def get_all_user_ids(self) -> dict[str, str | int]:
        response = (
            self.supabase_client.table(self._users_table)
            .select("user_id")
            .execute()
        )
        return {"message": response.data, "status_code": 200}

    @auth_retry()
    async def add_subscription_limits_for_all_users(self, subscription_limit: int) -> dict[str, str | int]:
        users = await self.get_all_user_ids()
        if users.get("status_code") != 200:
            return {"message": "Failed to fetch users", "status_code": 400}
        for u in users["message"]:
            await self.add_subscription_limit(u["user_id"], int(subscription_limit))
        return {"message": users["message"], "status_code": 200}

    # ─────────────────────────────────────────────────────────────────────
    # New UUID-based methods, used by /v1/* routes and arq workers.
    # These do not return the legacy {"message", "status_code"} envelope —
    # they return typed values or raise. The auth_retry decorator above
    # still applies (it wraps everything to catch JWT expiry).
    # ─────────────────────────────────────────────────────────────────────

    def _row_to_user(self, row: dict) -> User:
        return User(
            id=UUID(row["id"]),
            telegram_user_id=row.get("telegram_user_id"),
            auth_user_id=UUID(row["auth_user_id"]) if row.get("auth_user_id") else None,
            language_code=row.get("language_code") or "ru",
            is_premium=bool(row.get("is_premium", False)),
            created_at=row.get("created_at") or _utcnow(),
        )

    async def find_user_by_auth_id(self, auth_user_id: str) -> User | None:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .select("*")
            .eq("auth_user_id", str(auth_user_id))
            .limit(1)
            .execute()
        )
        return self._row_to_user(resp.data[0]) if resp.data else None

    async def find_user_by_telegram_id(self, telegram_user_id: int) -> User | None:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .select("*")
            .eq("telegram_user_id", int(telegram_user_id))
            .limit(1)
            .execute()
        )
        return self._row_to_user(resp.data[0]) if resp.data else None

    async def create_user_from_auth(self, auth_user_id: UUID, email: str | None) -> User:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .insert({
                "auth_user_id": str(auth_user_id),
                "language_code": "ru",
            })
            .execute()
        )
        user = self._row_to_user(resp.data[0])
        # Seed users_status with defaults.
        self.supabase_client.table(self._users_status_table).insert({
            "user_uuid": str(user.id),
            "daily_limit": DEFAULT_DAILY_LIMIT,
            "subscription_limit": 0,
            "last_processing_date": None,
        }).execute()
        return user

    async def update_user_language(self, user_id: UUID, language_code: str) -> User:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .update({"language_code": language_code})
            .eq("id", str(user_id))
            .execute()
        )
        return self._row_to_user(resp.data[0])

    async def set_telegram_user_id(self, user_id: UUID, telegram_user_id: int) -> None:
        self._ensure_session()
        self.supabase_client.table(self._users_table).update(
            {"telegram_user_id": int(telegram_user_id)}
        ).eq("id", str(user_id)).execute()

    async def merge_users(self, survivor: UUID, victim: UUID) -> None:
        """Merge `victim` into `survivor`. See docs/architecture/02-identity-and-auth.md."""
        self._ensure_session()
        # Move tasks.
        self.supabase_client.table(self._task_table).update(
            {"user_uuid": str(survivor)}
        ).eq("user_uuid", str(victim)).execute()
        # Sum subscription_limit, take max(daily_limit).
        s_status = self.supabase_client.table(self._users_status_table) \
            .select("*").eq("user_uuid", str(survivor)).execute()
        v_status = self.supabase_client.table(self._users_status_table) \
            .select("*").eq("user_uuid", str(victim)).execute()
        if s_status.data and v_status.data:
            s, v = s_status.data[0], v_status.data[0]
            self.supabase_client.table(self._users_status_table).update({
                "subscription_limit": int(s["subscription_limit"]) + int(v["subscription_limit"]),
                "daily_limit": max(int(s["daily_limit"]), int(v["daily_limit"])),
            }).eq("user_uuid", str(survivor)).execute()
            self.supabase_client.table(self._users_status_table) \
                .delete().eq("user_uuid", str(victim)).execute()
        # Take auth_user_id from victim onto survivor.
        v_user = self.supabase_client.table(self._users_table) \
            .select("auth_user_id").eq("id", str(victim)).execute()
        if v_user.data and v_user.data[0].get("auth_user_id"):
            self.supabase_client.table(self._users_table).update({
                "auth_user_id": v_user.data[0]["auth_user_id"],
            }).eq("id", str(survivor)).execute()
        # Delete the victim user row last.
        self.supabase_client.table(self._users_table) \
            .delete().eq("id", str(victim)).execute()

    # ─── Quota (atomic, via SQL functions in migration 0002) ───

    async def rpc_reserve_solve(self, user_id: UUID) -> dict:
        self._ensure_session()
        resp = self.supabase_client.rpc("reserve_solve", {"uid": str(user_id)}).execute()
        row = resp.data[0] if resp.data else {"spent_from": None, "remaining": -1}
        return {"spent_from": row.get("spent_from"), "remaining": int(row.get("remaining", -1))}

    async def rpc_refund_solve(self, user_id: UUID, bucket: Literal["daily", "subscription"]) -> None:
        self._ensure_session()
        self.supabase_client.rpc("refund_solve", {
            "uid": str(user_id), "bucket": bucket,
        }).execute()

    async def get_or_reset_balance(self, user_id: UUID) -> dict:
        self._ensure_session()
        resp = self.supabase_client.rpc("get_or_reset_balance", {
            "uid": str(user_id), "default_daily": DEFAULT_DAILY_LIMIT,
        }).execute()
        if not resp.data:
            return {"daily_limit": DEFAULT_DAILY_LIMIT, "subscription_limit": 0}
        row = resp.data[0]
        return {
            "daily_limit": int(row.get("daily_limit", DEFAULT_DAILY_LIMIT)),
            "subscription_limit": int(row.get("subscription_limit", 0)),
        }

    # ─── Account-link codes ───

    async def insert_link_code(self, code_hash: bytes, user_id: UUID, expires_at: datetime) -> None:
        self._ensure_session()
        self.supabase_client.table("account_links").insert({
            "code_hash": code_hash.hex(),  # Supabase accepts hex for bytea
            "user_id": str(user_id),
            "expires_at": expires_at.isoformat(),
        }).execute()

    async def consume_link_code(self, code_hash: bytes) -> dict | None:
        self._ensure_session()
        resp = (
            self.supabase_client.table("account_links")
            .select("user_id, expires_at, consumed_at")
            .eq("code_hash", code_hash.hex())
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data[0]
        if row.get("consumed_at"):
            return None
        expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        if expires_at < _utcnow():
            return None
        self.supabase_client.table("account_links").update(
            {"consumed_at": _utcnow().isoformat()}
        ).eq("code_hash", code_hash.hex()).execute()
        return {"user_id": UUID(row["user_id"])}

    # ─── Tasks ───

    async def insert_task(
        self,
        task_id: UUID,
        user_id: UUID,
        status: str,
        input_kind: str,
        input_text: str | None,
        image_path: str | None,
        thumbnail_path: str | None,
        spent_from: str,
    ) -> None:
        self._ensure_session()
        self.supabase_client.table(self._task_table).insert({
            "id": str(task_id),
            "user_uuid": str(user_id),
            "status": status,
            "input_kind": input_kind,
            "input_text": input_text,
            "image_path": image_path,
            "thumbnail_path": thumbnail_path,
            "spent_from": spent_from,
        }).execute()

    async def get_task(self, task_id: UUID) -> dict | None:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._task_table)
            .select("*")
            .eq("id", str(task_id))
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data[0]
        row["user_id"] = UUID(row["user_uuid"]) if row.get("user_uuid") else None
        row["id"] = UUID(row["id"])
        for field in ("created_at", "completed_at"):
            if row.get(field):
                row[field] = datetime.fromisoformat(row[field].replace("Z", "+00:00"))
        return row

    async def mark_task_done(self, task_id: UUID, solution: dict, model_used: str) -> None:
        self._ensure_session()
        self.supabase_client.table(self._task_table).update({
            "status": "done",
            "solution": solution,
            "model_used": model_used,
            "completed_at": _utcnow().isoformat(),
        }).eq("id", str(task_id)).execute()

    async def mark_task_failed(self, task_id: UUID, error_code: str, detail: str) -> None:
        self._ensure_session()
        self.supabase_client.table(self._task_table).update({
            "status": "failed",
            "error_code": error_code,
            "error_detail": detail[:500],
            "completed_at": _utcnow().isoformat(),
        }).eq("id", str(task_id)).execute()

    async def list_tasks(self, user_id: UUID, limit: int, before: datetime | None) -> list[dict]:
        self._ensure_session()
        q = (
            self.supabase_client.table(self._task_table)
            .select("id, status, input_kind, input_text, thumbnail_path, created_at")
            .eq("user_uuid", str(user_id))
            .order("created_at", desc=True)
            .limit(limit)
        )
        if before:
            q = q.lt("created_at", before.isoformat())
        resp = q.execute()
        rows = resp.data or []
        for r in rows:
            r["id"] = UUID(r["id"])
            r["created_at"] = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        return rows

    # ─── Storage ───

    async def upload_image(self, path: str, content: bytes) -> None:
        self._ensure_session()
        self.supabase_client.storage.from_(self.bucket_name).upload(
            path=path, file=content, file_options={"upsert": "true", "content-type": "image/jpeg"},
        )

    async def download_object(self, path: str) -> bytes:
        self._ensure_session()
        return self.supabase_client.storage.from_(self.bucket_name).download(path)

    async def signed_url(self, path: str, ttl: int) -> str:
        self._ensure_session()
        result = self.supabase_client.storage.from_(self.bucket_name).create_signed_url(
            path=path, expires_in=ttl,
        )
        return result["signedURL"] if isinstance(result, dict) else result

    # ─── Devices ───

    async def upsert_user_device(
        self,
        user_id: UUID,
        platform: str,
        token: str,
        app_version: str | None,
        locale: str | None,
    ) -> UUID:
        self._ensure_session()
        existing = (
            self.supabase_client.table("user_devices")
            .select("id")
            .eq("token", token)
            .limit(1)
            .execute()
        )
        if existing.data:
            self.supabase_client.table("user_devices").update({
                "user_id": str(user_id),
                "app_version": app_version,
                "locale": locale,
                "last_seen": _utcnow().isoformat(),
            }).eq("token", token).execute()
            return UUID(existing.data[0]["id"])
        resp = self.supabase_client.table("user_devices").insert({
            "user_id": str(user_id),
            "platform": platform,
            "token": token,
            "app_version": app_version,
            "locale": locale,
        }).execute()
        return UUID(resp.data[0]["id"])

    async def delete_user_device(self, user_id: UUID, token: str) -> None:
        self._ensure_session()
        self.supabase_client.table("user_devices").delete().eq(
            "user_id", str(user_id)
        ).eq("token", token).execute()

    async def delete_user_device_by_token(self, token: str) -> None:
        self._ensure_session()
        self.supabase_client.table("user_devices").delete().eq("token", token).execute()

    async def list_user_devices(self, user_id: UUID) -> list[dict]:
        self._ensure_session()
        resp = (
            self.supabase_client.table("user_devices")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )
        rows = resp.data or []
        for r in rows:
            r["user_id"] = UUID(r["user_id"]) if r.get("user_id") else None
        return rows

    # ─── Telegram bot bridges (called from /internal/*) ───

    async def upsert_telegram_user(self, data: dict) -> None:
        """Bot's /start handler calls this. Idempotent."""
        self._ensure_session()
        telegram_user_id = int(data.get("user_id") or data.get("telegram_user_id"))
        existing = (
            self.supabase_client.table(self._users_table)
            .select("id")
            .eq("telegram_user_id", telegram_user_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return
        resp = self.supabase_client.table(self._users_table).insert({
            "telegram_user_id": telegram_user_id,
            "username": data.get("username"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "language_code": data.get("language_code") or "ru",
            "is_premium": bool(data.get("is_premium", False)),
        }).execute()
        user_id = resp.data[0]["id"]
        self.supabase_client.table(self._users_status_table).insert({
            "user_uuid": user_id,
            "daily_limit": DEFAULT_DAILY_LIMIT,
            "subscription_limit": 0,
            "last_processing_date": None,
        }).execute()

    async def insert_legacy_solution(
        self, user_id: UUID, file_path: str, solution: dict, model: str,
    ) -> None:
        """Bot's solve path stores synchronously after the answer is back."""
        self._ensure_session()
        self.supabase_client.table(self._task_table).insert({
            "user_uuid": str(user_id),
            "image_path": file_path or None,
            "input_kind": "image" if file_path else "text",
            "solution": solution,
            "model_used": model,
            "status": "done",
            "completed_at": _utcnow().isoformat(),
        }).execute()

    async def close(self) -> None:
        """Used by the arq worker shutdown hook."""
        return None
