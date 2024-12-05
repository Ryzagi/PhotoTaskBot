GPT_MODEL = "gpt-4o-2024-11-20"
GEMINI_MODEL = "gemini-1.5-pro-002"

DOWNLOAD_ENDPOINT = "/tasker/api/download_image"
SOLVE_ENDPOINT = "/tasker/api/solve_task"
ADD_NEW_USER_ENDPOINT = "/tasker/api/add_new_user"
GET_EXIST_SOLUTION_ENDPOINT = "/tasker/api/get_exist_solution"
DONATE_ENDPOINT = "/tasker/api/donate"
TEXT_SOLVE_ENDPOINT = "/tasker/api/text_solve_task"
LATEX_TO_TEXT_SOLVE_ENDPOINT = "/tasker/api/latex_to_text_solve_task"
GET_CURRENT_BALANCE_ENDPOINT = "/tasker/api/get_current_balance"
GET_ALL_USER_IDS = "/tasker/api/get_all_user_ids"
ADD_SUBSCRIPTION_LIMITS_FOR_ALL_USERS = "/tasker/api/add_subscription_limits_for_all_users"

NETWORK = "app"

SUB_FOLDER = "/task_images/"
DEFAULT_DAILY_LIMIT = 1
TASK_HELPER_PROMPT_TEMPLATE_SYSTEM = "You are given an image of a math problem. Help the user solve it."

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

TEXT_TASK_HELPER_PROMPT_TEMPLATE_USER = """You are a top professor of STEM subjects.
You are a best professor at the university. You need to help students to solve the following problems.
Return the solutions in language of the tasks for the following problems in json format.
Full solution must be in language of the tasks.
Responds always must be in Markdown format.
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
PRICE_PER_IMAGE_IN_STARS = 10
