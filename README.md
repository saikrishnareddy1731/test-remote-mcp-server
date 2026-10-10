# Expense Tracker MCP Server

A FastMCP server backed by SQLite. It exposes:

- `add_expense`
- `list_expenses`
- `summarize`
- `expense:///categories`

## Install and test

```bash
cd "/Users/saikrishna/AI Engineer/MCP/expense-tracker-mcp-server"
uv sync
uv run pytest
```

## Run with MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector@0.17.2 \
  uv run fastmcp run main.py --no-banner
```

Open **Tools**, click **List Tools**, and select a tool.

## Run as a STDIO server

```bash
uv run main.py
```

The process waits for an MCP client over standard input/output. It is not a web
page and normally prints no output while idle.

## Database location

By default, data is stored in `expenses.db` beside `main.py` when that directory
is writable. In a read-only hosted environment, the server automatically falls
back to `/tmp/expense-tracker/expenses.db`. Override the path explicitly with:

```bash
EXPENSE_DB_PATH=/tmp/expenses.db uv run main.py
```

The `/tmp` fallback is ephemeral. Point `EXPENSE_DB_PATH` at persistent storage
in production if expenses must survive application restarts or redeployments.

## Remote proxy

`proxy.py` proxies the deployed endpoint configured in that file. Test it with:

```bash
npx -y @modelcontextprotocol/inspector@0.17.2 \
  uv run fastmcp run proxy.py --no-banner
```
