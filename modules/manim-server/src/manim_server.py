import os
import shutil
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Manim Server")

MANIM_EXECUTABLE = os.getenv("MANIM_EXECUTABLE", "manim")
BASE_DIR = Path(__file__).resolve().parent / "media"
WORK_DIR = BASE_DIR / "manim_tmp"
BASE_DIR.mkdir(parents=True, exist_ok=True)


@mcp.tool()
def execute_manim_code(manim_code: str) -> str:
    """Render a Manim Python scene and save its MP4 in the local media folder."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    script_path = WORK_DIR / "scene.py"

    try:
        script_path.write_text(manim_code, encoding="utf-8")
        result = subprocess.run(
            [MANIM_EXECUTABLE, "-ql", str(script_path)],
            capture_output=True,
            text=True,
            cwd=WORK_DIR,
            timeout=300,
            check=False,
        )

        if result.returncode == 0:
            videos = list(WORK_DIR.rglob("*.mp4"))
            latest = max(videos, key=lambda path: path.stat().st_mtime) if videos else None
            location = str(latest) if latest else str(WORK_DIR)
            return f"Execution successful. Video generated at: {location}"
        error = result.stderr.strip() or result.stdout.strip() or "Unknown Manim error"
        return f"Execution failed: {error}"
    except subprocess.TimeoutExpired:
        return "Execution failed: Manim rendering exceeded the 300-second limit."
    except Exception as exc:
        return f"Error during execution: {exc}"


@mcp.tool()
def cleanup_manim_temp_dir(directory: str) -> str:
    """Remove a generated directory only when it is inside this server's media folder."""
    try:
        requested = Path(directory).expanduser().resolve()
        media_root = BASE_DIR.resolve()
        if requested == media_root or media_root not in requested.parents:
            return "Cleanup refused: the directory must be inside the Manim media folder."
        if not requested.exists():
            return f"Directory not found: {requested}"
        shutil.rmtree(requested)
        return f"Cleanup successful for directory: {requested}"
    except Exception as exc:
        return f"Failed to clean up directory: {directory}. Error: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
