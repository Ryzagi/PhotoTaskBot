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


def _derive_title(solution: dict) -> str | None:
    """Short label for the task. Prefer the model's `title`; else fall back to the
    first problem statement, trimmed. Keeps photo tasks from showing just '(фото)'."""
    if not isinstance(solution, dict):
        return None
    title = (solution.get("title") or "").strip()
    if title:
        return title[:120]
    problems = solution.get("solutions") or []
    if problems and isinstance(problems[0], dict):
        first = (problems[0].get("problem") or "").strip()
        if first:
            return first[:120]
    return None


def _compute_streak(timestamps: list) -> int:
    """Consecutive days (ending today, or yesterday if nothing yet today) that
    have at least one solved task. `timestamps` are ISO strings or datetimes."""
    days: set[date] = set()
    for ts in timestamps:
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        days.add(ts.astimezone(UTC).date())
    if not days:
        return 0
    today = _utcnow().date()
    if today in days:
        cursor = today
    elif (today - timedelta(days=1)) in days:
        cursor = today - timedelta(days=1)
    else:
        return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak

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
    # Mobile (/v1/*) methods. The domain key is `user_id text` — the same
    # column the bot uses (Telegram id for bot users; the Supabase auth UUID,
    # stored as text, for mobile users). These return typed values, not the
    # legacy {"message", "status_code"} envelope.
    # ─────────────────────────────────────────────────────────────────────

    def _row_to_user(self, row: dict) -> User:
        uid = str(row["user_id"]) if row.get("user_id") is not None else None
        telegram = int(uid) if uid and uid.isdigit() else None
        return User(
            id=uid,
            telegram_user_id=telegram,
            auth_user_id=row.get("auth_user_id"),
            language_code=row.get("language_code") or "ru",
            display_name=row.get("display_name"),
            is_premium=str(row.get("is_premium")).lower() in ("true", "1", "t"),
            created_at=row.get("created_at") or _utcnow(),
        )

    async def find_user_by_auth_id(self, auth_user_id: str) -> User | None:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .select("*")
            .eq("auth_user_id", auth_user_id)
            .limit(1)
            .execute()
        )
        return self._row_to_user(resp.data[0]) if resp.data else None

    async def find_user_by_telegram_id(self, telegram_user_id: int) -> User | None:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .select("*")
            .eq("user_id", str(telegram_user_id))
            .limit(1)
            .execute()
        )
        return self._row_to_user(resp.data[0]) if resp.data else None

    async def create_user_from_auth(self, auth_user_id: str, email: str | None) -> User:
        """Mobile signup: user_id = the auth UUID (text). Seeds users_status."""
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .insert({
                "user_id": str(auth_user_id),
                "auth_user_id": str(auth_user_id),
                "username": (email or "").split("@")[0] or None,
                "language_code": "ru",
            })
            .execute()
        )
        user = self._row_to_user(resp.data[0])
        self.supabase_client.table(self._users_status_table).insert({
            "user_id": str(user.id),
            "daily_limit": DEFAULT_DAILY_LIMIT,
            "subscription_limit": 0,
            "last_processing_date": None,
        }).execute()
        return user

    async def update_user_language(self, user_id: str, language_code: str) -> User:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .update({"language_code": language_code})
            .eq("user_id", user_id)
            .execute()
        )
        return self._row_to_user(resp.data[0])

    async def update_user_display_name(self, user_id: str, display_name: str) -> User:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_table)
            .update({"display_name": display_name})
            .eq("user_id", user_id)
            .execute()
        )
        return self._row_to_user(resp.data[0])

    async def set_telegram_user_id(self, user_id: str, telegram_user_id: int) -> None:
        # In the text-key model "linking" is a merge; this is a no-op kept for API
        # compatibility with the link flow.
        return None

    async def merge_users(self, survivor: str, victim: str) -> None:
        """Reassign the victim's rows to the survivor user_id, then delete it.
        survivor/victim are user_id text values."""
        self._ensure_session()
        self.supabase_client.table(self._task_table).update(
            {"user_id": survivor}
        ).eq("user_id", victim).execute()
        # fold balances
        s = self.supabase_client.table(self._users_status_table).select("*").eq("user_id", survivor).execute()
        v = self.supabase_client.table(self._users_status_table).select("*").eq("user_id", victim).execute()
        if s.data and v.data:
            self.supabase_client.table(self._users_status_table).update({
                "subscription_limit": int(s.data[0].get("subscription_limit") or 0) + int(v.data[0].get("subscription_limit") or 0),
                "daily_limit": max(int(s.data[0].get("daily_limit") or 0), int(v.data[0].get("daily_limit") or 0)),
            }).eq("user_id", survivor).execute()
            self.supabase_client.table(self._users_status_table).delete().eq("user_id", victim).execute()
        # carry auth_user_id onto the survivor
        v_user = self.supabase_client.table(self._users_table).select("auth_user_id").eq("user_id", victim).execute()
        if v_user.data and v_user.data[0].get("auth_user_id"):
            self.supabase_client.table(self._users_table).update(
                {"auth_user_id": v_user.data[0]["auth_user_id"]}
            ).eq("user_id", survivor).execute()
        self.supabase_client.table(self._users_table).delete().eq("user_id", victim).execute()

    # ─── Quota (Python, keyed on user_id text — mirrors the bot's logic) ───

    async def get_or_reset_balance(self, user_id: str) -> dict:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._users_status_table)
            .select("daily_limit, subscription_limit, last_processing_date")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return {"daily_limit": DEFAULT_DAILY_LIMIT, "subscription_limit": 0}
        row = resp.data[0]
        daily = int(row.get("daily_limit") or 0)
        sub = int(row.get("subscription_limit") or 0)
        today = date.today().isoformat()
        if row.get("last_processing_date") != today:
            daily = DEFAULT_DAILY_LIMIT
            self.supabase_client.table(self._users_status_table).update(
                {"daily_limit": daily, "last_processing_date": today}
            ).eq("user_id", user_id).execute()
        return {"daily_limit": daily, "subscription_limit": sub}

    async def rpc_reserve_solve(self, user_id: str) -> dict:
        self._ensure_session()
        bal = await self.get_or_reset_balance(user_id)
        if bal["daily_limit"] > 0:
            self.supabase_client.table(self._users_status_table).update(
                {"daily_limit": bal["daily_limit"] - 1, "last_processing_date": date.today().isoformat()}
            ).eq("user_id", user_id).execute()
            return {"spent_from": "daily", "remaining": bal["daily_limit"] - 1}
        if bal["subscription_limit"] > 0:
            self.supabase_client.table(self._users_status_table).update(
                {"subscription_limit": bal["subscription_limit"] - 1}
            ).eq("user_id", user_id).execute()
            return {"spent_from": "subscription", "remaining": bal["subscription_limit"] - 1}
        return {"spent_from": None, "remaining": -1}

    async def rpc_refund_solve(self, user_id: str, bucket: Literal["daily", "subscription"]) -> None:
        self._ensure_session()
        col = "daily_limit" if bucket == "daily" else "subscription_limit"
        cur = (
            self.supabase_client.table(self._users_status_table)
            .select(col).eq("user_id", user_id).limit(1).execute()
        )
        if cur.data:
            self.supabase_client.table(self._users_status_table).update(
                {col: int(cur.data[0].get(col) or 0) + 1}
            ).eq("user_id", user_id).execute()

    # ─── Account-link codes ───

    async def insert_link_code(self, code_hash: bytes, user_id: str, expires_at: datetime) -> None:
        self._ensure_session()
        self.supabase_client.table("account_links").insert({
            "code_hash": code_hash.hex(),
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
        return {"user_id": str(row["user_id"])}

    # ─── Tasks ───

    async def insert_task(
        self,
        user_id: str,
        status: str,
        input_kind: str,
        input_text: str | None,
        image_path: str | None,
        thumbnail_path: str | None,
    ) -> str:
        """Insert a task (bigint id is DB-generated). Returns the new id as str."""
        self._ensure_session()
        resp = self.supabase_client.table(self._task_table).insert({
            "user_id": user_id,
            "status": status,
            "input_kind": input_kind,
            "input_text": input_text,
            "file_path": image_path,
            "image_path": image_path,
            "thumbnail_path": thumbnail_path,
        }).execute()
        return str(resp.data[0]["id"])

    async def get_task(self, task_id: str) -> dict | None:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._task_table)
            .select("*")
            .eq("id", task_id)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data[0]
        row["id"] = str(row["id"])
        row["user_id"] = str(row["user_id"]) if row.get("user_id") is not None else None
        for field in ("created_at", "completed_at"):
            if row.get(field):
                row[field] = datetime.fromisoformat(row[field].replace("Z", "+00:00"))
        return row

    async def mark_task_done(self, task_id: str, solution: dict, model_used: str) -> None:
        self._ensure_session()
        self.supabase_client.table(self._task_table).update({
            "status": "done",
            "solution": solution,
            "title": _derive_title(solution),
            "model_used": model_used,
            "completed_at": _utcnow().isoformat(),
        }).eq("id", task_id).execute()

    async def mark_task_failed(self, task_id: str, error_code: str, detail: str) -> None:
        self._ensure_session()
        self.supabase_client.table(self._task_table).update({
            "status": "failed",
            "error_code": error_code,
            "completed_at": _utcnow().isoformat(),
        }).eq("id", task_id).execute()

    async def list_tasks(
        self, user_id: str, limit: int, before: datetime | None,
        album_id: str | None = None, q: str | None = None,
    ) -> list[dict]:
        self._ensure_session()
        query = (
            self.supabase_client.table(self._task_table)
            .select("id, status, input_kind, input_text, title, thumbnail_path, file_path, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if album_id:
            query = query.eq("album_id", album_id)
        if q:
            # case-insensitive match on title OR input_text; strip PostgREST-special chars
            term = q.strip().replace("%", "").replace(",", " ").replace("*", "")
            if term:
                query = query.or_(f"title.ilike.%{term}%,input_text.ilike.%{term}%")
        if before:
            query = query.lt("created_at", before.isoformat())
        resp = query.execute()
        rows = resp.data or []
        for r in rows:
            r["id"] = str(r["id"])
            if not r.get("input_kind"):
                r["input_kind"] = "text" if not r.get("file_path") else "image"
            if not r.get("status"):
                r["status"] = "done"
            r["created_at"] = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        return rows

    async def get_user_stats(self, user_id: str) -> dict:
        """Total solved count + current daily streak for the Home/Profile screens."""
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._task_table)
            .select("created_at", count="exact")
            .eq("user_id", user_id)
            .eq("status", "done")
            .order("created_at", desc=True)
            .limit(400)
            .execute()
        )
        rows = resp.data or []
        solved_count = resp.count if resp.count is not None else len(rows)
        streak = _compute_streak([r["created_at"] for r in rows])
        return {"solved_count": solved_count, "streak": streak}

    # ─── Albums ───

    async def list_albums(self, user_id: str) -> list[dict]:
        self._ensure_session()
        rows = (
            self.supabase_client.table("albums")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        ).data or []
        # task counts + last-activity per album, aggregated in Python
        tasks = (
            self.supabase_client.table(self._task_table)
            .select("album_id, created_at")
            .eq("user_id", user_id)
            .execute()
        ).data or []
        counts: dict[str, int] = {}
        last: dict[str, str] = {}
        for t in tasks:
            aid = t.get("album_id")
            if not aid:
                continue
            counts[aid] = counts.get(aid, 0) + 1
            ts = t.get("created_at")
            if ts and (aid not in last or ts > last[aid]):
                last[aid] = ts
        out = []
        for r in rows:
            aid = r["id"]
            r["task_count"] = counts.get(aid, 0)
            r["last_updated"] = last.get(aid) or r["updated_at"]
            out.append(r)
        return out

    async def create_album(self, user_id: str, name: str, emoji: str | None, color: str | None) -> dict:
        self._ensure_session()
        resp = self.supabase_client.table("albums").insert({
            "user_id": user_id, "name": name, "emoji": emoji, "color": color,
        }).execute()
        row = resp.data[0]
        row["task_count"] = 0
        row["last_updated"] = row["updated_at"]
        return row

    async def update_album(self, user_id: str, album_id: UUID, fields: dict) -> dict | None:
        self._ensure_session()
        patch = {k: v for k, v in fields.items() if v is not None}
        patch["updated_at"] = _utcnow().isoformat()
        resp = (
            self.supabase_client.table("albums")
            .update(patch)
            .eq("id", str(album_id))
            .eq("user_id", user_id)
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data[0]
        row["task_count"] = 0
        row["last_updated"] = row["updated_at"]
        return row

    async def delete_album(self, user_id: str, album_id: UUID) -> None:
        self._ensure_session()
        self.supabase_client.table("albums").delete().eq(
            "id", str(album_id)
        ).eq("user_id", user_id).execute()

    async def assign_task_album(self, user_id: str, task_id: str, album_id: UUID | None) -> bool:
        self._ensure_session()
        resp = (
            self.supabase_client.table(self._task_table)
            .update({"album_id": str(album_id) if album_id else None})
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(resp.data)

    async def update_task_title(self, user_id: str, task_id: str, title: str) -> None:
        self._ensure_session()
        (
            self.supabase_client.table(self._task_table)
            .update({"title": title})
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )

    # ─── Task chat (R2-2) ───

    async def insert_message(self, task_id: str, user_id: str, role: str, content: str) -> None:
        self._ensure_session()
        self.supabase_client.table("task_messages").insert({
            "task_id": int(task_id),
            "user_id": user_id,
            "role": role,
            "content": content,
        }).execute()

    async def list_messages(self, task_id: str) -> list[dict]:
        self._ensure_session()
        resp = (
            self.supabase_client.table("task_messages")
            .select("role, content, created_at")
            .eq("task_id", task_id)
            .order("created_at", desc=False)
            .execute()
        )
        rows = resp.data or []
        for r in rows:
            r["created_at"] = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        return rows

    # ─── Google Play purchases (idempotency ledger) ───

    async def record_play_purchase(
        self, purchase_token: str, user_id: str, product_id: str, credits: int,
    ) -> bool:
        """Insert the purchase token; return False if it was already recorded.
        The PK on purchase_token also guards against a concurrent double-insert."""
        self._ensure_session()
        existing = (
            self.supabase_client.table("play_purchases")
            .select("purchase_token")
            .eq("purchase_token", purchase_token)
            .limit(1)
            .execute()
        )
        if existing.data:
            return False
        try:
            self.supabase_client.table("play_purchases").insert({
                "purchase_token": purchase_token,
                "user_id": user_id,
                "product_id": product_id,
                "credits": credits,
            }).execute()
        except Exception:
            # Lost a race to another verify of the same token → already granted.
            return False
        return True

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
        user_id: str,
        platform: str,
        token: str,
        app_version: str | None,
        locale: str | None,
    ) -> str:
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
                "user_id": user_id,
                "app_version": app_version,
                "locale": locale,
                "last_seen": _utcnow().isoformat(),
            }).eq("token", token).execute()
            return str(existing.data[0]["id"])
        resp = self.supabase_client.table("user_devices").insert({
            "user_id": user_id,
            "platform": platform,
            "token": token,
            "app_version": app_version,
            "locale": locale,
        }).execute()
        return str(resp.data[0]["id"])

    async def delete_user_device(self, user_id: str, token: str) -> None:
        self._ensure_session()
        self.supabase_client.table("user_devices").delete().eq(
            "user_id", user_id
        ).eq("token", token).execute()

    async def delete_user_device_by_token(self, token: str) -> None:
        self._ensure_session()
        self.supabase_client.table("user_devices").delete().eq("token", token).execute()

    async def list_user_devices(self, user_id: str) -> list[dict]:
        self._ensure_session()
        resp = (
            self.supabase_client.table("user_devices")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        rows = resp.data or []
        for r in rows:
            r["user_id"] = str(r["user_id"]) if r.get("user_id") is not None else None
        return rows

    # ─── Telegram bot bridges (called from /internal/*) ───

    async def upsert_telegram_user(self, data: dict) -> None:
        """Bot's /start handler calls this. Idempotent. Keyed on user_id text."""
        self._ensure_session()
        uid = str(data.get("user_id") or data.get("telegram_user_id"))
        existing = (
            self.supabase_client.table(self._users_table)
            .select("user_id")
            .eq("user_id", uid)
            .limit(1)
            .execute()
        )
        if existing.data:
            return
        self.supabase_client.table(self._users_table).insert({
            "user_id": uid,
            "username": data.get("username"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "language_code": data.get("language_code") or "ru",
            "is_premium": str(data.get("is_premium", False)),
        }).execute()
        self.supabase_client.table(self._users_status_table).insert({
            "user_id": uid,
            "daily_limit": DEFAULT_DAILY_LIMIT,
            "subscription_limit": 0,
            "last_processing_date": None,
        }).execute()

    async def insert_legacy_solution(
        self, user_id: str, file_path: str, solution: dict, model: str,
    ) -> None:
        """Bot's solve path stores synchronously after the answer is back."""
        self._ensure_session()
        self.supabase_client.table(self._task_table).insert({
            "user_id": user_id,
            "file_path": file_path or None,
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
