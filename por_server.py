"""MCP server for querying UK Scouts Policy, Organisation and Rules (POR)."""

import asyncio
import logging
import sys
from dataclasses import dataclass, field

import fitz  # pymupdf
from curl_cffi.requests import AsyncSession
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (stdout is reserved for MCP stdio transport)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("por-mcp")

mcp = FastMCP(
    "por",
    instructions="MCP server for querying UK Scouts Policy, Organisation and Rules (POR).",
)

PDF_URL = "https://prod-cms.scouts.org.uk//media/ddedf51l/por-autumn-2025.pdf"


@dataclass
class PorPage:
    page_num: int
    text: str


@dataclass
class PorCache:
    _pages: list[PorPage] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def ensure_loaded(self) -> None:
        async with self._lock:
            if self._pages:
                logger.debug("PDF already cached (%d pages)", len(self._pages))
                return

            logger.info("Downloading PDF from %s", PDF_URL)
            try:
                async with AsyncSession(impersonate="chrome") as client:
                    resp = await client.get(PDF_URL)
                    resp.raise_for_status()
            except Exception:
                logger.exception("Failed to download PDF")
                raise

            logger.info(
                "PDF downloaded (%d bytes), extracting text...",
                len(resp.content),
            )
            try:
                doc = fitz.open(stream=resp.content, filetype="pdf")
            except Exception:
                logger.exception("Failed to open PDF with pymupdf")
                raise

            pages: list[PorPage] = []
            for i, page in enumerate(doc):
                text = page.get_text()
                cleaned = "\n".join(
                    line.strip() for line in text.splitlines() if line.strip()
                )
                if cleaned:
                    pages.append(PorPage(page_num=i + 1, text=cleaned))
            total_pages = len(doc)
            doc.close()
            self._pages = pages
            logger.info(
                "PDF loaded: %d total pages, %d with text content",
                total_pages,
                len(self._pages),
            )

    async def search(self, query: str) -> list[PorPage]:
        async with self._lock:
            q = query.lower()
            results = [p for p in self._pages if q in p.text.lower()]
            logger.info("Search for %r: %d hits", query, len(results))
            return results


_cache = PorCache()


@mcp.tool(description="Free-text search over UK Scouts POR (including annexes).")
async def search_por(query: str) -> str:
    """Search UK Scouts Policy, Organisation and Rules (POR).

    Args:
        query: Search phrase to look for in POR content.
    """
    logger.info("search_por called with query=%r", query)

    if not query.strip():
        logger.warning("Empty query received")
        return "Query must not be empty."

    try:
        await _cache.ensure_loaded()
    except Exception:
        logger.exception("Failed to load POR PDF")
        return "Error: failed to load the POR document. Check server logs for details."

    hits = await _cache.search(query)

    if not hits:
        return f'No POR matches found for query: "{query}".'

    result = f'POR search results for query: "{query}" ({len(hits)} page hits).\n\n'
    for i, hit in enumerate(hits[:10]):
        snippet = "\n".join(hit.text.splitlines()[:40])
        result += f"Result {i + 1} (PDF page {hit.page_num}):\n\n{snippet}\n\n---\n\n"

    return result


if __name__ == "__main__":
    logger.info("Starting POR MCP server (stdio transport)")
    mcp.run(transport="stdio")
