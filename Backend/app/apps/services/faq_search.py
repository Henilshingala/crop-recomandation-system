"""
FAQ Keyword Search Module
=========================
Loads FAQ entries from faq.json and uses difflib.SequenceMatcher
for lightweight text similarity matching. Zero heavy dependencies.

Memory usage: ~2-5 MB for 1200+ FAQ entries (JSON only, no embeddings).
"""

import json
import logging
import os
import re
from difflib import SequenceMatcher
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────

_FAQ_PATHS = [
    os.path.join(os.path.dirname(__file__), "faq.json"),
    os.path.join(os.path.dirname(__file__), "..", "data", "faq.json"),
]
SIMILARITY_THRESHOLD = 0.60

# ── Module-level state (loaded once) ────────────────────────────────────

_faq_entries: list[dict] = []
_faq_questions_normalized: list[str] = []


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _load():
    """Load FAQ data from disk. Called once at first use."""
    global _faq_entries, _faq_questions_normalized

    if _faq_entries:
        return  # already loaded

    faq_path = None
    for path in _FAQ_PATHS:
        if os.path.isfile(path):
            faq_path = path
            break

    if faq_path is None:
        logger.error("FAQ file not found in any of: %s", _FAQ_PATHS)
        return

    try:
        with open(faq_path, "r", encoding="utf-8") as f:
            _faq_entries = json.load(f)
        logger.info("Loaded %d FAQ entries from %s", len(_faq_entries), faq_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load FAQ file: %s", e)
        _faq_entries = []
        return

    # Pre-normalize all FAQ questions for faster matching
    _faq_questions_normalized = [
        _normalize(entry["question"]) for entry in _faq_entries
    ]


@lru_cache(maxsize=256)
def _cached_search(query_normalized: str) -> tuple:
    best_score = 0.0
    best_idx = 0

    for idx, faq_q in enumerate(_faq_questions_normalized):
        score = SequenceMatcher(None, query_normalized, faq_q).ratio()
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_score >= SIMILARITY_THRESHOLD:
        return _faq_entries[best_idx]["answer"], best_score

    return None, best_score

def search_faq(user_query: str) -> tuple:
    """
    Search FAQ for the best match using difflib.SequenceMatcher.

    Returns:
        (answer, similarity_score) if score >= threshold,
        (None, best_score) otherwise.
    """
    _load()

    if not _faq_entries:
        return None, 0.0

    query_normalized = _normalize(user_query)
    
    answer, best_score = _cached_search(query_normalized)

    logger.info(
        "FAQ search: query=%r score=%.3f threshold=%.2f",
        user_query[:80],
        best_score,
        SIMILARITY_THRESHOLD,
    )

    return answer, best_score
