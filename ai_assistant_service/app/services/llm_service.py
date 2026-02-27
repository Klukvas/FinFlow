import json
import logging
from typing import Optional

import anthropic

from app.config import settings
from app.exceptions import LLMServiceError, LLMRateLimitError
from app.prompts.templates import SYSTEM_PROMPT, PROMPT_TEMPLATES
from app.schemas.analysis import AnalysisSection
from app.schemas.prompts import PromptId

logger = logging.getLogger(__name__)

_client: Optional[anthropic.AsyncAnthropic] = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def _build_user_prompt(prompt_id: PromptId, language: str, data: str) -> str:
    templates = PROMPT_TEMPLATES.get(prompt_id, {})
    template = templates.get(language, templates.get("en", ""))
    wrapped_data = f"<financial_data>\n{data}\n</financial_data>"
    return template.format(data=wrapped_data)


def _parse_sections(raw_text: str) -> list[AnalysisSection]:
    """Parse LLM response JSON into sections with fallback."""
    text = raw_text.strip()

    # Try to extract JSON array from the response
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [
                AnalysisSection(
                    title=item.get("title", "Analysis"),
                    content=item.get("content", ""),
                    priority=item.get("priority", "medium"),
                )
                for item in parsed
                if isinstance(item, dict) and item.get("content")
            ]
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON, using fallback")

    # Fallback: treat entire response as a single section
    return [
        AnalysisSection(
            title="Analysis",
            content=raw_text.strip(),
            priority="medium",
        )
    ]


async def analyze(
    prompt_id: PromptId, language: str, aggregated_data: str
) -> list[AnalysisSection]:
    """Send data to LLM and get structured analysis sections."""
    client = _get_client()
    system = SYSTEM_PROMPT.format(language=language)
    user_prompt = _build_user_prompt(prompt_id, language, aggregated_data)

    try:
        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text
        logger.info(
            f"LLM response received: prompt={prompt_id.value}, "
            f"tokens_in={response.usage.input_tokens}, tokens_out={response.usage.output_tokens}"
        )
        return _parse_sections(raw_text)

    except anthropic.RateLimitError as e:
        logger.error(f"Anthropic rate limit: {e}")
        raise LLMRateLimitError()
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error (prompt={prompt_id.value}, status={getattr(e, 'status_code', 'N/A')}): {e}")
        raise LLMServiceError("AI service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected LLM error: {e}")
        raise LLMServiceError()
