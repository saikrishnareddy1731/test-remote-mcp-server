from fastmcp.server import create_proxy

mcp = create_proxy(
    "https://splendid-gold-dingo.fastmcp.app/mcp",
    name="Sai Server Proxy",
)

if __name__ == "__main__":
    mcp.run()