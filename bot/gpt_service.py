import base64
import json
import time
from json import JSONDecodeError
from typing import Dict

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

    async def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    async def solve(self, photo_io):
        start_time = time.time()
        print(type(photo_io))
        image_base64 = await self.encode_image(photo_io)
        print("Image started")
        response = await self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful university professor. Help me with my homework!",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": TASK_HELPER_PROMPT_TEMPLATE_USER},
                        {
                            "role": "assistant",
                            "content": "Ready to solve the problem. Please provide the image of the problem.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        if "solution" not in response.choices[0].message.content:
            raise Exception("Failed to get solution")
        print("GPT result:", response.choices[0].message.content)
        end_time = time.time()
        print(f"Time elapsed: {end_time - start_time}")
        # dow = await self.download_task_photo(path, photo_io)
        result = self.parse_output_json(response.choices[0].message.content)
        return result

    def parse_output_json(
        self,
        response: str,
    ) -> Dict:
        """
        Parse response from OpenAI API.
        Args:
            response (str): response from OpenAI API
        Returns:
            Dict: parsed response
        """
        response = response.replace("\n", "")
        try:
            return json.loads(response)
        except JSONDecodeError:
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            # Extract the JSON-like content from the response
            json_content = response[start_idx : end_idx + 1]
            return json.loads(json_content)
