import os
from typing import Annotated, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Form, UploadFile, File

from constants import DOWNLOAD_ENDPOINT, SOLVE_ENDPOINT, ADD_NEW_USER_ENDPOINT
from gpt_service import TaskSolverGPT
from supabase_service import SupabaseService

load_dotenv()

app = FastAPI()
solver = TaskSolverGPT(openai_api_key=os.environ.get("OPENAI_API_KEY"))
db = SupabaseService(supabase_url=os.environ.get("SUPABASE_URL"), supabase_key=os.environ.get("SUPABASE_KEY"), user_email=os.environ.get("USER_EMAIL"), user_password=os.environ.get("USER_PASSWORD"))


@app.post(SOLVE_ENDPOINT)
async def solve_task(image_path: str = Form(...), file: UploadFile = File(...), user_id: str = Form(...)):
    proceed_processing = await db.proceed_processing(user_id)
    if proceed_processing:
        answer = await solver.solve(image_path, file)
        await db.update_last_processing_image_path(user_id=user_id, image_path=image_path)
        return {"message": "Task solved", "answer": answer}
    else:
        return {"message": "Daily limit exceeded", "answer": False}


@app.post(DOWNLOAD_ENDPOINT)
async def upload_image(file: Annotated[bytes, File(description="A file read as bytes")], image_path: str = Form(...)):
    response = await db.upload_file(file_path=image_path, file_bytes=file)
    return response


@app.post(ADD_NEW_USER_ENDPOINT)
async def add_new_user(user_data: dict):
    response = await db.add_new_user(user_data)
    return response


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
