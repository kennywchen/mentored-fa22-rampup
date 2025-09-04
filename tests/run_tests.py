#!/usr/bin/env python3
"""
Test runner script for script.py
Provides different ways to run the test suite
"""

import sys
import os
import subprocess
import argparse

def run_unittest():
    """Run tests using unittest framework."""
    print("Running tests with unittest...")
    result = subprocess.run([sys.executable, "test_script.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode

def run_pytest():
    """Run tests using pytest framework."""
    print("Running tests with pytest...")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "test_script.py", "-v"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("pytest not found. Install with: pip install pytest")
        return 1

def run_coverage():
    """Run tests with coverage reporting."""
    print("Running tests with coverage...")
    try:
        # Run tests with coverage
        result = subprocess.run([
            sys.executable, "-m", "coverage", "run", "--source=script", "test_script.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Generate coverage report
            report_result = subprocess.run([
                sys.executable, "-m", "coverage", "report", "-m"
            ], capture_output=True, text=True)
            print(report_result.stdout)
            if report_result.stderr:
                print("STDERR:", report_result.stderr)
        
        return result.returncode
    except FileNotFoundError:
        print("coverage not found. Install with: pip install coverage")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Run tests for script.py")
    parser.add_argument("--framework", choices=["unittest", "pytest", "coverage"], 
                       default="unittest", help="Test framework to use")
    parser.add_argument("--install-deps", action="store_true", 
                       help="Install test dependencies")
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"])
        return 0
    
    # Check if test file exists
    if not os.path.exists("test_script.py"):
        print("Error: test_script.py not found")
        return 1
    
    # Check if script.py exists
    if not os.path.exists("script.py"):
        print("Error: script.py not found")
        return 1
    
    # Run tests based on framework choice
    if args.framework == "unittest":
        return run_unittest()
    elif args.framework == "pytest":
        return run_pytest()
    elif args.framework == "coverage":
        return run_coverage()

if __name__ == "__main__":
    sys.exit(main())
