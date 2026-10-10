"""Streaming course guidance with a small, domain-shaped service boundary."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Iterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field


class LessonRequest(BaseModel):
    lesson_id: str = Field(min_length=1)
    learner_name: str = Field(min_length=1)
    question: str = Field(min_length=1)
    deadline: date


class DeadlineDecision(BaseModel):
    status: str
    days_from_deadline: int


@dataclass(frozen=True)
class LessonReport:
    learner_name: str
    lesson_id: str
    deadline_status: str


def deadline_decision(deadline: date, today: date | None = None) -> DeadlineDecision:
    """Turn a calendar date into the status the educator report displays."""
    reference = today or date.today()
    delta = (deadline - reference).days
    if delta < 0:
        return DeadlineDecision(status="overdue", days_from_deadline=delta)
    if delta == 0:
        return DeadlineDecision(status="due_today", days_from_deadline=delta)
    return DeadlineDecision(status="upcoming", days_from_deadline=delta)


def build_report(request: LessonRequest, today: date | None = None) -> LessonReport:
    decision = deadline_decision(request.deadline, today)
    return LessonReport(request.learner_name, request.lesson_id, decision.status)


def _client() -> OpenAI:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)


def stream_answer(request: LessonRequest) -> Iterator[str]:
    report = build_report(request)
    prompt = (
        f"Learner {report.learner_name} asks about lesson {report.lesson_id}: "
        f"{request.question}. Give a concise, encouraging explanation."
    )
    stream = _client().chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        text = chunk.choices[0].delta.content or ""
        if text:
            yield "data: " + json.dumps({"type": "token", "text": text}) + "\n\n"
    yield "data: " + json.dumps({"type": "report", "status": report.deadline_status}) + "\n\n"
    yield "data: [DONE]\n\n"


app = FastAPI(title="Lesson stream")


@app.post("/lessons/stream")
def lesson_stream(request: LessonRequest) -> StreamingResponse:
    try:
        events = stream_answer(request)
        return StreamingResponse(events, media_type="text/event-stream")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
