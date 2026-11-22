"""Generate deterministic DAG benchmarks and targeted edge cases."""
import random
import argparse
import hashlib
import json
from paths import SMALL_DATA, STRESS_DATA


def write(name, n, edges, d, releases, costs, destination=None):
    lines = [f'{n} {len(edges)}', *(f'{a+1} {b+1}' for a,b in edges),
             ' '.join(map(str,d)), str(len(releases)), ' '.join(map(str,releases)),
             str(len(costs)), *(f'{i+1} {j+1} {c}' for i,j,c in costs)]
    path=(destination or SMALL_DATA)/f'{name}.txt'
    path.write_text('\n'.join(lines)+'\n')
    return path


def generate_stress():
    destination=STRESS_DATA
    destination.mkdir(parents=True,exist_ok=True)
    configs=[('scale200',200,200,20,2000,'dag'),
             ('scale500',500,500,100,10000,'dag'),
             ('max_dense',1000,1000,500,100000,'dag'),
             ('max_sparse',1000,1000,500,1000,'dag'),
             ('bottleneck',1000,1000,10,10000,'dag'),
             ('max_chain',1000,1000,500,100000,'chain')]
    manifest=[]
    for label,n,q,m,k,shape in configs:
        for seed in (2026,2027):
            r=random.Random(seed)
            order=list(range(n));r.shuffle(order)
            edges=set()
            if shape=='chain':
                edges.update((order[a],order[a+1]) for a in range(n-1))
            while len(edges)<q:
                a,b=sorted(r.sample(range(n),2))
                edges.add((order[a],order[b]))
            # At least one valid team per job; all K pairs are unique.
            pairs={(i,r.randrange(m)) for i in range(n)}
            while len(pairs)<k:
                pairs.add((r.randrange(n),r.randrange(m)))
            costs=[(i,j,r.randint(1,1000)) for i,j in sorted(pairs)]
            durations=[r.randint(1,1000) for _ in range(n)]
            releases=[r.randint(1,1000) for _ in range(m)]
            path=write(f'{label}_{seed}',n,sorted(edges),durations,releases,costs,destination)
            loads=[0]*m
            for i,j in pairs:loads[j]+=1
            order_vars=sum(v*(v-1)//2 for v in loads)
            manifest.append(dict(file=path.name,seed=seed,n=n,q=q,m=m,k=k,shape=shape,
                                 expected_count=n,order_variables=order_vars,
                                 nonoverlap_constraints=2*order_vars,
                                 sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['small','stress','all'],default='all')
    args=parser.parse_args()
    if args.suite in ('stress','all'):generate_stress()
    if args.suite=='stress':return
    SMALL_DATA.mkdir(parents=True,exist_ok=True)
    write('cycle',3,[(0,1),(1,0),(1,2)],[2,3,4],[1],[(i,0,5) for i in range(3)])
    write('missing_team',3,[(0,1),(1,2)],[2,3,4],[1],[(1,0,2),(2,0,3)])
    write('single_team',4,[(0,3)],[2,4,3,1],[1],[(i,0,i+1) for i in range(4)])
    write('priority',1,[],[2],[1,4],[(0,0,10),(0,1,-100)])
    write('cost_tie',1,[],[2],[1,1],[(0,0,10),(0,1,-5)])
    for label,n,m,density in [('small',8,3,.5),('medium',20,5,.5),('large',60,10,.3)]:
        for seed in range(3):
            r=random.Random(2026+seed)
            order=list(range(n));r.shuffle(order)
            edges=[(order[a],order[b]) for a in range(n) for b in range(a+1,n) if r.random()<2/n]
            d=[r.randint(1,30) for _ in range(n)]
            releases=[r.randint(1,20) for _ in range(m)]
            costs=[]
            for i in range(n):
                teams=[j for j in range(m) if r.random()<density] or [r.randrange(m)]
                costs.extend((i,j,r.randint(1,100)) for j in teams)
            write(f'{label}_{seed}',n,edges,d,releases,costs)
if __name__=='__main__':
    main()
