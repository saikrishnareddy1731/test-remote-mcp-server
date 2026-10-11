# Nexus MCP Client

This package combines the repository's expense, math, and Manim MCP servers
through LangChain's `MultiServerMCPClient`.

- `client1.py` is a minimal terminal demonstration of discovery, tool routing,
  tool execution, and the final model response.
- `client2.py` is the stateful Streamlit chat application with streamed answers
  and inline Manim video playback.

## Run

```bash
cp .env.example .env
# Add OPENAI_API_KEY to .env
uv sync
uv run streamlit run client2.py
```

The paths to all three MCP servers are resolved relative to the repository, so
the client works after cloning without editing machine-specific paths.
