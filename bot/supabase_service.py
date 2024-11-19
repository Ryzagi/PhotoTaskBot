import json
from typing import Dict, Union
from datetime import date
from supabase import create_client, Client

from bot.constants import SUB_FOLDER, DEFAULT_DAILY_LIMIT


class SupabaseService:
    def __init__(self, supabase_url: str, supabase_key: str, user_email: str, user_password: str):
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name: str = "tasks"
        self._users_table = "users"
        self._users_status_table = "users_status"
        self._task_table = "tasks"

        self.supabase_client.auth.sign_in_with_password({"email": user_email, "password": user_password})

    # TODO: Implement the async upload_file method
    async def upload_file(self, file_path: str, file_bytes: bytes) -> Dict[str, Union[str, int]]:
        # Upload the bytes directly to Supabase Storage
        supabase_path = f"{SUB_FOLDER}{file_path}"
        try:
            self.supabase_client.storage.from_(self.bucket_name).upload(path=supabase_path, file=file_bytes)
            return {"message": "File uploaded successfully", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to upload file", "status_code": 400, "error": str(e)}

    async def add_new_user(self, user_data: dict) -> Dict[str, Union[str, int]]:
        # Add a new user to the "users" table in Supabase, if the user does not already exist
        user_id = user_data.get("user_id")
        if await self._is_exist(user_id):
            return {"message": "User already exists", "status_code": 200}
        try:
            self.supabase_client.table(self._users_table).insert(user_data).execute()
            self.supabase_client.table(self._users_status_table).insert(
                {"user_id": user_id, "last_processing_date": None, "daily_limit": DEFAULT_DAILY_LIMIT,
                 "subscription_limit": 0}).execute()
            return {"message": "User added successfully", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to add user", "status_code": str(e)}

    async def _is_exist(self, user_id: str) -> bool:
        # Check if the user with the given user_id exists in the Supabase table
        data = self.supabase_client.table(self._users_table).select("user_id").eq("user_id", user_id).execute()
        print(data)
        print(data.data)
        return len(data.data) > 0

    async def _get_last_processing_date(self, user_id: str) -> Dict[str, Union[str, int]]:
        # Get the last processing date for the user with the given user_id
        try:
            response = self.supabase_client.table(self._users_status_table).select("last_processing_date").eq("user_id",
                                                                                                              user_id).execute()
            print("Last processing date", response.data[0]["last_processing_date"])
            return {"last_processing_date": response.data[0]["last_processing_date"], "status_code": 200}
        except Exception as e:
            return {"message": "Failed to get last processing date", "status_code": str(e)}

    def _get_user_limits(self, user_id: str) -> Dict[str, Union[dict, int]]:
        # Get the limits for all users
        try:
            response = self.supabase_client.table(self._users_status_table).select("daily_limit",
                                                                                   "subscription_limit").eq("user_id",
                                                                                                            user_id).execute()
            print("Limits", response.data[0])
            return {"users_limits": response.data[0], "status_code": 200}
        except Exception as e:
            return {"message": f"Failed to get users limits. Error: {e}", "status_code": 400, "users_limits": None}

    async def proceed_processing(self, user_id: str) -> Union[bool, Dict[str, Union[str, int]]]:
        # Update the last processing date for the user with the given user_id
        try:
            user_limits = self._get_user_limits(user_id)["users_limits"]
            print("User limits", user_limits)
            if user_limits["daily_limit"] == 0:
                print("Daily limit is exceeded")
                if user_limits["subscription_limit"] > 0:
                    await self._decrease_subscription_limit(user_id=user_id,
                                                            subscription_limit=user_limits["subscription_limit"])
                    return True
                else:
                    last_processing_date = await self._get_last_processing_date(user_id)
                    if last_processing_date["last_processing_date"] == date.today().isoformat():
                        print("Last processing date is today. Daily limit is exceeded")
                        return False
                    else:
                        print("Daily limit is not exceeded")
                        await self._decrease_daily_limit(user_id)
                        return True
            else:
                print("Daily limit is not exceeded")
                # TODO Uncomment the line below
                #await self._decrease_daily_limit(user_id)
                return True
        except Exception as e:
            print("Failed to proceed processing", str(e))
            return False

    async def _decrease_daily_limit(self, user_id: str) -> Dict[str, Union[str, int]]:
        # Decrease the daily limit for the user with the given user_id
        daily_limit = DEFAULT_DAILY_LIMIT - 1
        try:
            today = date.today().isoformat()
            print(today)
            data_to_insert = {"daily_limit": daily_limit, "last_processing_date": today}
            print(data_to_insert)
            response = self.supabase_client.table(self._users_status_table).update(data_to_insert).eq("user_id",
                                                                                                      user_id).execute()
            print("Daily limit decreased", response)
            return {"message": "Daily limit decreased", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to decrease daily limit", "status_code": str(e)}

    async def _decrease_subscription_limit(self, user_id: str, subscription_limit: int) -> Dict[str, Union[str, int]]:
        # Decrease the daily limit for the user with the given user_id
        subscription_limit = subscription_limit - 1
        try:
            data_to_insert = {"subscription_limit": subscription_limit}
            response = self.supabase_client.table(self._users_status_table).update(data_to_insert).eq("user_id",
                                                                                                      user_id).execute()
            print("Subscription limit decreased", response)
            return {"message": "Subscription limit decreased", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to decrease subscription limit", "status_code": str(e)}

    async def update_last_processing_image_path(self, user_id: str, image_path: str) -> Dict[str, Union[str, int]]:
        # Update the last processing image path for the user with the given user_id
        try:
            data_to_insert = {"last_processing_image_path": image_path}
            self.supabase_client.table(self._users_status_table).update(data_to_insert).eq("user_id", user_id).execute()
            return {"message": "Last processing image path updated", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to update last processing image path", "status_code": str(e)}

    async def insert_solution(self, user_id: str, file_path: str, solution: str) -> Dict[str, Union[str, int]]:
        # Insert the solution into the "tasks" table in Supabase
        try:
            data_to_insert = {"user_id": user_id, "file_path": file_path, "solution": solution}
            self.supabase_client.table(self._task_table).insert(data_to_insert).execute()
            return {"message": "Solution inserted successfully", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to insert solution", "status_code": str(e)}

    async def get_exist_solution(self, user_id: str, file_path: str) -> Dict[str, Union[str, int]]:
        # Get the solutions for the user with the given user_id and file_path
        try:
            response = self.supabase_client.table(self._task_table).select("solution").eq("user_id",
                                                                                          user_id).eq("file_path",
                                                                                                      file_path).execute()
            print("Existing solution", response.data[0]["solution"])
            return {"message": response.data, "status_code": 200}
        except Exception as e:
            return {"message": "Failed to get solutions", "status_code": str(e)}

    async def add_subscription_limit(self, user_id: str, subscription_limit: int = 1) -> Dict[str, Union[str, int]]:
        # Add to the subscription limit for the user with the given user_id
        try:
            # Retrieve the current subscription_limit
            current_data = self.supabase_client.table(self._users_status_table).select("subscription_limit").eq(
                "user_id", user_id).execute()
            print("Current data", current_data.data)
            if not current_data or not current_data.data:
                return {"message": "User not found or invalid data", "status_code": 404}

            current_limit = current_data.data[0]["subscription_limit"]

            # Calculate the new subscription limit
            new_limit = current_limit + subscription_limit
            print("New limit", new_limit)
            # Update the subscription_limit in the database
            data_to_update = {"subscription_limit": new_limit}
            self.supabase_client.table(self._users_status_table).update(data_to_update).eq("user_id", user_id).execute()

            return {"message": "Subscription updated successfully", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to update subscription", "status_code": str(e)}



