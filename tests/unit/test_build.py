"""Check CMake invocation and missing-tool errors without compiling."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_cpp import BUILD_DIR, build_cpp
from paths import PROJECT_ROOT


class BuildTests(unittest.TestCase):
    @patch('build_cpp.subprocess.run')
    @patch('build_cpp.shutil.which', return_value='/tool/cmake')
    def test_targets_use_release_build(self, which, run):
        binaries = build_cpp('alns', 'heuristics')
        self.assertEqual(binaries['alns'], BUILD_DIR / 'alns')
        self.assertEqual(binaries['heuristics'], BUILD_DIR / 'heuristics')
        self.assertEqual(run.call_args_list[0].args[0], [
            '/tool/cmake', '-S', str(PROJECT_ROOT), '-B', str(BUILD_DIR),
            '-DCMAKE_BUILD_TYPE=Release'])
        self.assertEqual(run.call_args_list[1].args[0], [
            '/tool/cmake', '--build', str(BUILD_DIR), '--parallel',
            '--target', 'alns', 'heuristics'])

    @patch('build_cpp.subprocess.run')
    @patch('build_cpp.shutil.which', return_value=None)
    def test_missing_cmake_is_reported(self, which, run):
        with self.assertRaisesRegex(RuntimeError, 'CMake is required'):
            build_cpp()
        run.assert_not_called()

    def test_unknown_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown CMake target'):
            build_cpp('missing')


if __name__ == '__main__':
    unittest.main()
