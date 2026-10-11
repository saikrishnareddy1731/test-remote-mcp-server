# Expense Tracker MCP Server

This module provides the SQLite-backed expense tools used by the Nexus MCP
client:

- `add_expense`
- `list_expenses`
- `summarize`

## Run and test

```bash
uv sync
uv run pytest
uv run fastmcp run main.py --no-banner
```

Expense data is stored in `expenses.db` locally and that file is excluded from
version control. Set `EXPENSE_DB_PATH` to use a different writable database
location.

The repository root retains a matching entry point for compatibility with the
existing FastMCP Gateway deployment.
