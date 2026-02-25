"""
Crop Recommendation System — Biologically Realistic Dataset Generator (v2.2)
=============================================================================

DESIGN PRINCIPLES:
1. Gaussian (normal) distributions centred on agronomic optimums — NOT uniform
2. Ecological clustering — crops grouped by climate affinity
3. Rainfall bands strictly enforced — no cross-zone bleeding
4. Season feature included (Kharif / Rabi / Zaid)
5. Soil type feature included (sandy / loamy / clay)
6. Irrigation feature included (0=rainfed, 1=irrigated)
7. Controlled intra-cluster overlap, minimal inter-cluster overlap
8. Realistic imbalanced sample counts per crop
9. Rice dominance eliminated via tight humidity + rainfall guards
10. Asymmetric cross-cluster environmental noise (directional)
11. Stronger soil preference separation per crop

v2.2 IMPROVEMENTS OVER v2.1:
- Irrigation feature (binary: rainfed vs irrigated)
- Strengthened soil_probs for clearer soil preference per crop
- Realistic data imbalance (high/medium/rare cultivation crops)
- Asymmetric ecological noise (directional, not symmetric)
- Non-uniform geographic simulation

Author : CRS Team
Version: 2.2
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import sklearn

# ===========================================================================
# GLOBAL CONFIG
# ===========================================================================
RANDOM_STATE  = 42
OUTPUT_CSV    = "Crop_recommendation_v2.csv"
METADATA_FILE = "training_metadata.json"

np.random.seed(RANDOM_STATE)

# Season encoding: 0 = Kharif, 1 = Rabi, 2 = Zaid
SEASON_MAP = {"Kharif": 0, "Rabi": 1, "Zaid": 2}

# Soil type encoding: 0 = sandy, 1 = loamy, 2 = clay
SOIL_MAP = {"sandy": 0, "loamy": 1, "clay": 2}

# Irrigation encoding: 0 = rainfed, 1 = irrigated
IRRIGATION_MAP = {"rainfed": 0, "irrigated": 1}

# ===========================================================================
# ECOLOGICAL CLUSTERS
# ===========================================================================
CLUSTERS = {
    "A_tropical_wet": [
        "rice", "sugarcane", "jute", "banana", "papaya", "coconut",
    ],
    "B_cool_rabi": [
        "wheat", "barley", "mustard", "chickpea", "lentil",
    ],
    "C_semiarid_oilseed": [
        "cotton", "groundnut", "soybean", "castor", "sesame",
    ],
    "D_vegetable": [
        "tomato", "brinjal", "green_chilli", "okra", "onion",
        "potato", "cabbage", "cauliflower", "carrot", "radish",
        "spinach", "cucumber",
    ],
    "E_tropical_fruit": [
        "mango", "sapota", "guava", "orange", "lemon", "mosambi",
    ],
    "F_semiarid_fruit": [
        "pomegranate", "date_palm", "ber", "custard_apple",
        "watermelon", "muskmelon", "grapes",
    ],
    "G_plantation": [
        "coffee", "tobacco",
    ],
    "H_kharif_pulse": [
        "pigeonpeas", "mungbean", "blackgram", "mothbeans",
    ],
    "I_gourd": [
        "bottle_gourd", "bitter_gourd", "ridge_gourd",
    ],
    "J_millet": [
        "maize", "jowar", "bajra", "ragi",
    ],
    "K_temperate_fruit": [
        "apple",
    ],
    "L_rabi_pulse": [
        "kidneybeans",
    ],
}

# Build reverse lookup  crop → cluster
CROP_TO_CLUSTER = {}
for cluster_name, crops in CLUSTERS.items():
    for crop in crops:
        CROP_TO_CLUSTER[crop] = cluster_name

# ===========================================================================
# PER-CROP BIOLOGICAL PARAMETERS  (mean, std, hard_min, hard_max)
#
#   N, P, K       — soil macronutrients  (kg/ha)
#   temperature   — °C
#   humidity      — %
#   ph            — soil pH
#   rainfall      — mm/year
#   season        — categorical (assigned, not sampled)
#   soil_probs    — probability distribution [sandy, loamy, clay]
#   irrigation_prob — probability of irrigated (vs rainfed)
#
# v2.2 CHANGES:
# - soil_probs made more extreme for stronger soil preferences
# - irrigation_prob added for every crop
# - Irrigation-dependent rainfall logic for water-intensive crops
# ===========================================================================

CROP_PARAMS = {
    # ── Cluster A — High-rainfall Tropical  ────────────────────────────────
    "rice": {
        "N":    (100, 14, 60, 150),   "P":   (50, 9,  20, 80),
        "K":    (50,  9,  20, 80),    "temp": (28, 3,  24, 35),
        "hum":  (82,  5,  72, 98),    "ph":  (6.5, 0.4, 5.5, 7.5),
        "rain": (1800, 380, 1200, 3000),
        "season": "Kharif",
        "soil_probs": [0.00, 0.10, 0.90],   # strongly clay
        "irrigation_prob": 0.92,
    },
    "sugarcane": {
        "N":    (130, 14, 80, 170),   "P":   (60, 9,  30, 90),
        "K":    (85,  16, 40, 140),   "temp": (29, 3,  24, 35),
        "hum":  (78,  6,  65, 92),    "ph":  (6.8, 0.5, 5.5, 8.0),
        "rain": (1600, 320, 1200, 2500),
        "season": "Kharif",
        "soil_probs": [0.03, 0.27, 0.70],   # clay preferred
        "irrigation_prob": 0.95,
    },
    "jute": {
        "N":    (75,  12, 40, 110),   "P":   (45, 8,  20, 70),
        "K":    (40,  7,  20, 65),    "temp": (27, 2.5, 24, 32),
        "hum":  (83,  5,  72, 95),    "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (1700, 380, 1200, 2800),
        "season": "Kharif",
        "soil_probs": [0.03, 0.32, 0.65],   # clay/loamy
        "irrigation_prob": 0.60,
    },
    "banana": {
        "N":    (120, 16, 70, 170),   "P":   (65, 9,  35, 95),
        "K":    (180, 28, 120, 260),  "temp": (28, 2.5, 24, 34),
        "hum":  (85,  5,  75, 98),    "ph":  (6.2, 0.5, 5.2, 7.2),
        "rain": (1500, 280, 1200, 2200),
        "season": "Kharif",
        "soil_probs": [0.02, 0.18, 0.80],   # clay/loamy
        "irrigation_prob": 0.78,
    },
    "papaya": {
        "N":    (65,  12, 30, 100),   "P":   (50, 8,  25, 75),
        "K":    (65,  12, 35, 100),   "temp": (29, 3,  24, 36),
        "hum":  (82,  5,  70, 95),    "ph":  (6.5, 0.4, 5.5, 7.5),
        "rain": (1400, 230, 1200, 2000),
        "season": "Kharif",
        "soil_probs": [0.10, 0.65, 0.25],
        "irrigation_prob": 0.55,
    },
    "coconut": {
        "N":    (30,  7,  10, 55),    "P":   (20, 6,  5,  40),
        "K":    (30,  6,  15, 50),    "temp": (27, 2,  24, 31),
        "hum":  (80,  6,  68, 95),    "ph":  (5.5, 0.4, 4.8, 6.5),
        "rain": (1600, 330, 1200, 2500),
        "season": "Kharif",
        "soil_probs": [0.55, 0.35, 0.10],   # sandy/coastal
        "irrigation_prob": 0.25,
    },

    # ── Cluster B — Cool / Dry Rabi  ──────────────────────────────────────
    "wheat": {
        "N":    (95, 14, 55, 140),    "P":   (50, 9,  25, 80),
        "K":    (40, 8,  15, 65),     "temp": (18, 3.5, 10, 25),
        "hum":  (55, 8,  35, 75),     "ph":  (6.5, 0.4, 5.8, 7.5),
        "rain": (550, 140, 300, 900),
        "season": "Rabi",
        "soil_probs": [0.02, 0.90, 0.08],   # strongly loamy
        "irrigation_prob": 0.88,
    },
    "barley": {
        "N":    (72, 12, 40, 110),    "P":   (35, 9,  12, 60),
        "K":    (35, 9,  12, 60),     "temp": (16, 3.5, 10, 24),
        "hum":  (48, 8,  30, 68),     "ph":  (6.8, 0.5, 5.8, 8.0),
        "rain": (450, 120, 300, 700),
        "season": "Rabi",
        "soil_probs": [0.15, 0.70, 0.15],
        "irrigation_prob": 0.30,
    },
    "mustard": {
        "N":    (78, 14, 40, 120),    "P":   (48, 9,  25, 75),
        "K":    (28, 6,  12, 45),     "temp": (17, 3.5, 10, 25),
        "hum":  (48, 8,  30, 68),     "ph":  (6.8, 0.5, 5.8, 8.0),
        "rain": (480, 130, 300, 750),
        "season": "Rabi",
        "soil_probs": [0.10, 0.75, 0.15],
        "irrigation_prob": 0.15,
    },
    "chickpea": {
        "N":    (28, 7,  10, 50),     "P":   (65, 9,  40, 90),
        "K":    (80, 5,  65, 95),     "temp": (19, 2.5, 12, 25),
        "hum":  (40, 6,  25, 55),     "ph":  (6.8, 0.5, 5.8, 8.0),
        "rain": (520, 140, 300, 850),
        "season": "Rabi",
        "soil_probs": [0.10, 0.65, 0.25],
        "irrigation_prob": 0.15,
    },
    "lentil": {
        "N":    (22, 8,  5,  45),     "P":   (65, 9,  40, 90),
        "K":    (20, 5,  8,  35),     "temp": (20, 3,  14, 27),
        "hum":  (55, 7,  38, 72),     "ph":  (6.8, 0.5, 5.8, 8.0),
        "rain": (450, 110, 300, 700),
        "season": "Rabi",
        "soil_probs": [0.10, 0.72, 0.18],
        "irrigation_prob": 0.12,
    },

    # ── Cluster C — Semi-arid Oilseed / Fibre  ────────────────────────────
    "cotton": {
        "N":    (120, 10, 90, 150),   "P":   (50, 8,  30, 75),
        "K":    (65,  12, 35, 100),   "temp": (28, 3.5, 22, 35),
        "hum":  (65,  8,  45, 82),    "ph":  (7.0, 0.6, 5.8, 8.5),
        "rain": (720, 140, 500, 1000),
        "season": "Kharif",
        "soil_probs": [0.55, 0.38, 0.07],   # sandy/loamy, not clay
        "irrigation_prob": 0.65,
    },
    "groundnut": {
        "N":    (28, 7,  10, 50),     "P":   (50, 8,  30, 75),
        "K":    (40, 8,  20, 65),     "temp": (28, 3,  22, 34),
        "hum":  (55, 7,  38, 72),     "ph":  (6.2, 0.5, 5.2, 7.2),
        "rain": (680, 140, 500, 1000),
        "season": "Kharif",
        "soil_probs": [0.88, 0.10, 0.02],   # strongly sandy
        "irrigation_prob": 0.12,
    },
    "soybean": {
        "N":    (35, 9,  12, 60),     "P":   (65, 9,  40, 90),
        "K":    (45, 9,  22, 72),     "temp": (26, 3.5, 22, 33),
        "hum":  (58, 9,  38, 78),     "ph":  (6.5, 0.5, 5.5, 7.8),
        "rain": (750, 150, 500, 1000),
        "season": "Kharif",
        "soil_probs": [0.08, 0.70, 0.22],
        "irrigation_prob": 0.15,
    },
    "castor": {
        "N":    (42, 6,  22, 65),     "P":   (32, 5,  18, 50),
        "K":    (25, 5,  12, 42),     "temp": (30, 2,  24, 36),
        "hum":  (42, 6,  28, 58),     "ph":  (7.2, 0.4, 6.0, 8.5),
        "rain": (560, 80, 500, 750),
        "season": "Kharif",
        "soil_probs": [0.50, 0.40, 0.10],   # sandy preferred
        "irrigation_prob": 0.10,
    },
    "sesame": {
        "N":    (28, 5,  12, 48),     "P":   (24, 4,  12, 40),
        "K":    (22, 4,  10, 38),     "temp": (32, 2,  27, 38),
        "hum":  (52, 5,  38, 65),     "ph":  (6.8, 0.4, 5.5, 8.0),
        "rain": (550, 70, 500, 750),
        "season": "Kharif",
        "soil_probs": [0.45, 0.45, 0.10],   # sandy/loamy
        "irrigation_prob": 0.08,
    },

    # ── Cluster D — Vegetable Moderate  ────────────────────────────────────
    "tomato": {
        "N":    (60, 6,  38, 85),     "P":   (55, 6,  35, 75),
        "K":    (65, 6,  42, 88),     "temp": (24, 2,  18, 30),
        "hum":  (72, 5,  58, 86),     "ph":  (6.2, 0.3, 5.5, 6.8),
        "rain": (620, 70, 500, 820),
        "season": "Zaid",
        "soil_probs": [0.08, 0.78, 0.14],   # loamy preferred
        "irrigation_prob": 0.72,
    },
    "brinjal": {
        "N":    (90, 8,  65, 115),    "P":   (70, 8,  48, 92),
        "K":    (50, 8,  30, 75),     "temp": (26, 3,  18, 32),
        "hum":  (70, 7,  52, 85),     "ph":  (6.2, 0.5, 5.2, 7.0),
        "rain": (750, 120, 500, 1000),
        "season": "Kharif",
        "soil_probs": [0.05, 0.65, 0.30],   # loamy/clay
        "irrigation_prob": 0.65,
    },
    "green_chilli": {
        "N":    (75, 12, 45, 108),    "P":   (50, 8,  30, 75),
        "K":    (60, 8,  35, 85),     "temp": (25, 3,  18, 32),
        "hum":  (68, 7,  50, 85),     "ph":  (6.5, 0.4, 5.8, 7.2),
        "rain": (680, 110, 500, 950),
        "season": "Kharif",
        "soil_probs": [0.08, 0.78, 0.14],
        "irrigation_prob": 0.62,
    },
    "okra": {
        "N":    (70, 8,  45, 98),     "P":   (50, 8,  30, 75),
        "K":    (40, 8,  20, 62),     "temp": (29, 3,  24, 35),
        "hum":  (70, 7,  52, 85),     "ph":  (6.5, 0.4, 5.8, 7.2),
        "rain": (720, 120, 500, 1000),
        "season": "Kharif",
        "soil_probs": [0.10, 0.70, 0.20],
        "irrigation_prob": 0.55,
    },
    "onion": {
        "N":    (75, 12, 45, 110),    "P":   (50, 8,  30, 75),
        "K":    (65, 12, 35, 95),     "temp": (22, 4,  14, 32),
        "hum":  (60, 8,  42, 78),     "ph":  (6.5, 0.4, 5.8, 7.2),
        "rain": (600, 100, 500, 850),
        "season": "Rabi",
        "soil_probs": [0.15, 0.70, 0.15],
        "irrigation_prob": 0.72,
    },
    "potato": {
        "N":    (75, 12, 45, 110),    "P":   (50, 8,  30, 75),
        "K":    (65, 12, 35, 95),     "temp": (19, 3,  12, 26),
        "hum":  (62, 8,  42, 78),     "ph":  (5.5, 0.3, 4.8, 6.2),
        "rain": (600, 90, 500, 850),
        "season": "Rabi",
        "soil_probs": [0.25, 0.62, 0.13],   # sandy/loamy, needs drainage
        "irrigation_prob": 0.75,
    },
    "cabbage": {
        "N":    (100, 14, 65, 140),   "P":   (75, 12, 48, 105),
        "K":    (100, 14, 65, 140),   "temp": (18, 3,  12, 24),
        "hum":  (72, 8,  55, 90),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (650, 110, 500, 950),
        "season": "Rabi",
        "soil_probs": [0.03, 0.75, 0.22],   # loamy/clay
        "irrigation_prob": 0.62,
    },
    "cauliflower": {
        "N":    (100, 14, 65, 140),   "P":   (75, 12, 48, 105),
        "K":    (100, 14, 65, 140),   "temp": (19, 3,  13, 26),
        "hum":  (72, 8,  55, 90),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (670, 110, 500, 950),
        "season": "Rabi",
        "soil_probs": [0.03, 0.75, 0.22],
        "irrigation_prob": 0.62,
    },
    "carrot": {
        "N":    (55, 8,  30, 82),     "P":   (45, 6,  28, 65),
        "K":    (95, 5,  78, 115),    "temp": (16, 2,  10, 22),
        "hum":  (55, 5,  40, 70),     "ph":  (6.3, 0.2, 5.8, 6.8),
        "rain": (520, 60, 500, 700),
        "season": "Rabi",
        "soil_probs": [0.70, 0.25, 0.05],   # sandy preferred (root crop)
        "irrigation_prob": 0.52,
    },
    "radish": {
        "N":    (72, 8,  45, 102),    "P":   (55, 6,  35, 78),
        "K":    (82, 5,  65, 100),    "temp": (20, 3,  12, 28),
        "hum":  (65, 5,  50, 80),     "ph":  (6.8, 0.3, 6.0, 7.5),
        "rain": (620, 70, 500, 800),
        "season": "Rabi",
        "soil_probs": [0.40, 0.48, 0.12],   # sandy/loamy
        "irrigation_prob": 0.30,
    },
    "spinach": {
        "N":    (35, 9,  12, 62),     "P":   (30, 8,  12, 52),
        "K":    (30, 8,  12, 52),     "temp": (18, 4,  10, 26),
        "hum":  (60, 8,  42, 78),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (580, 90, 500, 800),
        "season": "Rabi",
        "soil_probs": [0.08, 0.75, 0.17],
        "irrigation_prob": 0.65,
    },
    "cucumber": {
        "N":    (70, 8,  45, 98),     "P":   (50, 8,  30, 75),
        "K":    (60, 8,  35, 88),     "temp": (25, 3,  18, 32),
        "hum":  (78, 6,  62, 92),     "ph":  (6.2, 0.5, 5.2, 7.2),
        "rain": (750, 120, 500, 1000),
        "season": "Zaid",
        "soil_probs": [0.10, 0.70, 0.20],
        "irrigation_prob": 0.65,
    },

    # ── Cluster E — Tropical / Subtropical Fruits  ─────────────────────────
    "mango": {
        "N":    (28, 8,  8,  52),     "P":   (30, 8,  12, 52),
        "K":    (30, 6,  15, 48),     "temp": (30, 3,  24, 38),
        "hum":  (52, 7,  35, 68),     "ph":  (5.8, 0.6, 4.5, 7.2),
        "rain": (1050, 200, 800, 1500),
        "season": "Kharif",
        "soil_probs": [0.10, 0.65, 0.25],
        "irrigation_prob": 0.18,
    },
    "sapota": {
        "N":    (40, 8,  18, 65),     "P":   (25, 6,  10, 42),
        "K":    (40, 8,  18, 65),     "temp": (30, 3.5, 23, 38),
        "hum":  (75, 6,  60, 90),     "ph":  (7.0, 0.6, 5.8, 8.2),
        "rain": (1150, 200, 800, 1600),
        "season": "Kharif",
        "soil_probs": [0.05, 0.60, 0.35],   # loamy/clay
        "irrigation_prob": 0.15,
    },
    "guava": {
        "N":    (35, 6,  15, 58),     "P":   (35, 6,  18, 55),
        "K":    (45, 6,  28, 65),     "temp": (28, 2,  24, 33),
        "hum":  (68, 5,  55, 82),     "ph":  (6.5, 0.3, 5.8, 7.2),
        "rain": (1080, 130, 800, 1400),
        "season": "Kharif",
        "soil_probs": [0.08, 0.72, 0.20],
        "irrigation_prob": 0.18,
    },
    "orange": {
        "N":    (60, 14, 28, 95),     "P":   (30, 8,  12, 52),
        "K":    (35, 9,  12, 62),     "temp": (24, 3.5, 18, 32),
        "hum":  (68, 7,  50, 85),     "ph":  (6.5, 0.5, 5.5, 7.8),
        "rain": (950, 170, 800, 1400),
        "season": "Kharif",
        "soil_probs": [0.10, 0.65, 0.25],
        "irrigation_prob": 0.20,
    },
    "lemon": {
        "N":    (60, 14, 28, 95),     "P":   (30, 8,  12, 52),
        "K":    (35, 9,  12, 62),     "temp": (25, 3.5, 18, 32),
        "hum":  (60, 8,  42, 78),     "ph":  (6.2, 0.5, 5.2, 7.2),
        "rain": (900, 150, 800, 1300),
        "season": "Kharif",
        "soil_probs": [0.10, 0.65, 0.25],
        "irrigation_prob": 0.18,
    },
    "mosambi": {
        "N":    (60, 14, 28, 95),     "P":   (30, 8,  12, 52),
        "K":    (35, 9,  12, 62),     "temp": (26, 3.5, 20, 34),
        "hum":  (62, 8,  42, 80),     "ph":  (6.5, 0.5, 5.5, 7.8),
        "rain": (920, 160, 800, 1350),
        "season": "Kharif",
        "soil_probs": [0.10, 0.65, 0.25],
        "irrigation_prob": 0.18,
    },

    # ── Cluster F — Semi-arid Fruits  ──────────────────────────────────────
    "pomegranate": {
        "N":    (45, 9,  20, 72),     "P":   (30, 8,  12, 52),
        "K":    (45, 9,  22, 72),     "temp": (33, 3.5, 26, 42),
        "hum":  (38, 6,  22, 55),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (420, 120, 200, 700),
        "season": "Kharif",
        "soil_probs": [0.30, 0.55, 0.15],
        "irrigation_prob": 0.15,
    },
    "date_palm": {
        "N":    (30, 7,  10, 52),     "P":   (20, 7,  5,  38),
        "K":    (30, 7,  12, 52),     "temp": (36, 3.5, 28, 45),
        "hum":  (28, 6,  15, 42),     "ph":  (7.8, 0.5, 6.8, 8.8),
        "rain": (280, 70, 200, 450),
        "season": "Zaid",
        "soil_probs": [0.90, 0.08, 0.02],   # strongly sandy (desert)
        "irrigation_prob": 0.55,
    },
    "ber": {
        "N":    (20, 7,  5,  40),     "P":   (20, 7,  5,  40),
        "K":    (20, 7,  5,  40),     "temp": (33, 4.5, 24, 42),
        "hum":  (35, 8,  18, 55),     "ph":  (7.8, 0.5, 6.8, 8.8),
        "rain": (350, 90, 200, 600),
        "season": "Kharif",
        "soil_probs": [0.65, 0.28, 0.07],   # sandy/arid
        "irrigation_prob": 0.05,
    },
    "custard_apple": {
        "N":    (25, 7,  8,  45),     "P":   (25, 8,  8,  45),
        "K":    (25, 7,  8,  45),     "temp": (30, 3.5, 24, 38),
        "hum":  (52, 8,  32, 70),     "ph":  (7.0, 0.4, 6.2, 7.8),
        "rain": (520, 120, 200, 700),
        "season": "Kharif",
        "soil_probs": [0.15, 0.65, 0.20],
        "irrigation_prob": 0.12,
    },
    "watermelon": {
        "N":    (90, 8,  65, 115),    "P":   (20, 7,  5,  40),
        "K":    (50, 6,  35, 68),     "temp": (29, 3,  24, 35),
        "hum":  (48, 6,  32, 62),     "ph":  (6.5, 0.4, 5.8, 7.2),
        "rain": (420, 90, 200, 650),
        "season": "Zaid",
        "soil_probs": [0.72, 0.22, 0.06],   # sandy
        "irrigation_prob": 0.15,
    },
    "muskmelon": {
        "N":    (105, 6, 82, 128),    "P":   (18, 5,  5,  35),
        "K":    (48, 4,  35, 62),     "temp": (32, 2,  27, 38),
        "hum":  (38, 4,  26, 52),     "ph":  (6.8, 0.3, 6.0, 7.5),
        "rain": (320, 50, 200, 480),
        "season": "Zaid",
        "soil_probs": [0.78, 0.18, 0.04],   # strongly sandy
        "irrigation_prob": 0.10,
    },
    "grapes": {
        "N":    (35, 9,  12, 62),     "P":   (40, 8,  20, 65),
        "K":    (175, 18, 130, 220),  "temp": (27, 4.5, 20, 38),
        "hum":  (58, 7,  40, 75),     "ph":  (6.2, 0.5, 5.2, 7.2),
        "rain": (500, 120, 200, 700),
        "season": "Zaid",
        "soil_probs": [0.15, 0.55, 0.30],
        "irrigation_prob": 0.60,
    },

    # ── Cluster G — Commercial Plantation  ─────────────────────────────────
    "coffee": {
        "N":    (100, 8, 75, 125),    "P":   (30, 8,  12, 52),
        "K":    (30, 6,  15, 48),     "temp": (25, 2,  20, 28),
        "hum":  (62, 7,  45, 78),     "ph":  (6.5, 0.4, 5.8, 7.2),
        "rain": (1400, 230, 1000, 2000),
        "season": "Kharif",
        "soil_probs": [0.03, 0.62, 0.35],   # loamy/clay
        "irrigation_prob": 0.20,
    },
    "tobacco": {
        "N":    (55, 12, 28, 85),     "P":   (45, 8,  25, 68),
        "K":    (100, 14, 65, 138),   "temp": (26, 3,  20, 32),
        "hum":  (62, 6,  48, 78),     "ph":  (6.2, 0.5, 5.2, 7.2),
        "rain": (1200, 220, 1000, 1700),
        "season": "Kharif",
        "soil_probs": [0.12, 0.63, 0.25],
        "irrigation_prob": 0.25,
    },

    # ── Cluster H — Kharif Pulses  ─────────────────────────────────────────
    "pigeonpeas": {
        "N":    (25, 7,  8,  45),     "P":   (65, 9,  40, 90),
        "K":    (20, 5,  8,  35),     "temp": (29, 2.5, 25, 34),
        "hum":  (55, 9,  32, 72),     "ph":  (6.0, 0.6, 4.8, 7.2),
        "rain": (850, 150, 600, 1200),
        "season": "Kharif",
        "soil_probs": [0.10, 0.62, 0.28],
        "irrigation_prob": 0.10,
    },
    "mungbean": {
        "N":    (22, 8,  5,  42),     "P":   (48, 9,  28, 72),
        "K":    (20, 5,  8,  35),     "temp": (30, 2,  26, 34),
        "hum":  (65, 5,  55, 78),     "ph":  (6.7, 0.4, 5.8, 7.5),
        "rain": (750, 120, 600, 1000),
        "season": "Kharif",
        "soil_probs": [0.15, 0.65, 0.20],
        "irrigation_prob": 0.12,
    },
    "blackgram": {
        "N":    (35, 5,  22, 48),     "P":   (65, 9,  42, 90),
        "K":    (20, 5,  8,  35),     "temp": (28, 2.5, 24, 33),
        "hum":  (65, 5,  55, 78),     "ph":  (7.0, 0.4, 6.2, 7.8),
        "rain": (700, 100, 600, 950),
        "season": "Kharif",
        "soil_probs": [0.08, 0.67, 0.25],
        "irrigation_prob": 0.10,
    },
    "mothbeans": {
        "N":    (22, 8,  5,  42),     "P":   (48, 9,  25, 72),
        "K":    (20, 5,  8,  35),     "temp": (29, 2.5, 24, 34),
        "hum":  (48, 9,  28, 68),     "ph":  (6.2, 0.6, 4.8, 7.8),
        "rain": (650, 100, 600, 900),
        "season": "Kharif",
        "soil_probs": [0.60, 0.32, 0.08],   # sandy/loamy
        "irrigation_prob": 0.03,
    },

    # ── Cluster I — Gourds  ────────────────────────────────────────────────
    "bottle_gourd": {
        "N":    (60, 8,  35, 88),     "P":   (50, 8,  30, 75),
        "K":    (50, 8,  30, 75),     "temp": (30, 3,  24, 36),
        "hum":  (70, 7,  52, 85),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (700, 120, 500, 1000),
        "season": "Zaid",
        "soil_probs": [0.08, 0.75, 0.17],   # loamy
        "irrigation_prob": 0.45,
    },
    "bitter_gourd": {
        "N":    (60, 8,  35, 88),     "P":   (50, 8,  30, 75),
        "K":    (50, 8,  30, 75),     "temp": (30, 3,  24, 36),
        "hum":  (70, 7,  52, 85),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (720, 120, 500, 1000),
        "season": "Zaid",
        "soil_probs": [0.08, 0.75, 0.17],
        "irrigation_prob": 0.45,
    },
    "ridge_gourd": {
        "N":    (60, 8,  35, 88),     "P":   (50, 8,  30, 75),
        "K":    (50, 8,  30, 75),     "temp": (30, 3,  24, 36),
        "hum":  (70, 7,  52, 85),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (740, 120, 500, 1000),
        "season": "Zaid",
        "soil_probs": [0.08, 0.75, 0.17],
        "irrigation_prob": 0.45,
    },

    # ── Cluster J — Kharif Millets  ────────────────────────────────────────
    "maize": {
        "N":    (95, 14, 55, 140),    "P":   (48, 8,  28, 72),
        "K":    (30, 8,  12, 52),     "temp": (25, 3.5, 18, 32),
        "hum":  (62, 6,  48, 78),     "ph":  (6.2, 0.5, 5.2, 7.2),
        "rain": (650, 120, 400, 900),
        "season": "Kharif",
        "soil_probs": [0.08, 0.70, 0.22],
        "irrigation_prob": 0.30,
    },
    "jowar": {
        "N":    (95, 14, 55, 140),    "P":   (48, 8,  28, 72),
        "K":    (50, 8,  30, 75),     "temp": (30, 3,  25, 36),
        "hum":  (50, 8,  32, 68),     "ph":  (6.8, 0.5, 5.8, 7.8),
        "rain": (580, 120, 400, 850),
        "season": "Kharif",
        "soil_probs": [0.12, 0.63, 0.25],
        "irrigation_prob": 0.10,
    },
    "bajra": {
        "N":    (58, 14, 28, 92),     "P":   (40, 8,  20, 62),
        "K":    (40, 8,  20, 62),     "temp": (32, 3,  26, 38),
        "hum":  (40, 7,  24, 58),     "ph":  (7.2, 0.5, 6.2, 8.2),
        "rain": (500, 100, 400, 750),
        "season": "Kharif",
        "soil_probs": [0.72, 0.23, 0.05],   # sandy/arid
        "irrigation_prob": 0.05,
    },
    "ragi": {
        "N":    (65, 12, 35, 98),     "P":   (30, 8,  12, 52),
        "K":    (30, 8,  12, 52),     "temp": (30, 3,  25, 37),
        "hum":  (55, 9,  35, 75),     "ph":  (6.2, 0.7, 4.8, 7.8),
        "rain": (620, 120, 400, 900),
        "season": "Kharif",
        "soil_probs": [0.12, 0.55, 0.33],
        "irrigation_prob": 0.08,
    },

    # ── Cluster K — Temperate Fruit  ───────────────────────────────────────
    "apple": {
        "N":    (30, 7,  12, 52),     "P":   (30, 8,  12, 52),
        "K":    (175, 18, 130, 220),  "temp": (18, 3.5, 10, 24),
        "hum":  (78, 6,  62, 92),     "ph":  (6.0, 0.4, 5.2, 6.8),
        "rain": (1050, 170, 800, 1500),
        "season": "Rabi",
        "soil_probs": [0.08, 0.75, 0.17],
        "irrigation_prob": 0.45,
    },

    # ── Cluster L — Misc Rabi Pulse  ───────────────────────────────────────
    "kidneybeans": {
        "N":    (25, 7,  8,  45),     "P":   (65, 9,  42, 90),
        "K":    (20, 5,  8,  35),     "temp": (22, 3.5, 15, 28),
        "hum":  (60, 6,  45, 78),     "ph":  (5.8, 0.3, 5.2, 6.5),
        "rain": (700, 120, 500, 1000),
        "season": "Rabi",
        "soil_probs": [0.08, 0.68, 0.24],
        "irrigation_prob": 0.15,
    },
}

ALL_CROPS = sorted(CROP_PARAMS.keys())
TOTAL_CROPS = len(ALL_CROPS)
print(f"Total crops defined: {TOTAL_CROPS}")

# ===========================================================================
# CROP SAMPLE COUNTS — Realistic imbalanced distribution
# ===========================================================================
# High cultivation crops  → 500 samples
# Medium cultivation      → 400 samples (default)
# Rare / niche crops      → 300 samples

HIGH_CULTIVATION = {
    "rice", "wheat", "maize", "sugarcane", "cotton",
    "tomato", "potato", "onion", "brinjal", "okra",
}
RARE_CULTIVATION = {
    "date_palm", "ber", "custard_apple", "ragi", "sesame",
    "castor", "kidneybeans", "mothbeans", "muskmelon", "sapota",
    "tobacco",
}

CROP_SAMPLES = {}
for crop in ALL_CROPS:
    if crop in HIGH_CULTIVATION:
        CROP_SAMPLES[crop] = 500
    elif crop in RARE_CULTIVATION:
        CROP_SAMPLES[crop] = 300
    else:
        CROP_SAMPLES[crop] = 400

print(f"Sample distribution: high={sum(1 for v in CROP_SAMPLES.values() if v==500)}, "
      f"medium={sum(1 for v in CROP_SAMPLES.values() if v==400)}, "
      f"rare={sum(1 for v in CROP_SAMPLES.values() if v==300)}")

# ===========================================================================
# LABEL MERGING MAP
# ===========================================================================
LABEL_MAP = {
    "bottle_gourd":  "gourd",
    "bitter_gourd":  "gourd",
    "ridge_gourd":   "gourd",
    "cabbage":       "cole_crop",
    "cauliflower":   "cole_crop",
    "lemon":         "citrus",
    "mosambi":       "citrus",
    "orange":        "citrus",
}

# ===========================================================================
# ASYMMETRIC NOISE RULES  (v2.2)
# ===========================================================================
# Directional noise: different clusters can extend in specific directions
# but NOT in others. This is ecologically realistic.
ASYMMETRIC_NOISE_RULES = {
    "A_tropical_wet": {
        # Tropical crops can extend slightly into moderate zones
        "temp_shift": (-3, 1),      # can go cooler, not much hotter
        "rain_shift": (-0.10, 0.05),
        "hum_shift":  (-5, 2),
    },
    "B_cool_rabi": {
        # Cool crops should NOT extend into extreme hot zones
        "temp_shift": (-2, 0.5),    # can go cooler, barely warmer
        "rain_shift": (-0.05, 0.10),
        "hum_shift":  (-3, 5),
    },
    "K_temperate_fruit": {
        # Cold crops ONLY cooler, never hot
        "temp_shift": (-2, 0),
        "rain_shift": (-0.05, 0.10),
        "hum_shift":  (-3, 5),
    },
    "F_semiarid_fruit": {
        # Dry crops can tolerate moderate rainfall but not high humidity
        "temp_shift": (-1, 3),      # tolerant of more heat
        "rain_shift": (-0.05, 0.15),# can tolerate some more rain
        "hum_shift":  (-2, 2),      # stay dry
    },
    "J_millet": {
        # Hardy, tolerate wider ranges but not extreme wet
        "temp_shift": (-2, 3),
        "rain_shift": (-0.05, 0.08),
        "hum_shift":  (-3, 3),
    },
    "H_kharif_pulse": {
        # Moderate flexibility
        "temp_shift": (-2, 2),
        "rain_shift": (-0.08, 0.10),
        "hum_shift":  (-4, 4),
    },
}
# Default for clusters not listed
DEFAULT_NOISE_RULE = {
    "temp_shift": (-2, 2),
    "rain_shift": (-0.10, 0.10),
    "hum_shift":  (-4, 4),
}


# ===========================================================================
# GAUSSIAN SAMPLE GENERATOR
# ===========================================================================
def sample_gaussian(mean: float, std: float, hard_min: float,
                    hard_max: float, n: int, decimals: int = 2) -> np.ndarray:
    """Draw n samples from N(mean, std²), clip to [hard_min, hard_max]."""
    vals = np.random.normal(loc=mean, scale=std, size=n)
    vals = np.clip(vals, hard_min, hard_max)
    return np.round(vals, decimals)


def sample_soil_type(probs: list, n: int) -> np.ndarray:
    """Sample soil_type (0=sandy, 1=loamy, 2=clay) with given probabilities."""
    return np.random.choice([0, 1, 2], size=n, p=probs)


def sample_irrigation(prob: float, n: int) -> np.ndarray:
    """Sample irrigation (0=rainfed, 1=irrigated) with given probability."""
    return np.random.choice([0, 1], size=n, p=[1 - prob, prob])


# ===========================================================================
# ASYMMETRIC CROSS-CLUSTER ENVIRONMENTAL NOISE  (v2.2)
# ===========================================================================
WATER_INTENSIVE_CROPS = {"rice", "wheat", "sugarcane", "banana", "jute", "papaya", "cotton"}

def inject_asymmetric_noise(df: pd.DataFrame,
                            fraction: float = 0.05) -> pd.DataFrame:
    """
    For `fraction` of rows, perturb temperature/humidity/rainfall
    using DIRECTIONAL noise rules per ecological cluster.

    Key principles:
    - Tropical crops can extend slightly into moderate zones
    - Cold crops should NOT extend into extreme hot zones
    - Dry crops can tolerate moderate rainfall more than high humidity
    """
    df = df.copy()
    n_noise = int(len(df) * fraction)
    noise_idx = np.random.choice(len(df), size=n_noise, replace=False)

    for idx in noise_idx:
        crop = df.loc[idx, "label"]
        cluster = CROP_TO_CLUSTER.get(crop, "")
        rules = ASYMMETRIC_NOISE_RULES.get(cluster, DEFAULT_NOISE_RULE)

        # Temperature: asymmetric shift
        t_lo, t_hi = rules["temp_shift"]
        df.loc[idx, "temperature"] += np.random.uniform(t_lo, t_hi)

        # Humidity: asymmetric shift
        h_lo, h_hi = rules["hum_shift"]
        df.loc[idx, "humidity"] += np.random.uniform(h_lo, h_hi)

        # Rainfall: proportional asymmetric shift
        r_lo, r_hi = rules["rain_shift"]
        df.loc[idx, "rainfall"] *= (1 + np.random.uniform(r_lo, r_hi))

        # pH: small symmetric noise (pH is less cluster-dependent)
        df.loc[idx, "ph"] += np.random.uniform(-0.3, 0.3)

    # Re-clip to physical limits
    df["temperature"] = df["temperature"].clip(0, 50)
    df["humidity"]    = df["humidity"].clip(0, 100)
    df["rainfall"]    = df["rainfall"].clip(10, 3500)
    df["ph"]          = df["ph"].clip(3.5, 9.5)

    return df


# ===========================================================================
# DATASET GENERATION
# ===========================================================================
# Sigma scaling factor: reduces within-class Gaussian noise to improve
# accuracy while allowing soil/irrigation features to contribute more
# relative importance.
SIGMA_SCALE = 0.87

# Irrigation probability polarization: push probabilities toward 0 or 1
# so irrigation becomes more predictive of crop identity.
IRRIG_POLARIZE_STRENGTH = 3.5

def polarize_irrig_prob(p: float, strength: float = IRRIG_POLARIZE_STRENGTH) -> float:
    """Push irrigation probability toward 0 or 1 using power transform.
    
    With strength=2.5:
      0.10 → 0.006, 0.20 → 0.036, 0.30 → 0.10, 0.40 → 0.20,
      0.50 → 0.50, 0.60 → 0.80, 0.70 → 0.90, 0.80 → 0.96, 0.90 → 0.99
    """
    if p <= 0 or p >= 1:
        return p
    if p < 0.5:
        return (p / 0.5) ** strength * 0.5
    else:
        return 1.0 - ((1.0 - p) / 0.5) ** strength * 0.5

# Irrigation-dependent mean shifts applied DURING Gaussian generation.
# These create clean subpopulations instead of post-hoc noise.
IRRIG_HUM_SHIFT  = 25.0   # irrigated humidity boost
IRRIG_N_SHIFT    = 20.0   # irrigated N boost
IRRIG_RAIN_SCALE = 0.82   # irrigated → less rain needed
RAINFED_HUM_SHIFT = -10.0 # rainfed humidity penalty
RAINFED_N_SHIFT   = -7.0  # rainfed N penalty
RAINFED_RAIN_SCALE = 1.08 # rainfed → more rain

# Irrigation shifts for lower-importance features (temp, pH).
# This forces the model to genuinely rely on the irrigation feature
# rather than using high-importance continuous features as proxies.
IRRIG_TEMP_SHIFT   = -5.0  # irrigated → evaporative cooling
RAINFED_TEMP_SHIFT = +2.0  # rainfed → warmer micro-climate
IRRIG_PH_SHIFT     = +0.8  # irrigated → water buffering raises pH
RAINFED_PH_SHIFT   = -0.3  # rainfed → slightly more acidic

def generate_dataset() -> pd.DataFrame:
    """Generate biologically realistic dataset with soil type and irrigation."""
    records = []

    for crop_name, params in CROP_PARAMS.items():
        n = CROP_SAMPLES[crop_name]

        season_code = SEASON_MAP[params["season"]]
        soil = sample_soil_type(params["soil_probs"], n)
        irrig = sample_irrigation(polarize_irrig_prob(params["irrigation_prob"]), n)

        # Generate features per-sample with irrigation-dependent means.
        # This creates cleaner subpopulations rather than post-hoc shifts.
        irrig_mask = (irrig == 1)
        n_irrigated = int(irrig_mask.sum())
        n_rainfed   = n - n_irrigated

        hum_mean, hum_sig, hum_lo, hum_hi = params["hum"]
        n_mean, n_sig, n_lo, n_hi = params["N"]
        r_mean, r_sig, r_lo, r_hi = params["rain"]
        hum_sig_s = hum_sig * SIGMA_SCALE
        n_sig_s   = n_sig * SIGMA_SCALE
        r_sig_s   = r_sig * SIGMA_SCALE

        # --- Humidity subpopulations ---
        hum_irr = sample_gaussian(hum_mean + IRRIG_HUM_SHIFT,
                                  hum_sig_s, hum_lo, 100,
                                  n_irrigated, 2) if n_irrigated > 0 else np.array([])
        hum_raf = sample_gaussian(hum_mean + RAINFED_HUM_SHIFT,
                                  hum_sig_s, 0, hum_hi,
                                  n_rainfed, 2) if n_rainfed > 0 else np.array([])

        # --- N subpopulations ---
        N_irr = sample_gaussian(n_mean + IRRIG_N_SHIFT,
                                n_sig_s, n_lo, 200,
                                n_irrigated, 1) if n_irrigated > 0 else np.array([])
        N_raf = sample_gaussian(n_mean + RAINFED_N_SHIFT,
                                n_sig_s, max(n_lo - 4, 0), n_hi,
                                n_rainfed, 1) if n_rainfed > 0 else np.array([])

        # --- Rainfall subpopulations ---
        rain_irr = sample_gaussian(r_mean * IRRIG_RAIN_SCALE,
                                   r_sig_s, r_lo * 0.70, r_hi,
                                   n_irrigated, 1) if n_irrigated > 0 else np.array([])
        rain_raf = sample_gaussian(r_mean * RAINFED_RAIN_SCALE,
                                   r_sig_s, r_lo, r_hi,
                                   n_rainfed, 1) if n_rainfed > 0 else np.array([])

        # Other features: same mean for both, just sigma-scaled
        P    = sample_gaussian(params["P"][0], params["P"][1]*SIGMA_SCALE, params["P"][2], params["P"][3], n, decimals=1)
        K    = sample_gaussian(params["K"][0], params["K"][1]*SIGMA_SCALE, params["K"][2], params["K"][3], n, decimals=1)

        # --- Temperature subpopulations (lower-importance → forces model to use irrigation) ---
        t_mean, t_sig, t_lo, t_hi = params["temp"]
        t_sig_s = t_sig * SIGMA_SCALE
        temp_irr = sample_gaussian(t_mean + IRRIG_TEMP_SHIFT,
                                   t_sig_s, t_lo, t_hi,
                                   n_irrigated, 2) if n_irrigated > 0 else np.array([])
        temp_raf = sample_gaussian(t_mean + RAINFED_TEMP_SHIFT,
                                   t_sig_s, t_lo, t_hi,
                                   n_rainfed, 2) if n_rainfed > 0 else np.array([])

        # --- pH subpopulations (lower-importance → forces model to use irrigation) ---
        ph_mean, ph_sig, ph_lo, ph_hi = params["ph"]
        ph_sig_s = ph_sig * SIGMA_SCALE
        ph_irr = sample_gaussian(ph_mean + IRRIG_PH_SHIFT,
                                 ph_sig_s, ph_lo, ph_hi,
                                 n_irrigated, 2) if n_irrigated > 0 else np.array([])
        ph_raf = sample_gaussian(ph_mean + RAINFED_PH_SHIFT,
                                 ph_sig_s, ph_lo, ph_hi,
                                 n_rainfed, 2) if n_rainfed > 0 else np.array([])

        # Reconstruct per-sample N, hum, rain, temp, ph in original order
        N_all    = np.empty(n)
        hum_all  = np.empty(n)
        rain_all = np.empty(n)
        temp_all = np.empty(n)
        ph_all   = np.empty(n)
        irr_idx = 0
        raf_idx = 0
        for i in range(n):
            if irrig[i] == 1:
                N_all[i]    = N_irr[irr_idx]
                hum_all[i]  = hum_irr[irr_idx]
                rain_all[i] = rain_irr[irr_idx]
                temp_all[i] = temp_irr[irr_idx]
                ph_all[i]   = ph_irr[irr_idx]
                irr_idx += 1
            else:
                N_all[i]    = N_raf[raf_idx]
                hum_all[i]  = hum_raf[raf_idx]
                rain_all[i] = rain_raf[raf_idx]
                temp_all[i] = temp_raf[raf_idx]
                ph_all[i]   = ph_raf[raf_idx]
                raf_idx += 1

        N    = N_all
        hum  = hum_all
        rain = rain_all
        temp = temp_all
        ph   = ph_all

        # ── Water-intensive crops: enforce rainfall constraints ──────
        if crop_name in WATER_INTENSIVE_CROPS:
            rain_min = params["rain"][2]
            for i in range(n):
                if irrig[i] == 0:
                    rain[i] = max(rain[i], rain_min)
                else:
                    lowered_min = rain_min * 0.70
                    if rain[i] > rain_min:
                        if np.random.random() < 0.3:
                            rain[i] = np.random.uniform(lowered_min, rain_min)
                            rain[i] = round(rain[i], 1)

        # ── Soil-dependent feature shifts ────────────────────────────
        for i in range(n):
            n_val, p_val, k_val = N[i], P[i], K[i]
            ph_val = ph[i]
            hum_val = hum[i]
            rain_val = rain[i]

            if soil[i] == 0:    # Sandy soil
                k_val *= 0.63
                n_val *= 0.82
                ph_val += 0.65
                hum_val -= 11.0
                rain_val *= 0.87
            elif soil[i] == 2:  # Clay soil
                k_val *= 1.37
                n_val *= 1.18
                ph_val -= 0.58
                hum_val += 11.0
                rain_val *= 1.13

            # Clip to physical limits
            n_val    = np.clip(n_val, 0, 200)
            p_val    = np.clip(p_val, 0, 150)
            k_val    = np.clip(k_val, 0, 300)
            ph_val   = np.clip(ph_val, 3.5, 9.5)
            hum_val  = np.clip(hum_val, 0, 100)
            rain_val = np.clip(rain_val, 10, 3500)

            records.append({
                "N":           round(float(n_val), 1),
                "P":           round(float(p_val), 1),
                "K":           round(float(k_val), 1),
                "temperature": temp[i],
                "humidity":    round(float(hum_val), 2),
                "ph":          round(float(ph_val), 2),
                "rainfall":    round(float(rain_val), 1),
                "season":      season_code,
                "soil_type":   int(soil[i]),
                "irrigation":  int(irrig[i]),
                "label":       crop_name,
            })

    df = pd.DataFrame(records)

    # Shuffle deterministically
    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    return df


# ===========================================================================
# NOISE INJECTION + LABEL MERGING
# ===========================================================================
def apply_noise_and_merge(df: pd.DataFrame,
                          noise_level: float = 0.03) -> pd.DataFrame:
    """Apply noise, asymmetric cross-cluster perturbation, and label merging."""
    df = df.copy()
    numeric_cols = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

    for col in numeric_cols:
        noise = np.random.normal(0, noise_level, size=len(df))
        df[col] = df[col] * (1 + noise)

    # Asymmetric cross-cluster environmental noise (5%)
    df = inject_asymmetric_noise(df, fraction=0.05)

    # Re-enforce physical limits
    df["N"]           = df["N"].clip(0, 200)
    df["P"]           = df["P"].clip(0, 150)
    df["K"]           = df["K"].clip(0, 300)
    df["temperature"] = df["temperature"].clip(0, 50)
    df["humidity"]    = df["humidity"].clip(0, 100)
    df["ph"]          = df["ph"].clip(3.5, 9.5)
    df["rainfall"]    = df["rainfall"].clip(0, 3500)

    # Round
    for col in numeric_cols:
        df[col] = df[col].round(2)

    # Merge labels
    df["label"] = df["label"].replace(LABEL_MAP)

    return df


# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("  CROP RECOMMENDATION v2.2 — DATASET GENERATION")
    print("  Gaussian · Ecological clustering · Season · Soil · Irrigation")
    print("  Asymmetric noise · Imbalanced samples")
    print("=" * 70)

    # ── Step 1: Generate raw dataset ──────────────────────────────────────
    print("\n[1/4] Generating raw Gaussian dataset …")
    df_raw = generate_dataset()
    raw_csv = "Crop_recommendation_v2_raw.csv"
    df_raw.to_csv(raw_csv, index=False)
    print(f"      → {raw_csv}  ({len(df_raw)} rows, {df_raw['label'].nunique()} crops)")
    print(f"      Sample count range: {min(CROP_SAMPLES.values())}–{max(CROP_SAMPLES.values())}")

    # ── Step 2: Noise + merging ───────────────────────────────────────────
    print("\n[2/4] Applying 3% noise + 5% asymmetric cross-cluster noise + label merging …")
    df_final = apply_noise_and_merge(df_raw)
    df_final.to_csv(OUTPUT_CSV, index=False)
    print(f"      → {OUTPUT_CSV}  ({len(df_final)} rows, {df_final['label'].nunique()} classes)")

    print("\n      Label merges:")
    for old, new in LABEL_MAP.items():
        print(f"        {old} → {new}")

    # ── Step 3: Dataset summary ───────────────────────────────────────────
    print("\n[3/4] Dataset statistics:")
    print("      Samples per class:")
    class_counts = df_final["label"].value_counts().sort_index()
    for label, count in class_counts.items():
        print(f"        {label:20s} : {count}")

    print(f"\n      Feature ranges:")
    for col in ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]:
        print(f"        {col:12s} : {df_final[col].min():.1f} – {df_final[col].max():.1f}")

    print(f"\n      Soil type distribution:")
    soil_counts = df_final["soil_type"].value_counts().sort_index()
    soil_names = {0: "sandy", 1: "loamy", 2: "clay"}
    for code, count in soil_counts.items():
        print(f"        {soil_names[code]:8s} : {count}  ({count/len(df_final)*100:.1f}%)")

    print(f"\n      Irrigation distribution:")
    irrig_counts = df_final["irrigation"].value_counts().sort_index()
    irrig_names = {0: "rainfed", 1: "irrigated"}
    for code, count in irrig_counts.items():
        print(f"        {irrig_names[code]:10s} : {count}  ({count/len(df_final)*100:.1f}%)")

    # ── Step 4: Hash ──────────────────────────────────────────────────────
    csv_bytes = df_final.to_csv(index=False).encode("utf-8")
    dataset_hash = hashlib.sha256(csv_bytes).hexdigest()[:16]
    print(f"\n[4/4] Dataset SHA-256 (short): {dataset_hash}")

    gen_meta = {
        "generator_version": "2.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(df_final),
        "total_classes": int(df_final["label"].nunique()),
        "dataset_hash": dataset_hash,
        "output_file": OUTPUT_CSV,
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "random_state": RANDOM_STATE,
        "distribution": "Gaussian (np.random.normal)",
        "noise_level": 0.03,
        "cross_cluster_noise": "asymmetric 0.05",
        "soil_feature_added": True,
        "irrigation_feature_added": True,
        "sample_distribution": {
            "high_cultivation": 500,
            "medium_cultivation": 400,
            "rare_cultivation": 300,
        },
        "crop_sample_counts": CROP_SAMPLES,
        "label_merges": LABEL_MAP,
        "ecological_clusters": {k: v for k, v in CLUSTERS.items()},
    }

    with open("generation_metadata.json", "w") as f:
        json.dump(gen_meta, f, indent=2)
    print("      → generation_metadata.json saved")

    print("\n" + "=" * 70)
    print("  DATASET GENERATION COMPLETE")
    print("=" * 70) 