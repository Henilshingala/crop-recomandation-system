"""
Translation Service
===================
Uses OpenRouter LLM to translate assistant responses into the user's
selected language. This is a lightweight post-processing layer —
it does NOT modify the FAQ search or assistant logic.

Environment variable required: OPENROUTER_API_KEY
"""

import logging
import os
import re

import requests

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3-8b-instruct"

# Map language codes to full language names for clearer prompts
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
}

# Phrases that suggest user wants to change language in chat
LANGUAGE_CHANGE_PATTERNS = [
    r"\b(answer|reply|respond|speak|talk|write)\b.*(in|to)\s+(english|hindi|gujarati|bengali|marathi|tamil|telugu|kannada|malayalam|punjabi|odia)",
    r"\b(change|switch|set)\b.*(language|lang|bhasha)",
    r"\bhindi\s+(me|mein|mai)\b",
    r"\benglish\s+(me|mein|mai)\b",
    r"\b(translate|conversion)\b",
]


def _is_language_change_request(message: str) -> bool:
    """Check if the user is asking to change the response language in chat."""
    msg_lower = message.lower().strip()
    for pattern in LANGUAGE_CHANGE_PATTERNS:
        if re.search(pattern, msg_lower):
            return True
    return False


def get_language_change_response(lang_code: str) -> str:
    """Return a polite redirect message in the user's selected language."""
    base_msg = (
        "To change the assistant language, please select your preferred "
        "language from the language menu in the website header. "
        "I will automatically respond in whichever language you select there. 🌐"
    )
    # If already English, return directly
    if lang_code == "en":
        return base_msg
    # Otherwise translate the redirect message itself
    translated = translate_text(base_msg, lang_code)
    return translated


def translate_text(text: str, lang_code: str) -> str:
    """
    Translate text into the target language using OpenRouter LLM.

    Args:
        text: The English text to translate.
        lang_code: Target language code (e.g. 'hi', 'gu', 'ta').

    Returns:
        Translated text, or the original English text if translation fails.
    """
    if not lang_code or lang_code == "en":
        return text

    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set, skipping translation")
        return text

    lang_name = LANGUAGE_NAMES.get(lang_code, lang_code)

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
                    {
                        "role": "system",
                        "content": (
                            "You are a translation assistant. "
                            "Translate the following text accurately into "
                            f"{lang_name}. "
                            "Return ONLY the translated text, nothing else. "
                            "Do not add explanations or notes."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Translate this text to {lang_name}:\n\n{text}",
                    },
                ],
            },
            timeout=20,
        )

        if resp.status_code != 200:
            logger.error(
                "Translation API error %s: %s",
                resp.status_code,
                resp.text[:300],
            )
            return text  # fallback to English

        data = resp.json()
        translated = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not translated:
            logger.warning("Empty translation response, returning original")
            return text

        return translated

    except Exception as e:
        logger.error("Translation failed: %s", e)
        return text  # fallback to English
