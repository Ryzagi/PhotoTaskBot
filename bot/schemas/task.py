from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SolutionBlock(BaseModel):
    type: Literal["text", "math"]
    content: str


class Problem(BaseModel):
    problem: str
    steps: list[SolutionBlock]
    solution: list[SolutionBlock]


class Solution(BaseModel):
    title: str | None = None
    solutions: list[Problem]


class TaskCreateText(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class TaskRef(BaseModel):
    task_id: str
    status: Literal["pending", "done", "failed"]


class TaskDetail(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    status: Literal["pending", "done", "failed"]
    input_kind: Literal["image", "text", "latex"]
    input_text: str | None = None
    thumbnail_url: str | None = None
    image_url: str | None = None
    solution: Solution | None = None
    album_id: str | None = None
    model_used: str | None = None
    error_code: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatThread(BaseModel):
    messages: list[ChatMessage]


class TaskListItem(BaseModel):
    id: str
    status: Literal["pending", "done", "failed"]
    input_kind: Literal["image", "text", "latex"]
    preview: str
    thumbnail_url: str | None = None
    created_at: datetime


class TaskList(BaseModel):
    items: list[TaskListItem]
    next_before: datetime | None = None
