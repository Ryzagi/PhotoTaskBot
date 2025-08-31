import inspect
from functools import wraps
from typing import Dict, Union, Callable, Any
from datetime import date, datetime, timedelta, UTC
from supabase import create_client, Client

from bot.constants import SUB_FOLDER, DEFAULT_DAILY_LIMIT

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
    async def upload_file(self, file_path: str, file_bytes: bytes) -> Dict[str, Union[str, int]]:
        supabase_path = f"{SUB_FOLDER}{file_path}"
        self.supabase_client.storage.from_(self.bucket_name).upload(
            path=supabase_path, file=file_bytes
        )
        return {"message": "File uploaded successfully", "status_code": 200}

    @auth_retry()
    async def add_new_user(self, user_data: dict) -> Dict[str, Union[str, int]]:
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
    async def _get_last_processing_date(self, user_id: str) -> Dict[str, Union[str, int]]:
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
    ) -> Union[bool, Dict[str, Union[str, int]]]:
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
    async def get_current_balance(self, user_id: str) -> Dict[str, Any]:
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
    async def _decrease_daily_limit(self, user_id: str) -> Dict[str, Union[str, int]]:
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
    async def _decrease_subscription_limit(self, user_id: str, subscription_limit: int) -> Dict[str, Union[str, int]]:
        new_limit = max(0, subscription_limit - 1)
        self.supabase_client.table(self._users_status_table).update(
            {"subscription_limit": new_limit}
        ).eq("user_id", user_id).execute()
        return {"message": "Subscription limit decreased", "status_code": 200}

    @auth_retry()
    async def update_last_processing_image_path(self, user_id: str, image_path: str) -> Dict[str, Union[str, int]]:
        self.supabase_client.table(self._users_status_table).update(
            {"last_processing_image_path": image_path}
        ).eq("user_id", user_id).execute()
        return {"message": "Last processing image path updated", "status_code": 200}


    @auth_retry()
    async def insert_solution(self, user_id: str, file_path: str, solution: dict) -> Dict[str, Union[str, int]]:
        self.supabase_client.table(self._task_table).insert(
            {"user_id": user_id, "file_path": file_path, "solution": solution}
        ).execute()
        return {"message": "Solution inserted successfully", "status_code": 200}


    @auth_retry()
    async def get_exist_solution(self, user_id: str, file_path: str) -> Dict[str, Union[str, int]]:
        response = (
            self.supabase_client.table(self._task_table)
            .select("solution")
            .eq("user_id", user_id)
            .eq("file_path", file_path)
            .execute()
        )
        return {"message": response.data, "status_code": 200}

    @auth_retry()
    async def add_subscription_limit(self, user_id: str, subscription_limit: int = 1) -> Dict[str, Union[str, int]]:
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
    async def get_all_user_ids(self) -> Dict[str, Union[str, int]]:
        response = (
            self.supabase_client.table(self._users_table)
            .select("user_id")
            .execute()
        )
        return {"message": response.data, "status_code": 200}

    @auth_retry()
    async def add_subscription_limits_for_all_users(self, subscription_limit: int) -> Dict[str, Union[str, int]]:
        users = await self.get_all_user_ids()
        if users.get("status_code") != 200:
            return {"message": "Failed to fetch users", "status_code": 400}
        for u in users["message"]:
            await self.add_subscription_limit(u["user_id"], int(subscription_limit))
        return {"message": users["message"], "status_code": 200}
