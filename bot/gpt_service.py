import base64
import time


from openai import AsyncOpenAI

from bot.constants import GPT_MODEL, TASK_HELPER_PROMPT_TEMPLATE_USER


class TaskSolverGPT:
    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(
            api_key=openai_api_key,
        )

    async def encode_image(self, photo_io):
        photo_bytes = await photo_io.read()
        return base64.b64encode(photo_bytes).decode("utf-8")

    async def solve(self, photo_io):
        start_time = time.time()
        image_base64 = await self.encode_image(photo_io)
        print('Image started')
        response = await self.client.chat.completions.create(
           model=GPT_MODEL,
           messages=[
               {"role": "system",
                "content": "You are a helpful task assistant. Help me with my homework!"},
               {"role": "user", "content": [
                   {"type": "text", "text": TASK_HELPER_PROMPT_TEMPLATE_USER},
                   {"type": "image_url", "image_url": {
                       "url": f"data:image/png;base64,{image_base64}"}
                    }
               ]}
           ],
           response_format={"type": "json_object"},
           temperature=0.0,
        )
        print(response.choices[0].message.content)
        end_time = time.time()
        print(f"Time elapsed: {end_time - start_time}")
        # dow = await self.download_task_photo(path, photo_io)
        return response.choices[0].message.content