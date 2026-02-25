#!/usr/bin/env python3
"""
Test runner script for CI/CD pipeline.
Runs tests without heavy ML training.
"""

import subprocess
import sys
import time
from pathlib import Path


def check_services_health():
    """Check if required services are running."""
    print("Checking service health...")
    
    services = [
        ("FastAPI ML Engine", "http://localhost:8000/health"),
        ("Django Gateway", "http://localhost:8001/api/health"),
    ]
    
    all_healthy = True
    
    for service_name, health_url in services:
        try:
            import requests
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"PASS {service_name} is healthy")
            else:
                print(f"FAIL {service_name} returned {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"FAIL {service_name} is not reachable: {e}")
            all_healthy = False
    
    return all_healthy


def run_unit_tests():
    """Run unit tests only."""
    print("Running unit tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "unit",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def run_contract_tests():
    """Run contract tests."""
    print("Running contract tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_contract.py",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def run_integration_tests():
    """Run integration tests."""
    print("Running integration tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_integration.py",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def run_phase6_validation():
    """Run Phase 6 validation."""
    print("Running Phase 6 validation...")
    
    cmd = [
        sys.executable, "validate_phase6.py"
    ]
    
    # Change to Aiml directory for validation
    import os
    current_dir = os.getcwd()
    os.chdir("Aiml")
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.chdir(current_dir)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def main():
    """Main test runner."""
    print("Starting CI test runner...")
    print()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)
    
    test_results = {}
    
    # Run Phase 6 validation (doesn't require services)
    test_results["phase6_validation"] = run_phase6_validation()
    print()
    
    # Check service health
    if not check_services_health():
        print("FAIL Services not healthy. Skipping integration and contract tests.")
        print()
        print("Test Results Summary:")
        for test_name, passed in test_results.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {test_name}: {status}")
        
        if all(test_results.values()):
            print("All available tests passed!")
            return 0
        else:
            print("Some tests failed!")
            return 1
    
    print()
    
    # Run contract tests
    test_results["contract_tests"] = run_contract_tests()
    print()
    
    # Run integration tests
    test_results["integration_tests"] = run_integration_tests()
    print()
    
    # Print summary
    print("Test Results Summary:")
    for test_name, passed in test_results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
    
    if all(test_results.values()):
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
