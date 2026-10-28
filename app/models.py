from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class TraceStep(BaseModel):
    name: str
    status: Literal["completed", "rejected", "failed"]
    detail: str
    duration_ms: float = 0


class Evidence(BaseModel):
    result_id: str
    sql: str
    rows: list[dict[str, Any]]
    row_count: int
    elapsed_ms: float


class AnalysisResponse(BaseModel):
    trace_id: str
    question: str
    title: str
    summary: str
    methodology: str
    findings: list[str]
    caveats: list[str]
    chart: dict[str, Any] | None
    evidence: list[Evidence]
    trace: list[TraceStep]


class SchemaResponse(BaseModel):
    tables: dict[str, dict[str, str]]

