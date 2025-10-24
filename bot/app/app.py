import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Form, UploadFile, File

from bot.constants import (
    DOWNLOAD_ENDPOINT,
    SOLVE_ENDPOINT,
    ADD_NEW_USER_ENDPOINT,
    GET_EXIST_SOLUTION_ENDPOINT,
    DONATE_ENDPOINT,
    TEXT_SOLVE_ENDPOINT,
    LATEX_TO_TEXT_SOLVE_ENDPOINT,
    GET_CURRENT_BALANCE_ENDPOINT,
    DAILY_LIMIT_EXCEEDED_MESSAGE,
    GET_ALL_USER_IDS,
    ADD_SUBSCRIPTION_LIMITS_FOR_ALL_USERS,
)
from bot.gemini_service import GeminiSolver
from bot.gpt_service import TaskSolverGPT
from bot.supabase_service import SupabaseService

load_dotenv()

app = FastAPI()
solver = TaskSolverGPT(openai_api_key=os.environ.get("OPENAI_API_KEY"))
db = SupabaseService(
    supabase_url=os.environ.get("SUPABASE_URL"),
    supabase_key=os.environ.get("SUPABASE_KEY"),
    user_email=os.environ.get("USER_EMAIL"),
    user_password=os.environ.get("USER_PASSWORD"),
)
gemini_solver = GeminiSolver(google_api_key=os.environ.get("GOOGLE_API_KEY"))


@app.post(SOLVE_ENDPOINT)
async def solve_task(
    image_path: str = Form(...), file: UploadFile = File(...), user_id: str = Form(...)
):
    try:
        # Try using the GeminiSolver first
        #answer = await gemini_solver.solve(file)
        answer = await solver.solve(file)
    except Exception as e:
        # Log the error and fall back to TaskSolverGPT
        print(f"Error with GeminiSolver: {e}. Falling back to TaskSolverGPT.")
        print(type(file))
        await file.seek(0)
        answer = await gemini_solver.solve(file)
    await db.update_last_processing_image_path(user_id=user_id, image_path=image_path)
    await db.insert_solution(user_id=user_id, file_path=image_path, solution=answer)
    print("GETTING SOLUTION", answer)
    return {"message": "Task solved", "answer": answer}


@app.post(DOWNLOAD_ENDPOINT)
async def upload_image(
    file: Annotated[bytes, File(description="A file read as bytes")],
    image_path: str = Form(...),
    user_id: str = Form(...),
):
    proceed_processing = await db.proceed_processing(user_id)
    if proceed_processing:
        response = await db.upload_file(file_path=image_path, file_bytes=file)
        return response
    else:
        return {
            "message": "Daily limit exceeded",
            "status_code": 429,
            "error": str(
                {
                    "message": "Daily limit exceeded",
                    "statusCode": 429,
                    "error": "Daily limit exceeded",
                }
            ),
        }


@app.post(ADD_NEW_USER_ENDPOINT)
async def add_new_user(user_data: dict):
    response = await db.add_new_user(user_data)
    return response


@app.post(GET_EXIST_SOLUTION_ENDPOINT)
async def get_exist_solution(image_path: str = Form(...), user_id: str = Form(...)):
    solution = await db.get_exist_solution(user_id=user_id, file_path=image_path)
    return {"message": "Solution found", "answer": solution}


@app.post(DONATE_ENDPOINT)
async def donate(user_data: dict):
    response = await db.add_subscription_limit(user_id=user_data["user_id"])
    return response


@app.post(TEXT_SOLVE_ENDPOINT)
async def text_solve_task(text: str = Form(...), user_id: str = Form(...)):
    print("TEXT SOLVE TASK", text)
    processing = await db.proceed_processing(user_id)
    if processing:
        try:
            answer = await solver.generate_text_solution(text)
            await db.insert_solution(user_id=user_id, file_path="", solution=answer)
            return {"message": "Task solved", "answer": answer}
        except Exception as e:
            # use Gemini as fallback
            print(f"Error with TaskSolverGPT: {e}. Falling back to GeminiSolver.")
            answer = await gemini_solver.generate_text(text)
            await db.insert_solution(user_id=user_id, file_path="", solution=answer)
            return {"message": "Task solved", "answer": answer}
    else:
        return {
            "message": "Daily limit exceeded",
            "status_code": 429,
            "answer": 429,
            "error": str(
                {
                    "message": "Daily limit exceeded",
                    "statusCode": 429,
                    "error": "Daily limit exceeded",
                }
            ),
        }


@app.post(LATEX_TO_TEXT_SOLVE_ENDPOINT)
async def latex_to_text_solve_task(text: str = Form(...), user_id: str = Form(...)):
    answer = await gemini_solver.generate_unicode_solution(text)
    await db.insert_solution(user_id=user_id, file_path="", solution=answer)
    return {"message": "Task solved", "answer": answer}


@app.post(GET_CURRENT_BALANCE_ENDPOINT)
async def get_current_balance(user_data: dict):
    balance = await db.get_current_balance(user_data["user_id"])
    print("Balance", balance)
    return balance


@app.post(GET_ALL_USER_IDS)
async def get_all_users():
    return await db.get_all_user_ids()


@app.post(ADD_SUBSCRIPTION_LIMITS_FOR_ALL_USERS)
async def add_subscription_limits_for_all_users(data: dict):
    return await db.add_subscription_limits_for_all_users(data["limit"])


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
