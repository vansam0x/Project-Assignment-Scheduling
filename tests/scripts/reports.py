"""Build comparison tables from validated runs within one experiment."""
import csv
from collections import defaultdict

ALGORITHMS = ('milp', 'greedy', 'lpt', 'critical_path', 'multistart', 'sa', 'alns')


def write_csv(path, fields, rows):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def objective(row):
    if any(row.get(key, '') == '' for key in ('count', 'makespan', 'cost')):
        return None
    return tuple(int(row[key]) for key in ('count', 'makespan', 'cost'))


def rank(value):
    return (-value[0], value[1], value[2])


def save_reports(directory, rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['suite'], row['instance']].append(row)
    comparison = []
    for (suite, instance), runs in sorted(groups.items()):
        first = runs[0]
        result = {key: first[key] for key in ('suite', 'instance', 'n', 'q', 'm', 'k')}
        best_by_algorithm = {}
        for algorithm in ALGORITHMS:
            selected = [row for row in runs if row['algorithm'] == algorithm]
            valid = [row for row in selected if objective(row) is not None]
            prefix = algorithm + '_'
            result[prefix + 'runs'] = len(selected)
            result[prefix + 'valid_runs'] = len(valid)
            if not selected:
                result[prefix + 'result'] = 'not_run'
                continue
            if not valid:
                result[prefix + 'result'] = 'no_solution'
                result[prefix + 'status'] = '|'.join(sorted({row['status'] for row in selected}))
                continue
            best = min(valid, key=lambda row: rank(objective(row)))
            value = objective(best)
            best_by_algorithm[algorithm] = value
            result[prefix + 'result'] = str(value)
            result[prefix + 'status'] = best['status']
            result[prefix + 'best_seed'] = best['seed']
            result[prefix + 'best_hits'] = sum(objective(row) == value for row in valid)
            for key, number in zip(('R', 'T', 'C'), value):
                result[prefix + key] = number
            if algorithm == 'milp':
                result['milp_proof'] = 'optimal' if best['status'] == 'optimal' else 'not_proven'
        if best_by_algorithm:
            best_value = min(best_by_algorithm.values(), key=rank)
            result['best_algorithms'] = '|'.join(a for a, v in best_by_algorithm.items() if v == best_value)
        comparison.append(result)
    fields = ['suite', 'instance', 'n', 'q', 'm', 'k', 'best_algorithms', 'milp_proof']
    fields += [a + '_' + key for a in ALGORITHMS for key in
               ('result', 'R', 'T', 'C', 'status', 'runs', 'valid_runs', 'best_seed', 'best_hits')]
    write_csv(directory / 'comparison.csv', fields, comparison)
    timing_fields = ['suite', 'instance', 'algorithm', 'seed', 'seconds', 'status', 'phase',
                     'wall_limit_seconds', 'memory_limit_mb', 'error']
    write_csv(directory / 'timing.csv', timing_fields,
              [{key: row.get(key, '') for key in timing_fields} for row in rows])
