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

# New /internal/* surface — HMAC-authenticated. Migrate the bot's call sites
# here over time using bot.internal_client.InternalClient. The legacy
# /tasker/api/* paths above remain mounted for compatibility during transition.
INTERNAL_USERS_UPSERT_ENDPOINT = "/internal/users"
INTERNAL_LINK_CONFIRM_ENDPOINT = "/internal/auth/link/confirm"
INTERNAL_SOLVE_IMAGE_ENDPOINT = "/internal/tasks/solve_image"
INTERNAL_SOLVE_TEXT_ENDPOINT = "/internal/tasks/solve_text"
INTERNAL_TOPUP_ENDPOINT = "/internal/topup"
INTERNAL_UPLOAD_ENDPOINT = "/internal/upload"
INTERNAL_GET_EXISTING_ENDPOINT = "/internal/tasks/get_existing"
INTERNAL_LATEX_TO_TEXT_ENDPOINT = "/internal/tasks/latex_to_text"
INTERNAL_BALANCE_ENDPOINT = "/internal/balance"
INTERNAL_USERS_LIST_ENDPOINT = "/internal/users/list"
INTERNAL_ADD_SUBS_FOR_ALL_ENDPOINT = "/internal/admin/add_subscription_for_all"

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

1. **Problem Field**:
   - Wrap ALL math expressions in $ delimiters
   - Example: "Решите неравенство $3^x - \\frac{702}{3^x - 1} \\ge 0$"

2. **Steps/Solution Fields - TYPE USAGE**:

   **Use "type": "text" for:**
   - ANY content with Cyrillic (Russian) text
   - Explanatory sentences, lists, descriptions
   - Inline math with $...$ delimiters
   - **LaTeX tables** (tabular environment)
   - **ALWAYS properly close math with $** before punctuation

   **Use "type": "math" ONLY for:**
   - Pure mathematical expressions
   - NO Cyrillic text, NO descriptive text

3. **PUNCTUATION RULES**:
   - **NEVER use `\\.` (backslash-dot)** - it's invalid in math mode
   - Always write periods as plain `.` (not `\\.`)
   - **ALWAYS close math expressions with `$` before punctuation**
   - Correct: "$\\theta \\in [0, \\pi]$. Тогда..." (period AFTER closing $)
   - Wrong: "$\\theta \\in [0, \\pi]\\. Тогда..." (backslash-dot invalid)
   - Wrong: "$\\theta \\in [0, \\pi] Тогда$" (no $ closure before text)

4. **TABLE FORMATTING - CRITICAL FOR TABLE TASKS**:

   When task contains "Заполните таблицу", "fill.*table", or "complete.*table":

   **Generate ONE text item with complete table structure.**
   
   **Critical command syntax:**
   - **ALWAYS write `\\footnotesize` correctly** (double backslash + footnotesize)
   - NEVER write `\footnotesize` or corrupted versions
   - NEVER use form feed characters (\x0c) or control codes

   **Key rules:**
   - ALWAYS use \\footnotesize for tables (required for readability)
   - Keep answers brief (5-10 words per cell max)
   - Use abbreviations: "Ж/д" instead of "Железные дороги"
   - Split long lists with commas, not full sentences
   - Use wider columns: p{5.5cm} or p{6cm} for better text wrapping
   - First row should be headers with \\textbf{}

   Example:
   {
     "type": "text",
     "content": "\\footnotesize\\begin{tabular}{|l|p{5.5cm}|p{5.5cm}|p{5.5cm}|}\\n\\hline\\n\\textbf{Вопрос} & \\textbf{Нефть} & \\textbf{Газ} & \\textbf{Уголь} \\\\\\n\\hline\\n7. Запасы & Саудовская Аравия, Венесуэла & Россия, Иран, Катар & США, Россия, Китай \\\\\\n\\hline\\n\\end{tabular}"
   }

5. **Comparison Operators**:
   - Always use: $\\ge$, $\\le$, $\\neq$ (inside $ delimiters)
   - Never use: >=, <=, !=

6. **Forbidden**:
   - Never use "type": "math" for text with Cyrillic
   - Never use: `\\.` (backslash-dot) - use plain `.`
   - Never use: `\\,` outside math mode
   - Never use: \\cancel, \\newline in text
   - Never use bare operators outside $...$
   - Never write long sentences in table cells

7. **Language Consistency**:
   - If problem is in Russian, solution must be in Russian
   - If problem is in English, solution must be in English
   - If problem has no language, solution must be in Russian
   - Always keep consistent language throughout problem, steps, solution
   
Example for MATH problem with proper punctuation:
{
  "solutions": [{
    "problem": "Решите уравнение $x^2 - 5x + 6 = 0$",
    "steps": [
      {"type": "text", "content": "Вычислим дискриминант $D = b^2 - 4ac$."},
      {"type": "math", "content": "D = (-5)^2 - 4 \\cdot 1 \\cdot 6 = 1"},
      {"type": "text", "content": "Корни: $x = \\frac{-b \\pm \\sqrt{D}}{2a}$. Подставим значения."}
    ],
    "solution": [
      {"type": "math", "content": "x_1 = 2, \\quad x_2 = 3"}
    ]
  }]
}

Your answer must be in the language of the problems. So if the problems are in Russian, respond in Russian, if in English, respond in English.
"""



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
You are a best professor at the university. You need to help students to solve the following problems.
Return the solutions in language of tasks for the following problems in json format.
If you see that task in russian language, solution must be in russian language too.
Or if you see that task without any language, solution must be in russian language.
Don't ask questions at the end, just solve the problems.
Your answers must be short and to the point.

CRITICAL LATEX RULES FOR MARKDOWN OUTPUT:

1. **Use proper LaTeX syntax**:
   - Fractions: `\\frac{1}{4}` (NOT `\\tfrac`)
   - Decimals: Use regular comma `0,5` or period `0.5` (NOT `0{,}5`)
   - Powers: `2^{-1}` or `0.5^x`
   - Comparisons: `\\ge`, `\\le`, `\\neq`

2. **Inline math delimiters**:
   - Always wrap math in single `$` signs
   - Example: "Решим уравнение $0.5^x = \\frac{1}{4}$"

3. **Type usage**:
   - Use `"type": "text"` for ALL content (text + inline math)
   - Never use `"type": "math"` in this format

4. **Forbidden**:
   - `\\tfrac`, `\\dfrac` - use `\\frac` only
   - `{,}` for commas - use plain `,`
   - Double backslashes in math - use single `\\`

Example:
{
  "solutions": [{
    "problem": "Решите уравнение $0.5^x = \\frac{1}{4}$",
    "steps": [
      {"type": "text", "content": "Представим $0.5 = \\frac{1}{2} = 2^{-1}$ и $\\frac{1}{4} = 2^{-2}$"},
      {"type": "text", "content": "Получаем: $(2^{-1})^x = 2^{-2}$"},
      {"type": "text", "content": "Следовательно: $2^{-x} = 2^{-2}$, откуда $-x = -2$"}
    ],
    "solution": [
      {"type": "text", "content": "Ответ: $x = 2$"}
    ]
  }]
}

Output the solutions in the following JSON format:
{
    "solutions": [
        {
            "problem": "problem_1",
            "steps": [
                {
                    "type": "text",
                    "content": "step_1 with inline math $...$"
                },
                {
                    "type": "text",
                    "content": "step_2 with inline math $...$"
                }
            ],
            "solution": [
                {
                    "type": "text",
                    "content": "solution_1 with inline math $...$"
                }
            ]
        }
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
