"""
OpenRouter LLM Client
=====================
Calls the OpenRouter API (meta-llama/llama-3-8b-instruct) as a fallback
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
MODEL = "meta-llama/llama-3-8b-instruct"

SYSTEM_PROMPT_BASE = (
    "You are Krishi Mitra, an agricultural assistant helping farmers "
    "with crop selection, soil management, fertilizers, irrigation, "
    "and pest control. Provide clear and practical farming advice."
)

# Map language codes to full language names for response language instruction
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "gu": "Gujarati",
    "bn": "Bengali",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ne": "Nepali",
    "sd": "Sindhi",
    "sa": "Sanskrit",
    "mai": "Maithili",
    "mni": "Manipuri",
    "ks": "Kashmiri",
    "gom": "Konkani",
    "brx": "Bodo",
    "sat": "Santali",
    "doi": "Dogri",
    "ur": "Urdu",
}

FALLBACK_RESPONSES = {
    "en": (
        "I couldn't access external knowledge right now, but generally "
        "farmers can consult agricultural experts or local Krishi Vigyan "
        "Kendra (KVK) for region-specific advice."
    ),
    "hi": (
        "अभी बाहरी जानकारी तक पहुँचने में समस्या हो रही है। "
        "किसान अपने क्षेत्र की सलाह के लिए कृषि विशेषज्ञों या "
        "स्थानीय कृषि विज्ञान केन्द्र (KVK) से संपर्क कर सकते हैं।"
    ),
}

FALLBACK_RESPONSE = FALLBACK_RESPONSES["en"]


def _get_fallback(lang_code: str = "en") -> str:
    """Return a fallback message in the requested language if available, else English."""
    return FALLBACK_RESPONSES.get(lang_code, FALLBACK_RESPONSES["en"])


def call_openrouter(user_message: str) -> str:
    """
    Send a chat completion request to OpenRouter.
    Always generates responses in English — translation is handled separately.

    Args:
        user_message: The user's question (in English).

    Returns:
        The assistant's reply in English. Never returns empty — returns a
        fallback message if the API call fails.
    """
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not configured, returning fallback")
        return FALLBACK_RESPONSE

    system_content = f"{SYSTEM_PROMPT_BASE} Always respond in English."

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
