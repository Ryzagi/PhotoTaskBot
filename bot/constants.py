GPT_MODEL = "gpt-5-mini-2025-08-07"
GEMINI_MODEL = "gemini-2.5-flash"

DOWNLOAD_ENDPOINT = "/tasker/api/download_image"
SOLVE_ENDPOINT = "/tasker/api/solve_task"
ADD_NEW_USER_ENDPOINT = "/tasker/api/add_new_user"
GET_EXIST_SOLUTION_ENDPOINT = "/tasker/api/get_exist_solution"
DONATE_ENDPOINT = "/tasker/api/donate"
TEXT_SOLVE_ENDPOINT = "/tasker/api/text_solve_task"
LATEX_TO_TEXT_SOLVE_ENDPOINT = "/tasker/api/latex_to_text_solve_task"
GET_CURRENT_BALANCE_ENDPOINT = "/tasker/api/get_current_balance"
GET_ALL_USER_IDS = "/tasker/api/get_all_user_ids"
ADD_SUBSCRIPTION_LIMITS_FOR_ALL_USERS = (
    "/tasker/api/add_subscription_limits_for_all_users"
)

NETWORK = "app"

SUB_FOLDER = "/task_images/"

DEFAULT_DAILY_LIMIT = 3

TASK_HELPER_PROMPT_TEMPLATE_SYSTEM = (
    "You are given an image of a math problem. Help the user solve it."
)

LOADING_MESSAGE = """Решаю задачу 🐼

Подождите ⏳"""

DAILY_LIMIT_EXCEEDED_MESSAGE = """Ежедневный лимит решений исчерпан. Завтра можно будет решить новую задачу 🚀 

Или воспользуйтесь командой /donate для увеличения лимита решений 🌟
"""

_TASK_HELPER_PROMPT_TEMPLATE_USER = """    
Return the solutions in language of tasks for the following problems in json format.
Middle dot (·) is used to product two numbers.
Respond always in LaTeX proper syntax. Avoid to use ⅔ or ¾, use 2/3 or 3/4 instead.
Full solution must be in language of tasks.
Output the solutions in the following JSON format:
    {
        "solutions": [
            {
                "problem": "problem_1",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ],
                "solution": "solution_1",
            },
            {
                "problem": "problem_2",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ],
                "solution": "solution_2",
            },
            ...
        ]
    }
"""

__TASK_HELPER_PROMPT_TEMPLATE_USER = """    
Return the solutions in language of tasks for the following problems in json format.
Middle dot (·) is used to product two numbers.
Respond always in LaTeX proper syntax. Avoid to use ⅔ or ¾, use 2/3 or 3/4 instead.
Full solution must be in language of tasks.
Ensure that all backslashes in LaTeX commands are escaped with an additional backslash (e.g., `\\frac`, `\\times`).
Output the solutions in the following JSON format, using "type" and "content" fields:
    {
    "solutions": [
        {
            "problem": "problem_1",
            "steps": [
                {
                    "type": "text",
                    "content": "First, we simplify the equation."
                },
                {
                    "type": "math",
                    "content": "-2.3 \\times (-5) = 2.3 \\times 5"
                },
                {
                    "type": "math",
                    "content": "2.3 \\times 5 = 11.5"
                }
            ],
            "solution": [
                {
                    "type": "math",
                    "content": "11.5"
                }
            ]
        },
        {
            "problem": "problem_2",
            "steps": [
                {
                    "type": "text",
                    "content": "Convert 0.8 to a fraction."
                },
                {
                    "type": "math",
                    "content": "0.8 = \\frac{4}{5}"
                },
                {
                    "type": "text",
                    "content": "Subtract \\( \\frac{2}{3} \\) from \\( \\frac{4}{5} \\)."
                },
                {
                    "type": "math",
                    "content": "\\frac{4}{5} - \\frac{2}{3} = \\frac{12}{15} - \\frac{10}{15} = \\frac{2}{15}"
                }
            ],
            "solution": [
                {
                    "type": "math",
                    "content": "-\\frac{7}{3}"
                }
            ]
        }
    ]
}
"""
TASK_HELPER_PROMPT_TEMPLATE_USER = """You are the best professor of STEM subjects.
You are a best professor at the university. You need to help students to solve the following problems.
Return the solutions in language of tasks for the following problems in json format.
If you see that task in russian language, solution must be in russian language too.
Or if you see that task without any language, solution must be in russian language.
Middle dot (·) is used to product two numbers.
Respond always in LaTeX proper syntax. Avoid to use ⅔ or ¾, use 2/3 or 3/4 instead.
Remember, LaTeX must be correctly formatted.
Full solution must be in language of tasks.

Math Presentation Style:

1. Default to Rendered LaTeX: Always use LaTeX for math. Use double dollar signs for display equations (equations intended to be on their own separate lines) and single dollar signs for inline math within text. Ensure math renders properly and not as raw code. Use the backslash-mathbf command for vectors where appropriate (e.g., for r).
Formatting Display Math Within Lists: When a display math equation (using double dollar signs) belongs to a list item (like a numbered or bullet point), follow this specific structure: First, write the text part of the list item. Then, start the display math equation on a completely new line immediately following that text. Critically, this new line containing the display math equation MUST begin at the absolute start of the line, with ZERO leading spaces or any indentation. Explicitly, do NOT add spaces or tabs before the opening double dollar sign to visually align it with the list item's text. This strict zero-indentation rule for display math lines within lists is essential for ensuring correct rendering.
2. Goal: Prioritize clean, readable, professional presentation resembling scientific documents. Ensure clear separation between math notation, text explanations.
3. Inline vs. Display for Brevity: Prefer inline math (`$ ... $`) for short equations fitting naturally in text to improve readability and flow. Reserve display math (`$$ ... $$`) for longer/complex equations or those requiring standalone emphasis.
4. Spacing After Display Math: For standard paragraph separation after display math (`$$...$$`), ensure exactly one blank line (two newlines in Markdown source) exists between the closing `$$` line and the subsequent paragraph text.

Ensure that all backslashes in LaTeX commands are escaped with an additional backslash (e.g., `\\frac`, `\\times`).
Output the solutions in the following JSON format, using "type" and "content" fields:
    {
    "solutions": [
        {
            "problem": "Описание задачи",
            "steps": [
                {
                    "type": "text",
                    "content": "Объяснение или шаг решения"
                },
                {
                    "type": "math",
                    "content": "Математическое выражение"
                },
                ...
            ],
            "solution": [
                {
                    "type": "math",
                    "content": "Финальный ответ"
                }
            ]
        },
        ...
    ]
}
"""

