#!/usr/bin/env python3
"""
Test runner for RISC-V toolchain
Verifies all components work correctly
"""

import subprocess
import os
import sys
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def run_command(cmd, capture=True):
    """Run a shell command and return output"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=5)
            return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"


def test_program(name, expected_output):
    """Test a single program"""
    print(f"  Testing {Colors.BLUE}{name}{Colors.RESET}...", end=" ")
    
    # Run the program
    code, stdout, stderr = run_command(f"python3 vm.py build/{name}.bin")
    
    if code != 0:
        print(f"{Colors.RED}FAIL{Colors.RESET} (exit code {code})")
        if stderr:
            print(f"    Error: {stderr}")
        return False
    
    # Check output
    output = stdout.strip()
    if output == expected_output:
        print(f"{Colors.GREEN}PASS{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}FAIL{Colors.RESET}")
        print(f"    Expected: {expected_output}")
        print(f"    Got:      {output}")
        return False


def test_multifile(expected_output):
    """Test the multi-file linked program"""
    print(f"  Testing {Colors.BLUE}multifile{Colors.RESET}...", end=" ")
    
    code, stdout, stderr = run_command(f"python3 vm.py build/multifile")
    
    if code != 0:
        print(f"{Colors.RED}FAIL{Colors.RESET} (exit code {code})")
        if stderr:
            print(f"    Error: {stderr}")
        return False
    
    output = stdout.strip()
    if output == expected_output:
        print(f"{Colors.GREEN}PASS{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}FAIL{Colors.RESET}")
        print(f"    Expected: {expected_output}")
        print(f"    Got:      {output}")
        return False


def main():
    print(f"{Colors.BOLD}=== RISC-V Toolchain Test Suite ==={Colors.RESET}\n")
    
    # Check if build directory exists
    if not os.path.exists("build"):
        print(f"{Colors.YELLOW}Build directory not found. Running make...{Colors.RESET}\n")
        code, _, _ = run_command("make all > /dev/null 2>&1", capture=False)
        if code != 0:
            print(f"{Colors.RED}Build failed! Run 'make all' to see errors.{Colors.RESET}")
            sys.exit(1)
        print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test single-file programs
    print(f"{Colors.BOLD}Testing single-file programs:{Colors.RESET}")
    
    test_cases = [
        ("hello", "42\n"),
        ("factorial", "120\n"),
        ("fibonacci", "0 1 1 2 3 5 8 13 21 34 \n"),
        ("sum_array", "150\n"),
    ]
    
    for name, expected in test_cases:
        if test_program(name, expected):
            tests_passed += 1
        else:
            tests_failed += 1
    
    print()
    
    # Test multi-file program
    print(f"{Colors.BOLD}Testing multi-file linking:{Colors.RESET}")
    if test_multifile("12 24\n"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # Summary
    print(f"{Colors.BOLD}=== Test Summary ==={Colors.RESET}")
    total = tests_passed + tests_failed
    print(f"Passed: {Colors.GREEN}{tests_passed}{Colors.RESET}/{total}")
    if tests_failed > 0:
        print(f"Failed: {Colors.RED}{tests_failed}{Colors.RESET}/{total}")
    else:
        print(f"Failed: {tests_failed}/{total}")
    
    print()
    
    if tests_failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
