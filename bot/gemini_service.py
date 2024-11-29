import asyncio
import io
import json
import time
from json import JSONDecodeError
from typing import Dict

import google.generativeai as genai

from bot.constants import TASK_HELPER_PROMPT_TEMPLATE_USER, GEMINI_MODEL, TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER, \
    LATEX_TO_TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER
from PIL import Image


class GeminiSolver:
    def __init__(self, google_api_key: str):
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel(model_name=GEMINI_MODEL)
        self._prompt = TASK_HELPER_PROMPT_TEMPLATE_USER
        self._text_model = genai.GenerativeModel(model_name=GEMINI_MODEL,
                                                 system_instruction=TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER)

        self._latex_to_text_model = genai.GenerativeModel(model_name=GEMINI_MODEL,
                                                          system_instruction=LATEX_TO_TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER)

    async def solve(self, photo_io):
        start_time = time.time()
        # Read the file content asynchronously
        content = await photo_io.read()
        # Wrap it in a BytesIO object so PIL can open it
        image = Image.open(io.BytesIO(content))

        result = self.model.generate_content(
            [image, self._prompt]
        )
        end_time = time.time()
        print(f"Time elapsed: {end_time - start_time}")
        print("GEMINI result:", result.text)

        result = self.parse_output_json(result.text)

        return result

    async def generate_text(self, user_input) -> dict:
        """
        Generate text based on the input text and prompt.
        Args:
            user_input (str): user input text
        Returns:
            str: generated text
        """

        result = self._text_model.generate_content(user_input)
        print("GEMINI TEXT result:", result.text)
        parsed_result = self.parse_output_json(result.text)
        return parsed_result

    async def generate_unicode_solution(self, user_input: str) -> dict:
        """
        Generate solution based on the input text and prompt.
        Args:
            user_input (str): user input text
        Returns:
            str: generated solution
        """
        result = self._latex_to_text_model.generate_content(user_input)
        parsed_result = self.parse_output_json(result.text)
        return parsed_result

    def parse_output_json(self, response: str, ) -> Dict:
        """
        Parse response from AI API.
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
            json_content = response[start_idx: end_idx + 1]
            return json.loads(json_content)
