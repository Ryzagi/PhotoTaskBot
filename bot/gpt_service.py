import asyncio
import base64
import json
import time
from json import JSONDecodeError
from typing import Dict

import httpx
from openai import AsyncOpenAI

from bot.constants import GPT_MODEL, TASK_HELPER_PROMPT_TEMPLATE_USER, TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER, \
    OPENAI_OUTPUT_FORMAT, LATEX_TASK_HELPER_PROMPT_TEMPLATE_USER


class TaskSolverGPT:
    def __init__(self, openai_api_key: str):
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,  # Total connection pool size
                max_keepalive_connections=20  # Persistent connections
            ),
            timeout=60.0
        )
        self.client = AsyncOpenAI(
            api_key=openai_api_key,
            http_client=http_client,
            max_retries=2
        )

    async def encode_image(self, photo_io):
        """Encode image to base64, handling both sync and async file objects."""
        if isinstance(photo_io, bytes):
            photo_bytes = photo_io
        elif hasattr(photo_io, 'read'):
            # Check if it's an async reader (has async read method)
            if asyncio.iscoroutinefunction(photo_io.read):
                photo_bytes = await photo_io.read()
            else:
                photo_bytes = photo_io.read()
        else:
            raise ValueError(f"Unsupported photo_io type: {type(photo_io)}")

        return base64.b64encode(photo_bytes).decode("utf-8")

    async def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    async def solve(self, photo_io):
        start_time = time.time()
        print(type(photo_io))
        image_base64 = await self.encode_image(photo_io)
        print("Image started")
        response = await self.client.responses.create(
            model=GPT_MODEL,
            input=[
                {
                    "role": "system",
                    "content": LATEX_TASK_HELPER_PROMPT_TEMPLATE_USER,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "You are a helpful university professor. Help me with my homework!"},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    ],
                }
            ],
            reasoning={
                "effort": "minimal"
            },
            text={"format": OPENAI_OUTPUT_FORMAT}
        )
        output_text = response.output_text
        if "solutions" not in output_text:
            raise Exception("Failed to get solutions")
        print("GPT result:", output_text)
        end_time = time.time()
        print(f"Time elapsed: {end_time - start_time}")
        # dow = await self.download_task_photo(path, photo_io)
        result = self.parse_output_json(output_text)
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

    async def generate_text_solution(self, user_input: str) -> dict:
        """
        Generate solution based on the input text and prompt.
        Args:
            user_input (str): user input text
        Returns:
            str: generated solution
        """
        response = await self.client.responses.create(
            model=GPT_MODEL,
            input=[
                {"role": "system",
                    "content": TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "You are a helpful university professor. Help me with my homework!"},
                        {
                            "type": "input_text",
                            "text": user_input,
                        },
                    ],
                }
            ],
            reasoning={
                "effort": "minimal"
            },
            text={"format": OPENAI_OUTPUT_FORMAT}
        )
        output_text = response.output_text
        print("GPT TEXT result:", output_text)
        parsed_result = self.parse_output_json(output_text)
        return parsed_result
