"""Configure and build the C++ executables through CMake."""
import shutil
import subprocess

from paths import PROJECT_ROOT

BUILD_DIR = PROJECT_ROOT / '.build'
TARGETS = ('alns', 'heuristics')


def build_cpp(*targets):
    targets = targets or TARGETS
    if any(target not in TARGETS for target in targets):
        raise ValueError(f'Unknown CMake target: {targets}')
    cmake = (shutil.which('cmake') or
             shutil.which('cmake', path=str(BUILD_DIR / 'tools/cmake/bin')))
    if cmake is None:
        raise RuntimeError('CMake is required; install CMake and add it to PATH')
    subprocess.run([cmake, '-S', str(PROJECT_ROOT), '-B', str(BUILD_DIR),
                    '-DCMAKE_BUILD_TYPE=Release'], check=True)
    subprocess.run([cmake, '--build', str(BUILD_DIR), '--parallel',
                    '--target', *targets], check=True)
    return {target: BUILD_DIR / target for target in targets}
