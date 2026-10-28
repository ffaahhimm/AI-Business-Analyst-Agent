from __future__ import annotations

from typing import Any


def percent_change(current: float, previous: float) -> float:
    return 0 if previous == 0 else (current - previous) / previous * 100


def revenue_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        key = str(row["label"])
        grouped[key] = {"current": float(row["current"]), "previous": float(row["previous"])}
    for value in grouped.values():
        value["change"] = value["current"] - value["previous"]
        value["change_pct"] = percent_change(value["current"], value["previous"])
    return grouped


def return_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        sold = int(row["sold"])
        returned = int(row["returned"])
        result.append(
            {
                "label": row["label"],
                "sold": sold,
                "returned": returned,
                "return_rate": returned / sold * 100 if sold else 0,
            }
        )
    return sorted(result, key=lambda row: row["return_rate"], reverse=True)

