"""Independent schedule validator; no OR-Tools dependency."""
from collections import deque
from pathlib import Path
import sys


def read_instance(path):
    t=iter(map(int,Path(path).read_text().split()))
    n,q=next(t),next(t)
    edges=[(next(t)-1,next(t)-1) for _ in range(q)]
    d=[next(t) for _ in range(n)]
    m=next(t);s=[next(t) for _ in range(m)];k=next(t)
    costs={}
    for _ in range(k):
        i,j,c=next(t)-1,next(t)-1,next(t)
        costs[i,j]=min(c,costs.get((i,j),c))
    return n,edges,d,m,s,costs


def maximum_count(data):
    n,edges,_,_,_,costs=data
    successors=[[] for _ in range(n)]; degree=[0]*n
    allowed={i for i,j in costs}; invalid=set(range(n))-allowed
    for a,b in edges:
        successors[a].append(b);degree[b]+=1
    queue=deque(i for i in range(n) if degree[i]==0)
    visited=set()
    while queue:
        a=queue.popleft();visited.add(a)
        for b in successors[a]:
            if a in invalid:invalid.add(b)
            degree[b]-=1
            if degree[b]==0:queue.append(b)
    return len(visited-invalid)


def validate(data, output):
    n,edges,d,m,s,costs=data
    numbers=list(map(int,output.split()))
    if not numbers:raise ValueError('Empty output')
    count=numbers[0]
    if count<0 or count>n or len(numbers)!=1+3*count:raise ValueError('Wrong output length/count')
    chosen={};teams=[[] for _ in range(m)]
    total=0;span=0
    for p in range(count):
        i,j,start=numbers[1+3*p:4+3*p];i-=1;j-=1
        if i in chosen or (i,j) not in costs:raise ValueError('Duplicate/invalid assignment')
        if start<s[j]:raise ValueError('Team unavailable')
        chosen[i]=(j,start);teams[j].append((start,start+d[i]))
        total+=costs[i,j];span=max(span,start+d[i])
    for a,b in edges:
        if b in chosen and (a not in chosen or chosen[b][1]<chosen[a][1]+d[a]):
            raise ValueError('Precedence/selection violated')
    for intervals in teams:
        intervals.sort()
        if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):raise ValueError('Overlap')
    if count!=maximum_count(data):raise ValueError('Not maximum job count')
    return count,span,total

if __name__=='__main__':
    print(validate(read_instance(sys.argv[1]),Path(sys.argv[2]).read_text()))
