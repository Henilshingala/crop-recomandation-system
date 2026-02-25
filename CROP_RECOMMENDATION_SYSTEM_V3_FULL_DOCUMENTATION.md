# CROP RECOMMENDATION SYSTEM — V3 FULL TECHNICAL DOCUMENTATION

---

**Version:** V3  
**Date Generated:** 2026-02-23  
**Environment Type:** Production (Deployed) + Local Development  
**Repository:** [https://github.com/Henilshingala/crop-recomandation-system](https://github.com/Henilshingala/crop-recomandation-system)

---

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [ML Model Details](#2-ml-model-details)
3. [Backend Details](#3-backend-details)
4. [Frontend Details](#4-frontend-details)
5. [Complete Data Flow](#5-complete-data-flow)
6. [Known Limitations & Technical Debt](#6-known-limitations--technical-debt)
7. [Full Folder Structure](#7-full-folder-structure)
8. [Version Tag](#8-version-tag)

---

## 1. Project Architecture

### 1.1 Frontend Framework and Version

- **Framework:** React 18.3.1
- **Build Tool:** Vite 6.3.5
- **Language:** TypeScript (ESNext target, strict mode)
- **CSS Framework:** Tailwind CSS 4.1.12 (via `@tailwindcss/vite` plugin)
- **UI Component Libraries:**
  - Radix UI (multiple primitives: accordion, dialog, dropdown-menu, popover, select, tabs, tooltip, etc.)
  - Lucide React 0.487.0 (icon library)
  - Motion 12.23.24 (animation library, formerly Framer Motion)
  - Recharts 2.15.2 (charting)
  - Embla Carousel React 8.6.0
  - Sonner 2.0.3 (toast notifications)
  - class-variance-authority 0.7.1 + clsx 2.1.1 + tailwind-merge 3.2.0 (utility class management)
- **Package Manager:** pnpm

### 1.2 Backend Framework and Version

- **Framework:** Django >= 5.0 (Python)
- **API Framework:** Django REST Framework >= 3.14
- **WSGI Server:** Gunicorn 22.0.0 (pinned to avoid worker-spawn bug in 25.x)
- **Database:** SQLite3 (file-based, `db.sqlite3`)
- **Static Files:** WhiteNoise >= 6.6.0
- **CORS:** django-cors-headers >= 4.3
- **Image Handling:** Pillow >= 10.0
- **HTTP Client:** requests >= 2.31.0 (for HuggingFace API calls)
- **Environment:** python-dotenv >= 1.0
- **Cloud Storage:** django-cloudinary-storage >= 0.3.0

### 1.3 ML Framework and Version

- **API Framework:** FastAPI >= 0.104
- **ASGI Server:** Uvicorn >= 0.24
- **Validation:** Pydantic >= 2.0
- **ML Libraries:**
  - scikit-learn >= 1.3
  - XGBoost >= 2.0
  - LightGBM >= 4.1
  - imbalanced-learn >= 0.11
- **Data Libraries:**
  - NumPy >= 1.24
  - Pandas >= 2.0
  - joblib >= 1.3
- **Visualization (training only):** Matplotlib >= 3.7
- **Python Version:** 3.11

### 1.4 System Architecture Type

The system follows a **decoupled gateway architecture** (3-tier, distributed microservices pattern):

```
┌────────────────────┐     REST API     ┌──────────────────────┐   Inference Request   ┌──────────────────────┐
│   React Frontend   │ ───────────────► │   Django Gateway     │ ────────────────────► │  FastAPI ML Engine   │
│   (Vercel)         │ ◄─────────────── │   (Render)           │ ◄──────────────────── │  (HuggingFace)       │
│                    │   Enriched Data  │                      │   Top-3 Predictions   │                      │
└────────────────────┘                  └──────────────────────┘                       └──────────────────────┘
```

- **Frontend (Vercel):** React SPA — handles user input, validation, and result visualization.
- **Backend Gateway (Render):** Django REST API — acts as a secure intermediary. Zero ML dependencies. Routes all inference to the HuggingFace Space. Enriches responses with metadata, images, and nutrition data from its own database and CSV files.
- **ML Engine (HuggingFace Spaces):** FastAPI server — loads the stacked ensemble model, performs inference, and returns raw predictions with confidence scores and nutrition data.

### 1.5 How Components Communicate

- **Frontend → Backend:** REST API over HTTPS. The frontend sends POST requests with JSON bodies to the Django backend at `/api/predict/`. It uses the native `fetch` API.
- **Backend → ML Engine:** REST API over HTTPS. The Django backend's `hf_service.py` sends POST requests (using the Python `requests` library) to the HuggingFace Space's `/predict` endpoint. Includes retry logic (2 retries) with a 10-second timeout.
- **ML Engine → Backend:** JSON response containing `predictions` array (top-3 crops with confidence scores and nutrition data) plus `model_info` and `environment_info`.
- **Backend → Frontend:** JSON response enriched with image URLs (from GitHub raw content), expected yield, season info, risk levels, and nutrition data from the `Nutrient.csv` file.

### 1.6 Deployment Platforms

| Component | Platform | URL |
|-----------|----------|-----|
| **Frontend** | Vercel | `https://crop-recomandation-system.vercel.app/` |
| **Backend** | Render (Free Tier, 512 MB RAM) | `https://crop-recomandation-system.onrender.com/` |
| **ML Model** | HuggingFace Spaces (Docker SDK) | `https://huggingface.co/spaces/shingala/CRS` → `https://shingala-crs.hf.space` |

### 1.7 Environment Setup Details

#### Frontend Environment

- **`.env` file:** Contains `VITE_API_BASE_URL=http://localhost:8000/api` for local development.
- **Production fallback:** Hardcoded in `api.ts` as `https://crop-recomandation-system.onrender.com/api`.
- **Build command:** `vite build`
- **Dev command:** `vite` (served on `http://localhost:5173` by default)
- **Path aliases:** `@` → `./src` (configured in `vite.config.ts` and `tsconfig.json`)

#### Backend Environment

- **`.env.example` variables:**
  - `DJANGO_SECRET_KEY` — auto-generated on Render
  - `DJANGO_DEBUG` — `False` in production
  - `DJANGO_ALLOWED_HOSTS` — `.onrender.com,localhost`
  - `CORS_ALLOWED_ORIGINS` — `http://localhost:5173,http://localhost:5174,https://crop-recomandation-system.vercel.app`
  - `HF_MODEL_URL` — `https://shingala-crs.hf.space`
  - `HF_TOKEN` — optional Bearer token for private Spaces
  - `AI_ML_DIR` — optional path to Aiml directory
  - `SECURE_SSL_REDIRECT` — `True`/`False`
- **Render deployment (render.yaml):**
  - Region: Oregon
  - Root dir: `Backend/app`
  - Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py sync_crops`
  - Start: `python manage.py migrate --noinput && python manage.py sync_crops && gunicorn app.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile -`

#### ML Engine Environment

- **Dockerfile** (at project root, for HuggingFace):
  - Base: `python:3.11-slim`
  - Installs `libgomp1` (required by LightGBM)
  - Copies `Aiml/` directory and `app.py` wrapper
  - Exposes port 7860
  - CMD: `python -m uvicorn app:app --host 0.0.0.0 --port 7860`
- **`app.py`** (project root): Wrapper that dynamically loads `Aiml/app.py` via `importlib`, changes CWD to `Aiml/` so relative file paths (joblib, CSV) work.

---

## 2. ML Model Details

### 2.1 Algorithm Used

**Stacked Ensemble V3** — A two-level stacking architecture:

- **Level 1 (Base Models):**
  - `BalancedRF` — Balanced Random Forest Classifier
  - `XGBoost` — XGBoost Classifier
  - `LightGBM` — LightGBM Classifier
  - Each base model is trained using K-Fold cross-validation. The fold models are stored and used at inference time — predictions from all folds are averaged for each base model.

- **Level 2 (Meta-Learner):**
  - A meta-learner that takes the concatenated probability outputs of all three base models as input features and produces the final probability distribution.
  - Meta-features shape: `[1, num_base_models × num_classes]`

### 2.2 Why This Algorithm Was Selected

- **Stacking** combines the strengths of diverse model families (tree-based: RF, gradient boosting: XGB/LGBM), reducing variance and improving generalization.
- **Balanced RF** handles class imbalance natively.
- **XGBoost and LightGBM** provide high accuracy with regularization.
- **The meta-learner** learns optimal blending weights, outperforming simple averaging or voting.
- Previous iterations (V1: single RF on synthetic data, V2: calibrated RF on real-world data) had limitations. V3's stacked ensemble achieved statistically optimal performance with real-world data integration and honest feature engineering (no data leakage).

### 2.3 Dataset Types Used

**Both — Original and Synthetic, with Real-World Integration**

#### Original Dataset
- `Crop_recommendation.csv` — 150 KB, the foundational Kaggle-style dataset with 7 features (N, P, K, temperature, humidity, ph, rainfall) and crop labels.

#### Synthetic Datasets
- `crop_recommendation_synthetic_v1.csv` — 518 KB, generated by `00_config.py` using `numpy.linspace` with offset-based shuffling. 200 rows per crop across 51+ crop types.
- `Crop_recommendation_v2.csv` — 1.26 MB, extended synthetic dataset.
- `Crop_recommendation_synthetic_AplusB.csv` — 1.53 MB, combined synthetic dataset.

#### Real-World Datasets
- `ICRISAT-District_Level_Data.csv` — 9.26 MB, district-level agricultural data from ICRISAT.
- `data_core.csv` — 374 KB, core features extracted from real-world sources.
- `temperature.csv` — 2 KB, temperature reference data.
- `rainfall.csv` — 5.6 KB, rainfall reference data.
- `real_world_merged_dataset.csv` — 26.9 MB, the final merged dataset used for training the honest model. **186,440 total samples** across 19 crop classes.
- `real_world_ml_dataset.csv` — 23.3 MB, ML-ready subset.

### 2.4 How Synthetic Data Was Generated

Synthetic data generation is implemented in `00_config.py`:

1. **Parameter ranges** are defined per crop in the `crop_params` dictionary, specifying min/max for N, P, K, temperature, humidity, pH, and rainfall.
2. For each crop, `ROWS_PER_CROP` (200) values are generated using `numpy.linspace` between min and max for each feature.
3. Values are rounded to appropriate decimal places and clipped to stay within range.
4. Features are **offset-shuffled** using modular arithmetic (`(i + offset) % ROWS_PER_CROP`) to create diverse feature combinations while maintaining agronomic validity.
5. The complete DataFrame is shuffled once with `random_state=42` and saved to CSV.

### 2.5 Exact Feature List (in correct order)

The V3 stacked ensemble model uses **11 features** in the following exact order:

| # | Feature | Type | Description |
|---|---------|------|-------------|
| 1 | `n` | float | Nitrogen content (kg/ha) |
| 2 | `p` | float | Phosphorus content (kg/ha) |
| 3 | `k` | float | Potassium content (kg/ha) |
| 4 | `temperature` | float | Temperature (°C) |
| 5 | `humidity` | float | Humidity (%) |
| 6 | `ph` | float | Soil pH |
| 7 | `rainfall` | float | Rainfall (mm) |
| 8 | `season` | int | 0=Kharif, 1=Rabi, 2=Zaid |
| 9 | `soil_type` | int | 0=Sandy, 1=Loamy, 2=Clay |
| 10 | `irrigation` | int | 0=Rainfed, 1=Irrigated |
| 11 | `moisture` | float | Soil moisture (%) |

**Note:** Feature names are **lowercase** in the model. The API accepts uppercase N, P, K and maps them to lowercase internally.

### 2.6 Data Preprocessing Steps

1. **Leaky feature removal:** 11 post-planting and geography-identity features removed: `yield`, `area`, `production`, `state_encoded`, `district_encoded`, `jun-sep`, `oct-dec`, `jan-feb`, `mar-may`, `rain_monsoon`, `rain_postmonsoon`. Total leaked importance was 0.2319.
2. **Season inference:** If season is not provided, it is inferred from temperature: `>= 28°C → Kharif (0)`, `<= 22°C → Rabi (1)`, `else → Zaid (2)`.
3. **Default imputation:** `soil_type` defaults to 1 (loamy), `irrigation` defaults to 0 (rainfed), `moisture` defaults to 43.5%.
4. **Feature ordering:** Input DataFrame is reindexed to match the exact `FEATURES` list order from `stacked_v3_config.joblib`.

### 2.7 Label Encoding Method

- **joblib-serialized LabelEncoder** (`label_encoder_v3.joblib`) from scikit-learn.
- Encodes 19 crop names to integer indices (0-18).
- Classes (alphabetical): barley, castor, chickpea, cotton, finger_millet, groundnut, linseed, maize, mustard, pearl_millet, pigeonpea, rice, safflower, sesamum, sorghum, soybean, sugarcane, sunflower, wheat.
- `inverse_transform()` is used at inference time to convert predicted indices back to crop names.

### 2.8 Scaling/Normalization Method

- **No explicit feature scaling** is applied at inference time. The `calibration_config.json` has an empty `feature_scaling` field: `{}`.
- The tree-based models (RF, XGBoost, LightGBM) in the stacked ensemble are inherently scale-invariant.
- **Bayesian calibration** is applied via `CalibratedClassifierCV` with `sigmoid` method and `cv=3` for the honest model variant.

### 2.9 Training Accuracy

From `training_metadata_real_honest.json`:

| Metric | Value |
|--------|-------|
| **Top-1 Accuracy (honest)** | 77.37% |
| **Top-3 Accuracy (honest)** | 98.74% |
| **Base Top-1 Accuracy** | 78.58% |
| **Base Top-3 Accuracy** | 98.89% |
| **Max Confidence** | 95.28% |

### 2.10 Testing Accuracy

- **Top-1 Test Accuracy:** 77.37% (on 20% test split, 37,288 samples)
- **Top-3 Test Accuracy:** 98.74%
- **Comparison with leaky model:** The previous leaky model achieved 90.18% top-1 (with 22 features including post-planting data). The honest model sacrifices 12.82% top-1 accuracy but eliminates all data leakage.

### 2.11 Cross-Validation Details

- **Method:** K-Fold cross-validation
- **CV Mean Accuracy:** 78.65%
- **CV Standard Deviation:** 0.00077 (extremely stable)
- **Random State:** 42
- **Calibration CV:** 3-fold (for CalibratedClassifierCV with sigmoid method)
- **Base model parameters:** n_estimators=150, max_depth=25

### 2.12 How Top 3 Crops Are Calculated

In `Aiml/app.py`, `predict()` endpoint:

1. Each base model (BalancedRF, XGBoost, LightGBM) produces probability vectors. For each base model, predictions from all fold models are **averaged** across folds.
2. The three averaged probability vectors are **horizontally stacked** into a meta-feature vector.
3. The meta-learner produces the **final probability distribution** over all 19 classes.
4. Post-processing is applied (temperature scaling, inverse-frequency weighting, class thresholds, entropy penalty).
5. `numpy.argsort(proba)[-top_n:][::-1]` selects the indices of the **top N** (default 3) highest probabilities.
6. For each top index, the label encoder's `inverse_transform` maps the index to the crop name.

### 2.13 How Probability/Confidence Is Calculated

The raw probability from the meta-learner undergoes four post-processing steps:

1. **Temperature Scaling** (`apply_temperature`): Applies softmax temperature `T` (default 1.0). When T=1.0, no change. When T>1, probabilities are smoothed; when T<1, sharpened. Formula: `exp(log(p)/T) / sum(exp(log(p)/T))`.

2. **Inverse-Frequency Weighting** (`apply_inv_freq`): Multiplies probabilities by pre-computed inverse-frequency weights (19 values from `calibration_config.json`). This boosts underrepresented crops (e.g., safflower: weight 2.44) and slightly downweights overrepresented ones (e.g., rice: weight 0.62). Result is re-normalized.

3. **Class Thresholds**: Each class has a per-class threshold (from `stacked_v3_config.joblib`). Probabilities are divided by these thresholds and re-normalized. Thresholds range from 0.35 (safflower) to 0.55 (sorghum).

4. **Entropy Penalty** (`apply_entropy_penalty`): If the entropy of the distribution is below `ENTROPY_THRESHOLD` (0.4), the dominant class is penalized by `DOMINANCE_PENALTY` (0.15 = 15%). The removed probability mass is redistributed proportionally to other classes. This prevents over-confident single-crop predictions.

**Final confidence** is `proba[idx] * 100`, rounded to 2 decimal places.

### 2.14 How Threshold Logic (< 50%) Is Handled

- **Backend (`ml_inference.py`):** The `_risk_level()` function maps confidence to risk labels:
  - `>= 80%` → `"low"` risk
  - `>= 50%` → `"medium"` risk
  - `< 50%` → `"high"` risk
- **Frontend (`ResultsSection.tsx`):** The `ConfidenceBar` component uses color-coded visual indicators:
  - `>= 75%` → Green gradient (`from-green-500 to-emerald-500`)
  - `>= 50%` → Yellow gradient (`from-yellow-400 to-amber-500`)
  - `< 50%` → Red gradient (`from-orange-400 to-red-500`)
- The confidence badge in the top-3 cards also uses color coding: green (>=75%), yellow (>=50%), red (<50%).
- There is **no hard filtering** that removes low-confidence results; all top-3 are always returned and displayed.

### 2.15 Model File Name and Format

| File | Format | Size | Purpose |
|------|--------|------|---------|
| `stacked_ensemble_v3.joblib` | joblib | 152.9 MB | V3 stacked ensemble (fold_models + meta_learner) |
| `label_encoder_v3.joblib` | joblib | 438 B | LabelEncoder for 19 classes |
| `stacked_v3_config.joblib` | joblib | 917 B | Feature names, tuning params, thresholds |
| `model_real_world_honest.joblib` | joblib | 235.9 MB | Honest RF model (CalibratedClassifierCV) |
| `model_real_world_honest_v2.joblib` | joblib | 55.4 MB | Honest RF v2 |
| `model_rf.joblib` | joblib | 46.9 MB | V2 synthetic RF model |
| `label_encoder.joblib` | joblib | 612 B | LabelEncoder for V2 synthetic model |
| `label_encoder_real_honest.joblib` | joblib | 438 B | LabelEncoder for honest model |
| `binary_classifiers_v3.joblib` | joblib | 1.7 KB | Binary classifiers for V3 |
| `hybrid_v2_config.joblib` | joblib | 1.9 KB | Hybrid V2 configuration |
| `calibration_config.json` | JSON | 2.1 KB | Calibration parameters |

### 2.16 Where the Model Is Stored

- **Production:** Inside the Docker container on HuggingFace Spaces. The Dockerfile copies the entire `Aiml/` directory into `/app/Aiml/`. The `app.py` wrapper changes CWD to `Aiml/` before loading.
- **Local development:** In the `Aiml/` directory at the project root.
- **The backend (Render) does NOT store or load any ML models.** It has zero ML dependencies.

### 2.17 Model Loading Logic

In `Aiml/app.py` (module-level, at import time):

```python
stacked_model = joblib.load("stacked_ensemble_v3.joblib")
label_encoder = joblib.load("label_encoder_v3.joblib")
config = joblib.load("stacked_v3_config.joblib")
nutrients_df = pd.read_csv("Nutrient.csv")

FOLD_MODELS = stacked_model["fold_models"]  # dict: {"BalancedRF": [...], "XGBoost": [...], "LightGBM": [...]}
META_LEARNER = stacked_model["meta_learner"]
FEATURES = config["feature_names"]  # ['n', 'p', 'k', ...]

TEMPERATURE = config.get("temperature", 1.0)
INV_FREQ_WEIGHTS = np.array(config.get("inv_freq_weights", []))
CLASS_THRESHOLDS = np.array(config.get("class_thresholds", []))
ENTROPY_THRESHOLD = config.get("entropy_threshold", 0.4)
DOMINANCE_PENALTY = config.get("dominance_penalty", 0.15)
```

If loading fails, a fallback feature list is used but the server will error on prediction attempts.

---

## 3. Backend Details

### 3.1 Full List of API Endpoints

#### 3.1.1 POST `/api/predict/` — Crop Prediction

- **HTTP Method:** POST
- **Permission:** AllowAny
- **View:** `CropPredictionView` (class-based APIView)

**Request Format (JSON):**

```json
{
  "N": 90,
  "P": 42,
  "K": 43,
  "temperature": 24.5,
  "humidity": 68,
  "ph": 6.7,
  "rainfall": 120,
  "mode": "original",
  "soil_type": 1,
  "irrigation": 0,
  "moisture": 43.5
}
```

| Field | Type | Required | Range | Default | Description |
|-------|------|----------|-------|---------|-------------|
| N | float | Yes | 0-150 | — | Nitrogen (kg/ha) |
| P | float | Yes | 0-150 | — | Phosphorus (kg/ha) |
| K | float | Yes | 0-300 | — | Potassium (kg/ha) |
| temperature | float | Yes | 0-50 | — | Temperature (°C) |
| humidity | float | Yes | 0-100 | — | Humidity (%) |
| ph | float | Yes | 3.5-9.5 | — | Soil pH |
| rainfall | float | Yes | 0-3000 | — | Rainfall (mm) |
| mode | string | No | original/synthetic/both | "original" | Prediction mode |
| soil_type | int | No | 0-2 | 1 | 0=sandy, 1=loamy, 2=clay |
| irrigation | int | No | 0-1 | 0 | 0=rainfed, 1=irrigated |
| moisture | float | No | 0-100 | 43.5 | Soil moisture (%) |

**Response Format (200 OK):**

```json
{
  "mode": "original",
  "top_1": {
    "crop": "rice",
    "confidence": 98.6,
    "risk_level": "low",
    "image_url": "https://raw.githubusercontent.com/.../rice1.jpeg",
    "image_urls": ["...url1", "...url2", "...url3"],
    "expected_yield": "3-6 tons/hectare",
    "season": "Kharif",
    "nutrition": {
      "protein_g": 72.0,
      "fat_g": 6.0,
      "carbs_g": 790.0,
      "fiber_g": 13.0,
      "iron_mg": 7.0,
      "calcium_mg": 100.0,
      "vitamin_a_mcg": 0.0,
      "vitamin_c_mg": 0.0,
      "energy_kcal": 3600.0,
      "water_g": 120.0
    }
  },
  "top_3": [ "...same structure as top_1, 3 items..." ],
  "model_info": {
    "type": "stacked-ensemble-v3",
    "coverage": 19,
    "version": "3.0"
  }
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Invalid input (validation failure) |
| 500 | Prediction error |
| 503 | ML service (HuggingFace) unavailable |

#### 3.1.2 GET `/api/health/` — Health Check

- **HTTP Method:** GET
- **Permission:** AllowAny

**Response:**

```json
{
  "status": "healthy",
  "database": "ok",
  "ml_model": "ok",
  "modes": ["original", "synthetic", "both"],
  "crop_count": 59,
  "original_crops": 19,
  "synthetic_crops": 51
}
```

#### 3.1.3 GET `/api/crops/available/?mode=original` — Available Crops

- **HTTP Method:** GET
- **Permission:** AllowAny
- **Query Parameter:** `mode` (original | synthetic | both)

**Response:**

```json
{
  "mode": "original",
  "count": 19,
  "crops": ["barley", "castor", "chickpea", "..."]
}
```

#### 3.1.4 CRUD `/api/crops/` — Crop Management (DRF Router)

| Method | URL | Permission | Description |
|--------|-----|------------|-------------|
| GET | `/api/crops/` | AllowAny | List all crops (paginated, 20/page) |
| POST | `/api/crops/` | IsAuthenticated | Create a crop |
| GET | `/api/crops/{id}/` | AllowAny | Get specific crop |
| PUT | `/api/crops/{id}/` | IsAuthenticated | Update crop |
| DELETE | `/api/crops/{id}/` | IsAuthenticated | Delete crop |

#### 3.1.5 GET `/api/logs/` — Prediction Logs (Read-Only)

| Method | URL | Permission | Description |
|--------|-----|------------|-------------|
| GET | `/api/logs/` | IsAuthenticated | List all prediction logs |
| GET | `/api/logs/{id}/` | IsAuthenticated | Get specific log |

#### 3.1.6 Other URLs

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Home page (renders `apps/index.html` template) |
| GET | `/admin/` | Django Admin Panel |
| GET | `/media/crops/` | Media crops listing (HTML index) |
| GET | `/media/crops/{filename}` | Media crops redirect (to GitHub/Cloudinary) |

### 3.2 Prediction Pipeline Implementation Details

1. `CropPredictionView.post()` receives the request.
2. `PredictionInputSerializer` validates all fields against defined ranges.
3. `predict_top_crops()` from `ml_inference.py` is called with validated data.
4. `_predict_via_hf()` constructs a payload and calls `call_hf_model()` from `hf_service.py`.
5. `call_hf_model()` sends a POST request to `{HF_MODEL_URL}/predict` with retry logic (2 attempts, 10s timeout).
6. Response is normalized: extracts `top_3` or `predictions`, adds `risk_level` per crop.
7. Back in the view, `_enrich()` adds image URLs (from Crop DB), expected yield, season, and nutrition data (from `Nutrient.csv`).
8. `top_1` is derived from `top_3[0]`.
9. `_log_prediction()` saves the request to `PredictionLog` model (async-safe, failure-tolerant).

### 3.3 Mode Selection Logic

All three modes (`original`, `synthetic`, `both`) are **routed to the same HuggingFace Space**. The mode tag is preserved in the response for frontend display purposes, but the actual model used is always the V3 stacked ensemble (19 real-world crops). The `_ORIGINAL_CROPS` (19), `_SYNTHETIC_CROPS` (51), and merged lists are used only for the `/api/crops/available/` endpoint.

### 3.4 Error Handling Logic

- **Validation errors:** DRF serializer returns 400 with field-specific error details.
- **HuggingFace unreachable:** `call_hf_model()` returns `None` after 2 retries → `predict_top_crops()` raises `ConnectionError` → view returns 503.
- **Unexpected errors:** Caught by generic `Exception` handler in view → returns 500 with error details.
- **Prediction logging failures:** Caught silently with `logger.warning()` — never affects the response.
- **Nutrition CSV lookup failures:** Caught silently — `nutrition` field is set to `None`.

### 3.5 Logging Mechanism

- **Django logging configuration** in `settings.py`:
  - Format: `{levelname} {asctime} {module} {message}`
  - Handlers: Console (StreamHandler)
  - Loggers: `apps` (INFO), `django` (INFO)
- **HF service logging:** Logs each attempt (warning for timeout/connection errors, error for HTTP errors, exception for unexpected errors).
- **Prediction logging to database:** Every prediction is stored in `PredictionLog` model with input parameters, results, IP address, and timestamp.

### 3.6 CORS Configuration

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://crop-recomandation-system.vercel.app"
]
# Supports wildcard "*" via CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["accept", "accept-encoding", "authorization", "content-type", "dnt", "origin", "user-agent", "x-csrftoken", "x-requested-with"]
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
```

`CorsMiddleware` is placed **first** in the middleware stack.

### 3.7 Middleware Used

1. `corsheaders.middleware.CorsMiddleware` — CORS handling (must be first)
2. `django.middleware.security.SecurityMiddleware` — Security headers
3. `whitenoise.middleware.WhiteNoiseMiddleware` — Static file serving
4. `django.contrib.sessions.middleware.SessionMiddleware` — Session management
5. `django.middleware.common.CommonMiddleware` — Common HTTP handling
6. `django.middleware.csrf.CsrfViewMiddleware` — CSRF protection
7. `django.contrib.auth.middleware.AuthenticationMiddleware` — Auth
8. `django.contrib.messages.middleware.MessageMiddleware` — Messages
9. `django.middleware.clickjacking.XFrameOptionsMiddleware` — Clickjacking protection

### 3.8 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | insecure fallback | Secret key (auto-generated on Render) |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,.onrender.com` | Allowed hosts |
| `RENDER_EXTERNAL_HOSTNAME` | — | Auto-set by Render |
| `HF_MODEL_URL` / `HF_API_URL` | `https://shingala-crs.hf.space` | HuggingFace Space URL |
| `HF_TOKEN` | `""` | Optional auth token |
| `CORS_ALLOWED_ORIGINS` | localhost + vercel | Comma-separated origins |
| `SECURE_SSL_REDIRECT` | `False` | HTTPS redirect |
| `AI_ML_DIR` | — | Override path to Aiml directory |
| `PYTHON_VERSION` | `3.11.0` | Python version on Render |

### 3.9 Backend Dependencies (`Backend/app/requirements.txt`)

```
Django>=5.0
djangorestframework>=3.14
django-cors-headers>=4.3
Pillow>=10.0
gunicorn==22.0.0
python-dotenv>=1.0
whitenoise>=6.6.0
requests>=2.31.0
django-cloudinary-storage>=0.3.0
```

---

## 4. Frontend Details

### 4.1 Framework and Version

- **React:** 18.3.1
- **TypeScript:** ESNext target, strict mode
- **Build Tool:** Vite 6.3.5
- **CSS:** Tailwind CSS 4.1.12

### 4.2 Folder Structure

```
Frontend/
├── .env                          # API base URL
├── index.html                    # SPA entry point
├── package.json                  # Dependencies and scripts
├── pnpm-lock.yaml                # Lock file
├── postcss.config.mjs            # PostCSS configuration
├── tsconfig.json                 # TypeScript config
├── tsconfig.node.json            # Node TypeScript config
├── vite.config.ts                # Vite configuration
├── dist/                         # Production build output
├── guidelines/                   # Design guidelines
├── node_modules/                 # Dependencies
└── src/
    ├── main.tsx                  # Application entry point
    ├── vite-env.d.ts             # Vite type definitions
    ├── styles/
    │   ├── index.css             # Global styles import
    │   ├── tailwind.css           # Tailwind base imports
    │   ├── fonts.css              # Font definitions
    │   └── theme.css              # Theme variables
    └── app/
        ├── App.tsx               # Root application component
        ├── components/
        │   ├── InputForm.tsx     # Soil parameter input form
        │   ├── ResultsSection.tsx # Prediction results display
        │   ├── ui/               # 48 Radix-based UI primitives
        │   └── figma/            # Figma-generated components
        └── services/
            └── api.ts            # API service layer
```

### 4.3 Input Fields Collected

**Required Fields (7):**

| Field | Name Attribute | Type | Range | Icon |
|-------|---------------|------|-------|------|
| Nitrogen (N) | `nitrogen` | number | 0-150 kg/ha | FlaskConical (blue) |
| Phosphorus (P) | `phosphorus` | number | 0-150 kg/ha | FlaskConical (orange) |
| Potassium (K) | `potassium` | number | 0-300 kg/ha | FlaskConical (purple) |
| Temperature | `temperature` | number | 0-50 °C | Thermometer (red) |
| Humidity | `humidity` | number | 0-100 % | Droplet (blue) |
| Soil pH | `ph` | number | 3.5-9.5 pH | Gauge (green) |
| Rainfall | `rainfall` | number | 0-3000 mm | CloudRain (sky) |

**Advanced Fields (3, collapsible):**

| Field | Name Attribute | Type | Options/Range | Default |
|-------|---------------|------|---------------|---------|
| Soil Type | `soil_type` | select | 0=Sandy, 1=Loamy, 2=Clay | 1 (Loamy) |
| Irrigation | `irrigation` | select | 0=Rainfed, 1=Irrigated | 0 (Rainfed) |
| Soil Moisture | `moisture` | number | 0-100 % | 43.5 |

**Mode Selection (1):**

| Field | Name Attribute | Type | Options | Default |
|-------|---------------|------|---------|---------|
| Prediction Mode | `mode` | hidden (radio-like cards) | original/synthetic/both | original |

### 4.4 Validation Logic

Validation is implemented in `InputForm.tsx`:

1. **`VALIDATION_RANGES` object** defines min, max, and unit for each numeric field.
2. **`validateField()`** function checks: empty → pass, NaN → error message, below min → error, above max → error.
3. **`handleInputBlur()`** validates on blur (when user leaves a field) and updates the `errors` state.
4. **`handleSubmit()`** validates all 7 required fields before submission. If any error exists, `onSubmit` is not called.
5. Visual feedback: Fields with errors get a red border (`border-red-500`), with error text displayed below.

### 4.5 How Data Is Sent to Backend

In `App.tsx` → `handleSubmit()`:

1. `FormData` is extracted from the form element.
2. Values are parsed: `parseFloat()` for numeric fields, `parseInt()` for soil_type/irrigation.
3. A `PredictionInput` object is constructed with fields mapped: `nitrogen → N`, `phosphorus → P`, `potassium → K`, etc.
4. `getPrediction(input)` from `api.ts` is called.
5. In `api.ts`, a `fetch()` POST request is made to `${API_BASE_URL}/predict/` with `Content-Type: application/json` and `JSON.stringify(input)` as the body.
6. The response is parsed as JSON and returned as `PredictionResponse`.

### 4.6 How Response Is Parsed

In `api.ts` → `getPrediction()`:

1. If `response.ok` is false, error details are extracted from the JSON body or status text, and an `Error` is thrown.
2. If the response is ok, `response.json()` is called and the result is cast to `PredictionResponse`.
3. In `App.tsx`, the response is validated: `response.top_1` and `response.top_3` must exist, otherwise an error is thrown.
4. On success, `setResults(response)` updates the state, triggering `ResultsSection` to render.
5. Network errors (`Failed to fetch`, `NetworkError`) are caught and re-thrown with a user-friendly message.

### 4.7 How Top 3 Crops Are Displayed

In `ResultsSection.tsx`:

1. **Hero Card (Top-1/Selected):** A large card with gradient header showing the selected crop name (5xl font), confidence badge, mode badge, image carousel (`AutoCarousel` with 3-second auto-rotation), nutrition table (per kg), season, expected yield, confidence bar, and model coverage info.
2. **Top-3 Grid:** Three clickable cards in a responsive grid (`grid-cols-1 md:grid-cols-3`). Each shows: crop image, rank badge (#1 gold, #2 silver, #3 bronze), confidence badge (color-coded), crop name, confidence bar, yield, and season.
3. **Interaction:** Clicking a top-3 card updates `selectedIdx` state, which changes the hero card to display that crop's details. Page scrolls to top smoothly.
4. **Important Note:** An amber info box warns users to consult local agricultural experts.
5. **Try Another:** A button at the bottom reloads the page for a new analysis.

### 4.8 How Confidence < 50% Is Handled

- **Visual indicators only** — no crops are hidden or filtered.
- `ConfidenceBar` component: `< 50%` → red/orange gradient bar, red text color.
- Top-3 card badges: `< 50%` → `bg-red-100 text-red-700 border-red-200`.
- `< 75%` but `>= 50%` → yellow/amber indicators.
- `>= 75%` → green indicators.
- The backend adds `risk_level: "high"` for `< 50%` confidence (available but not explicitly displayed in the current frontend).

### 4.9 State Management Method

**React `useState` hooks** (no external state management library):

| State Variable | Type | Location | Purpose |
|---------------|------|----------|---------|
| `results` | `PredictionResponse \| null` | `App.tsx` | Stores the API response |
| `isLoading` | `boolean` | `App.tsx` | Loading spinner state |
| `error` | `string \| null` | `App.tsx` | Error message display |
| `errors` | `Record<string, string>` | `InputForm.tsx` | Field validation errors |
| `mode` | `'original' \| 'synthetic' \| 'both'` | `InputForm.tsx` | Selected prediction mode |
| `showAdvanced` | `boolean` | `InputForm.tsx` | Advanced params visibility |
| `selectedIdx` | `number` | `ResultsSection.tsx` | Selected crop in top-3 |
| `idx` | `number` | `AutoCarousel` | Current carousel slide |

### 4.10 UI Conditional Rendering Logic

In `App.tsx`:

```
if isLoading → Show spinner + "Analyzing your soil data..."
if error → Show red error box with message and help text
if results && !isLoading → Show <ResultsSection>
if !results && !isLoading → Show "How It Works" info card
```

In `ResultsSection.tsx`:

```
if !top_1 || !top_3.length → Show yellow "No recommendations" box
if selected.image_urls.length > 0 → Show AutoCarousel
else → Show single image (image_url or placeholder)
if selected.nutrition → Show nutrition table
Always show: confidence bar, season, yield, model info
```

---

## 5. Complete Data Flow

### Step-by-Step Data Flow

```
User Input → Frontend Validation → API Call → Backend Processing → HF Model Prediction → Post-Processing → Response Enrichment → Frontend Display
```

#### Step 1: User Input

The user fills in 7 required fields (N, P, K, temperature, humidity, ph, rainfall) and optionally configures 3 advanced fields (soil_type, irrigation, moisture) and selects a prediction mode (original/synthetic/both) in `InputForm.tsx`.

#### Step 2: Frontend Validation

`InputForm.tsx` → `handleSubmit()`:

1. `FormData` is extracted from the `<form>` element.
2. Each of the 7 required fields is validated against `VALIDATION_RANGES`: check not empty, check is number (`isNaN`), check within `[min, max]`.
3. If any validation error exists, error is displayed below the field and submission is blocked.
4. If all pass, `onSubmit(e)` triggers `App.tsx` → `handleSubmit()`.

#### Step 3: API Call

`App.tsx` → `handleSubmit()` → `api.ts` → `getPrediction()`:

1. State set: `isLoading=true`, `error=null`, `results=null`.
2. Form values parsed and mapped: `nitrogen→N`, `phosphorus→P`, `potassium→K`, etc.
3. `fetch()` sends POST to `${VITE_API_BASE_URL}/predict/` with `Content-Type: application/json`.

#### Step 4: Backend Processing

`views.py` → `CropPredictionView.post()`:

1. `PredictionInputSerializer` validates all fields with DRF validators.
2. If validation fails → 400 with error details.
3. `predict_top_crops()` called from `ml_inference.py`.
4. `_predict_via_hf()` constructs payload, calls `call_hf_model()`.
5. `hf_service.py` → POST to `https://shingala-crs.hf.space/predict` with retry logic (2 attempts, 10s timeout).

#### Step 5: Model Prediction (HuggingFace)

`Aiml/app.py` → `predict()`:

1. `PredictionInput` Pydantic model validates incoming JSON.
2. Season inferred from temperature if not provided: `>=28°C → Kharif(0)`, `<=22°C → Rabi(1)`, `else → Zaid(2)`.
3. Input features assembled: `[n, p, k, temperature, humidity, ph, rainfall, season, soil_type, irrigation, moisture]`.
4. DataFrame created and reindexed to match `FEATURES`.
5. **Base model predictions:** For BalancedRF, XGBoost, LightGBM — all fold models predict `predict_proba(X)[0]`, averaged.
6. **Meta-learner:** Three probability vectors horizontally stacked (`numpy.hstack`), reshaped to `(1, -1)`. Meta-learner's `predict_proba()` → final probability vector.

#### Step 6: Post-Processing

1. **Temperature scaling:** `apply_temperature(proba, T=1.0)` — no-op at T=1.0.
2. **Inverse-frequency weighting:** Multiplies by pre-computed weights, re-normalizes.
3. **Class thresholds:** `proba / thresholds`, re-normalized.
4. **Entropy penalty:** If entropy < 0.4, dominant class penalized by 15%.

#### Step 7: Top-3 Selection

1. `numpy.argsort(proba)[-3:][::-1]` → top 3 indices.
2. `label_encoder.inverse_transform([idx])` → crop names.
3. Confidence = `proba[idx] * 100`, rounded to 2 decimals.
4. Nutrition looked up from `Nutrient.csv`.

#### Step 8: Response Enrichment (Backend)

1. `_predict_via_hf()` normalizes response: extracts predictions, adds `risk_level`.
2. `_enrich()` adds per-crop: `image_url`, `image_urls` (from Crop DB → GitHub), `expected_yield`, `season`, `nutrition`.
3. `top_1` set to `top_3[0]`.
4. `_log_prediction()` saves to `PredictionLog`.

#### Step 9: Frontend Display

1. `setResults(response)` triggers re-render.
2. `ResultsSection` renders hero card (top-1) + top-3 grid.
3. Color coding applied based on confidence thresholds.
4. User can click cards to change the selected crop in the hero view.

---

## 6. Known Limitations & Technical Debt

### 6.1 Hardcoded Logic

1. **Season inference** is hardcoded: `>=28°C → Kharif`, `<=22°C → Rabi`, `else → Zaid`. Does not account for geography or calendar dates.
2. **Default values**: `soil_type=1` (loamy), `irrigation=0` (rainfed), `moisture=43.5%` — may not be universally appropriate.
3. **Crop image mapping** in `crop_sync.py` → `_CROP_IMAGES`: 39 crops mapped to GitHub URLs. New crops need manual updates.
4. **Crop metadata** (season, yield) in `_CROP_METADATA`: hardcoded for ~50 crops.
5. **Nutrition name mapping** in `Aiml/app.py` → `NUTRITION_MAPPING`: 5 crop name translations.
6. **Synthetic crop list** (`_SYNTHETIC_CROPS`): 51 crops, hardcoded.
7. **Validation ranges** hardcoded in both frontend and backend — must be manually kept in sync.
8. **HuggingFace fallback URL** hardcoded as `https://shingala-crs.hf.space`.

### 6.2 Scalability Risks

1. **SQLite in production:** Does not support concurrent writes well. Should migrate to PostgreSQL.
2. **Render free tier (512 MB RAM):** Django + SQLite + Gunicorn (2 workers) may hit limits under sustained traffic.
3. **HuggingFace cold starts:** 30-60 seconds after idle, causing timeouts for first requests.
4. **Single-point-of-failure on HuggingFace:** No local fallback model on the backend.
5. **Model file size** (152.9 MB) increases Docker image size and startup time.

### 6.3 Security Weaknesses

1. **SECRET_KEY** has hardcoded insecure fallback if env var not set.
2. **DEBUG** defaults to `True` if env var not set.
3. **CORS wildcard support:** `*` enables `CORS_ALLOW_ALL_ORIGINS = True`.
4. **No rate limiting** on any endpoint.
5. **No authentication** on the prediction endpoint (`AllowAny`).
6. **IP logging** without explicit GDPR compliance.
7. **`SECURE_SSL_REDIRECT`** defaults to `False`.

### 6.4 Performance Bottlenecks

1. **Synchronous HF calls:** `requests` library blocks Gunicorn workers (up to 10s per attempt × 2 attempts).
2. **Nutrient.csv read on every request:** No caching.
3. **3 DB queries per prediction:** `Crop.objects.get()` called per crop in top-3.
4. **No response caching:** Identical inputs always trigger full HF API calls.
5. **Model loading at startup:** 152.9 MB loaded into RAM on HuggingFace.

### 6.5 Incomplete Features

1. **Mode selection is cosmetic:** All 3 modes route to same HF V3 model (19 crops).
2. **Not all crops have images:** 39 of 59 crops covered; rest get placeholders.
3. **Vitamin A/C nutrition fields** defined in frontend types but not provided by HF API.
4. **No frontend for prediction history/analytics** (admin-only).
5. **No user authentication system** — no login, registration, or user history.

### 6.6 Experimental Logic

1. **Entropy penalty** — empirically tuned threshold (0.4) and penalty (0.15).
2. **Inverse-frequency weighting** — can artificially boost rare crops.
3. **Class thresholds** — manually tuned per crop (0.35-0.55).
4. **Temperature scaling** set to 1.0 (no-op) — experimented but unused.
5. **Multiple model files** (V1, V2, V2.2, V3, honest, hybrid) — only V3 active; rest are technical debt.

---

## 7. Full Folder Structure

```
CRS/  (Project Root)
│
├── .git/                                    # Git repository
├── .gitattributes                           # Git attributes (441 B)
├── .github/                                 # GitHub workflows
├── .gitignore                               # Git ignore rules (463 B)
├── Dockerfile                               # HuggingFace Docker config (403 B)
├── app.py                                   # HuggingFace entrypoint wrapper (933 B)
├── requirements.txt                         # HuggingFace deployment deps (269 B)
├── render.yaml                              # Render deployment config (796 B)
├── README.md                                # Project documentation (3.6 KB)
│
├── Aiml/                                    # ═══ ML ENGINE ═══
│   ├── app.py                               # FastAPI ML API server (10.5 KB)
│   ├── predict.py                           # V2 standalone prediction (2.7 KB)
│   ├── requirements.txt                     # ML dependencies (644 B)
│   ├── Dockerfile                           # ML Docker config (331 B)
│   ├── README.md                            # ML documentation (17.8 KB)
│   │
│   ├── # Training Scripts
│   ├── 00_config.py                         # Synthetic data generation (9.2 KB)
│   ├── 01_dataset_generation.py             # Dataset generation pipeline (48.7 KB)
│   ├── 02_baseline_model.py                 # Baseline model training (1.3 KB)
│   ├── 02_train_and_evaluate.py             # Training & evaluation (20 KB)
│   ├── 03_crossvalidation_eval.py           # Cross-validation (1.1 KB)
│   ├── 03_real_world_validation.py          # Real-world validation (45.2 KB)
│   ├── 04_data_augmentation.py              # Data augmentation (1.8 KB)
│   ├── 05_trained_model_eval.py             # Model evaluation (1.7 KB)
│   ├── 06_stress_test.py                    # Stress testing (1.6 KB)
│   ├── 07_single_inference.py               # Single inference test (1.5 KB)
│   ├── 08_top3_recommendations.py           # Top-3 test (1.4 KB)
│   ├── 09_real_world_pipeline.py            # Real-world pipeline (52.6 KB)
│   ├── 10_honest_model.py                   # Honest model training (31.5 KB)
│   ├── final_stacked_model.py               # V3 stacked ensemble builder (52.5 KB)
│   ├── hybrid_model.py                      # Hybrid model experiments (53.4 KB)
│   │
│   ├── # Model Files
│   ├── stacked_ensemble_v3.joblib           # V3 Stacked Ensemble (152.9 MB)
│   ├── stacked_v3_config.joblib             # V3 config (917 B)
│   ├── label_encoder_v3.joblib              # V3 label encoder (438 B)
│   ├── binary_classifiers_v3.joblib         # V3 binary classifiers (1.7 KB)
│   ├── model_real_world_honest.joblib       # Honest RF (235.9 MB)
│   ├── model_real_world_honest_v2.joblib    # Honest RF v2 (55.4 MB)
│   ├── model_rf.joblib                      # V2 synthetic RF (46.9 MB)
│   ├── label_encoder.joblib                 # V2 label encoder (612 B)
│   ├── label_encoder_real_honest.joblib     # Honest label encoder (438 B)
│   ├── calibration_config.json              # Calibration params (2.1 KB)
│   │
│   ├── # Datasets
│   ├── Crop_recommendation.csv              # Original Kaggle (150 KB)
│   ├── Crop_recommendation_v2.csv           # Extended synthetic (1.26 MB)
│   ├── crop_recommendation_synthetic_v1.csv # V1 synthetic (519 KB)
│   ├── ICRISAT-District_Level_Data.csv      # ICRISAT real-world (9.26 MB)
│   ├── real_world_merged_dataset.csv        # Merged real-world (26.9 MB)
│   ├── real_world_ml_dataset.csv            # ML-ready (23.3 MB)
│   ├── Nutrient.csv                         # Crop nutrition (3 KB)
│   │
│   ├── # Metadata & Reports
│   ├── training_metadata_real_honest.json   # Honest model metadata (5.9 KB)
│   ├── calibration_config.json              # Calibration config (2.1 KB)
│   ├── confusion_matrix_real_honest.png     # Honest confusion matrix (122.7 KB)
│   └── ...                                  # Additional reports and visualizations
│
├── Backend/                                 # ═══ DJANGO GATEWAY ═══
│   ├── README.md                            # Backend documentation (18 KB)
│   └── app/
│       ├── manage.py                        # Django management script (1.1 KB)
│       ├── requirements.txt                 # Backend dependencies (781 B)
│       ├── Procfile                         # Render process file (184 B)
│       ├── .env.example                     # Environment template (984 B)
│       ├── db.sqlite3                       # SQLite database (278.5 KB)
│       │
│       ├── app/                             # Django project config
│       │   ├── __init__.py
│       │   ├── settings.py                  # Django settings (9.3 KB)
│       │   ├── urls.py                      # Root URL config (922 B)
│       │   ├── wsgi.py                      # WSGI config (636 B)
│       │   └── asgi.py                      # ASGI config (399 B)
│       │
│       ├── apps/                            # Main Django app
│       │   ├── __init__.py
│       │   ├── apps.py                      # App config (146 B)
│       │   ├── models.py                    # Crop + PredictionLog (6.9 KB)
│       │   ├── views.py                     # API views (13.6 KB)
│       │   ├── urls.py                      # App URL routing (1.9 KB)
│       │   ├── serializers.py               # DRF serializers (5.3 KB)
│       │   ├── admin.py                     # Admin config (10.4 KB)
│       │   ├── ml_inference.py              # ML inference gateway (7 KB)
│       │   │
│       │   ├── services/
│       │   │   ├── hf_service.py            # HuggingFace client (2.6 KB)
│       │   │   └── crop_sync.py             # Crop DB sync (16 KB)
│       │   │
│       │   ├── management/commands/
│       │   │   ├── sync_crops.py            # Crop sync command (3.6 KB)
│       │   │   ├── seed_crops.py            # Legacy seeding (8.7 KB)
│       │   │   └── update_banana_images.py  # Banana fix (1.6 KB)
│       │   │
│       │   ├── migrations/                  # DB migrations
│       │   └── templates/apps/              # HTML templates
│       │
│       └── media/crops/                     # Crop images
│
└── Frontend/                                # ═══ REACT FRONTEND ═══
    ├── .env                                 # API base URL (45 B)
    ├── index.html                           # SPA entry point (353 B)
    ├── package.json                         # Dependencies (2.7 KB)
    ├── vite.config.ts                       # Vite config (509 B)
    ├── tsconfig.json                        # TypeScript config (651 B)
    │
    └── src/
        ├── main.tsx                         # App entry point (189 B)
        ├── styles/
        │   ├── index.css                    # Global styles
        │   ├── tailwind.css                 # Tailwind imports
        │   ├── fonts.css                    # Font definitions
        │   └── theme.css                    # Theme variables
        │
        └── app/
            ├── App.tsx                      # Root component (5.3 KB)
            ├── components/
            │   ├── InputForm.tsx             # Input form (13.3 KB)
            │   ├── ResultsSection.tsx        # Results display (15.6 KB)
            │   ├── ui/                       # 48 Radix UI primitives
            │   └── figma/                    # Figma components
            └── services/
                └── api.ts                   # API service layer (3.8 KB)
```

---

## 8. Version Tag

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   Version:          V3 (Stacked Ensemble)                       ║
║   Date Generated:   2026-02-23                                   ║
║   Environment:      Production (Deployed) + Local Development    ║
║                                                                  ║
║   Frontend:         Vercel                                       ║
║   Backend:          Render                                       ║
║   ML Engine:        HuggingFace Spaces                          ║
║                                                                  ║
║   Model Version:    3.0 (Stacked Ensemble V3)                   ║
║   Model Type:       BalancedRF + XGBoost + LightGBM + Meta      ║
║   Total Classes:    19 real-world crops                          ║
║   Total Features:   11                                           ║
║   Top-1 Accuracy:   77.37% (honest, no data leakage)            ║
║   Top-3 Accuracy:   98.74%                                       ║
║                                                                  ║
║   Generated by:     Automated Documentation System               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*End of V3 Full Technical Documentation*
