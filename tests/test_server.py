import asyncio
import importlib

from fastmcp import Client


def test_expense_tools_end_to_end(tmp_path, monkeypatch):
    database = tmp_path / "expenses.db"
    monkeypatch.setenv("EXPENSE_DB_PATH", str(database))

    import main

    main = importlib.reload(main)

    async def scenario():
        async with Client(main.mcp) as client:
            added = await client.call_tool(
                "add_expense",
                {
                    "date": "2026-10-10",
                    "amount": 25.50,
                    "category": "Food & Dining",
                    "subcategory": "Dinner",
                    "note": "Test meal",
                },
            )
            assert added.data["status"] == "success"

            listed = await client.call_tool(
                "list_expenses",
                {"start_date": "2026-10-01", "end_date": "2026-10-31"},
            )
            assert listed.data["count"] == 1
            assert listed.data["expenses"][0]["amount"] == 25.50

            summary = await client.call_tool(
                "summarize",
                {"start_date": "2026-10-01", "end_date": "2026-10-31"},
            )
            assert summary.data["grand_total"] == 25.50
            assert summary.data["summary"][0]["expense_count"] == 1

            resource = await client.read_resource("expense:///categories")
            assert resource

    asyncio.run(scenario())


def test_invalid_date_range(tmp_path, monkeypatch):
    monkeypatch.setenv("EXPENSE_DB_PATH", str(tmp_path / "expenses.db"))

    import main

    main = importlib.reload(main)

    async def scenario():
        async with Client(main.mcp) as client:
            result = await client.call_tool(
                "list_expenses",
                {"start_date": "2026-11-01", "end_date": "2026-10-01"},
                raise_on_error=False,
            )
            assert result.is_error

    asyncio.run(scenario())
