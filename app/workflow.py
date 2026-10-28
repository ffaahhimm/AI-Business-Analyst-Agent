from __future__ import annotations

import re
from time import perf_counter
from uuid import uuid4

from app.analysis import revenue_summary, return_summary
from app.models import AnalysisResponse, Evidence, TraceStep
from app.sql_guard import QueryResult, SQLValidationError, run_readonly_sql


def _periods(question: str) -> tuple[str, str, str]:
    year = re.search(r"\b(20\d{2})\b", question)
    target_year = int(year.group(1)) if year else 2024
    if re.search(r"\b(q[2-4]|second|third|fourth)\b", question, re.IGNORECASE):
        quarter = re.search(r"\bq([1-4])\b", question, re.IGNORECASE)
        current_quarter = int(quarter.group(1)) if quarter else 2
        start_month = (current_quarter - 1) * 3 + 1
        current_start = f"{target_year}-{start_month:02d}-01"
        previous_year = target_year if current_quarter > 1 else target_year - 1
        previous_quarter = current_quarter - 1 or 4
        previous_start = f"{previous_year}-{(previous_quarter - 1) * 3 + 1:02d}-01"
        current_end_month = start_month + 3
        current_end_year = target_year + (1 if current_end_month > 12 else 0)
        current_end = f"{current_end_year}-{(current_end_month - 1) % 12 + 1:02d}-01"
        return previous_start, current_start, current_end
    return f"{target_year}-01-01", f"{target_year}-07-01", f"{target_year + 1}-01-01"


def _evidence(result: QueryResult) -> Evidence:
    return Evidence(
        result_id=result.result_id,
        sql=result.sql,
        rows=result.rows,
        row_count=len(result.rows),
        elapsed_ms=round(result.elapsed_ms, 2),
    )


def analyze(question: str) -> AnalysisResponse:
    started = perf_counter()
    trace_id = str(uuid4())
    trace: list[TraceStep] = [
        TraceStep(name="classify_question", status="completed", detail="Matched the question to a supported deterministic analysis.")
    ]
    evidence: list[Evidence] = []
    normalized = question.lower()
    try:
        if any(token in normalized for token in ("return", "refund")):
            sql = """
                SELECT p.category AS label,
                       SUM(oi.quantity) AS sold,
                       SUM(CASE WHEN o.returned = 1 THEN oi.quantity ELSE 0 END) AS returned
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.order_id
                JOIN products p ON p.product_id = oi.product_id
                GROUP BY p.category
                ORDER BY returned DESC
            """
            result = run_readonly_sql(sql)
            rows = return_summary(result.rows)
            evidence.append(_evidence(result))
            top = rows[0] if rows else {"label": "No data", "return_rate": 0}
            summary = f"{top['label']} has the highest observed return rate at {top['return_rate']:.1f}%."
            findings = [
                f"{row['label']}: {row['return_rate']:.1f}% return rate ({row['returned']} returned of {row['sold']} sold)."
                for row in rows
            ]
            chart = {"type": "bar", "title": "Return rate by category", "x": [r["label"] for r in rows], "y": [round(r["return_rate"], 1) for r in rows], "y_label": "Return rate (%)"}
            title = "Returns concentration"
            methodology = "Grouped sold and returned units by product category across the seeded dataset."
        elif any(token in normalized for token in ("revenue", "sales", "income")):
            previous_start, current_start, current_end = _periods(normalized)
            sql = f"""
                SELECT r.region_name AS label,
                       SUM(CASE WHEN o.order_date >= '{current_start}' AND o.order_date < '{current_end}' THEN oi.quantity * oi.unit_price * (1 - oi.discount) ELSE 0 END) AS current,
                       SUM(CASE WHEN o.order_date >= '{previous_start}' AND o.order_date < '{current_start}' THEN oi.quantity * oi.unit_price * (1 - oi.discount) ELSE 0 END) AS previous
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.order_id
                JOIN regions r ON r.region_id = o.region_id
                WHERE o.order_date >= '{previous_start}'
                GROUP BY r.region_name
                ORDER BY current DESC
            """
            result = run_readonly_sql(sql)
            summary_rows = revenue_summary(result.rows)
            evidence.append(_evidence(result))
            total_current = sum(row["current"] for row in summary_rows.values())
            total_previous = sum(row["previous"] for row in summary_rows.values())
            change = total_current - total_previous
            pct = (change / total_previous * 100) if total_previous else 0
            ranked = sorted(summary_rows.items(), key=lambda item: item[1]["change"])
            summary = f"Net revenue {'increased' if change >= 0 else 'decreased'} by ${abs(change):,.0f} ({abs(pct):.1f}%) in the comparison window."
            findings = [
                f"{label}: ${values['change']:,.0f} change ({values['change_pct']:.1f}%)."
                for label, values in ranked
            ]
            chart = {"type": "bar", "title": "Revenue change by region", "x": [label for label, _ in ranked], "y": [round(v["change"], 2) for _, v in ranked], "y_label": "Revenue change ($)"}
            title = "Revenue comparison"
            methodology = f"Compared discounted item revenue from {previous_start} to {current_start} by region."
        else:
            trace[0] = TraceStep(name="classify_question", status="rejected", detail="Supported topics are revenue/sales comparisons and returns.")
            raise ValueError("I can currently analyze revenue or sales comparisons and return rates. Try one of those questions.")
        trace.append(TraceStep(name="run_readonly_sql", status="completed", detail=f"Executed {len(evidence[0].rows)} evidence rows."))
        trace.append(TraceStep(name="deterministic_analysis", status="completed", detail="Calculated comparisons from query output; no generated numbers."))
        trace.append(TraceStep(name="assemble_report", status="completed", detail="Attached chart data, caveats, SQL, and trace references."))
        return AnalysisResponse(
            trace_id=trace_id,
            question=question,
            title=title,
            summary=summary,
            methodology=methodology,
            findings=findings,
            caveats=["This is descriptive analysis of synthetic data; contribution does not prove causation.", "The MVP uses a fixed local dataset and no external model."],
            chart=chart,
            evidence=evidence,
            trace=trace,
        )
    except (SQLValidationError, ValueError) as exc:
        trace.append(TraceStep(name="workflow_failure", status="failed", detail=str(exc)))
        raise
