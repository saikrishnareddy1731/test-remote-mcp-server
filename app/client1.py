import asyncio
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
MATH_SERVER = REPO_ROOT / "modules" / "math-server"
MANIM_SERVER = REPO_ROOT / "modules" / "manim-server"

SERVERS = {
    "math": {
        "transport": "stdio",
        "command": str(MATH_SERVER / ".venv" / "bin" / "python"),
        "args": [str(MATH_SERVER / "main.py")],
    },
    "expense": {
        "transport": "stdio",
        "command": str(REPO_ROOT / ".venv" / "bin" / "fastmcp"),
        "args": [
            "run",
            str(REPO_ROOT / "main.py"),
            "--no-banner",
        ],
    },
    "manim": {
        "transport": "stdio",
        "command": str(MANIM_SERVER / ".venv" / "bin" / "python"),
        "args": [str(MANIM_SERVER / "src" / "manim_server.py")],
        "env": {
            "MANIM_EXECUTABLE": str(MANIM_SERVER / ".venv" / "bin" / "manim"),
        },
    },
}


async def main() -> None:
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()

    print(f"Loaded {len(tools)} tools:\n")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    named_tools = {tool.name: tool for tool in tools}
    print("Available tools:", named_tools.keys())

    llm = ChatOpenAI(model="gpt-5")
    llm_with_tools = llm.bind_tools(tools)

    prompt = "Draw a triangle rotating in place using the Manim tool"
    user_message = HumanMessage(content=prompt)
    response = await llm_with_tools.ainvoke([user_message])

    if not response.tool_calls:
        print(f"Model response: {response.content}")
        return

    tool_call = response.tool_calls[0]
    selected_tool = tool_call["name"]
    selected_tool_args = tool_call["args"]
    if selected_tool not in named_tools:
        raise ValueError(f"Model selected an unknown tool: {selected_tool}")

    tool_result = await named_tools[selected_tool].ainvoke(selected_tool_args)
    print(f"Tool result: {tool_result}")

    tool_message = ToolMessage(
        content=tool_result,
        tool_call_id=tool_call["id"],
        name=selected_tool,
    )
    final_response = await llm_with_tools.ainvoke(
        [user_message, response, tool_message]
    )
    print(f"Final response: {final_response.content}")


if __name__ == "__main__":
    asyncio.run(main())
