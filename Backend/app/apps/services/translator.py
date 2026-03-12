"""
Translation Service
===================
Uses OpenRouter LLM to translate assistant responses between languages.
Provides translate_to_english() for inbound user messages and
translate_text() for outbound answers to the user's selected language.

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


def _clean_translation(translated: str, original: str) -> str:
    """
    Strip echoed source text and common LLM preamble from translation output.
    """
    if not translated:
        return translated

    # Strip if the LLM echoed the original text before the translation
    if original and translated.startswith(original):
        translated = translated[len(original):].strip()

    # Strip common LLM preamble patterns
    preamble_patterns = [
        r"^here\s+is\s+the\s+translat(?:ion|ed\s+text)\s*[:\-]\s*",
        r"^translat(?:ion|ed\s+text)\s*[:\-]\s*",
        r"^the\s+translat(?:ion|ed\s+text)\s+is\s*[:\-]?\s*",
    ]
    for pattern in preamble_patterns:
        translated = re.sub(pattern, "", translated, flags=re.IGNORECASE).strip()

    # If the LLM appended the original after the translation, strip it
    if original and translated.endswith(original):
        translated = translated[: -len(original)].strip()

    return translated


def translate_to_english(text: str, source_lang_code: str) -> str:
    """
    Translate user input from source language to English.

    Args:
        text: The user's message in their selected language.
        source_lang_code: Source language code (e.g. 'hi', 'gu').

    Returns:
        English translation, or the original text if translation fails
        or the source is already English.
    """
    if not source_lang_code or source_lang_code == "en":
        return text

    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set, skipping translation to English")
        return text

    lang_name = LANGUAGE_NAMES.get(source_lang_code, source_lang_code)

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
                            "Translate the following text from "
                            f"{lang_name} to English. "
                            "Return ONLY the English translation, nothing else. "
                            "Do not add explanations or notes."
                        ),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
            },
            timeout=20,
        )

        if resp.status_code != 200:
            logger.error("Translation-to-English API error %s: %s", resp.status_code, resp.text[:300])
            return text

        data = resp.json()
        translated = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not translated:
            logger.warning("Empty translation-to-English response, returning original")
            return text

        return _clean_translation(translated, text)

    except Exception as e:
        logger.error("Translation to English failed: %s", e)
        return text


def translate_text(text: str, lang_code: str) -> str:
    """
    Translate English text into the target language using OpenRouter LLM.

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
                            "Translate the following English text accurately into "
                            f"{lang_name}. "
                            "Return ONLY the translated text, nothing else. "
                            "Do not add explanations, notes, or the original English text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": text,
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

        return _clean_translation(translated, text)

    except Exception as e:
        logger.error("Translation failed: %s", e)
        return text  # fallback to English
