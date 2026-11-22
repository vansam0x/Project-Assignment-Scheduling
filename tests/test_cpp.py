"""Compile and validate every heuristic on semantic and malformed-input cases."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from check import read_instance, validate
from compare_heuristics import ALGORITHMS

ROOT = Path(__file__).resolve().parent.parent


class CppHeuristicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / '.build').mkdir(exist_ok=True)
        cls.binary = ROOT / '.build/test-heuristics'
        subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Wpedantic',
                        str(ROOT / 'solutions/heuristics/main.cpp'), '-o', str(cls.binary)], check=True)

    def test_known_objectives(self):
        cases = [
            # A cycle and its descendant are excluded; an independent job survives.
            ('4 3\n1 2\n2 1\n2 3\n2 3 4 5\n1\n1\n4\n1 1 2\n2 1 2\n3 1 2\n4 1 -7\n', (1, 6, -7)),
            # Duplicate assignment: the cheapest cost for the same pair is used.
            ('2 1\n1 2\n2 3\n1\n1\n3\n1 1 50\n1 1 -4\n2 1 2\n', (2, 6, -2)),
            ('2 1\n1 2\n2 3\n1\n1\n1\n2 1 5\n', (0, 0, 0)),
            ('1 1\n1 1\n2\n1\n1\n1\n1 1 3\n', (0, 0, 0)),
            ('1 0\n2\n2\n1 4\n2\n1 1 10\n1 2 -100\n', (1, 3, 10)),
            ('1 0\n2\n2\n1 1\n2\n1 1 10\n1 2 -5\n', (1, 3, -5)),
        ]
        with tempfile.TemporaryDirectory(dir=ROOT / '.build') as directory:
            path = Path(directory) / 'input.txt'
            for raw, expected in cases:
                path.write_text(raw)
                data = read_instance(path)
                for algorithm in ALGORITHMS:
                    with self.subTest(algorithm=algorithm, expected=expected):
                        output = subprocess.run([str(self.binary), algorithm, '100', '7'], input=raw,
                                                text=True, capture_output=True, check=True).stdout
                        self.assertEqual(validate(data, output), expected)

    def test_invalid_input_is_rejected(self):
        for raw in ('', '2 1\n1 3\n', '1 0\n0\n', '1 0\n2\n0\n',
                    '1 0\n2\n1\n1\n1\n1 2 5\n'):
            with self.subTest(raw=raw):
                result = subprocess.run([str(self.binary), 'alns'], input=raw,
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')

    def test_seed_reproducibility(self):
        raw = (ROOT / 'tests/instances/medium_0.txt').read_text()
        for algorithm in ('multistart', 'sa', 'alns'):
            with self.subTest(algorithm=algorithm):
                command = [str(self.binary), algorithm, '200', '9']
                first = subprocess.run(command, input=raw, text=True, capture_output=True, check=True)
                second = subprocess.run(command, input=raw, text=True, capture_output=True, check=True)
                self.assertEqual(first.stdout, second.stdout)


if __name__ == '__main__':
    unittest.main()
