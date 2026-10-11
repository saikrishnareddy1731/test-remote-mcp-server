# MCP Math Server

A ready-to-run FastMCP server exposing seven typed arithmetic tools:

- `add`
- `subtract`
- `multiply`
- `divide`
- `power`
- `modulo`
- `square_root`

## Requirements

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Node.js/`npx` only when using MCP Inspector

## Install and test

```bash
cd mcp-math-server
uv sync
uv run pytest
```

## Open in MCP Inspector

FastMCP 4 uses the `dev inspector` subcommand:

```bash
uv run fastmcp dev inspector main.py
```

Do not separately start `npx @modelcontextprotocol/inspector`; the command above
starts the server and Inspector together.

## Run as a STDIO MCP server

```bash
uv run main.py
```

The process waits for an MCP client over standard input/output. This is expected;
it is not a web page.

## Inspector manual STDIO configuration

If you start MCP Inspector separately, configure:

```text
Transport: STDIO
Command:   uv
Arguments: run main.py
```

Run the Inspector from this project directory so it can find `main.py`.

## Example MCP host configuration

Replace `/absolute/path/to/mcp-math-server` with the extracted project path:

```json
{
  "mcpServers": {
    "math": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-math-server",
        "run",
        "main.py"
      ]
    }
  }
}
```
