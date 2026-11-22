"""Reproducible subprocess benchmark, independent checks and CSV results."""
import argparse
import csv
from paths import PROJECT_ROOT, RESULTS_DIR, SMALL_DATA
import subprocess
import sys
import time
from check import read_instance,validate

ROOT=PROJECT_ROOT

def run(command, instance, timeout):
    begin=time.perf_counter()
    try:
        result=subprocess.run(command,input=instance.read_text(),capture_output=True,text=True,
                              cwd=ROOT,timeout=timeout)
        return result.returncode,result.stdout,result.stderr,time.perf_counter()-begin
    except subprocess.TimeoutExpired:
        return -1,'','Wall-clock timeout',time.perf_counter()-begin


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--milp-seconds',type=float,default=2)
    parser.add_argument('--iterations',type=int,default=2000)
    args=parser.parse_args()
    if args.milp_seconds<=0 or args.iterations<0:parser.error('Invalid budget')
    destination=RESULTS_DIR;destination.mkdir(exist_ok=True)
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-pedantic',
                    'solutions/alns/main.cpp','-o','solutions/alns/alns'],cwd=ROOT,check=True)
    rows=[]
    expected={'sample':(5,235,145),'cycle':(0,0,0),'missing_team':(0,0,0),
              'single_team':(4,11,10),'priority':(1,3,10),'cost_tie':(1,3,-5)}
    for instance in sorted(SMALL_DATA.glob('*.txt')):
        data=read_instance(instance)
        jobs=[('milp','', [sys.executable,'solutions/milp/solve.py','--time-limit',str(args.milp_seconds)],3*args.milp_seconds+10),
              ('greedy',0,['solutions/alns/alns','0','0'],30)]
        jobs.extend(('alns',seed,['solutions/alns/alns',str(args.iterations),str(seed)],30) for seed in (1,2,3))
        for algorithm,seed,command,timeout in jobs:
            code,out,err,seconds=run(command,instance,timeout)
            stem=f'{instance.stem}_{algorithm}_{seed}'
            status='wall_timeout' if code==-1 else 'not_proven' if code else 'optimal' if algorithm=='milp' else 'feasible'
            objective=('','','')
            if code==0:
                objective=validate(data,out)
                if algorithm=='milp' and instance.stem in expected:
                    assert objective==expected[instance.stem],(instance.stem,objective)
            elif code not in (-1,1) or (code==1 and 'optimality not proven' not in err):
                raise RuntimeError(f'{stem}: execution failed: {err}')
            row=dict(instance=instance.stem,n=data[0],m=data[3],k=len(data[5]),algorithm=algorithm,
                     seed=seed,iterations=args.iterations if algorithm=='alns' else 0,
                     milp_seconds_per_phase=args.milp_seconds if algorithm=='milp' else '',status=status,count=objective[0],makespan=objective[1],cost=objective[2],seconds=round(seconds,6))
            rows.append(row)
            print(f'{instance.stem} {algorithm} {seed}: {status} {objective} {seconds:.3f}s',flush=True)
    # Every successful heuristic must be lexicographically no better than a proven optimum.
    for row in rows:
        exact=next((r for r in rows if r['instance']==row['instance'] and r['algorithm']=='milp' and r['status']=='optimal'),None)
        if exact and row['status']=='feasible':
            assert (row['makespan'],row['cost']) >= (exact['makespan'],exact['cost'])
    with (destination/'milp.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]), lineterminator="\n");writer.writeheader();writer.writerows(rows)

if __name__=='__main__':main()
