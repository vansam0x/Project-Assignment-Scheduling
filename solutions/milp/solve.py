"""Lexicographic MILP scheduling with OR-Tools/SCIP (integer input costs)."""

import argparse
import sys
from itertools import combinations

from ortools.linear_solver import pywraplp


def read_instance(stream):
    tokens = iter(map(int, stream.read().split()))
    try:
        n, q = next(tokens), next(tokens)
        edges = [(next(tokens) - 1, next(tokens) - 1) for _ in range(q)]
        durations = [next(tokens) for _ in range(n)]
        m = next(tokens)
        releases = [next(tokens) for _ in range(m)]
        k = next(tokens)
        costs = {}
        for _ in range(k):
            i, j, c = next(tokens) - 1, next(tokens) - 1, next(tokens)
            if not (0 <= i < n and 0 <= j < m):
                raise ValueError("Invalid assignment index")
            costs[i, j] = min(c, costs.get((i, j), c))
    except StopIteration as exc:
        raise ValueError("Incomplete input") from exc
    if n < 1 or m < 1 or any(v < 1 for v in durations + releases):
        raise ValueError("Counts, durations and releases must be positive")
    if any(not (0 <= a < n and 0 <= b < n) for a, b in edges):
        raise ValueError("Invalid precedence index")
    if next(tokens, None) is not None:
        raise ValueError("Unexpected trailing input")
    return n, edges, durations, m, releases, costs


def solve(instance, time_limit=None):
    n, edges, d, m, s, costs = instance
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("SCIP backend is unavailable")
    if time_limit is not None:
        solver.SetTimeLimit(max(1, int(time_limit * 1000)))
    horizon = max(s) + sum(d)
    big_m = horizon + max(d)
    y = [solver.BoolVar(f"y_{i}") for i in range(n)]
    u = [solver.IntVar(0, horizon, f"u_{i}") for i in range(n)]
    end = solver.IntVar(0, horizon, "makespan")
    x = {(i, j): solver.BoolVar(f"x_{i}_{j}") for i, j in costs}
    by_job = [[] for _ in range(n)]
    by_team = [[] for _ in range(m)]
    for i, j in x:
        by_job[i].append(x[i, j])
        by_team[j].append(i)
        solver.Add(u[i] >= s[j] - horizon * (1 - x[i, j]))
    for i in range(n):
        solver.Add(solver.Sum(by_job[i]) == y[i])
        solver.Add(u[i] <= (horizon - d[i]) * y[i])
        solver.Add(end >= u[i] + d[i] * y[i])
    for a, b in edges:
        solver.Add(y[b] <= y[a])
        solver.Add(u[b] >= u[a] + d[a] - big_m * (1 - y[b]))
    for j, jobs in enumerate(by_team):
        for a, b in combinations(jobs, 2):
            order = solver.BoolVar(f"order_{a}_{b}_{j}")
            inactive = 2 - x[a, j] - x[b, j]
            solver.Add(u[a] + d[a] <= u[b] + big_m * (1 - order + inactive))
            solver.Add(u[b] + d[b] <= u[a] + big_m * (order + inactive))

    count = solver.Sum(y)
    total_cost = solver.Sum(c * x[pair] for pair, c in costs.items())
    phases = [("count", count, True), ("makespan", end, False),
              ("cost", total_cost, False)]
    for name, objective, maximize in phases:
        if maximize:
            solver.Maximize(objective)
        else:
            solver.Minimize(objective)
        status = solver.Solve()
        if status != pywraplp.Solver.OPTIMAL:
            raise RuntimeError(
                f"Phase {name}: status={status}; optimality not proven. "
                "No lexicographic optimum is reported. Increase/omit --time-limit."
            )
        optimum = round(solver.Objective().Value())
        print(f"{name}: {optimum} (OPTIMAL)", file=sys.stderr)
        if name != "cost":
            solver.Add(objective == optimum)
    return [(i + 1, j + 1, round(u[i].solution_value()))
            for (i, j), var in sorted(x.items()) if var.solution_value() > 0.5]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--time-limit", type=float, help="Seconds per optimization phase")
    args = parser.parse_args()
    if args.time_limit is not None and args.time_limit <= 0:
        parser.error("--time-limit must be positive")
    try:
        schedule = solve(read_instance(sys.stdin), args.time_limit)
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(len(schedule))
    for row in schedule:
        print(*row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
