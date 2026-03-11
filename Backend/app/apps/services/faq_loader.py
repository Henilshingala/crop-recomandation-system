"""
FAQ Semantic Search Module
==========================
Loads FAQ entries from faq.json and uses SentenceTransformers (all-MiniLM-L6-v2)
to find the best-matching answer via cosine similarity.

Embeddings are computed once at module load and cached in memory.
"""

import json
import logging
import os

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────

FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "faq.json")
MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.70

# ── Module-level state (loaded once) ────────────────────────────────────

_faq_entries: list[dict] = []
_faq_embeddings: np.ndarray | None = None
_model: SentenceTransformer | None = None


def _load():
    """Load FAQ data and pre-compute embeddings. Called once at first use."""
    global _faq_entries, _faq_embeddings, _model

    if _model is not None:
        return  # already loaded

    # Load FAQ JSON
    try:
        with open(FAQ_PATH, "r", encoding="utf-8") as f:
            _faq_entries = json.load(f)
        logger.info("Loaded %d FAQ entries from %s", len(_faq_entries), FAQ_PATH)
    except FileNotFoundError:
        logger.error("FAQ file not found at %s", FAQ_PATH)
        _faq_entries = []
        return
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in FAQ file: %s", e)
        _faq_entries = []
        return

    # Load SentenceTransformer model
    try:
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Loaded SentenceTransformer model: %s", MODEL_NAME)
    except Exception as e:
        logger.error("Failed to load SentenceTransformer model: %s", e)
        return

    # Pre-compute FAQ question embeddings
    questions = [entry["question"] for entry in _faq_entries]
    _faq_embeddings = _model.encode(questions, convert_to_numpy=True)
    logger.info("Pre-computed embeddings for %d FAQ questions", len(questions))


def search_faq(user_query: str) -> tuple[str | None, float]:
    """
    Search FAQ for the best semantic match to the user query.

    Returns:
        (answer, similarity_score) if score >= threshold,
        (None, best_score) otherwise.
    """
    _load()  # ensure loaded

    if not _faq_entries or _model is None or _faq_embeddings is None:
        return None, 0.0

    # Encode user query
    query_embedding = _model.encode([user_query], convert_to_numpy=True)

    # Compute cosine similarities
    similarities = cosine_similarity(query_embedding, _faq_embeddings)[0]

    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])

    logger.info(
        "FAQ search: query=%r best_match=%r score=%.3f threshold=%.2f",
        user_query,
        _faq_entries[best_idx]["question"],
        best_score,
        SIMILARITY_THRESHOLD,
    )

    if best_score >= SIMILARITY_THRESHOLD:
        return _faq_entries[best_idx]["answer"], best_score

    return None, best_score
