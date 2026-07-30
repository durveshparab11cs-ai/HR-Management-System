#!/usr/bin/env python3
"""
Check code coverage against threshold.
Usage: python check_coverage.py --threshold 75
"""

import argparse
import re
import sys
from pathlib import Path

def parse_lcov_file(lcov_file):
    """Parse LCOV coverage file and extract coverage percentage."""
    if not Path(lcov_file).exists():
        print(f"❌ Coverage file not found: {lcov_file}")
        return None
    
    with open(lcov_file, 'r') as f:
        content = f.read()
    
    # Extract coverage statistics
    lines_valid = re.search(r'LF:(\d+)', content)
    lines_hit = re.search(r'LH:(\d+)', content)
    
    if not lines_valid or not lines_hit:
        print("❌ Could not parse coverage data")
        return None
    
    valid = int(lines_valid.group(1))
    hit = int(lines_hit.group(1))
    
    if valid == 0:
        return 0
    
    coverage = (hit / valid) * 100
    return coverage

def check_file_coverage(coverage_dir='coverage'):
    """Check coverage for all files in directory."""
    coverage_file = Path(coverage_dir) / 'lcov.info'
    
    coverage = parse_lcov_file(str(coverage_file))
    
    if coverage is None:
        print("❌ Failed to calculate coverage")
        return False
    
    return coverage

def main():
    parser = argparse.ArgumentParser(
        description='Check code coverage against threshold'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=75,
        help='Coverage threshold percentage (default: 75)'
    )
    parser.add_argument(
        '--coverage-dir',
        default='coverage',
        help='Coverage file directory (default: coverage)'
    )
    
    args = parser.parse_args()
    
    coverage = check_file_coverage(args.coverage_dir)
    
    if coverage is None:
        sys.exit(1)
    
    print(f"\n📊 Code Coverage Report")
    print(f"{'=' * 50}")
    print(f"Coverage: {coverage:.2f}%")
    print(f"Threshold: {args.threshold}%")
    print(f"{'=' * 50}\n")
    
    if coverage >= args.threshold:
        print(f"✅ Coverage meets threshold ({coverage:.2f}% >= {args.threshold}%)")
        return 0
    else:
        shortfall = args.threshold - coverage
        print(f"❌ Coverage below threshold ({coverage:.2f}% < {args.threshold}%)")
        print(f"   Need {shortfall:.2f}% more coverage")
        return 1

if __name__ == '__main__':
    sys.exit(main())
