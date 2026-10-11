# Manim MCP Server

This module exposes Manim rendering through Model Context Protocol tools.

## Tools

- `execute_manim_code`: renders a supplied Manim scene at low preview quality
  and returns the generated MP4 path.
- `cleanup_manim_temp_dir`: removes generated content only from the module's
  own media directory.

## Setup

From this directory:

```bash
uv sync
uv run python src/manim_server.py
```

The multi-server clients configure `MANIM_EXECUTABLE` automatically. For a
standalone MCP client, point it to `.venv/bin/manim` on macOS/Linux or the
equivalent executable in your environment.

Generated files are written beneath `src/media/manim_tmp/` and are excluded
from version control.

## Attribution

This module is adapted from the open-source Manim MCP Server by `abhiemj` and
retains its MIT license in `LICENSE.txt`.
