import asyncio
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI


load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
MATH_SERVER = REPO_ROOT / "modules" / "math-server"
MANIM_SERVER = REPO_ROOT / "modules" / "manim-server"
MANIM_MEDIA_DIR = MANIM_SERVER / "src" / "media" / "manim_tmp"

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


def extract_text(content: Any) -> str:
    """Extract displayable text from a LangChain content value."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def latest_manim_video() -> Path | None:
    """Return the newest rendered MP4, if Manim created one."""
    if not MANIM_MEDIA_DIR.exists():
        return None
    videos = list(MANIM_MEDIA_DIR.rglob("*.mp4"))
    return max(videos, key=lambda path: path.stat().st_mtime) if videos else None


async def stream_response(model, messages, placeholder):
    """Stream into a Streamlit placeholder and return message plus visible text."""
    complete_message = None
    rendered_text = ""

    async for chunk in model.astream(messages):
        rendered_text += extract_text(chunk.content)
        if rendered_text:
            placeholder.markdown(rendered_text)
        complete_message = (
            chunk if complete_message is None else complete_message + chunk
        )

    if complete_message is None:
        raise RuntimeError("The model returned no response chunks.")
    return complete_message, rendered_text


async def run_agent(prompt: str) -> tuple[str, str | None]:
    status_placeholder = st.empty()
    status = status_placeholder.status("Connecting to MCP servers...", expanded=False)
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()
    named_tools = {tool.name: tool for tool in tools}
    status.update(label=f"Connected · {len(tools)} tools available", state="running")

    llm = ChatOpenAI(
        model="gpt-5",
        streaming=True,
        reasoning_effort="minimal",
        timeout=120,
        max_retries=2,
    )
    llm_with_tools = llm.bind_tools(tools)

    system_message = SystemMessage(
        content=(
            f"Today is {date.today().isoformat()}. You are an MCP assistant with "
            "math, expense, and Manim tools. For expense requests, resolve relative "
            "dates such as 'last 2 weeks' using today's date and call the appropriate "
            "expense tool without asking the user to provide exact dates. For animation "
            "requests, call execute_manim_code with complete executable Manim code."
        )
    )
    conversation = [system_message]
    for message in st.session_state.messages[:-1]:
        if message["role"] == "user":
            conversation.append(HumanMessage(content=message["content"]))
        else:
            conversation.append(AIMessage(content=message["content"]))
    user_message = HumanMessage(content=prompt)
    conversation.append(user_message)

    status.update(label="Choosing the best MCP tool...", state="running")
    first_placeholder = st.empty()
    response, first_text = await stream_response(
        llm_with_tools,
        conversation,
        first_placeholder,
    )

    if not response.tool_calls:
        status_placeholder.empty()
        if not first_text:
            first_text = "I couldn't produce a response. Please try again."
            first_placeholder.markdown(first_text)
        return first_text, None

    tool_call = response.tool_calls[0]
    selected_tool = tool_call["name"]
    selected_tool_args = tool_call["args"]

    if selected_tool not in named_tools:
        raise ValueError(f"Model selected an unknown tool: {selected_tool}")

    first_placeholder.empty()
    status.update(label=f"Running {selected_tool}...", state="running")

    tool_result = await named_tools[selected_tool].ainvoke(selected_tool_args)

    tool_message = ToolMessage(
        content=tool_result,
        tool_call_id=tool_call["id"],
        name=selected_tool,
    )

    status.update(label="Preparing the answer...", state="running")
    _, final_text = await stream_response(
        llm_with_tools,
        [*conversation, response, tool_message],
        st.empty(),
    )
    status_placeholder.empty()

    video_value = None
    if selected_tool == "execute_manim_code":
        video_path = latest_manim_video()
        if video_path:
            st.video(str(video_path))
            st.caption(str(video_path))
            video_value = str(video_path)
        else:
            st.warning("Manim completed, but no generated MP4 was found.")

    return final_text, video_value


st.set_page_config(
    page_title="MCP Chat",
    page_icon="🧰",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    :root {
        --ink: #f8fafc;
        --muted: #a5b4cf;
        --violet: #8b5cf6;
        --cyan: #22d3ee;
        --pink: #f472b6;
    }
    .stApp {
        color: var(--ink);
        background:
            radial-gradient(circle at 12% 12%, rgba(91, 33, 182, .35), transparent 30%),
            radial-gradient(circle at 88% 18%, rgba(8, 145, 178, .28), transparent 30%),
            radial-gradient(circle at 55% 90%, rgba(219, 39, 119, .16), transparent 35%),
            linear-gradient(145deg, #050816 0%, #0b1023 48%, #090d1c 100%);
        background-attachment: fixed;
    }
    .block-container {max-width: 920px; padding-top: 2rem; padding-bottom: 8rem;}
    header[data-testid="stHeader"] {background: rgba(5, 8, 22, .72); backdrop-filter: blur(16px);}
    [data-testid="stToolbar"] {color: #cbd5e1;}
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1023 0%, #111936 100%);
        border-right: 1px solid rgba(139, 92, 246, .22);
    }
    section[data-testid="stSidebar"] * {color: #e2e8f0;}
    .hero-card {
        position: relative;
        overflow: hidden;
        padding: 1.65rem 1.8rem;
        border-radius: 28px;
        color: white;
        border: 1px solid rgba(255,255,255,.16);
        background: linear-gradient(120deg, rgba(91,33,182,.94), rgba(109,40,217,.90) 45%, rgba(8,145,178,.90));
        box-shadow: 0 24px 70px rgba(76, 29, 149, .38), inset 0 1px 0 rgba(255,255,255,.22);
        margin-bottom: 1.2rem;
    }
    .hero-card:after {
        content: ""; position: absolute; width: 220px; height: 220px;
        right: -55px; top: -100px; border-radius: 50%;
        background: rgba(255,255,255,.16); filter: blur(2px);
    }
    .hero-card h1 {margin: 0; font-size: 2.35rem; letter-spacing: -.04em;}
    .hero-card p {margin: .42rem 0 .8rem; color: rgba(255,255,255,.82); font-size: 1.02rem;}
    .server-row {display:flex; gap:.55rem; flex-wrap:wrap;}
    .server-pill {
        display:inline-flex; align-items:center; gap:.38rem; padding:.38rem .68rem;
        border-radius:999px; font-size:.78rem; font-weight:650;
        background:rgba(7,12,32,.32); border:1px solid rgba(255,255,255,.18);
    }
    .pulse {width:7px; height:7px; border-radius:50%; background:#4ade80; box-shadow:0 0 12px #4ade80;}
    [data-testid="stChatMessage"] {
        padding: 1.05rem 1.15rem;
        border: 1px solid rgba(148, 163, 184, .15);
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(24,32,60,.86), rgba(15,23,42,.82));
        box-shadow: 0 12px 38px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.04);
        backdrop-filter: blur(18px);
        margin-bottom: .85rem;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {color:#edf2ff;}
    [data-testid="stChatMessageAvatarUser"] {
        background: linear-gradient(135deg, #ec4899, #8b5cf6) !important;
        box-shadow: 0 0 22px rgba(236,72,153,.32);
    }
    [data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #06b6d4, #3b82f6) !important;
        box-shadow: 0 0 22px rgba(34,211,238,.28);
    }
    [data-testid="stBottom"] {
        background: linear-gradient(180deg, transparent, rgba(5,8,22,.96) 35%);
    }
    [data-testid="stChatInput"] {max-width: 920px; margin: 0 auto;}
    [data-testid="stChatInput"] > div {
        border: 1px solid rgba(139,92,246,.62) !important;
        border-radius: 20px !important;
        background: rgba(16,24,48,.92) !important;
        box-shadow: 0 16px 55px rgba(0,0,0,.35), 0 0 28px rgba(109,40,217,.12);
    }
    [data-testid="stChatInput"] textarea {color:#f8fafc !important; caret-color:#22d3ee;}
    [data-testid="stChatInput"] textarea::placeholder {color:#7f8da8 !important;}
    [data-testid="stStatusWidget"] {
        border-radius: 14px; color:#dbeafe;
        background:rgba(30,41,72,.75); border-color:rgba(34,211,238,.22);
    }
    .empty-state {
        text-align:center; padding:2.2rem 1rem 1rem; color:#93a4c3;
    }
    .empty-state .orb {
        display:grid; place-items:center; width:70px; height:70px; margin:0 auto 1rem;
        border-radius:22px; font-size:1.8rem;
        background:linear-gradient(135deg,#7c3aed,#0891b2);
        box-shadow:0 16px 40px rgba(109,40,217,.35);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="hero-card">
      <h1>✦ Nexus MCP</h1>
      <p>Your intelligent workspace for calculations, expenses, and cinematic animations.</p>
      <div class="server-row">
        <span class="server-pill"><i class="pulse"></i> Math</span>
        <span class="server-pill"><i class="pulse"></i> Expenses</span>
        <span class="server-pill"><i class="pulse"></i> Manim Studio</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("MCP servers")
    st.success("Math Server")
    st.success("Expense Tracker")
    st.success("Manim Server")
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
          <div class="orb">✦</div>
          <strong style="color:#e2e8f0;font-size:1.1rem">What will we create today?</strong>
          <div style="margin-top:.35rem">Ask a calculation, explore spending, or generate a Manim animation.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    avatar = "🧑" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("video"):
            st.video(message["video"])

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        try:
            answer, video = asyncio.run(run_agent(prompt))
            if not answer:
                answer = "The requested tool completed successfully."
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "video": video,
                }
            )
        except Exception as exc:
            st.exception(exc)
