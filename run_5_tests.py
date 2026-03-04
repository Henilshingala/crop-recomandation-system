"""
Run 5 validation test cases against the CRS API and produce a report.
"""
import requests, json, time, sys
from datetime import datetime

API = "https://shingala-crs.hf.space/recommend"

TESTS = [
    {
        "id": 1,
        "name": "Strong Rice Signal (Monsoon Dominant)",
        "input": {"N": 110, "P": 50, "K": 50, "temperature": 28, "humidity": 92, "ph": 6.3, "rainfall": 450},
        "expected_top3": ["rice", "jute", "coconut"],
        "must_dominate": "rice",
        "fail_if": "If vegetables win here → rainfall weighting is weak.",
    },
    {
        "id": 2,
        "name": "Wheat / Rabi Cold Crop",
        "input": {"N": 100, "P": 50, "K": 50, "temperature": 18, "humidity": 60, "ph": 6.8, "rainfall": 120},
        "expected_top3": ["wheat", "barley", "mustard"],
        "must_dominate": "wheat",
        "fail_if": "If tropical crop appears → temperature constraint is broken.",
    },
    {
        "id": 3,
        "name": "Banana Tropical High Water",
        "input": {"N": 180, "P": 100, "K": 250, "temperature": 30, "humidity": 90, "ph": 6.5, "rainfall": 2500},
        "expected_top3": ["banana", "sugarcane", "coconut"],
        "must_dominate": "banana",
        "fail_if": "If rice wins → rainfall logic too generic.",
    },
    {
        "id": 4,
        "name": "Arid / Bajra Zone",
        "input": {"N": 40, "P": 30, "K": 30, "temperature": 35, "humidity": 30, "ph": 7.5, "rainfall": 80},
        "expected_top3": ["bajra", "jowar", "ber"],
        "must_dominate": "bajra",
        "fail_if": "If vegetable appears → humidity constraint weak.",
    },
    {
        "id": 5,
        "name": "Cotton Semi-Arid Warm",
        "input": {"N": 120, "P": 60, "K": 60, "temperature": 32, "humidity": 55, "ph": 7.0, "rainfall": 150},
        "expected_top3": ["cotton", "jowar", "green_chilli"],
        "must_dominate": "cotton",
        "fail_if": "If banana appears → rainfall over-weighted.",
    },
]

# Aliases for flexible matching
ALIASES = {
    "pearl_millet": "bajra", "bajra": "bajra",
    "finger_millet": "ragi", "ragi": "ragi",
    "sorghum": "jowar", "jowar": "jowar",
    "pigeonpea": "pigeonpea", "pigeonpeas": "pigeonpea",
    "sesamum": "sesame", "sesame": "sesame",
}

TROPICAL = {"rice", "banana", "coconut", "sugarcane", "jute", "papaya", "mango"}
VEGETABLES = {"tomato", "potato", "onion", "brinjal", "okra", "spinach", "carrot", "radish", "cucumber"}

def norm(name):
    n = name.lower().strip().replace(" ", "_")
    return ALIASES.get(n, n)

def run_test(tc):
    start = time.time()
    try:
        r = requests.post(API, json=tc["input"], timeout=120)
        latency = round((time.time() - start) * 1000)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"error": str(e), "latency_ms": round((time.time() - start) * 1000)}

    recs = data.get("top_recommendations", data.get("top_3", []))
    top3 = []
    for c in recs[:3]:
        crop = c.get("crop", "?")
        conf = c.get("confidence", 0)
        tier = c.get("advisory_tier", "?")
        consensus = c.get("model_consensus", "?")
        top3.append({"crop": crop, "confidence": conf, "tier": tier, "consensus": consensus})

    actual_names = [norm(c["crop"]) for c in top3]
    expected_names = [norm(e) for e in tc["expected_top3"]]

    # Scoring
    dominator = norm(tc["must_dominate"])
    dominator_rank = None
    for i, a in enumerate(actual_names):
        if a == dominator:
            dominator_rank = i + 1
            break

    overlap = len(set(actual_names) & set(expected_names))

    # Check fail conditions
    warnings = []
    if tc["id"] == 1 and set(actual_names) & VEGETABLES:
        warnings.append(tc["fail_if"])
    if tc["id"] == 2 and set(actual_names) & TROPICAL:
        warnings.append(tc["fail_if"])
    if tc["id"] == 3 and actual_names[0] == "rice":
        warnings.append(tc["fail_if"])
    if tc["id"] == 4 and set(actual_names) & VEGETABLES:
        warnings.append(tc["fail_if"])
    if tc["id"] == 5 and "banana" in actual_names:
        warnings.append(tc["fail_if"])

    # Pass criteria: must_dominate in top 1 = PASS, in top 3 = PARTIAL, else FAIL
    if dominator_rank == 1:
        verdict = "PASS"
    elif dominator_rank and dominator_rank <= 3:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return {
        "top3": top3,
        "actual_names": actual_names,
        "expected_names": expected_names,
        "dominator": dominator,
        "dominator_rank": dominator_rank,
        "overlap": overlap,
        "verdict": verdict,
        "warnings": warnings,
        "latency_ms": latency,
        "fallback_mode": data.get("fallback_mode", False),
        "all_not_recommended": data.get("all_not_recommended", False),
        "stress_index": data.get("stress_index"),
        "warning_text": data.get("warning"),
    }


