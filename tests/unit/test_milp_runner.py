"""Verify actual model-build deadlines and recovery from limited child processes."""
import json
import importlib
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
milp_runner = importlib.import_module('milp_runner')
SMALL_DATA = importlib.import_module('paths').SMALL_DATA


class MilpRunnerTests(unittest.TestCase):
    def setUp(self):
        self.path = SMALL_DATA / 'sample.txt'

    def test_real_solve_emits_timings(self):
        result = milp_runner.run_milp(self.path, phase_limit=1, build_limit=5)
        self.assertEqual(result['status'], 'optimal')
        self.assertEqual((result['count'], result['makespan'], result['cost']), (5, 235, 145))
        self.assertGreater(result['build_seconds'], 0)
        self.assertGreater(result['solve_seconds'], 0)
        self.assertGreater(result['peak_rss_mb'], 0)

    def test_total_deadline_includes_child_startup(self):
        result = milp_runner.run_milp(self.path, total_limit=0.01)
        self.assertEqual(result['status'], 'wall_timeout')
        self.assertEqual(result['wall_limit_seconds'], 0.01)
        self.assertLess(result['seconds'], 0.5)

    def test_real_build_deadline(self):
        result = milp_runner.run_milp(self.path, build_limit=0.000001)
        self.assertEqual(result['status'], 'build_timeout')
        self.assertEqual(result['phase'], 'build')
        self.assertEqual(result['count'], '')

    @patch('milp_runner.subprocess.run')
    def test_wall_timeout_recovers_last_valid_schedule(self, run):
        schedule = [[1, 5, 25], [2, 2, 85], [3, 6, 90], [4, 3, 85], [5, 5, 210]]
        first = dict(details={'phase': 'count', 'status': 'feasible', 'count_optimal': True},
                     schedule=schedule)
        second = dict(details={'phase': 'makespan'}, schedule=None)
        stderr = '\n'.join('MILP_PROGRESS ' + json.dumps(event) for event in (first, second))
        run.side_effect = subprocess.TimeoutExpired('worker', 1, stderr=stderr.encode())
        result = milp_runner.run_milp(self.path, wall_limit=1)
        self.assertEqual(result['status'], 'wall_timeout')
        self.assertEqual(result['phase'], 'makespan')
        self.assertEqual((result['count'], result['makespan'], result['cost']), (5, 235, 145))

    @patch('milp_runner.subprocess.run')
    def test_native_allocation_failure_is_recorded(self, run):
        event = dict(details={'phase': 'build', 'status': 'no_solution'}, schedule=None)
        stderr = 'MILP_PROGRESS ' + json.dumps(event) + '\nstd::bad_alloc\n'
        run.return_value = subprocess.CompletedProcess('worker', -6, '', stderr)
        result = milp_runner.run_milp(self.path)
        self.assertEqual(result['status'], 'memory_limit')
        self.assertEqual(result['exit_code'], -6)
        self.assertEqual(result['count'], '')

    def test_incomplete_progress_does_not_erase_previous_snapshot(self):
        event = dict(details={'phase': 'count'}, schedule=[])
        stderr = 'MILP_PROGRESS ' + json.dumps(event) + '\nMILP_PROGRESS {"details":'
        details, schedule = milp_runner.parse_events(stderr)
        self.assertEqual(details['phase'], 'count')
        self.assertEqual(schedule, [])


if __name__ == '__main__':
    unittest.main()
