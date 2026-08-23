"""Validation behavior of the Pydantic schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

# The schemas only need pydantic, not fastapi.
from bot.schemas.task import Problem, Solution, SolutionBlock, TaskCreateText
from bot.schemas.user import Balance, MeResponse


def test_balance_accepts_zero():
    Balance(daily=0, subscription=0)


def test_balance_rejects_negative():
    with pytest.raises(ValidationError):
        Balance(daily=-1, subscription=0)


def test_text_task_min_length():
    with pytest.raises(ValidationError):
        TaskCreateText(text="")


def test_text_task_max_length():
    with pytest.raises(ValidationError):
        TaskCreateText(text="x" * 10_001)


def test_solution_block_type_must_be_known():
    with pytest.raises(ValidationError):
        SolutionBlock(type="other", content="x")


def test_problem_round_trip():
    p = Problem(
        problem="Solve $x^2 = 4$",
        steps=[SolutionBlock(type="text", content="step 1"),
               SolutionBlock(type="math", content="x = 2")],
        solution=[SolutionBlock(type="math", content="x = 2")],
    )
    sol = Solution(solutions=[p])
    dumped = sol.model_dump()
    Solution.model_validate(dumped)


def test_me_response_round_trip():
    me = MeResponse(
        id=str(uuid4()),
        telegram_linked=False,
        language_code="ru",
        balance=Balance(daily=3, subscription=0),
        created_at=datetime.now(UTC),
    )
    MeResponse.model_validate(me.model_dump(mode="json"))
