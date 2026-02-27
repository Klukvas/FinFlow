import asyncio
import hashlib
import json
import logging
from typing import Optional
from uuid import UUID

from app.clients.financial_data_client import fetch_data
from app.exceptions import InsufficientDataError
from app.prompts.registry import PROMPT_DATA_SOURCES, PROMPT_MIN_THRESHOLDS
from app.schemas.prompts import PromptId

logger = logging.getLogger(__name__)


async def aggregate_data(
    prompt_id: PromptId,
    user_id: int,
    workspace_id: UUID,
) -> tuple[str, str]:
    """Fetch all required data for a prompt in parallel.

    Returns (formatted_data_string, data_hash).
    Raises InsufficientDataError if minimum thresholds are not met.
    """
    sources = PROMPT_DATA_SOURCES.get(prompt_id, [])
    if not sources:
        raise InsufficientDataError("No data sources configured for this prompt")

    # Fetch all sources in parallel
    tasks = [fetch_data(source, user_id, workspace_id) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combine results
    aggregated: dict[str, Optional[dict]] = {}
    for source, result in zip(sources, results):
        if isinstance(result, Exception):
            logger.warning(f"Data fetch exception for {source}: {result}")
            aggregated[source] = None
        else:
            aggregated[source] = result

    # Check minimum thresholds
    thresholds = PROMPT_MIN_THRESHOLDS.get(prompt_id, {})
    for source, min_count in thresholds.items():
        data = aggregated.get(source)
        if data is None:
            logger.warning(
                f"Insufficient data: source={source} unavailable, "
                f"user={user_id}, workspace={workspace_id}"
            )
            raise InsufficientDataError(
                "Not enough financial data for this analysis. "
                "Please add more records and try again."
            )
        items = data.get("items", [])
        if len(items) < min_count:
            logger.warning(
                f"Insufficient data: source={source}, required={min_count}, "
                f"found={len(items)}, user={user_id}, workspace={workspace_id}"
            )
            raise InsufficientDataError(
                "Not enough financial data for this analysis. "
                "Please add more records and try again."
            )

    # Resolve category IDs to names using categories data
    _resolve_category_names(aggregated)

    # Format data as readable text for LLM
    formatted = _format_data(aggregated)

    # Compute hash for caching
    data_hash = hashlib.sha256(formatted.encode()).hexdigest()

    return formatted, data_hash


def _resolve_category_names(aggregated: dict[str, Optional[dict]]) -> None:
    """Replace category_id with category name in expenses, incomes, recurring.

    Creates new item dicts instead of mutating the originals.
    """
    categories_data = aggregated.get("categories")
    if not categories_data:
        return

    cat_map: dict[int, str] = {
        item["id"]: item["name"]
        for item in categories_data.get("items", [])
        if "id" in item and "name" in item
    }
    if not cat_map:
        return

    for source in ("expenses", "incomes", "recurring"):
        data = aggregated.get(source)
        if not data:
            continue
        new_items = []
        for item in data.get("items", []):
            cat_id = item.get("category_id")
            if cat_id is not None:
                new_item = {k: v for k, v in item.items() if k != "category_id"}
                new_item["category"] = cat_map.get(cat_id, f"Unknown ({cat_id})")
                new_items.append(new_item)
            else:
                new_items.append(item)
        aggregated[source] = {**data, "items": new_items}


MAX_ITEMS_PER_SOURCE = 100


def _format_data(aggregated: dict[str, Optional[dict]]) -> str:
    """Format aggregated data as a readable text block for the LLM."""
    sections = []
    for source, data in aggregated.items():
        if data is None:
            continue
        items = data.get("items", [])
        if not items:
            continue
        total = len(items)
        section_lines = [f"=== {source.upper()} ({total} records) ==="]
        for item in items[:MAX_ITEMS_PER_SOURCE]:
            section_lines.append(json.dumps(item, ensure_ascii=False, default=str))
        if total > MAX_ITEMS_PER_SOURCE:
            section_lines.append(f"... and {total - MAX_ITEMS_PER_SOURCE} more records (truncated)")
        sections.append("\n".join(section_lines))
    return "\n\n".join(sections)
