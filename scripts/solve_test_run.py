import asyncio
import os
import time
from io import BytesIO

from dotenv import load_dotenv

from bot.gpt_service import TaskSolverGPT

load_dotenv()

async def main():
    solver = TaskSolverGPT(openai_api_key=os.environ.get("OPENAI_API_KEY"))

    # Read files synchronously, wrap in BytesIO for async compatibility
    files = []
    for i in range(3):
        with open(f"images/test_image_{i}.jpg", "rb") as f:
            file_bytes = f.read()
            files.append(BytesIO(file_bytes))

    start = time.time()
    results = await asyncio.gather(*[solver.solve(f) for f in files])
    end = time.time()

    print(f"Total time: {end - start:.2f}s")
    print(f"Expected if sequential: ~{len(files) * 30}s")
    print("Expected if parallel: ~30s")

if __name__ == "__main__":
    asyncio.run(main())
