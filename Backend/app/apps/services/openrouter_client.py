"""
OpenRouter LLM Client
=====================
Calls the OpenRouter API (mistralai/mistral-7b-instruct) as a fallback
when no FAQ match is found.

Environment variable required: OPENROUTER_API_KEY
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-7b-instruct"

SYSTEM_PROMPT = (
    "You are an agricultural assistant helping farmers. "
    "Provide helpful advice about crops, soil, fertilizers, and farming practices. "
    "Answer clearly and simply."
)

FALLBACK_RESPONSE = (
    "I'm currently unable to retrieve external knowledge, but based on general "
    "farming practices, I recommend consulting your local Krishi Vigyan Kendra "
    "(KVK) or agriculture extension officer for specific advice on your query. "
    "They can provide region-specific guidance on crops, soil management, and "
    "best farming practices."
)


def call_openrouter(user_message: str, lang_code: str = "en") -> str:
    """
    Send a chat completion request to OpenRouter.

    Args:
        user_message: The user's question.
        lang_code: Language code for response (e.g. 'hi', 'gu', 'en').

    Returns:
        The assistant's reply text. Never returns empty — returns a
        fallback message if the API call fails.
    """
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not configured, returning fallback")
        return FALLBACK_RESPONSE

    # Build system prompt with language instruction
    system_content = SYSTEM_PROMPT
    if lang_code and lang_code != "en":
        system_content += f"\n\nIMPORTANT: You MUST reply in the language with code '{lang_code}'. Every word of your response must be in that language."

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_message},
                ],
            },
            timeout=30,
        )

        if resp.status_code != 200:
            logger.error(
                "OpenRouter API error %s: %s",
                resp.status_code,
                resp.text[:500],
            )
            return FALLBACK_RESPONSE

        data = resp.json()
        text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not text:
            logger.warning("Empty response from OpenRouter")
            return FALLBACK_RESPONSE

        return text

    except requests.Timeout:
        logger.error("OpenRouter request timed out")
        return FALLBACK_RESPONSE
    except requests.RequestException as e:
        logger.error("OpenRouter request failed: %s", e)
        return FALLBACK_RESPONSE
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Failed to parse OpenRouter response: %s", e)
        return FALLBACK_RESPONSE
