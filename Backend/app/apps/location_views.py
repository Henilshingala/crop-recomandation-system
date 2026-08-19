"""
Location API views — serve india.json data lazily.
The full india.json (~17 MB) is loaded once into memory at module level.
Frontend fetches only the slice it needs via cascading dropdowns.
"""

import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# ── Load data once ──────────────────────────────────────────────
_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "india.json")

_INDIA_DATA: list[dict] | None = None


def _get_data() -> list[dict]:
    """Lazy-load india.json on first request (not at import time)."""
    global _INDIA_DATA
    if _INDIA_DATA is None:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            _INDIA_DATA = json.load(f)
    return _INDIA_DATA


def _find_state(state_name: str) -> dict | None:
    """Find a state entry by name (case-insensitive)."""
    for s in _get_data():
        if s["state"].lower() == state_name.lower():
            return s
    return None


# ── API Views ───────────────────────────────────────────────────

@require_GET
def location_states(request):
    """Return all states with their codes."""
    data = _get_data()
    states = [{"state": s["state"], "stateCode": s["stateCode"]} for s in data]
    return JsonResponse({"states": states})


@require_GET
def location_districts(request):
    """Return districts and cities for a given state."""
    state_name = request.GET.get("state", "").strip()
    if not state_name:
        return JsonResponse({"error": "state parameter required"}, status=400)

    state = _find_state(state_name)
    if not state:
        return JsonResponse({"error": f"State '{state_name}' not found"}, status=404)

    districts = [d["district"] for d in state.get("districts", [])]
    cities = state.get("cities", [])
    return JsonResponse({"districts": sorted(districts), "cities": sorted(cities)})


@require_GET
def location_subdistricts(request):
    """Return sub-districts for a given state + district."""
    state_name = request.GET.get("state", "").strip()
    district_name = request.GET.get("district", "").strip()

    if not state_name or not district_name:
        return JsonResponse(
            {"error": "state and district parameters required"}, status=400
        )

    state = _find_state(state_name)
    if not state:
        return JsonResponse({"error": f"State '{state_name}' not found"}, status=404)

    for d in state.get("districts", []):
        if d["district"].lower() == district_name.lower():
            sub_districts = [sd["subDistrict"] for sd in d.get("subDistricts", [])]
            return JsonResponse({"subDistricts": sorted(sub_districts)})

    return JsonResponse(
        {"error": f"District '{district_name}' not found in {state_name}"}, status=404
    )


@require_GET
def location_villages(request):
    """Return villages for a given state + district + sub-district."""
    state_name = request.GET.get("state", "").strip()
    district_name = request.GET.get("district", "").strip()
    sub_district_name = request.GET.get("subdistrict", "").strip()

    if not state_name or not district_name or not sub_district_name:
        return JsonResponse(
            {"error": "state, district, and subdistrict parameters required"},
            status=400,
        )

    state = _find_state(state_name)
    if not state:
        return JsonResponse({"error": f"State '{state_name}' not found"}, status=404)

    for d in state.get("districts", []):
        if d["district"].lower() == district_name.lower():
            for sd in d.get("subDistricts", []):
                if sd["subDistrict"].lower() == sub_district_name.lower():
                    villages = sorted(sd.get("villages", []))
                    return JsonResponse({"villages": villages})
            return JsonResponse(
                {"error": f"Sub-district '{sub_district_name}' not found"},
                status=404,
            )

    return JsonResponse(
        {"error": f"District '{district_name}' not found"}, status=404
    )
