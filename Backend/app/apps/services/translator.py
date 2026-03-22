"""
Translation Service
===================
Primary: HuggingFace NLLB-200 dedicated translation model (200 languages).
Fallback: OpenRouter LLM translation when NLLB is unavailable.

Environment variables:
    HF_TOKEN         — required for NLLB-200 translation
    OPENROUTER_API_KEY — fallback LLM translation
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

HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_NLLB_URL = "https://api-inference.huggingface.co/models/facebook/nllb-200-distilled-600M"

# NLLB-200 language codes for Indic + other supported languages
NLLB_LANG_CODES = {
    "en":  "eng_Latn",
    "hi":  "hin_Deva",
    "gu":  "guj_Gujr",
    "bn":  "ben_Beng",
    "mr":  "mar_Deva",
    "ta":  "tam_Taml",
    "te":  "tel_Telu",
    "kn":  "kan_Knda",
    "ml":  "mal_Mlym",
    "pa":  "pan_Guru",
    "or":  "ory_Orya",
    "as":  "asm_Beng",
    "ne":  "npi_Deva",
    "sd":  "snd_Arab",
    "sa":  "san_Deva",
    "mai": "mai_Deva",
    "mni": "mni_Beng",
    "ks":  "kas_Arab",
    "gom": "gom_Deva",
    "brx": "brx_Deva",
    "sat": "sat_Olck",
    "doi": "doi_Deva",
    "ur":  "urd_Arab",
}

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


def _is_mostly_latin(text: str) -> bool:
    """Return True if the text is mostly ASCII/Latin-script (likely already English)."""
    if not text:
        return True
    latin_count = sum(1 for c in text if ord(c) < 256)
    return (latin_count / len(text)) > 0.85


def _translate_nllb(text: str, src_nllb: str, tgt_nllb: str) -> str | None:
    """
    Translate text using HuggingFace NLLB-200 Inference API.
    Returns the translated string, or None on any failure.
    """
    if not HF_TOKEN:
        return None
    try:
        resp = requests.post(
            HF_NLLB_URL,
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": text,
                "parameters": {"src_lang": src_nllb, "tgt_lang": tgt_nllb},
            },
            timeout=30,
        )
        if resp.status_code == 503:
            # Model is loading — log and let fallback handle it
            logger.warning("NLLB model loading (503), falling back to LLM translation")
            return None
        if resp.status_code != 200:
            logger.warning("NLLB API error %s: %s", resp.status_code, resp.text[:200])
            return None
        data = resp.json()
        if isinstance(data, list) and data:
            translated = data[0].get("translation_text", "").strip()
            if translated:
                return translated
        logger.warning("NLLB returned empty translation")
        return None
    except Exception as e:
        logger.warning("NLLB translation failed: %s", e)
        return None


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
    Tries NLLB-200 first; falls back to LLM translation.
    If the text is already Latin-script it is returned as-is.

    Args:
        text: The user's message in their selected language.
        source_lang_code: Source language code (e.g. 'hi', 'gu').

    Returns:
        English translation, or the original text if translation fails
        or the source is already English / Latin-script.
    """
    if not source_lang_code or source_lang_code == "en":
        return text

    # Skip translation if message is already in Latin script (user typed English)
    if _is_mostly_latin(text):
        return text

    # ── Primary: NLLB-200 ───────────────────────────────────────────
    src_nllb = NLLB_LANG_CODES.get(source_lang_code)
    if src_nllb and src_nllb != "eng_Latn":
        result = _translate_nllb(text, src_nllb, "eng_Latn")
        if result:
            logger.info("NLLB translated %s→en: %r", source_lang_code, result[:60])
            return result

    # ── Fallback: LLM translation ────────────────────────────────────
    if not OPENROUTER_API_KEY:
        logger.warning("No translation available (no HF_TOKEN / OPENROUTER_API_KEY)")
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
                    {"role": "user", "content": text},
                ],
            },
            timeout=20,
        )

        if resp.status_code != 200:
            logger.error("LLM translate-to-en error %s", resp.status_code)
            return text

        data = resp.json()
        translated = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return _clean_translation(translated, text) if translated else text

    except Exception as e:
        logger.error("LLM translation to English failed: %s", e)
        return text


def translate_text(text: str, lang_code: str) -> str:
    """
    Translate English text into the target language.
    Tries NLLB-200 first; falls back to LLM translation.

    Args:
        text: The English text to translate.
        lang_code: Target language code (e.g. 'hi', 'gu', 'ta').

    Returns:
        Translated text, or the original English text if translation fails.
    """
    if not lang_code or lang_code == "en":
        return text

    # ── Primary: NLLB-200 ───────────────────────────────────────────
    tgt_nllb = NLLB_LANG_CODES.get(lang_code)
    if tgt_nllb and tgt_nllb != "eng_Latn":
        result = _translate_nllb(text, "eng_Latn", tgt_nllb)
        if result:
            logger.info("NLLB translated en→%s: %r", lang_code, result[:60])
            return result

    # ── Fallback: LLM translation ────────────────────────────────────
    if not OPENROUTER_API_KEY:
        logger.warning("No translation available (no HF_TOKEN / OPENROUTER_API_KEY)")
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
                    {"role": "user", "content": text},
                ],
            },
            timeout=20,
        )

        if resp.status_code != 200:
            logger.error("LLM translation error %s", resp.status_code)
            return text

        data = resp.json()
        translated = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return _clean_translation(translated, text) if translated else text

    except Exception as e:
        logger.error("LLM translation failed: %s", e)
        return text
