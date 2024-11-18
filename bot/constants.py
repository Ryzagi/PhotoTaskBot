GPT_MODEL = "gpt-4o"

DOWNLOAD_ENDPOINT = "/tasker/api/download_image"
SOLVE_ENDPOINT = "/tasker/api/solve_task"
ADD_NEW_USER_ENDPOINT = "/tasker/api/add_new_user"
GET_EXIST_SOLUTION_ENDPOINT = "/tasker/api/get_exist_solution"

SUB_FOLDER = "/task_images/"
DEFAULT_DAILY_LIMIT = 1
TASK_HELPER_PROMPT_TEMPLATE_SYSTEM = "You are given an image of a math problem. Help the user solve it."


_TASK_HELPER_PROMPT_TEMPLATE_USER = """    
Return the solutions in language of tasks for the following problems in json format.
Responds in LaTex format. Avoid to use ⅔ or ¾, use 2/3 or 3/4 instead.
Output the solutions in the following JSON format:
    {
        "solutions": [
            {
                "problem": "problem_1",
                "solution": "solution_1",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ]
            },
            {
                "problem": "problem_2",
                "solution": "solution_2",
                "steps": [
                    "step_1",
                    "step_2",
                    ...
                ]
            },
            ...
        ]
    }
"""

TASK_HELPER_PROMPT_TEMPLATE_USER = """    
Return the solutions in language of tasks for the following problems in json format.
Middle dot (·) is used to product two numbers.
Respond always in LaTeX proper syntax. Avoid to use ⅔ or ¾, use 2/3 or 3/4 instead.
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

AMOUNT = 1
