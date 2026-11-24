"""Check lexicographic aggregation and missing-solution reporting."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reports import save_reports


class ReportTests(unittest.TestCase):
    def test_best_is_an_actual_run_and_zero_is_a_solution(self):
        base = dict(suite='small', instance='example', n=5, q=2, m=2, k=6,
                    seconds=1, status='validated')
        rows = [dict(base, algorithm='sa', seed=seed, count=r, makespan=t, cost=c)
                for seed, r, t, c in [(1, 5, 20, 1), (2, 5, 10, 100), (3, 5, 10, 100)]]
        rows.append(dict(base, algorithm='milp', seed='', count='', makespan='', cost='', status='memory_limit'))
        rows.append(dict(base, algorithm='greedy', seed=0, count=0, makespan=0, cost=0))
        with tempfile.TemporaryDirectory() as directory:
            save_reports(Path(directory), rows)
            with (Path(directory) / 'comparison.csv').open() as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row['sa_result'], '(5, 10, 100)')
            self.assertEqual(row['sa_best_hits'], '2')
            self.assertEqual(row['sa_runs'], '3')
            self.assertEqual(row['best_algorithms'], 'sa')
            self.assertEqual(row['greedy_result'], '(0, 0, 0)')
            self.assertEqual(row['milp_result'], 'no_solution')
            self.assertEqual(row['alns_result'], 'not_run')
            with (Path(directory) / 'timing.csv').open() as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), len(rows))


if __name__ == '__main__':
    unittest.main()
