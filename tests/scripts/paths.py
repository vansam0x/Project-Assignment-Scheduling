"""Shared locations for test data, scripts and CSV results."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = PROJECT_ROOT / 'tests'
SMALL_DATA = TEST_ROOT / 'data/small'
STRESS_DATA = TEST_ROOT / 'data/stress'
RESULTS_DIR = TEST_ROOT / 'results'
