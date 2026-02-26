"""
HuggingFace ML Gateway — Service Layer
=======================================
Calls the HuggingFace Space with timeout and error handling.
"""

import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_TIMEOUT = 30  # seconds (increased for HF cold starts)


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
        except requests.exceptions.Timeout:
            logger.warning("HF call attempt %d/%d timed out", attempt, _MAX_RETRIES)
            last_exc = TimeoutError("ML service timeout")
        except requests.exceptions.ConnectionError:
            logger.warning("HF call attempt %d/%d connection failed", attempt, _MAX_RETRIES)
            last_exc = ConnectionError("ML service unavailable")
        except requests.exceptions.HTTPError as exc:
            logger.error("HF call attempt %d/%d HTTP error: %s", attempt, _MAX_RETRIES, exc.status_code)
            last_exc = ConnectionError(f"ML service error: {exc.status_code}")
        except Exception as exc:
            logger.error("HF call attempt %d/%d unexpected error: %s", attempt, _MAX_RETRIES, type(exc).__name__)
            last_exc = RuntimeError("ML service error")

    logger.error("All %d HF call attempts failed", _MAX_RETRIES)
    return None
