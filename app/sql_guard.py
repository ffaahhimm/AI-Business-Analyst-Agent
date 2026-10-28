from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from app.db import query


ALLOWED_TABLES = {"orders", "order_items", "products", "regions"}
MAX_ROWS = 500
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|"
    r"load_extension|into|grant|revoke)\b|--|/\*|\*/|;",
    re.IGNORECASE,
)


class SQLValidationError(ValueError):
    pass


@dataclass(frozen=True)
class QueryResult:
    result_id: str
    sql: str
    rows: list[dict[str, object]]
    elapsed_ms: float


def validate_sql(sql: str, max_rows: int = MAX_ROWS) -> str:
    normalized = sql.strip()
    if not normalized or not re.match(r"^select\b", normalized, re.IGNORECASE):
        raise SQLValidationError("Only a single SELECT statement is allowed.")
    if FORBIDDEN.search(normalized):
        raise SQLValidationError("Query rejected: writes, multiple statements, comments, or unsafe functions are not allowed.")
    tables = set(re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", normalized, re.IGNORECASE))
    unknown = tables - ALLOWED_TABLES
    if unknown:
        raise SQLValidationError(f"Query rejected: table(s) not approved: {', '.join(sorted(unknown))}.")
    if max_rows < 1 or max_rows > MAX_ROWS:
        raise SQLValidationError(f"max_rows must be between 1 and {MAX_ROWS}.")
    if not re.search(r"\blimit\s+\d+\b", normalized, re.IGNORECASE):
        normalized += f" LIMIT {max_rows}"
    return normalized


def run_readonly_sql(sql: str, max_rows: int = MAX_ROWS) -> QueryResult:
    safe_sql = validate_sql(sql, max_rows)
    started = perf_counter()
    try:
        rows = query(safe_sql)
    except sqlite3.Error as exc:
        raise SQLValidationError(f"Query could not be executed: {exc}") from exc
    return QueryResult(str(uuid4()), safe_sql, rows[:max_rows], (perf_counter() - started) * 1000)

