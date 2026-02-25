#!/usr/bin/env python3
"""
Extreme input validation to test model behavior and check for bias.
Tests desert, flood, and high nitrogen cases.
"""

import sys
import requests
import json
import time
from typing import List, Dict, Any

class ExtremeInputValidator:
    """Validator for extreme input cases."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    def test_desert_case(self) -> Dict[str, Any]:
        """Test desert conditions - low rainfall, high temperature."""
        print("Testing desert case...")
        
        desert_cases = [
            {
                "name": "Extreme Desert",
                "N": 20, "P": 15, "K": 10,
                "temperature": 45, "humidity": 15, "ph": 8.5, "rainfall": 10,
                "moisture": 5.0, "season": 0, "soil_type": 0, "irrigation": 0,
                "mode": "real", "top_n": 5
            },
            {
                "name": "Arid Desert",
                "N": 10, "P": 8, "K": 5,
                "temperature": 40, "humidity": 20, "ph": 8.0, "rainfall": 25,
                "moisture": 10.0, "season": 0, "soil_type": 0, "irrigation": 0,
                "mode": "synthetic", "top_n": 5
            },
            {
                "name": "Semi-Arid",
                "N": 30, "P": 25, "K": 20,
                "temperature": 35, "humidity": 30, "ph": 7.5, "rainfall": 50,
                "moisture": 20.0, "season": 0, "soil_type": 1, "irrigation": 1,
                "mode": "both", "top_n": 5
            }
        ]
        
        results = []
        for case in desert_cases:
            try:
                response = requests.post(f"{self.base_url}/predict", json=case, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    crops = [p["crop"] for p in data["predictions"]]
                    confidences = [p["confidence"] for p in data["predictions"]]
                    
                    results.append({
                        "case": case["name"],
                        "mode": case["mode"],
                        "crops": crops,
                        "confidences": confidences,
                        "top_crop": crops[0] if crops else None,
                        "top_confidence": confidences[0] if confidences else 0
                    })
                    
                    print(f"  {case['name']} ({case['mode']}): {crops[0]} ({confidences[0]:.1f}%)")
                else:
                    print(f"  {case['name']}: Failed with status {response.status_code}")
            except Exception as e:
                print(f"  {case['name']}: Error - {e}")
        
        self.results["desert"] = results
        return results
    
    def test_flood_case(self) -> Dict[str, Any]:
        """Test flood conditions - high rainfall, high humidity."""
        print("Testing flood case...")
        
        flood_cases = [
            {
                "name": "Extreme Flood",
                "N": 60, "P": 40, "K": 35,
                "temperature": 25, "humidity": 95, "ph": 5.5, "rainfall": 400,
                "moisture": 90.0, "season": 0, "soil_type": 2, "irrigation": 0,
                "mode": "real", "top_n": 5
            },
            {
                "name": "Heavy Rainfall",
                "N": 80, "P": 60, "K": 50,
                "temperature": 22, "humidity": 90, "ph": 6.0, "rainfall": 300,
                "moisture": 80.0, "season": 0, "soil_type": 2, "irrigation": 0,
                "mode": "synthetic", "top_n": 5
            },
            {
                "name": "Waterlogged",
                "N": 70, "P": 50, "K": 40,
                "temperature": 20, "humidity": 85, "ph": 5.8, "rainfall": 250,
                "moisture": 85.0, "season": 1, "soil_type": 2, "irrigation": 0,
                "mode": "both", "top_n": 5
            }
        ]
        
        results = []
        for case in flood_cases:
            try:
                response = requests.post(f"{self.base_url}/predict", json=case, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    crops = [p["crop"] for p in data["predictions"]]
                    confidences = [p["confidence"] for p in data["predictions"]]
                    
                    results.append({
                        "case": case["name"],
                        "mode": case["mode"],
                        "crops": crops,
                        "confidences": confidences,
                        "top_crop": crops[0] if crops else None,
                        "top_confidence": confidences[0] if confidences else 0
                    })
                    
                    print(f"  {case['name']} ({case['mode']}): {crops[0]} ({confidences[0]:.1f}%)")
                else:
                    print(f"  {case['name']}: Failed with status {response.status_code}")
            except Exception as e:
                print(f"  {case['name']}: Error - {e}")
        
        self.results["flood"] = results
        return results
    
    def test_high_nitrogen_case(self) -> Dict[str, Any]:
        """Test high nitrogen conditions."""
        print("Testing high nitrogen case...")
        
        high_n_cases = [
            {
                "name": "Very High N",
                "N": 180, "P": 60, "K": 80,
                "temperature": 28, "humidity": 70, "ph": 7.0, "rainfall": 120,
                "moisture": 60.0, "season": 0, "soil_type": 1, "irrigation": 1,
                "mode": "real", "top_n": 5
            },
            {
                "name": "Excessive N",
                "N": 200, "P": 80, "K": 100,
                "temperature": 30, "humidity": 65, "ph": 7.2, "rainfall": 100,
                "moisture": 55.0, "season": 0, "soil_type": 1, "irrigation": 1,
                "mode": "synthetic", "top_n": 5
            },
            {
                "name": "Balanced High N",
                "N": 150, "P": 90, "K": 120,
                "temperature": 26, "humidity": 68, "ph": 6.8, "rainfall": 110,
                "moisture": 58.0, "season": 2, "soil_type": 3, "irrigation": 1,
                "mode": "both", "top_n": 5
            }
        ]
        
        results = []
        for case in high_n_cases:
            try:
                response = requests.post(f"{self.base_url}/predict", json=case, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    crops = [p["crop"] for p in data["predictions"]]
                    confidences = [p["confidence"] for p in data["predictions"]]
                    
                    results.append({
                        "case": case["name"],
                        "mode": case["mode"],
                        "crops": crops,
                        "confidences": confidences,
                        "top_crop": crops[0] if crops else None,
                        "top_confidence": confidences[0] if confidences else 0
                    })
                    
                    print(f"  {case['name']} ({case['mode']}): {crops[0]} ({confidences[0]:.1f}%)")
                else:
                    print(f"  {case['name']}: Failed with status {response.status_code}")
            except Exception as e:
                print(f"  {case['name']}: Error - {e}")
        
        self.results["high_nitrogen"] = results
        return results
    
    def analyze_bias(self) -> Dict[str, Any]:
        """Analyze results for potential bias."""
        print("Analyzing for bias...")
        
        all_predictions = []
        for category, results in self.results.items():
            for result in results:
                all_predictions.extend(result["crops"])
        
        # Count crop frequencies
        crop_counts = {}
        for crop in all_predictions:
            crop_counts[crop] = crop_counts.get(crop, 0) + 1
        
        # Find dominant crops
        total_predictions = len(all_predictions)
        dominant_crops = sorted(crop_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Check if any crop dominates (>40% of predictions)
        bias_detected = False
        for crop, count in dominant_crops[:5]:
            percentage = (count / total_predictions) * 100
            if percentage > 40:
                bias_detected = True
                print(f"  ⚠️  BIAS DETECTED: {crop} appears in {percentage:.1f}% of predictions")
            else:
                print(f"  {crop}: {percentage:.1f}%")
        
        analysis = {
            "total_predictions": total_predictions,
            "unique_crops": len(crop_counts),
            "dominant_crops": dominant_crops[:10],
            "bias_detected": bias_detected,
            "top_crop_percentage": (dominant_crops[0][1] / total_predictions * 100) if dominant_crops else 0
        }
        
        if not bias_detected:
            print("  ✅ No significant bias detected")
        
        return analysis
    
    def test_confidence_distribution(self) -> Dict[str, Any]:
        """Test confidence distribution across predictions."""
        print("Analyzing confidence distribution...")
        
        all_confidences = []
        for category, results in self.results.items():
            if category in ["bias_analysis", "confidence_distribution"]:
                continue
            print(f"Processing category: {category}, type: {type(results)}")
            if isinstance(results, list):
                for result in results:
                    print(f"Result type: {type(result)}")
                    if isinstance(result, dict) and "confidences" in result:
                        if isinstance(result["confidences"], list):
                            all_confidences.extend(result["confidences"])
        
        if not all_confidences:
            return {"error": "No confidence data available"}
        
        # Calculate statistics
        avg_confidence = sum(all_confidences) / len(all_confidences)
        min_confidence = min(all_confidences)
        max_confidence = max(all_confidences)
        
        # Check distribution
        high_conf = sum(1 for c in all_confidences if c > 80)
        medium_conf = sum(1 for c in all_confidences if 50 <= c <= 80)
        low_conf = sum(1 for c in all_confidences if c < 50)
        
        distribution = {
            "total_predictions": len(all_confidences),
            "average_confidence": round(avg_confidence, 2),
            "min_confidence": round(min_confidence, 2),
            "max_confidence": round(max_confidence, 2),
            "high_confidence_count": high_conf,
            "medium_confidence_count": medium_conf,
            "low_confidence_count": low_conf,
            "high_confidence_percent": round((high_conf / len(all_confidences)) * 100, 1),
            "medium_confidence_percent": round((medium_conf / len(all_confidences)) * 100, 1),
            "low_confidence_percent": round((low_conf / len(all_confidences)) * 100, 1)
        }
        
        print(f"  Average confidence: {avg_confidence:.1f}%")
        print(f"  Range: {min_confidence:.1f}% - {max_confidence:.1f}%")
        print(f"  High confidence (>80%): {distribution['high_confidence_percent']:.1f}%")
        print(f"  Medium confidence (50-80%): {distribution['medium_confidence_percent']:.1f}%")
        print(f"  Low confidence (<50%): {distribution['low_confidence_percent']:.1f}%")
        
        return distribution
    
    def generate_report(self) -> str:
        """Generate validation report."""
        report = []
        report.append("# Extreme Input Validation Report\\n")
        
        # Bias analysis
        if "bias_analysis" in self.results:
            bias = self.results["bias_analysis"]
            report.append("## Bias Analysis")
            report.append(f"- Total predictions: {bias['total_predictions']}")
            report.append(f"- Unique crops: {bias['unique_crops']}")
            report.append(f"- Bias detected: {'Yes' if bias['bias_detected'] else 'No'}")
            report.append(f"- Top crop percentage: {bias['top_crop_percentage']:.1f}%")
            report.append("")
        
        # Confidence distribution
        if "confidence_distribution" in self.results:
            conf = self.results["confidence_distribution"]
            report.append("## Confidence Distribution")
            report.append(f"- Average confidence: {conf['average_confidence']}%")
            report.append(f"- High confidence: {conf['high_confidence_percent']}%")
            report.append(f"- Medium confidence: {conf['medium_confidence_percent']}%")
            report.append(f"- Low confidence: {conf['low_confidence_percent']}%")
            report.append("")
        
        # Detailed results
        for category, results in self.results.items():
            if category in ["bias_analysis", "confidence_distribution"]:
                continue
                
            report.append(f"## {category.title()} Results")
            for result in results:
                report.append(f"### {result['case']} ({result['mode']})")
                report.append(f"- Top crop: {result['top_crop']}")
                report.append(f"- Top confidence: {result['top_confidence']:.1f}%")
                report.append(f"- All crops: {', '.join(result['crops'])}")
                report.append("")
        
        return "\\n".join(report)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all extreme input tests."""
        print("=== STARTING EXTREME INPUT VALIDATION ===\\n")
        
        # Run test cases
        self.test_desert_case()
        print()
        
        self.test_flood_case()
        print()
        
        self.test_high_nitrogen_case()
        print()
        
        # Analyze results
        self.results["bias_analysis"] = self.analyze_bias()
        print()
        
        self.results["confidence_distribution"] = self.test_confidence_distribution()
        print()
        
        # Generate report
        report = self.generate_report()
        print(report)
        
        # Save report
        with open("extreme_input_validation_report.md", "w") as f:
            f.write(report)
        
        print("=== EXTREME INPUT VALIDATION COMPLETE ===")
        
        return self.results


def main():
    """Main validation function."""
    validator = ExtremeInputValidator()
    results = validator.run_all_tests()
    
    # Check for bias
    if results["bias_analysis"]["bias_detected"]:
        print("⚠️  WARNING: Model bias detected. Consider retraining with class balancing.")
        return 1
    else:
        print("✅ No significant bias detected.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
