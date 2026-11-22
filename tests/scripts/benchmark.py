"""Run MILP with a 30-second phase budget and save independently checked CSV results."""
import argparse
import csv
import json
import subprocess
import sys
import time

from check import read_instance, validate
from paths import PROJECT_ROOT, RESULTS_DIR, SMALL_DATA

ROOT = PROJECT_ROOT
DETAIL_FIELDS = ('phase', 'count_optimal', 'makespan_optimal', 'cost_optimal',
                 'objective_value', 'best_bound', 'relative_gap')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--milp-seconds', type=float, default=30)
    parser.add_argument('--iterations', type=int, default=2000)
    args = parser.parse_args()
    if args.milp_seconds <= 0 or args.iterations < 0:
        parser.error('Invalid budget')
    RESULTS_DIR.mkdir(exist_ok=True)
    subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Wpedantic',
                    'solutions/alns/main.cpp', '-o', 'solutions/alns/alns'], cwd=ROOT, check=True)
    rows = []
    expected = {'sample': (5, 235, 145), 'cycle': (0, 0, 0), 'missing_team': (0, 0, 0),
                'single_team': (4, 11, 10), 'priority': (1, 3, 10), 'cost_tie': (1, 3, -5)}
    for instance in sorted(SMALL_DATA.glob('*.txt')):
        data = read_instance(instance)
        jobs = [('milp', '', [sys.executable, 'solutions/milp/solve.py', '--time-limit',
                             str(args.milp_seconds)], 3 * args.milp_seconds + 10),
                ('greedy', 0, ['solutions/alns/alns', '0', '0'], 30)]
        jobs.extend(('alns', seed, ['solutions/alns/alns', str(args.iterations), str(seed)], 30)
                    for seed in (1, 2, 3))
        for algorithm, seed, command, timeout in jobs:
            start = time.perf_counter()
            objective = ('', '', '')
            details = {}
            try:
                process = subprocess.run(command, input=instance.read_text(), capture_output=True,
                                         text=True, cwd=ROOT, timeout=timeout)
                seconds = time.perf_counter() - start
                if algorithm == 'milp':
                    payload = next((line.removeprefix('MILP_RESULT ') for line in process.stderr.splitlines()
                                    if line.startswith('MILP_RESULT ')), None)
                    if payload is None:
                        raise RuntimeError(process.stderr)
                    details = json.loads(payload)
                    status = details.get('status', 'no_solution')
                else:
                    status = 'feasible'
                if process.returncode == 0:
                    objective = validate(data, process.stdout, require_maximum=algorithm != 'milp')
                    if status == 'optimal' and instance.stem in expected:
                        assert objective == expected[instance.stem], (instance.stem, objective)
                elif algorithm != 'milp' or status != 'no_solution':
                    raise RuntimeError(process.stderr)
            except subprocess.TimeoutExpired:
                seconds = time.perf_counter() - start
                status = 'wall_timeout'
            row = dict(instance=instance.stem, n=data[0], q=len(data[1]), m=data[3], k=len(data[5]),
                       algorithm=algorithm, seed=seed,
                       iterations=args.iterations if algorithm == 'alns' else 0,
                       milp_seconds_per_phase=args.milp_seconds if algorithm == 'milp' else '',
                       status=status, count=objective[0], makespan=objective[1], cost=objective[2],
                       seconds=round(seconds, 6))
            row.update({key: details.get(key, '') for key in DETAIL_FIELDS})
            rows.append(row)
            print(f'{instance.stem} {algorithm} {seed}: {status} {objective} {seconds:.3f}s', flush=True)
    for row in rows:
        exact = next((other for other in rows if other['instance'] == row['instance']
                      and other['algorithm'] == 'milp' and other['status'] == 'optimal'), None)
        if exact and row['algorithm'] != 'milp' and row['count'] != '':
            assert (row['count'], -row['makespan'], -row['cost']) <= (
                exact['count'], -exact['makespan'], -exact['cost'])
    with (RESULTS_DIR / 'milp.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    main()
