"""Exercise the shared budgets without changing saved benchmark results."""
import csv
import importlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
benchmark = importlib.import_module('benchmark')
paths = importlib.import_module('paths')


class SharedBudgetTests(unittest.TestCase):
    def test_all_algorithms_use_same_limits(self):
        with tempfile.TemporaryDirectory(dir=paths.PROJECT_ROOT / '.build') as directory:
            root = Path(directory)
            data, results = root / 'data', root / 'results'
            data.mkdir()
            shutil.copy(paths.SMALL_DATA / 'sample.txt', data)
            with patch.object(benchmark, 'SMALL_DATA', data), patch.object(benchmark, 'RESULTS_DIR', results):
                directory = benchmark.main(['--suite', 'small', '--time-limit', '0.5',
                                '--memory-mb', '512', '--seeds', '1'])
            with (directory / 'runs.csv').open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual({row['algorithm'] for row in rows},
                             {'milp', *benchmark.COMPARISON_ALGORITHMS})
            for row in rows:
                with self.subTest(algorithm=row['algorithm']):
                    self.assertEqual(float(row['wall_limit_seconds']), 0.5)
                    self.assertEqual(int(row['memory_limit_mb']), 512)
                    self.assertNotEqual(row['count'], '')
                    expected_cost = 150 if row['algorithm'] in ('lpt', 'critical_path') else 145
                    self.assertEqual((int(row['count']), int(row['makespan']), int(row['cost'])),
                                     (5, 235, expected_cost))
                    if row['algorithm'] in ('sa', 'multistart', 'alns'):
                        self.assertGreater(float(row['seconds']), 0.3)
                    self.assertLess(float(row['seconds']), 1.0)

    def test_memory_cap_is_applied_before_program_start(self):
        limits = importlib.import_module('resource_limits')
        process = subprocess.run(
            [sys.executable, '-c', 'import resource; print(resource.getrlimit(resource.RLIMIT_AS)[0])'],
            preexec_fn=limits.limit_memory(512), capture_output=True, text=True, check=True)
        self.assertEqual(int(process.stdout), 512 * 1024 * 1024)

    def test_timeout_checkpoint_ignores_incomplete_last_schedule(self):
        stderr = b'SCHEDULE_BEGIN\n0\nSCHEDULE_END\nSCHEDULE_BEGIN\n2\n'
        self.assertEqual(benchmark.recover_schedule(stderr), '0\n')


if __name__ == '__main__':
    unittest.main()
