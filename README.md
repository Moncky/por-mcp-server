# POR MCP Server

MCP server that lets an LLM query the UK Scouts Policy, Organisation and Rules (POR), including Scottish variations and annexes. On first use it downloads the official POR PDF and caches the extracted text in memory, then exposes a single MCP tool: `search_por`.

## Build and run (uv)

```bash
cd por-mcp-server
uv run por_server.py
```

The server speaks MCP over stdio, so you normally do **not** run it directly. Instead, point your MCP client (e.g. Cursor, Claude Desktop) at the server.

Example Claude Desktop config snippet:

```jsonc
{
  "mcpServers": {
    "por": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/absolute/path/to/por-mcp-server",
        "por_server.py"
      ]
    }
  }
}
```

## Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run por_server.py
```

## Build and run (Docker)

```bash
cd por-mcp-server
docker build -t por-mcp-server:latest .
```

To run the server via Docker (stdio MCP, no ports exposed):

```bash
docker run -i --rm por-mcp-server:latest
```

Example Claude Desktop config that runs via Docker:

```jsonc
{
  "mcpServers": {
    "por": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "por-mcp-server:latest"
      ]
    }
  }
}
```

## Tool: `search_por`

- **Name**: `search_por`
- **Description**: Free-text search over UK Scouts POR (including annexes).
- **Input schema**:
  - `query` (string, required) – search phrase.
- **Behaviour**:
  - On first call, downloads the official POR PDF (~7MB) and extracts text from all 429 pages (~1.5s).
  - Performs a case-insensitive substring search over the cached text.
  - Returns up to 10 matching pages with snippets and PDF page numbers so the LLM can quote and reason about POR.

## Example queries

Once the server is connected to your MCP client, you can ask your LLM questions like:

- *"What are the rules around overnight camping with Scouts?"* — the LLM will call `search_por` with a query like `"camping"` or `"nights away"` and cite the relevant POR chapters.
- *"Can a Beaver Scout section accept a 5-year-old?"* — triggers a search for age-related rules and membership requirements.
- *"What safeguarding training is required for adult volunteers?"* — searches for DBS, safety, and training policies.
- *"Are there specific rules for water activities in Scotland?"* — finds Scottish POR variations and water activity annexes.
- *"What is the minimum adult-to-young-person ratio for a hillwalking expedition?"* — searches ratios, adventurous activities, and supervision rules.

The LLM handles choosing the right search terms, interpreting the results, and quoting POR back to you with page references — you just ask your question in plain English.

## License

MIT — see [LICENSE](LICENSE).
