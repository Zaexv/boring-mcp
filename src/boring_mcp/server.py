"""Boring MCP server — wires all layers together with FastMCP."""

from __future__ import annotations

import os
from typing import Literal

from fastmcp import Context, FastMCP

from boring_mcp.backpressure import BackpressureGuard
from boring_mcp.config import BackpressureConfig
from boring_mcp.repositories.chroma import ChromaRepository
from boring_mcp.scoring.scorer import Sampler, StructureScorer
from boring_mcp.scoring.tiers import Tiers
from boring_mcp.services.behavior_service import BehaviorService
from boring_mcp.services.health_service import HealthService

Transport = Literal["stdio", "http", "sse", "streamable-http"]


def create_server() -> FastMCP:
    """Create and configure the Boring MCP server."""
    mcp = FastMCP(
        "Boring MCP",
        instructions=(
            "Agent behavioral guidance via vector similarity search. "
            "Call the `boring` tool before every other tool call."
        ),
    )

    # Configuration
    chroma_path = os.environ.get("BORING_MCP_CHROMA_PATH", "./data/chroma")

    # Infrastructure
    repository = ChromaRepository(persist_path=chroma_path)
    behavior_service = BehaviorService(repository=repository)
    health_service = HealthService(repository=repository)
    guard = BackpressureGuard()
    config = BackpressureConfig.from_env(os.environ)
    scorer = StructureScorer(tiers=Tiers.from_config(config), sampling=config.sampling)

    def _make_sampler(ctx: Context) -> Sampler:
        async def sampler(prompt: str) -> str:
            response = await ctx.sample(prompt)
            return response.text or ""

        return sampler

    # --- Tool: boring (backpressure — must be called before every other tool) ---
    @mcp.tool()
    async def boring() -> str:
        """Sleep for 30 seconds. MANDATORY before every other tool call.

        This is intentional backpressure. The agent must call this tool
        before invoking any other tool. Skipping it will cause denial.
        """
        return await guard.apply_backpressure()

    # --- Tool: store_behavior ---
    @mcp.tool()
    async def store_behavior(
        sentence: str,
        collection: str,
        ctx: Context,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Store a behavioral sentence. Backpressure scales with input structure.

        Highly structured input applies directly; vague input triggers a boring
        pause. No prior `boring` call is required for this tool.

        Args:
            sentence: The behavioral instruction to store.
            collection: Collection name (e.g., 'tone', 'persona').
            metadata: Optional key-value metadata.
        """
        from boring_mcp.tools.behaviors import store_behavior as _handler

        message = await guard.scored_backpressure(sentence, scorer, _make_sampler(ctx))
        handled = await _handler(
            sentence, collection, metadata, service=behavior_service
        )
        return f"{message}\n{handled}"

    # --- Tool: query_behaviors ---
    @mcp.tool()
    async def query_behaviors(
        query: str,
        ctx: Context,
        collection: str | None = None,
        top_k: int = 5,
    ) -> str:
        """Retrieve relevant behaviors. Backpressure scales with query structure.

        No prior `boring` call is required for this tool.

        Args:
            query: The context to match against.
            collection: Filter by collection (queries all if omitted).
            top_k: Number of results (default: 5).
        """
        from boring_mcp.tools.behaviors import query_behaviors as _handler

        message = await guard.scored_backpressure(query, scorer, _make_sampler(ctx))
        handled = await _handler(query, collection, top_k, service=behavior_service)
        return f"{message}\n{handled}"

    # --- Tool: delete_behavior ---
    @mcp.tool()
    @guard.guarded
    async def delete_behavior(behavior_id: str) -> str:
        """Remove a specific behavior by ID.

        Args:
            behavior_id: The behavior's ID.
        """
        from boring_mcp.tools.behaviors import delete_behavior as _handler

        return await _handler(behavior_id, service=behavior_service)

    # --- Tool: list_collections ---
    @mcp.tool()
    @guard.guarded
    async def list_collections() -> str:
        """List all available behavior collections."""
        from boring_mcp.tools.collections import list_collections as _handler

        return await _handler(service=behavior_service)

    # --- Tool: health_check ---
    @mcp.tool()
    @guard.guarded
    async def health_check() -> str:
        """Returns service health status including ChromaDB connectivity."""
        from boring_mcp.tools.health import health_check as _handler

        return await _handler(service=health_service)

    # --- Resource: behaviors://{collection} ---
    @mcp.resource("behaviors://{collection}")
    async def get_collection_resource(collection: str) -> str:
        """Get all behaviors in a given collection."""
        from boring_mcp.resources.behaviors import get_collection_behaviors

        return await get_collection_behaviors(collection, service=behavior_service)

    # --- Resource: behaviors://summary ---
    @mcp.resource("behaviors://summary")
    async def get_summary_resource() -> str:
        """Get a summary of all collections and their counts."""
        from boring_mcp.resources.behaviors import get_behaviors_summary

        return await get_behaviors_summary(service=behavior_service)

    return mcp


# Module-level server instance for entry point
_server: FastMCP | None = None


def get_server() -> FastMCP:
    """Get or create the server singleton."""
    global _server  # noqa: PLW0603
    if _server is None:
        _server = create_server()
    return _server


def main() -> None:
    """Entry point for the boring-mcp command."""
    raw = os.environ.get("BORING_MCP_TRANSPORT", "stdio")
    valid_transports: dict[str, Transport] = {
        "stdio": "stdio",
        "http": "http",
        "sse": "sse",
        "streamable-http": "streamable-http",
    }
    transport: Transport = valid_transports.get(raw, "stdio")
    server = get_server()
    server.run(transport=transport)


if __name__ == "__main__":
    main()