def main():
    print(f"Running 5 test cases against {API}...")
    results = []
    for tc in TESTS:
        print(f"  TC{tc['id']}: {tc['name']}...", end=" ", flush=True)
        res = run_test(tc)
        res["tc"] = tc
        results.append(res)
        if "error" in res:
            print(f"ERROR ({res['latency_ms']}ms)")
        else:
            print(f"{res['verdict']} ({res['latency_ms']}ms)")

    # Build report
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("=" * 80)
    lines.append("  CROP RECOMMENDATION SYSTEM — 5-SCENARIO VALIDATION REPORT")
    lines.append(f"  Generated: {now}")
    lines.append(f"  API: {API}")
    lines.append("=" * 80)
    lines.append("")

    pass_count = sum(1 for r in results if r.get("verdict") == "PASS")
    partial_count = sum(1 for r in results if r.get("verdict") == "PARTIAL")
    fail_count = sum(1 for r in results if r.get("verdict") == "FAIL")
    error_count = sum(1 for r in results if "error" in r)

    lines.append(f"  SUMMARY: {pass_count} PASS | {partial_count} PARTIAL | {fail_count} FAIL | {error_count} ERROR")
    lines.append("")

    for res in results:
        tc = res["tc"]
        lines.append("-" * 80)
        lines.append(f"  TEST CASE {tc['id']} — {tc['name']}")
        lines.append("-" * 80)
        inp = tc["input"]
        lines.append(f"  Input: N={inp['N']} P={inp['P']} K={inp['K']} Temp={inp['temperature']}°C "
                      f"Humidity={inp['humidity']}% pH={inp['ph']} Rainfall={inp['rainfall']}mm")
        lines.append("")

        if "error" in res:
            lines.append(f"  ❌ ERROR: {res['error']}")
            lines.append(f"  Latency: {res['latency_ms']}ms")
            lines.append("")
            continue

        # Expected vs Actual table
        lines.append(f"  {'EXPECTED':30s} | {'ACTUAL (System Result)':50s}")
        lines.append(f"  {'-'*30} | {'-'*50}")
        for i in range(3):
            exp = tc["expected_top3"][i] if i < len(tc["expected_top3"]) else "—"
            if i < len(res["top3"]):
                a = res["top3"][i]
                act = f"{a['crop']} ({a['confidence']:.1f}% | {a['tier']} | {a['consensus']})"
            else:
                act = "—"
            match = "✅" if i < len(res["actual_names"]) and i < len(res["expected_names"]) and norm(exp) == res["actual_names"][i] else "  "
            lines.append(f"  {match} #{i+1} {exp:25s} | {act}")

        lines.append("")
        lines.append(f"  Must Dominate: {tc['must_dominate']}")
        lines.append(f"  Actual Rank of '{tc['must_dominate']}': {'#' + str(res['dominator_rank']) if res['dominator_rank'] else 'NOT IN TOP 3'}")
        lines.append(f"  Top-3 Overlap with Expected: {res['overlap']}/3")
        lines.append(f"  Fallback Mode: {res['fallback_mode']}  |  All Not Recommended: {res['all_not_recommended']}")
        if res["stress_index"] is not None:
            lines.append(f"  Stress Index: {res['stress_index']:.4f}")
        if res["warning_text"]:
            lines.append(f"  API Warning: {res['warning_text']}")
        lines.append(f"  Latency: {res['latency_ms']}ms")
        lines.append("")

        # Verdict
        v = res["verdict"]
        icon = "✅" if v == "PASS" else ("⚠️" if v == "PARTIAL" else "❌")
        lines.append(f"  VERDICT: {icon} {v}")

        if res["warnings"]:
            for w in res["warnings"]:
                lines.append(f"  ⚠ ISSUE: {w}")

        lines.append("")

    # Final summary table
    lines.append("=" * 80)
    lines.append("  FINAL SCORECARD")
    lines.append("=" * 80)
    lines.append(f"  {'TC':4s} {'Name':40s} {'Verdict':10s} {'Dominator Rank':16s} {'Overlap':8s} {'Latency':10s}")
    lines.append(f"  {'—'*4} {'—'*40} {'—'*10} {'—'*16} {'—'*8} {'—'*10}")
    for res in results:
        tc = res["tc"]
        if "error" in res:
            lines.append(f"  {tc['id']:<4d} {tc['name']:40s} {'ERROR':10s} {'—':16s} {'—':8s} {res['latency_ms']}ms")
        else:
            rank_str = f"#{res['dominator_rank']}" if res['dominator_rank'] else "MISSING"
            lines.append(f"  {tc['id']:<4d} {tc['name']:40s} {res['verdict']:10s} {rank_str:16s} {res['overlap']}/3{'':<4s} {res['latency_ms']}ms")

    lines.append("")
    score_pct = round((pass_count * 100 + partial_count * 50) / max(len(results), 1))
    lines.append(f"  Overall Score: {score_pct}% ({pass_count} full pass + {partial_count} partial out of {len(results)} tests)")
    lines.append("=" * 80)
    lines.append("")

    report = "\n".join(lines)
    print(report)

    with open("test_5_scenarios_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to test_5_scenarios_report.txt")


if __name__ == "__main__":
    main()
