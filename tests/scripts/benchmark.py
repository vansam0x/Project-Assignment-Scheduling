"""Attempt MILP on every selected instance and record actual outcomes in CSV."""
import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone

from build_cpp import build_cpp
from check import read_instance, validate, maximum_count
from milp_runner import DETAIL_FIELDS, run_milp
from paths import RESULTS_DIR, SMALL_DATA, STRESS_DATA
from resource_limits import limit_memory
from reports import save_reports, write_csv


COMPARISON_ALGORITHMS = ('greedy', 'lpt', 'critical_path', 'multistart', 'sa', 'alns')


def log(message):
    """Print an immediate, human-readable progress message."""
    print(f'[benchmark] {message}', flush=True)


def recover_schedule(stderr):
    if isinstance(stderr, bytes):
        stderr = stderr.decode(errors='replace')
    blocks = (stderr or '').split('SCHEDULE_BEGIN\n')[1:]
    for block in reversed(blocks):
        if 'SCHEDULE_END\n' in block:
            return block.split('SCHEDULE_END\n', 1)[0]
    return None


def verify_stress():
    for entry in json.loads((STRESS_DATA / 'manifest.json').read_text()):
        path = STRESS_DATA / entry['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
        data = read_instance(path)
        n, edges, durations, m, releases, costs = data
        assert (n, len(edges), m, len(costs)) == (entry['n'], entry['q'], entry['m'], entry['k'])
        assert 1 <= n <= 1000 and 1 <= len(edges) <= 1000
        assert 1 <= m <= 500 and 1 <= len(costs) <= 100000
        assert len(set(edges)) == len(edges)
        assert all(0 <= a < n and 0 <= b < n and a != b for a, b in edges)
        assert all(0 <= i < n and 0 <= j < m for i, j in costs)
        assert all(1 <= value <= 1000 for value in durations + releases)
        assert maximum_count(data) == entry['expected_count']


def save_rows(path, rows):
    common = ('suite', 'instance', 'n', 'q', 'm', 'k', 'algorithm', 'seed', 'iterations',
              'milp_seconds_per_phase', 'status', 'count', 'makespan', 'cost', 'seconds')
    fields = list(dict.fromkeys([*common, *DETAIL_FIELDS,
                                *(key for row in rows for key in row)]))
    write_csv(path, fields, rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('small', 'stress', 'all'), default='all')
    parser.add_argument('--time-limit', type=float, default=30,
                        help='Total wall time per algorithm run, including model construction')
    parser.add_argument('--memory-mb', type=int, default=2048,
                        help='Address-space cap per child process in MiB (Linux)')
    parser.add_argument('--seeds', type=int, nargs='+', default=[1, 2, 3])
    parser.add_argument('--milp-only', action='store_true')
    args = parser.parse_args(argv)
    if args.time_limit <= 0 or args.memory_mb <= 0:
        parser.error('Time and memory limits must be positive')
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory = RESULTS_DIR
    for filename in ('config.csv', 'runs.csv', 'comparison.csv', 'timing.csv'):
        (directory / filename).unlink(missing_ok=True)
    output = directory / 'runs.csv'
    write_csv(directory / 'config.csv', ['run_id', 'suite', 'time_limit_seconds', 'memory_mb', 'seeds', 'milp_only'],
              [dict(run_id=run_id, suite=args.suite, time_limit_seconds=args.time_limit,
                    memory_mb=args.memory_mb, seeds=' '.join(map(str, args.seeds)), milp_only=args.milp_only)])
    log(f'suite={args.suite} time_limit={args.time_limit:g}s memory={args.memory_mb}MiB '
        f'seeds={args.seeds} milp_only={args.milp_only}')
    log(f'results={directory}')
    rows = []
    instances = []
    if args.suite in ('small', 'all'):
        instances.extend(('small', path) for path in sorted(SMALL_DATA.glob('*.txt')))
    if args.suite in ('stress', 'all'):
        verify_stress()
        instances.extend(('stress', path) for path in sorted(STRESS_DATA.glob('*.txt')))
    if not instances:
        parser.error('No input files found')
    log(f'prepared {len(instances)} instance(s)')
    if not args.milp_only:
        log('building C++ algorithms')
    binaries = {} if args.milp_only else build_cpp('alns', 'heuristics')
    if not args.milp_only:
        log('C++ algorithms ready')
    expected = {'sample': (5, 235, 145), 'cycle': (0, 0, 0), 'missing_team': (0, 0, 0),
                'single_team': (4, 11, 10), 'priority': (1, 3, 10), 'cost_tie': (1, 3, -5)}

    def record(row):
        key = row['suite'], row['instance'], row['algorithm'], str(row['seed'])
        rows[:] = [old for old in rows if (old['suite'], old['instance'], old['algorithm'], str(old['seed'])) != key]
        rows.append(row)
        save_rows(output, rows)
        save_reports(directory, rows)

    for suite, path in instances:
        data = read_instance(path)
        log(f'{suite}/{path.stem}: start algorithm=milp '
            f'limit={args.time_limit:g}s memory={args.memory_mb}MiB')
        row = dict(suite=suite, instance=path.stem, n=data[0], q=len(data[1]), m=data[3], k=len(data[5]),
                   algorithm='milp', seed='', iterations=0, milp_seconds_per_phase='')
        row.update(run_milp(path, phase_limit=args.time_limit, build_limit=args.time_limit,
                            memory_limit=args.memory_mb, total_limit=args.time_limit))
        if row['status'] == 'optimal' and path.stem in expected:
            assert (row['count'], row['makespan'], row['cost']) == expected[path.stem]
        record(row)
        log(f"{suite}/{path.stem}: done algorithm=milp status={row['status']} "
            f"phase={row['phase']} R/T/C=({row['count']},{row['makespan']},{row['cost']}) "
            f"elapsed={row['seconds']:.3f}s")
        if args.milp_only:
            continue
        for algorithm in COMPARISON_ALGORITHMS:
            randomized = algorithm in ('multistart', 'sa', 'alns')
            for seed in args.seeds if randomized else [0]:
                # Time is the stopping criterion; the iteration cap is only a CLI sentinel.
                iterations = 2147483647 if randomized else 0
                search_seconds = max(0.001, args.time_limit - min(0.1, args.time_limit * 0.1))
                command = ([str(binaries['alns']), str(iterations), str(seed), str(search_seconds)]
                           if algorithm == 'alns' else
                           [str(binaries['heuristics']), algorithm, str(iterations), str(seed), str(search_seconds)])
                log(f'{suite}/{path.stem}: start algorithm={algorithm} seed={seed} '
                    f'limit={args.time_limit:g}s memory={args.memory_mb}MiB')
                started = time.perf_counter()
                objective = ('', '', '')
                error, exit_code = '', ''
                try:
                    process = subprocess.run(command, input=path.read_text(), text=True,
                                             capture_output=True, timeout=args.time_limit,
                                             preexec_fn=limit_memory(args.memory_mb),
                                             env={**os.environ, "SCHEDULING_PROGRESS": "1",
                                                  "SCHEDULING_DEADLINE": str(time.monotonic() + search_seconds)})
                    elapsed = time.perf_counter() - started
                    exit_code = process.returncode
                    if exit_code == 0:
                        objective = validate(data, process.stdout)
                        status = 'validated'
                    else:
                        saved = recover_schedule(process.stderr)
                        if saved is not None:
                            objective = validate(data, saved)
                        error = process.stderr[-300:]
                        status = ('memory_limit' if any(word in process.stderr.lower() for word in
                                  ('bad_alloc', 'cannot allocate memory', 'out of memory')) else 'process_error')
                except subprocess.TimeoutExpired as exc:
                    elapsed = time.perf_counter() - started
                    saved = recover_schedule(exc.stderr)
                    if saved is not None:
                        objective = validate(data, saved)
                    status, error = 'wall_timeout', 'Total wall time exceeded; no complete schedule returned'
                other = dict(suite=suite, instance=path.stem, n=data[0], q=len(data[1]), m=data[3], k=len(data[5]),
                             algorithm=algorithm, seed=seed, iterations='', milp_seconds_per_phase='',
                             status=status, count=objective[0], makespan=objective[1], cost=objective[2], seconds=round(elapsed, 6))
                other.update({key: '' for key in DETAIL_FIELDS})
                other.update(wall_limit_seconds=args.time_limit, memory_limit_mb=args.memory_mb,
                             exit_code=exit_code, error=error)
                if row['status'] == 'optimal' and objective[0] != '':
                    assert (objective[0], -objective[1], -objective[2]) <= (row['count'], -row['makespan'], -row['cost'])
                record(other)
                log(f"{suite}/{path.stem}: done algorithm={algorithm} seed={seed} "
                    f"status={status} R/T/C=({objective[0]},{objective[1]},{objective[2]}) "
                    f"elapsed={elapsed:.3f}s")
    log(f'completed; results={directory}')
    return directory


if __name__ == '__main__':
    main()
