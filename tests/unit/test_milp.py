"""Check incumbent handling and lexicographic proof flags independently of timeouts."""
from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check import read_instance, validate
from paths import PROJECT_ROOT, SMALL_DATA

spec = importlib.util.spec_from_file_location('milp_solver', PROJECT_ROOT / 'solutions/milp/solve.py')
milp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(milp)


class MilpTests(unittest.TestCase):
    def setUp(self):
        self.instance = read_instance(SMALL_DATA / 'sample.txt')
        self.details = {}

    def solve_with_statuses(self, statuses):
        real = milp.pywraplp.Solver.CreateSolver('SCIP')
        pending = iter(statuses)

        class ControlledSolver:
            def __getattr__(self, name):
                return getattr(real, name)

            def Solve(self):
                status = next(pending)
                if status in (milp.pywraplp.Solver.OPTIMAL, milp.pywraplp.Solver.FEASIBLE):
                    self_test.assertEqual(real.Solve(), milp.pywraplp.Solver.OPTIMAL)
                return status

        self_test = self
        with patch.object(milp.pywraplp.Solver, 'CreateSolver', return_value=ControlledSolver()):
            with redirect_stderr(io.StringIO()):
                return milp.solve(self.instance, details=self.details)

    def check_schedule(self, schedule):
        text = str(len(schedule)) + '\n' + '\n'.join(' '.join(map(str, row)) for row in schedule)
        return validate(self.instance, text, require_maximum=False)

    def test_proven_optimum(self):
        schedule = self.solve_with_statuses([0, 0, 0])
        self.assertEqual(self.check_schedule(schedule), (5, 235, 145))
        self.assertEqual(self.details['status'], 'optimal')
        self.assertTrue(self.details['cost_optimal'])
        self.assertEqual(self.details['relative_gap'], 0)

    def test_makespan_incumbent_stops_before_cost(self):
        schedule = self.solve_with_statuses([0, 1])
        self.check_schedule(schedule)
        self.assertEqual(self.details['status'], 'feasible')
        self.assertEqual(self.details['phase'], 'makespan')
        self.assertTrue(self.details['count_optimal'])
        self.assertFalse(self.details['makespan_optimal'])
        self.assertFalse(self.details['cost_optimal'])
        self.assertLessEqual(self.details['best_bound'], self.details['objective_value'])

    def test_no_new_incumbent_preserves_previous_phase(self):
        schedule = self.solve_with_statuses([0, 0, milp.pywraplp.Solver.NOT_SOLVED])
        self.check_schedule(schedule)
        self.assertEqual(self.details['status'], 'feasible')
        self.assertEqual(self.details['phase'], 'cost')
        self.assertTrue(self.details['makespan_optimal'])
        self.assertFalse(self.details['cost_optimal'])
        self.assertIsNone(self.details['relative_gap'])

    def test_no_initial_incumbent_is_not_an_empty_optimum(self):
        with self.assertRaisesRegex(RuntimeError, 'no usable incumbent'):
            self.solve_with_statuses([milp.pywraplp.Solver.NOT_SOLVED])
        self.assertEqual(self.details['status'], 'no_solution')

    def test_partial_schedule_validation_is_optional(self):
        self.assertEqual(validate(self.instance, '0\n', require_maximum=False), (0, 0, 0))
        with self.assertRaisesRegex(ValueError, 'Not maximum'):
            validate(self.instance, '0\n')

    def test_abnormal_solver_exit_is_not_a_timeout(self):
        with self.assertRaisesRegex(RuntimeError, 'no usable incumbent'):
            self.solve_with_statuses([milp.pywraplp.Solver.ABNORMAL])
        self.assertEqual(self.details['status'], 'solver_error')
        self.assertEqual(self.details['solver_status'], milp.pywraplp.Solver.ABNORMAL)


if __name__ == '__main__':
    unittest.main()
