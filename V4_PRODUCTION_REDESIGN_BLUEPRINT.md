# Crop Recommendation System V4 — Production Redesign Blueprint

**Document version:** 1.0  
**Target:** 2026 best practices | Academic defensibility | Stability & correctness

---

## 1. V4 Target Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │ InputForm   │  │ api.ts      │  │ env config  │  │ ErrorBoundary + retry logic │ │
│  │ mode: real/ │  │ no hardcode │  │ .env.local  │  │ request cancellation       │ │
│  │ synthetic/  │  │ base URL    │  │             │  │                             │ │
│  │ both        │  │             │  │             │  │                             │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘  └─────────────────────────────┘ │
└─────────┼────────────────┼──────────────────────────────────────────────────────────┘
          │                │
          │   POST /api/predict  { mode, N, P, K, ... }
          ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DJANGO REST GATEWAY (Backend)                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ Middleware: RateLimit │ API-Key │ CircuitBreaker │ PayloadSizeLimit (64KB)       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │ views.py    │  │ ml_inference│  │ hf_service  │  │ local_fallback_service      │ │
│  │ predict_top │  │ mode routing│  │ async +     │  │ (Django-managed lightweight │ │
│  │ _crops()    │  │             │  │ retry+back  │  │  model for HF outage)       │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────────┘ │
│         │                │                │                        │                 │
│  ┌──────┴────────────────┴────────────────┴────────────────────────┴──────────────┐ │
│  │ CIRCUIT BREAKER: HF open → route to local_fallback or 503                       │ │
│  │ CACHE: Response cache (input hash → prediction) TTL 1h                          │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────┬───────────────────────────────────────────────────────────────────────────┘
          │
          │  HTTP POST { mode, N, P, K, ... }  (HF_MODEL_URL from env)
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    HUGGINGFACE / LOCAL ML ENGINE (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ POST /predict  →  mode routing                                                    ││
│  │   mode=real      → ModelRealV4 (19 crops, stacked_ensemble_v3.joblib)            ││
│  │   mode=synthetic → ModelSyntheticV4 (51 crops, model_rf.joblib)                  ││
│  │   mode=both      → ModelBothV4 (HybridPredictorV2 / simplified blend)            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────────┐  │
│  │ stacked_ensemble│  │ model_rf        │  │ hybrid_v2_config + honest_v2 + synth │  │
│  │ _v3.joblib      │  │ .joblib         │  │ (lazy load "both" on first request)  │  │
│  │ label_encoder_  │  │ label_encoder   │  │                                     │  │
│  │ v3.joblib       │  │ .joblib         │  │                                     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
          │
          │  SQLite (Backend)
          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SQLite3 (Backend/app/db.sqlite3)                                                     │
│  apps_crop (indexed) | apps_predictionlog (partitioned by created_at) | WAL mode      │
│  Backups: cron daily copy to Backup/ | retention 7 days                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Model Strategy Redesign

### 2.1 Model Inventory (V4 — Keep Only These)

| Mode     | Model File(s)                         | Encoder                  | Crops | Features |
|----------|--------------------------------------|--------------------------|-------|----------|
| real     | `stacked_ensemble_v3.joblib`         | `label_encoder_v3.joblib`| 19    | 11 (incl. moisture) |
| synthetic| `model_rf.joblib`                    | `label_encoder.joblib`   | 51    | 10 (no moisture) |
| both     | `model_real_world_honest_v2.joblib` + `model_rf.joblib` | `label_encoder_real_honest.joblib` + `label_encoder.joblib` | 54 unified | 11 + 10 |

### 2.2 Post-Processing Simplification

**Remove from V3 inference path:**
- Temperature scaling (keep only if validated on holdout; otherwise remove)
- Inverse-frequency weighting (remove unless calibrated on validation set)
- Per-class thresholds (remove)
- Entropy penalty (remove)

**V4 approach:** Use raw model probabilities or a single calibrated scaling factor (e.g. Platt scaling at training) — no runtime probability manipulation.

### 2.3 Season Inference

Replace simplistic `if temp>=28: Kharif` with latitude-aware logic or explicit user input:

```
season = user_provided or infer_from_month_lat(lat, month) or infer_from_temp(temp)
# Store inference method in response: "inferred" | "provided" | "default"
```

### 2.4 Default Imputations

- `moisture`: 43.5 only for real/both models; synthetic model has no moisture → skip.
- Document defaults in API schema; avoid silent bias. Add `imputation_used: true` in response when defaults applied.

### 2.5 Model Registry (Minimal)

Create `Aiml/model_registry.json`:

```json
{
  "real": {
    "model": "stacked_ensemble_v3.joblib",
    "encoder": "label_encoder_v3.joblib",
    "config": "stacked_v3_config.joblib",
    "crops": 19,
    "features": ["n","p","k","temperature","humidity","ph","rainfall","season","soil_type","irrigation","moisture"]
  },
  "synthetic": {
    "model": "model_rf.joblib",
    "encoder": "label_encoder.joblib",
    "crops": 51,
    "features": ["N","P","K","temperature","humidity","ph","rainfall","season","soil_type","irrigation"]
  },
  "both": {
    "real_model": "model_real_world_honest_v2.joblib",
    "real_encoder": "label_encoder_real_honest.joblib",
    "synth_model": "model_rf.joblib",
    "synth_encoder": "label_encoder.joblib",
    "config": "hybrid_v2_config.joblib",
    "crops": 54
  }
}
```

---

## 3. Mode Logic Implementation Plan

### 3.1 Naming: Standardize to `real` | `synthetic` | `both`

- Frontend currently uses `original` → change to `real` everywhere (API, serializers, frontend).
- Backend `MODE_CHOICES` → `[("real", "Real"), ("synthetic", "Synthetic"), ("both", "Both")]`.

### 3.2 Data Flow (End-to-End)

| Step | Layer        | Action |
|------|--------------|--------|
| 1    | InputForm    | `mode: 'real' | 'synthetic' | 'both'` |
| 2    | api.ts       | Send `mode` in JSON body |
| 3    | views.py     | `mode = vd.get("mode", "real")` |
| 4    | ml_inference | `payload["mode"] = mode` before HF call |
| 5    | hf_service   | Pass payload as-is (includes mode) |
| 6    | Aiml/app.py  | Read `mode` from request; route to correct predictor |

### 3.3 Aiml/app.py Mode Routing (Implementation)

```python
# PredictionInput schema - ADD:
mode: Optional[Literal["real", "synthetic", "both"]] = Field("real", description="Model mode")

# Predictor registry (lazy load):
_real_predictor = None
_synthetic_predictor = None
_both_predictor = None

def _get_real_predictor():
    global _real_predictor
    if _real_predictor is None:
        _real_predictor = RealPredictorV4()  # loads V3 stack
    return _real_predictor

def _get_synthetic_predictor():
    global _synthetic_predictor
    if _synthetic_predictor is None:
        _synthetic_predictor = SyntheticPredictorV4()  # loads model_rf
    return _synthetic_predictor

def _get_both_predictor():
    global _both_predictor
    if _both_predictor is None:
        _both_predictor = BothPredictorV4()  # loads HybridPredictorV2 artifacts
    return _both_predictor

@app.post("/predict")
async def predict(data: PredictionInput):
    mode = (data.mode or "real").lower()
    if mode not in ("real", "synthetic", "both"):
        mode = "real"

    if mode == "real":
        pred = _get_real_predictor().predict(data)
    elif mode == "synthetic":
        pred = _get_synthetic_predictor().predict(data)
    else:
        pred = _get_both_predictor().predict(data)

    return format_response(pred, mode=mode)
```

### 3.4 Real Predictor (RealPredictorV4)

- Load `stacked_ensemble_v3.joblib`, `label_encoder_v3.joblib`, `stacked_v3_config.joblib`.
- Use 11 features; infer season if not provided.
- **Remove** temperature, inv_freq, class_thresholds, entropy_penalty from inference. Use raw meta-learner output or single calibration from config.
- Return top_n crops with confidence.

### 3.5 Synthetic Predictor (SyntheticPredictorV4)

- Load `model_rf.joblib`, `label_encoder.joblib`.
- Use 10 features (no moisture). Map input: N→n, P→p, K→k if needed.
- Infer season; default soil_type=1, irrigation=0.
- Return top_n from 51 crops.

### 3.6 Both Predictor (BothPredictorV4)

- Load `model_real_world_honest_v2.joblib`, `label_encoder_real_honest.joblib`, `model_rf.joblib`, `label_encoder.joblib`, `hybrid_v2_config.joblib`.
- Instantiate `HybridPredictorV2` from hybrid_model.py (or refactor to a standalone inference module).
- **Simplify HybridPredictorV2** for production: keep confidence-adaptive blending (w_real, w_synth) and crop mapping; remove entropy penalty, binary classifiers, SHAP scaling if not validated.
- Return unified top_n from 54 crops.

### 3.7 Academic Defensibility

- Document in project report: "Mode real uses model trained on real-world data (19 crops); mode synthetic uses model trained on synthetic dataset (51 crops); mode both uses a hybrid that combines both model outputs via confidence-adaptive blending, following the methodology in [hybrid_model.py / paper reference]."
- Store `model_info` in response: `{ "mode": "real", "model": "stacked-ensemble-v3", "crops": 19 }` etc.

---

## 4. Backend Refactor Plan

### 4.1 Async HF Calls

- Replace `requests.post` with `httpx.AsyncClient` or `aiohttp`.
- Use `asyncio` in Django: wrap view with `async def` and `sync_to_async` for DB, or use Django async views (Django 4.1+).
- Alternative: run HF call in thread pool via `asyncio.to_thread()` to avoid blocking.

### 4.2 Retry with Exponential Backoff

```python
# hf_service.py
BACKOFF_BASE = 1.0  # seconds
MAX_RETRIES = 3

async def call_hf_model_async(payload: dict) -> Optional[dict]:
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt == MAX_RETRIES - 1:
                return None
            await asyncio.sleep(BACKOFF_BASE * (2 ** attempt))
    return None
```

### 4.3 Circuit Breaker

- Use `pybreaker` or custom: track failures in a sliding window (e.g. 5 failures in 60s → open circuit).
- When open: return 503 with `Retry-After: 60` or route to local fallback.

### 4.4 Rate Limiting

- `django-ratelimit` or custom middleware: 60 req/min per IP for `/api/predict/`.
- Return 429 with `Retry-After` header.

### 4.5 API Key (Optional but Recommended)

- Add `X-API-Key` header validation for `/api/predict/`.
- `API_KEYS` from env (comma-separated) or database table for keys.
- Public demo: allow anonymous with stricter rate limit (e.g. 10/min).

### 4.6 Structured Error Codes

```python
ERROR_CODES = {
    "ML_UNAVAILABLE": ("HuggingFace ML service temporarily unavailable", 503),
    "RATE_LIMITED": ("Too many requests", 429),
    "INVALID_INPUT": ("Invalid input parameters", 400),
    "PAYLOAD_TOO_LARGE": ("Request body too large", 413),
}
```

### 4.7 Nutrition CSV Caching

- Load `Nutrient.csv` once at startup (Django `AppConfig.ready()` or module-level).
- Store in memory dict: `{crop_name_lower: nutrition_dict}`.
- No per-request file read.

### 4.8 Gunicorn Workers

- Increase to 4 workers (or `2 * CPU + 1`).
- Add `--preload` to share memory if acceptable.

### 4.9 Environment Separation

- `DJANGO_SETTINGS_MODULE`: `app.settings` (base) + `app.settings_dev` / `app.settings_prod` override.
- `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `HF_MODEL_URL` from env only in prod.

### 4.10 Remove Insecure Fallbacks

- `SECRET_KEY`: fail startup if not set in prod.
- `DEBUG`: default `False`; require explicit `DJANGO_DEBUG=true` for dev.
- `HF_MODEL_URL`: no hardcoded fallback; fail if missing.

---

## 5. SQLite Optimization Strategy

### 5.1 WAL Mode

SQLite OPTIONS does not support init_command. Use one of:

**Option A — Migration:**
```python
# migrations/0xxx_enable_wal.py
from django.db import migrations

def enable_wal(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite3":
        schema_editor.connection.execute("PRAGMA journal_mode=WAL;")
        schema_editor.connection.execute("PRAGMA synchronous=NORMAL;")
        schema_editor.connection.execute("PRAGMA cache_size=-64000;")

class Migration(migrations.Migration):
    dependencies = [("apps", "0xxx_previous")]
    operations = [migrations.RunPython(enable_wal, migrations.RunPython.noop)]
```

**Option B — Post-migrate script:**
```bash
sqlite3 Backend/app/db.sqlite3 "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=-64000;"
```

### 5.2 Indexing

```sql
-- apps_predictionlog: queries by date, IP
CREATE INDEX idx_predictionlog_created ON apps_predictionlog(created_at);
CREATE INDEX idx_predictionlog_ip ON apps_predictionlog(ip_address) WHERE ip_address IS NOT NULL;

-- apps_crop: name already indexed
-- Add if needed: CREATE INDEX idx_crop_name_lower ON apps_crop(LOWER(name));
```

### 5.3 Backup Automation

- Cron script: `cp Backend/app/db.sqlite3 Backups/db_$(date +%Y%m%d).sqlite3`
- Retention: delete backups older than 7 days.
- Use `sqlite3 db.sqlite3 ".backup 'backup.sqlite3'"` for safe backup (no lock issues).

### 5.4 Retention Policy

- Add management command: `python manage.py prune_logs --days 90`
- Delete `PredictionLog` where `created_at < now() - 90 days`.

### 5.5 Concurrent Writes

- WAL mode reduces lock contention.
- Keep writes minimal (single insert per prediction).
- Batch log inserts optional (queue + bulk_create) if load increases.

### 5.6 IP Logging Compliance

- Add `PRIVACY_CONSENT_REQUIRED` setting.
- If true: do not log IP unless `X-Consent-Logging: true` header.
- Document in privacy policy; add checkbox in frontend for consent.
- Alternatively: hash IP before storage (SHA256) for analytics without PII.

---

## 6. Async + Caching Strategy

### 6.1 Response Caching (No Redis)

- In-memory cache: `cachetools.TTLCache(maxsize=1000, ttl=3600)`.
- Key: hash of `(mode, N, P, K, temp, humidity, ph, rainfall, soil_type, irrigation, moisture)`.
- On cache hit: return cached response; skip HF call.

### 6.2 Optional Redis (If Added Later)

- `django-redis` for distributed cache.
- Same key strategy; TTL 1 hour.
- Use for multi-instance deployments.

### 6.3 Django View Async Pattern

```python
# views.py
from asgiref.sync import sync_to_async

@sync_to_async
def _predict_sync(mode, ...):
    return predict_top_crops(...)

async def post(self, request):
    result = await _predict_sync(mode, ...)
    return Response(result)
```

Or use Django 4.1+ async views with `httpx` for non-blocking HF calls.

---

## 7. Security Hardening Plan

### 7.1 Prediction Endpoint

- Rate limit: 60/min per IP.
- API key optional: `X-API-Key` header.
- Payload size: 64 KB max (Django `DATA_UPLOAD_MAX_MEMORY_SIZE`).
- Validate all inputs (already in serializer); reject out-of-range.

### 7.2 CORS

- Remove wildcard. Set `CORS_ALLOWED_ORIGINS` from env: frontend domains only.
- Never use `CORS_ALLOW_ALL_ORIGINS = True` in prod.

### 7.3 WAF (If on Cloud)

- Cloudflare or similar: enable bot protection, rate limiting at edge.
- No code change; infrastructure.

### 7.4 Brute-Force Protection

- Rate limiting covers this.
- Optional: CAPTCHA for unauthenticated after N requests (e.g. 100/hour).

### 7.5 Secrets

- All secrets from env; no defaults for prod.
- Rotate `DJANGO_SECRET_KEY`, `HF_TOKEN`, API keys periodically (document in runbook).

---

## 8. Deployment Architecture

### 8.1 HuggingFace Space

- Keep HF for ML; cold start acceptable if documented.
- Add `/health` that checks model load status.
- Use HF paid tier if needed for no sleep.

### 8.2 Local Fallback (Resilience)

- Option A: Deploy a lightweight FastAPI ML service alongside Django (same Render service or separate).
- Option B: Embed a minimal model (e.g. synthetic only, smaller) in Django process for fallback when HF is down.
- When circuit breaker opens → try local fallback → if fail, 503.

### 8.3 Environment Variables (No Hardcoding)

| Variable           | Required | Description                    |
|--------------------|----------|--------------------------------|
| DJANGO_SECRET_KEY  | Yes (prod) | Django secret                 |
| HF_MODEL_URL       | Yes      | ML engine base URL             |
| HF_TOKEN           | No       | HF Space token if private      |
| CORS_ALLOWED_ORIGINS | Yes    | Comma-separated frontend URLs  |
| DJANGO_DEBUG       | Yes      | false in prod                  |
| API_KEYS           | No       | Comma-separated for auth       |

### 8.4 Staging

- Deploy staging on Render (separate service) with `HF_MODEL_URL` pointing to staging HF Space or same.
- Run integration tests against staging in CI.

### 8.5 Docker Image Size

- Multi-stage build: builder installs deps; runtime copies only `Aiml/` + `app.py`.
- Exclude `*.pyc`, `__pycache__`, `.git`, training CSVs (keep only inference artifacts).
- Use `python:3.11-slim`; add only `libgomp1` for XGBoost/LightGBM.

### 8.6 Secret Rotation

- Document: rotate `DJANGO_SECRET_KEY` (invalidates sessions); rotate `HF_TOKEN` (update env).
- No automatic rotation in app; manual or pipeline step.

---

## 9. Monitoring + Observability Plan

### 9.1 Health Endpoints

- `GET /api/health/`: DB + ML connectivity (call HF `/` if possible; timeout 5s).
- `GET /api/health/ready/`: readiness (DB + models loaded).

### 9.2 Logging

- Structured JSON logs: `{"ts":"...","level":"INFO","msg":"...","request_id":"...","mode":"real"}`.
- Log prediction latency, mode, cache hit/miss.
- No PII in logs.

### 9.3 Metrics (If Resources Allow)

- Prometheus-compatible `/metrics`: request count, latency histogram, error count by endpoint.
- Or use Render metrics / external APM (e.g. Sentry).

### 9.4 Alerting

- Render: alert on service down, high error rate.
- Optional: Sentry for exception tracking.
- No custom alerting in code; use platform features.

### 9.5 Model Drift (Future)

- Log prediction inputs (anonymized) + outputs periodically.
- Offline: compare feature distributions over time; flag if shift > threshold.
- No real-time drift in V4; document as future work.

---

## 10. Step-by-Step Migration Timeline

| Phase | Steps | Est. |
|-------|-------|------|
| **Phase 1: Mode Fix (Critical)** | 1. Add `mode` to HF payload in ml_inference.py<br>2. Add mode to Aiml PredictionInput; implement Real/Synthetic/Both predictors<br>3. Refactor Aiml/app.py routing<br>4. Ensure hybrid artifacts exist (run hybrid_model.py if needed)<br>5. Standardize frontend/backend to real/synthetic/both | 3–5 days |
| **Phase 2: Backend Hardening** | 1. Add rate limiting middleware<br>2. Async HF calls (httpx)<br>3. Retry with backoff<br>4. Circuit breaker<br>5. Nutrition CSV cache<br>6. Remove DEBUG/SECRET_KEY fallbacks for prod | 2–3 days |
| **Phase 3: SQLite + Security** | 1. WAL mode + indexes<br>2. Backup script + cron<br>3. Prune logs command<br>4. CORS restrict<br>5. Payload size limit<br>6. IP consent handling | 1–2 days |
| **Phase 4: Frontend** | 1. Remove hardcoded API URL; use env only<br>2. Add retry logic (exponential backoff)<br>3. Request cancellation (AbortController)<br>4. Error boundary<br>5. Rename original→real in UI | 1–2 days |
| **Phase 5: Deployment** | 1. Staging env<br>2. CI: pytest + contract test Django↔FastAPI<br>3. Docker slim image<br>4. Health checks<br>5. Monitoring hooks | 2–3 days |
| **Phase 6: ML Cleanup** | 1. Simplify V3 post-processing (remove unvalidated layers)<br>2. Model registry JSON<br>3. Document mode logic for report | 1–2 days |

**Total:** ~2–3 weeks for full V4.

---

## 11. Clean Folder Structure (V4)

```
CRS/
├── Aiml/
│   ├── app.py                    # FastAPI entry; mode routing; Real/Synthetic/Both predictors
│   ├── predictors/
│   │   ├── __init__.py
│   │   ├── real.py               # RealPredictorV4 (V3 stack)
│   │   ├── synthetic.py          # SyntheticPredictorV4 (model_rf)
│   │   └── both.py               # BothPredictorV4 (HybridPredictorV2)
│   ├── model_registry.json
│   ├── stacked_ensemble_v3.joblib
│   ├── label_encoder_v3.joblib
│   ├── stacked_v3_config.joblib
│   ├── model_rf.joblib
│   ├── label_encoder.joblib
│   ├── model_real_world_honest_v2.joblib
│   ├── label_encoder_real_honest.joblib
│   ├── hybrid_v2_config.joblib
│   ├── Nutrient.csv
│   ├── hybrid_model.py           # Training only; predictors/both.py imports HybridPredictorV2
│   ├── final_stacked_model.py    # Training only
│   └── predict.py                # CLI; not used in API
├── Backend/
│   └── app/
│       ├── app/
│       │   ├── settings.py
│       │   ├── settings_prod.py
│       │   └── urls.py
│       ├── apps/
│       │   ├── ml_inference.py   # Adds mode to payload; cache layer
│       │   ├── services/
│       │   │   ├── hf_service.py # Async + retry + circuit breaker
│       │   │   └── cache.py      # TTL cache
│       │   ├── middleware/
│       │   │   ├── rate_limit.py
│       │   │   └── circuit_breaker.py
│       │   └── management/
│       │       └── commands/
│       │           └── prune_logs.py
│       └── db.sqlite3
├── Frontend/
│   └── src/
│       ├── app/
│       │   ├── api.ts            # Env-based URL; retry; AbortController
│       │   ├── components/
│       │   │   ├── InputForm.tsx # mode: real|synthetic|both
│       │   │   └── ErrorBoundary.tsx
│       │   └── App.tsx
│       └── .env.example          # VITE_API_BASE_URL=
├── scripts/
│   ├── backup_db.sh
│   └── prune_backups.sh
├── app.py                        # HF Spaces entrypoint
├── Dockerfile
├── render.yaml
└── V4_PRODUCTION_REDESIGN_BLUEPRINT.md
```

---

## 12. What to Remove Completely

| Item | Location | Reason |
|------|----------|--------|
| Temperature scaling at inference | Aiml/app.py | Unvalidated; remove or validate on holdout |
| Inverse-frequency weighting | Aiml/app.py | Unvalidated |
| Class thresholds | Aiml/app.py | Unvalidated |
| Entropy penalty | Aiml/app.py | Unvalidated |
| Hardcoded HF_MODEL_URL | settings.py | Security; use env only |
| Hardcoded SECRET_KEY | settings.py | Security |
| DEBUG=True default | settings.py | Security |
| CORS wildcard | settings.py | Security |
| Nutrition CSV read per request | views.py, ml_inference | Performance |
| model_real_world_honest.joblib (v1) | Aiml/ | Superseded by v2 |
| Redundant legacy models | Aiml/ | Keep only V4 registry models |
| `original` mode name | Everywhere | Use `real` |
| Synchronous requests.post | hf_service.py | Replace with async |
| 2 Gunicorn workers | render.yaml | Increase to 4 |
| Full-page reload retry | Frontend | Use in-component retry |
| Duplicate validation | Frontend + Backend | Keep backend as source of truth; frontend for UX only |

---

## Appendix A: Contract Test (Django ↔ FastAPI)

```python
# tests/contract/test_predict_contract.py
def test_predict_request_response_contract():
    payload = {
        "mode": "real", "N": 90, "P": 42, "K": 43,
        "temperature": 24, "humidity": 68, "ph": 6.7, "rainfall": 120,
    }
    resp = requests.post(f"{HF_URL}/predict", json=payload, timeout=30)
    assert resp.status_code == 200
    data = resp.json()
    assert "predictions" in data or "top_3" in data
    assert data.get("model_info", {}).get("coverage", 0) in (19, 51, 54)
```

---

## Appendix B: HybridPredictorV2 Simplification

For production "both" mode, consider reducing HybridPredictorV2 complexity:
- Keep: real + synthetic model calls, confidence-adaptive blending (w_real, w_synth), crop name mapping.
- Remove: entropy penalty, binary classifier overrides, SHAP feature scaling (unless validated).
- Document: "Blending weights are confidence-adaptive: high real confidence → favor real model; low → equal blend."

---

*End of V4 Production Redesign Blueprint*
