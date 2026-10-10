"""Expense Tracker MCP server backed by SQLite."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date as Date
from pathlib import Path
from typing import Any

from fastmcp import FastMCP


PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = Path(
    os.getenv("EXPENSE_DB_PATH", str(PROJECT_DIR / "expenses.db"))
).expanduser()
CATEGORIES_PATH = PROJECT_DIR / "categories.json"

mcp = FastMCP(
    "ExpenseTracker",
    instructions=(
        "Track expenses, list entries by date range, summarize spending, "
        "and read the category catalog. Dates use YYYY-MM-DD format."
    ),
)


def _connect() -> sqlite3.Connection:
    """Open a configured SQLite connection with dictionary-style rows."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the database schema if it does not already exist."""
    with _connect() as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _validate_date(value: str, field_name: str) -> str:
    """Validate and normalize an ISO calendar date."""
    try:
        return Date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from exc


def _validate_range(start_date: str, end_date: str) -> tuple[str, str]:
    start = _validate_date(start_date, "start_date")
    end = _validate_date(end_date, "end_date")
    if start > end:
        raise ValueError("start_date cannot be later than end_date")
    return start, end


@mcp.tool()
def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = "",
) -> dict[str, Any]:
    """Add an expense and return its generated ID.

    Args:
        date: Expense date in YYYY-MM-DD format.
        amount: Non-negative expense amount.
        category: Main spending category.
        subcategory: Optional spending subcategory.
        note: Optional description of the expense.
    """
    normalized_date = _validate_date(date, "date")
    if amount < 0:
        raise ValueError("amount cannot be negative")

    normalized_category = category.strip()
    if not normalized_category:
        raise ValueError("category cannot be empty")

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO expenses(date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                normalized_date,
                float(amount),
                normalized_category,
                subcategory.strip(),
                note.strip(),
            ),
        )

    return {
        "status": "success",
        "id": cursor.lastrowid,
        "message": "Expense added successfully",
    }


@mcp.tool()
def list_expenses(start_date: str, end_date: str) -> dict[str, Any]:
    """List expenses within an inclusive date range.

    Args:
        start_date: First date to include, in YYYY-MM-DD format.
        end_date: Last date to include, in YYYY-MM-DD format.
    """
    start, end = _validate_range(start_date, end_date)

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, id DESC
            """,
            (start, end),
        ).fetchall()

    expenses = [dict(row) for row in rows]
    return {
        "status": "success",
        "count": len(expenses),
        "expenses": expenses,
    }


@mcp.tool()
def summarize(
    start_date: str,
    end_date: str,
    category: str | None = None,
) -> dict[str, Any]:
    """Summarize expenses by category for an inclusive date range.

    Args:
        start_date: First date to include, in YYYY-MM-DD format.
        end_date: Last date to include, in YYYY-MM-DD format.
        category: Optional exact category filter.
    """
    start, end = _validate_range(start_date, end_date)
    query = """
        SELECT
            category,
            ROUND(SUM(amount), 2) AS total_amount,
            COUNT(*) AS expense_count
        FROM expenses
        WHERE date BETWEEN ? AND ?
    """
    parameters: list[Any] = [start, end]

    if category and category.strip():
        query += " AND category = ?"
        parameters.append(category.strip())

    query += " GROUP BY category ORDER BY total_amount DESC, category ASC"

    with _connect() as connection:
        rows = connection.execute(query, parameters).fetchall()

    summary = [dict(row) for row in rows]
    return {
        "status": "success",
        "start_date": start,
        "end_date": end,
        "category_filter": category.strip() if category else None,
        "grand_total": round(
            sum(float(row["total_amount"] or 0) for row in summary), 2
        ),
        "summary": summary,
    }


@mcp.resource("expense:///categories", mime_type="application/json")
def categories() -> str:
    """Return the expense category catalog as JSON."""
    try:
        content = CATEGORIES_PATH.read_text(encoding="utf-8")
        json.loads(content)
        return content
    except FileNotFoundError:
        return json.dumps({"categories": ["Other"]}, indent=2)
    except json.JSONDecodeError as exc:
        raise ValueError(f"categories.json contains invalid JSON: {exc}") from exc


init_db()


if __name__ == "__main__":
    # STDIO is the default for local MCP hosts and Inspector.
    mcp.run(transport="stdio", show_banner=False)