LATEX_TASK_HELPER_PROMPT_TEMPLATE_USER = """You are a top tier professor helping students solve STEM problems.

CRITICAL LATEX FORMATTING RULES:

1. **Problem Field Format**:
   - Wrap ALL math expressions in $ delimiters
   - Use proper LaTeX syntax: $3^x$, $\\frac{a}{b}$, $x \\ge 0$
   - Example: "Решите неравенство $3^x - \\frac{702}{3^x - 1} \\ge 0$"

2. **Steps/Solution Fields**:
   - **type: "text"**: Explanatory text. Include inline math with proper spacing
     - Correct: "значение $t \\ge 4$ удовлетворяет условию"
     - Wrong: "значение $\\ge$ 4" or "значение \\ge 4"
   - **type: "math"**: Pure LaTeX WITHOUT outer $ delimiters
     - Example: "t - \\frac{702}{t-1} \\ge 0"

3. **Inline Math Rules**:
   - Comparison operators MUST be inside math mode with surrounding values
   - Use: "$x \\ge 4$" not "$\\ge$ 4" or "\\ge 4"
   - Use: "$a = b$" not "a = b"

4. **Forbidden**:
   - Never use: >=, <=, != (use \\ge, \\le, \\neq)
   - Never use bare operators: "\\ge", "\\cdot" outside $...$
   - Never use: \\cancel, \\newline, \\quad, \\;

5. **Cyrillic Text**:
   - Use only in "text" type fields
   - Keep Cyrillic outside $...$ delimiters

Example:
{
  "solutions": [{
    "problem": "Решите уравнение $x^2 - 5x + 6 = 0$",
    "steps": [
      {"type": "text", "content": "Дискриминант $D = b^2 - 4ac$ равен"},
      {"type": "math", "content": "D = 25 - 24 = 1"},
      {"type": "text", "content": "Корни находим по формуле $x = \\frac{-b \\pm \\sqrt{D}}{2a}$"}
    ],
    "solution": [
      {"type": "math", "content": "x_1 = 2, \\quad x_2 = 3"}
    ]
  }]
}

Return in task language (Russian for Russian tasks)."""



LATEX_TO_TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER = """
You are the best copywriter in the world. You need to rewrite the following Latex text in a more understandable way without using Latex.
Return the solutions in language of solutions (in Russian) for the following problems in json format.
Responds always must be in Markdown with unicode format.
Output the solutions in the following JSON format:
    {
        "solutions": [
            {
                "problem": "problem_1",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ],
                "solution": "solution_1",
            },
            {
                "problem": "problem_2",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ],
                "solution": "solution_2",
            },
            ...
        ]
    }
"""

TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER = """You are the best professor of STEM subjects.
You are a best professor at the university. You need to help students to solve the following problems
Return the solutions in language of tasks for the following problems in json format.
If you see that task in russian language, solution must be in russian language too.
Or if you see that task without any language, solution must be in russian language.
Dont ask a questions at the end, just solve the problems.
Your answers must be short and to the point.
Output should be in Markdown format.
Output the solutions in the following JSON format:
    Output the solutions in the following JSON format:
    {
        "solutions": [
            {
                "problem": "problem_1",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ],
                "solution": "solution_1",
            },
            {
                "problem": "problem_2",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ],
                "solution": "solution_2",
            },
            ...
        ]
    }
"""


OPENAI_OUTPUT_FORMAT = {
    "type": "json_schema",
    "name": "task_solution",
    "schema": {
        "type": "object",
        "properties": {
            "solutions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "problem": {
                            "type": "string",
                            "description": "Problem statement with inline math wrapped in $ delimiters. Use LaTeX syntax: $3^x$, $\\frac{a}{b}$, $\\ge$, etc."
                        },
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["text", "math"]
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "For 'text': plain text or text with inline math ($...$). For 'math': LaTeX expression without outer $ delimiters"
                                    }
                                },
                                "required": ["type", "content"],
                                "additionalProperties": False
                            }
                        },
                        "solution": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["text", "math"]
                                    },
                                    "content": {
                                        "type": "string"
                                    }
                                },
                                "required": ["type", "content"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["problem", "steps", "solution"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["solutions"],
        "additionalProperties": False
    }
}





PRICE_PER_IMAGE_IN_STARS = 5
