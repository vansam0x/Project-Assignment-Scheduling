"""Compare C++ scheduling heuristics against the same decoder and MILP references."""
import argparse
import csv
from paths import PROJECT_ROOT, RESULTS_DIR, SMALL_DATA, STRESS_DATA
import subprocess
import time

from check import read_instance, validate
from benchmark import DETAIL_FIELDS

ROOT = PROJECT_ROOT
ALGORITHMS = ('greedy', 'lpt', 'critical_path', 'multistart', 'sa')
COMPARISON_ALGORITHMS = (*ALGORITHMS, 'alns')
RANDOMIZED = {'multistart', 'sa', 'alns'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('small', 'stress', 'all'), default='all')
    parser.add_argument('--iterations', type=int, default=2000)
    parser.add_argument('--stress-iterations', type=int, default=200)
    parser.add_argument('--seeds', type=int, nargs='+', default=[1, 2, 3])
    parser.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args()
    if args.iterations < 0 or args.stress_iterations < 0 or args.timeout <= 0:
        parser.error('Budgets must be nonnegative, timeout must be positive')
    binary = ROOT / 'solutions/heuristics/heuristics'
    subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Wpedantic',
                    str(ROOT / 'solutions/heuristics/main.cpp'), '-o', str(binary)], check=True)
    alns_binary = ROOT / 'solutions/alns/alns'
    subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Wpedantic',
                    str(ROOT / 'solutions/alns/main.cpp'), '-o', str(alns_binary)], check=True)
    destination = RESULTS_DIR
    destination.mkdir(exist_ok=True)
    references = {}
    milp_rows = {}
    with (RESULTS_DIR / 'milp.csv').open() as stream:
        for row in csv.DictReader(stream):
            if row['algorithm'] == 'milp':
                milp_rows[row['instance']] = row
            if row['algorithm'] == 'milp' and row['status'] == 'optimal':
                references[row['instance']] = tuple(int(row[key]) for key in ('count', 'makespan', 'cost'))
    instances = []
    if args.suite in ('small', 'all'):
        instances.extend(('small', path) for path in sorted(SMALL_DATA.glob('*.txt')))
    if args.suite in ('stress', 'all'):
        instances.extend(('stress', path) for path in sorted(STRESS_DATA.glob('*.txt')))
    if not instances:
        parser.error('No instances found; run tests/scripts/generate.py first')
    rows = []
    for suite, path in instances:
        data = read_instance(path)
        budget = args.iterations if suite == 'small' else args.stress_iterations
        raw = path.read_text()
        record = dict(suite=suite, instance=path.stem, n=data[0], q=len(data[1]),
                      m=data[3], k=len(data[5]), algorithm='milp', seed='', iterations=0,
                      milp_seconds_per_phase='', status='not_run', count='', makespan='',
                      cost='', seconds='')
        record.update({key: '' for key in DETAIL_FIELDS})
        if suite == 'small' and path.stem in milp_rows:
            source = milp_rows[path.stem]
            record.update({key: source[key] for key in record if key in source})
        rows.append(record)
        for algorithm in COMPARISON_ALGORITHMS:
            seeds = args.seeds if algorithm in RANDOMIZED else [0]
            iterations = budget if algorithm in RANDOMIZED else 0
            for seed in seeds:
                command = ([str(alns_binary), str(iterations), str(seed)] if algorithm == 'alns'
                           else [str(binary), algorithm, str(iterations), str(seed)])
                start = time.perf_counter()
                stem = f'{suite}_{path.stem}_{algorithm}_{seed}'
                objective = ('', '', '')
                try:
                    process = subprocess.run(command, input=raw, text=True, capture_output=True,
                                             timeout=args.timeout, check=True)
                    elapsed = time.perf_counter() - start
                    objective = validate(data, process.stdout)
                    reference = references.get(path.stem) if suite == 'small' else None
                    if reference:
                        assert objective >= reference, (stem, objective, reference)
                    status = 'validated'
                except subprocess.TimeoutExpired:
                    elapsed = time.perf_counter() - start
                    status = 'timeout'
                row = dict(suite=suite, instance=path.stem, n=data[0], q=len(data[1]),
                           m=data[3], k=len(data[5]), algorithm=algorithm, seed=seed,
                           iterations=iterations, milp_seconds_per_phase='', status=status,
                           count=objective[0], makespan=objective[1], cost=objective[2],
                           seconds=round(elapsed, 6))
                row.update({key: '' for key in DETAIL_FIELDS})
                rows.append(row)
        print(f'{suite}/{path.stem}: completed all {len(COMPARISON_ALGORITHMS)} algorithms', flush=True)
    with (destination / 'heuristics.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    main()
