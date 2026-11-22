"""Validate full-scale instances, run greedy/ALNS, estimate MILP size."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from check import read_instance,validate,maximum_count


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iterations',type=int,default=200)
    parser.add_argument('--seeds',type=int,nargs='+',default=[1,2,3])
    parser.add_argument('--timeout',type=float,default=30)
    args=parser.parse_args()
    if args.iterations<0 or args.timeout<=0:parser.error('Invalid budget')
    folder=Path(__file__).resolve().parent
    destination=folder/'results';destination.mkdir(exist_ok=True)
    manifest=json.loads((folder/'manifest.json').read_text())
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-pedantic',
                    'solutions/alns/main.cpp','-o','solutions/alns/alns'],cwd=ROOT,check=True)
    rows=[]
    for entry in manifest:
        path=folder/'instances'/entry['file'];raw=path.read_text()
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
        data=read_instance(path);n,edges,d,m,s,costs=data
        assert (n,len(edges),m,len(costs))==(entry['n'],entry['q'],entry['m'],entry['k'])
        assert 1<=n<=1000 and 1<=len(edges)<=1000 and 1<=m<=500 and 1<=len(costs)<=100000
        assert len(set(edges))==len(edges)
        assert all(0<=a<n and 0<=b<n and a!=b for a,b in edges)
        assert all(0<=i<n and 0<=j<m for i,j in costs)
        assert all(1<=v<=1000 for v in d+s)
        assert maximum_count(data)==entry['expected_count']
        loads=[0]*m
        for i,j in costs:loads[j]+=1
        assert sum(v*(v-1)//2 for v in loads)==entry['order_variables']
        for algorithm,iterations,seed in [('greedy',0,0)]+[('alns',args.iterations,v) for v in args.seeds]:
            stem=f'{path.stem}_{algorithm}_{seed}'
            start=time.perf_counter()
            try:
                result=subprocess.run([str(ROOT/'solutions/alns/alns'),str(iterations),str(seed)],
                                      input=raw,text=True,capture_output=True,timeout=args.timeout)
                elapsed=time.perf_counter()-start
                if result.returncode:raise RuntimeError(result.stderr)
                count,span,cost=validate(data,result.stdout)
                status='validated'
            except subprocess.TimeoutExpired:
                elapsed=time.perf_counter()-start;count=span=cost='';status='timeout'
            row=dict(instance=path.stem,n=n,q=len(edges),m=m,k=len(costs),algorithm=algorithm,
                     seed=seed,iterations=iterations,order_variables=entry['order_variables'],status=status,count=count,makespan=span,cost=cost,seconds=round(elapsed,6))
            rows.append(row)
            print(f'{stem}: {status} ({count},{span},{cost}) {elapsed:.3f}s',flush=True)
    with (destination/'benchmark.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]), lineterminator="\n");writer.writeheader();writer.writerows(rows)

if __name__=='__main__':main()
