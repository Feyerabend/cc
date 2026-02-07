#!/usr/bin/env python3
"""
Comprehensive Test Runner for SVG Renderer
Runs all test suites with coverage reporting and detailed output
"""

import sys
import os
import unittest
import argparse
from pathlib import Path


def run_tests(test_suite=None, verbosity=2, failfast=False, coverage=True):
    """
    Run test suite with optional coverage
    
    Args:
        test_suite: Specific test suite to run (or None for all)
        verbosity: Test output verbosity level
        failfast: Stop on first failure
        coverage: Enable coverage reporting
    """
    
    if coverage:
        try:
            import coverage as cov
            # Start coverage
            cov_instance = cov.Coverage(source=['svg_renderer'])
            cov_instance.start()
            print("✓ Coverage tracking enabled")
        except ImportError:
            print("! Coverage module not found. Install with: pip install coverage")
            coverage = False
    
    # Discover and run tests
    loader = unittest.TestLoader()
    
    if test_suite:
        # Run specific test suite
        suite = loader.loadTestsFromName(test_suite)
    else:
        # Discover all tests
        suite = loader.discover('.', pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=failfast
    )
    
    print("\n" + "="*70)
    print("RUNNING SVG RENDERER TEST SUITE")
    print("="*70 + "\n")
    
    result = runner.run(suite)
    
    # Stop coverage and report
    if coverage:
        cov_instance.stop()
        cov_instance.save()
        
        print("\n" + "="*70)
        print("COVERAGE REPORT")
        print("="*70)
        cov_instance.report()
        
        # Generate HTML report
        print("\nGenerating HTML coverage report...")
        cov_instance.html_report(directory='htmlcov')
        print("✓ HTML report generated in 'htmlcov/' directory")
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print(f"Skipped:       {len(result.skipped)}")
    
    if result.testsRun > 0:
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        print(f"Success rate:  {success_rate:.2f}%")
    
    print("="*70)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run SVG Renderer test suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with coverage
  python run_tests.py
  
  # Run specific test file
  python run_tests.py -s test_svg_renderer
  
  # Run with minimal output
  python run_tests.py -v 1
  
  # Run without coverage
  python run_tests.py --no-coverage
  
  # Run unit tests only
  python run_tests.py -s test_svg_renderer.TestColor
  
  # Run property tests
  python run_tests.py -s test_properties
  
  # Run integration tests
  python run_tests.py -s test_integration
  
  # Stop on first failure
  python run_tests.py -f
        """
    )
    
    parser.add_argument(
        '-s', '--suite',
        help='Specific test suite to run (e.g., test_svg_renderer, test_properties)',
        default=None
    )
    
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='Test output verbosity (0=quiet, 1=normal, 2=verbose)'
    )
    
    parser.add_argument(
        '-f', '--failfast',
        action='store_true',
        help='Stop on first test failure'
    )
    
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable coverage reporting'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick unit tests only (skip integration and property tests)'
    )
    
    args = parser.parse_args()
    
    # Determine test suite
    test_suite = args.suite
    if args.quick:
        test_suite = 'test_svg_renderer'
        print("Quick mode: Running unit tests only\n")
    
    # Run tests
    exit_code = run_tests(
        test_suite=test_suite,
        verbosity=args.verbosity,
        failfast=args.failfast,
        coverage=not args.no_coverage
    )
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
