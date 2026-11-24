"""Run OR-Tools/SCIP in a resource-limited child and recover valid incumbents."""
import json
import subprocess
import sys
import time

from check import read_instance, validate
from paths import PROJECT_ROOT
from resource_limits import limit_memory

DETAIL_FIELDS = (
    'phase', 'count_optimal', 'makespan_optimal', 'cost_optimal',
    'objective_value', 'best_bound', 'relative_gap', 'build_seconds', 'solve_seconds',
    'peak_rss_mb', 'build_limit_seconds', 'memory_limit_mb', 'wall_limit_seconds',
    'order_variables', 'solver_status', 'exit_code', 'error',
)


def parse_events(stderr):
    details, schedule = {}, None
    for line in stderr.splitlines():
        if line.startswith('MILP_PROGRESS '):
            try:
                event = json.loads(line.removeprefix('MILP_PROGRESS '))
            except json.JSONDecodeError:
                continue
            details.update(event['details'])
            if event['schedule'] is not None:
                schedule = event['schedule']
        elif line.startswith('MILP_RESULT '):
            try:
                details.update(json.loads(line.removeprefix('MILP_RESULT ')))
            except json.JSONDecodeError:
                continue
    return details, schedule


def run_milp(path, phase_limit=30, build_limit=30, memory_limit=2048, wall_limit=None, total_limit=None):
    wall_limit = wall_limit or build_limit + 3 * phase_limit + 10
    data = read_instance(path)
    loads = [0] * data[3]
    for job, team in data[5]:
        loads[team] += 1
    command = [sys.executable, str(PROJECT_ROOT / 'solutions/milp/solve.py'),
               '--time-limit', str(phase_limit), '--build-time-limit', str(build_limit),
               '--memory-limit-mb', str(memory_limit), '--progress']
    if total_limit is not None:
        reserve = min(0.1, total_limit * 0.1)
        command.extend(['--deadline', str(time.monotonic() + total_limit - reserve)])
        wall_limit = total_limit
    started = time.perf_counter()
    output, stderr, code = '', '', ''
    timed_out = False
    try:
        process = subprocess.run(command, input=path.read_text(), capture_output=True,
                                 text=True, timeout=wall_limit, cwd=PROJECT_ROOT,
                                 preexec_fn=limit_memory(memory_limit))
        output, stderr, code = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stderr = exc.stderr or ''
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors='replace')
    elapsed = time.perf_counter() - started
    details, saved = parse_events(stderr)
    status = details.get('status', 'process_error')
    memory_messages = [line for line in stderr.splitlines()
                       if any(word in line.lower() for word in (
                           'bad_alloc', 'memoryerror', 'insufficient memory', 'out of memory',
                           'cannot allocate memory', 'failed to allocate', 'no memory left'))]
    if timed_out:
        status = 'wall_timeout'
    elif code != 0:
        if memory_messages:
            status = 'memory_limit'
        elif isinstance(code, int) and code < 0:
            status = 'process_error'
        elif status not in ('build_timeout', 'memory_limit', 'no_solution', 'solver_error'):
            status = 'process_error'
    if code == 0 and output:
        objective = validate(data, output, require_maximum=False)
    elif saved is not None:
        text = str(len(saved)) + '\n' + '\n'.join(' '.join(map(str, row)) for row in saved)
        objective = validate(data, text, require_maximum=False)
    else:
        objective = ('', '', '')
    if code == 0 and status not in ('optimal', 'feasible'):
        raise RuntimeError(f'Unexpected MILP success status: {status}')
    if status == 'optimal' and code != 0:
        status = 'process_error'
    error = ''
    if status in ('memory_limit', 'process_error', 'solver_error', 'wall_timeout', 'build_timeout', 'no_solution'):
        messages = [line for line in stderr.splitlines() if not line.startswith(('MILP_', 'count:', 'makespan:', 'cost:'))]
        error = ' | '.join([*memory_messages[-1:], *messages[-2:]])[:300] if messages else status
    row = dict(status=status, count=objective[0], makespan=objective[1], cost=objective[2],
               seconds=round(elapsed, 6))
    row.update({key: details.get(key, '') for key in DETAIL_FIELDS})
    row.update(build_limit_seconds=build_limit, memory_limit_mb=memory_limit,
               wall_limit_seconds=wall_limit, order_variables=sum(v * (v - 1) // 2 for v in loads),
               exit_code=code, error=error)
    if status in ('memory_limit', 'process_error', 'wall_timeout') and details.get('phase') != 'build':
        row['solve_seconds'] = ''
    return row
