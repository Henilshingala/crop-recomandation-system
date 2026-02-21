"""
HuggingFace ML Gateway — Service Layer
=======================================
Calls the HuggingFace Space internally for real-world (v3) inference.
Provides retry logic and clean error handling.
"""

import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_TIMEOUT = 10  # seconds


def _get_hf_url() -> str:
    """Return the HF /predict endpoint URL from settings."""
    base = getattr(settings, "HF_MODEL_URL", "") or ""
    base = base.rstrip("/")
    if not base:
        raise RuntimeError("HF_MODEL_URL is not configured")
    return f"{base}/predict"


def _get_hf_headers() -> dict:
    """Return request headers, including auth if HF_TOKEN is set."""
    headers = {"Content-Type": "application/json"}
    token = getattr(settings, "HF_TOKEN", "") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def call_hf_model(payload: dict) -> Optional[dict]:
    """
    POST *payload* to the HuggingFace Space /predict endpoint.

    Parameters
    ----------
    payload : dict
        Must contain: N, P, K, temperature, humidity, ph, rainfall,
        moisture, and optionally season, soil_type, irrigation, top_n.

    Returns
    -------
    dict   – parsed JSON on success
    None   – on failure (after retries)
    """
    url = _get_hf_url()
    headers = _get_hf_headers()
    last_exc: Optional[Exception] = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout as exc:
            logger.warning("HF call attempt %d/%d timed out: %s", attempt, _MAX_RETRIES, exc)
            last_exc = exc
        except requests.exceptions.ConnectionError as exc:
            logger.warning("HF call attempt %d/%d connection error: %s", attempt, _MAX_RETRIES, exc)
            last_exc = exc
        except requests.exceptions.HTTPError as exc:
            logger.error("HF call attempt %d/%d HTTP error: %s", attempt, _MAX_RETRIES, exc)
            last_exc = exc
        except Exception as exc:
            logger.exception("HF call attempt %d/%d unexpected error: %s", attempt, _MAX_RETRIES, exc)
            last_exc = exc

    logger.error("All %d HF call attempts failed. Last error: %s", _MAX_RETRIES, last_exc)
    return None
