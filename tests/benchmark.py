"""Reproducible subprocess benchmark, independent feasibility checks and report."""
import argparse
import csv
import json
from importlib.metadata import version
import platform
from pathlib import Path
import subprocess
import sys
import time
from check import read_instance,validate

ROOT=Path(__file__).resolve().parent.parent

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
    destination=ROOT/'tests/results';destination.mkdir(exist_ok=True)
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-pedantic',
                    'solutions/alns/main.cpp','-o','solutions/alns/alns'],cwd=ROOT,check=True)
    rows=[]
    expected={'sample':(5,235,145),'cycle':(0,0,0),'missing_team':(0,0,0),
              'single_team':(4,11,10),'priority':(1,3,10),'cost_tie':(1,3,-5)}
    for instance in sorted((ROOT/'tests/instances').glob('*.txt')):
        data=read_instance(instance)
        jobs=[('milp','', [sys.executable,'solutions/milp/solve.py','--time-limit',str(args.milp_seconds)],3*args.milp_seconds+10),
              ('greedy',0,['solutions/alns/alns','0','0'],30)]
        jobs.extend(('alns',seed,['solutions/alns/alns',str(args.iterations),str(seed)],30) for seed in (1,2,3))
        for algorithm,seed,command,timeout in jobs:
            code,out,err,seconds=run(command,instance,timeout)
            stem=f'{instance.stem}_{algorithm}_{seed}'
            (destination/f'{stem}.log').write_text(err)
            status='wall_timeout' if code==-1 else 'not_proven' if code else 'optimal' if algorithm=='milp' else 'feasible'
            objective=('','','')
            if code==0:
                objective=validate(data,out)
                (destination/f'{stem}.out').write_text(out)
                if algorithm=='milp' and instance.stem in expected:
                    assert objective==expected[instance.stem],(instance.stem,objective)
            elif code not in (-1,1) or (code==1 and 'optimality not proven' not in err):
                raise RuntimeError(f'{stem}: execution failed: {err}')
            row=dict(instance=instance.stem,n=data[0],m=data[3],k=len(data[5]),algorithm=algorithm,
                     seed=seed,status=status,count=objective[0],makespan=objective[1],cost=objective[2],seconds=round(seconds,6))
            rows.append(row)
            print(f'{instance.stem} {algorithm} {seed}: {status} {objective} {seconds:.3f}s',flush=True)
    # Every successful heuristic must be lexicographically no better than a proven optimum.
    for row in rows:
        exact=next((r for r in rows if r['instance']==row['instance'] and r['algorithm']=='milp' and r['status']=='optimal'),None)
        if exact and row['status']=='feasible':
            assert (row['makespan'],row['cost']) >= (exact['makespan'],exact['cost'])
    with (destination/'benchmark.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    metadata={'python':sys.version,'platform':platform.platform(),'ortools':version('ortools'),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
              'milp_seconds_per_phase':args.milp_seconds,'milp_wall_timeout':3*args.milp_seconds+10,
              'alns_iterations':args.iterations,'alns_seeds':[1,2,3]}
    (destination/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    report=['# Kết quả thực nghiệm','',
            f'MILP: {args.milp_seconds:g} giây mỗi pha (tối đa 3 pha); ALNS: {args.iterations} vòng lặp, seed 1/2/3.',
            'Thời gian là wall-clock của subprocess, gồm khởi động và dựng mô hình; không gồm biên dịch C++.',
            'Mọi nghiệm xuất ra đã qua bộ kiểm tra độc lập: đội hợp lệ, thời điểm sẵn sàng, tiền nhiệm, không chồng lấn và số công việc tối đa.',
            'MILP dừng khi chưa chứng minh tối ưu được ghi `not_proven`; mã hiện tại không xuất incumbent trong trường hợp này.',
            '', '| Test | N | MILP (R,T,C) | MILP giây | Greedy (T,C) | ALNS tốt nhất (T,C) | T ALNS min–max | ALNS giây TB |',
            '| --- | ---: | --- | ---: | --- | --- | --- | ---: |']
    for name in sorted({r['instance'] for r in rows}):
        group=[r for r in rows if r['instance']==name];exact=group[0];greedy=group[1];heur=group[2:]
        best=min(heur,key=lambda r:(r['makespan'],r['cost']))
        value=f"({exact['count']},{exact['makespan']},{exact['cost']})" if exact['status']=='optimal' else exact['status']
        report.append(f"| {name} | {exact['n']} | {value} | {exact['seconds']:.3f} | ({greedy['makespan']},{greedy['cost']}) | ({best['makespan']},{best['cost']}) | {min(r['makespan'] for r in heur)}–{max(r['makespan'] for r in heur)} | {sum(r['seconds'] for r in heur)/3:.3f} |")
    report+=['','ALNS tốt nhất là nghiệm tốt nhất trong ba lần chạy; không phải giá trị trung bình hoặc chứng minh tối ưu.',
             'Khi makespan khác nhau, không so chi phí riêng lẻ để xếp hạng. Khi MILP chưa chứng minh tối ưu, chưa thể tính khoảng cách tới tối ưu.',
             'Các ngân sách dừng khác nhau và Python/C++ có chi phí khởi động khác nhau; bảng này đánh giá thực dụng, không phải so sánh tốc độ thuật toán trong điều kiện đồng nhất.',
             '', 'Dữ liệu chi tiết: [benchmark.csv](./benchmark.csv); cấu hình: [metadata.json](./metadata.json).']
    (destination/'report.md').write_text('\n'.join(report)+'\n')

if __name__=='__main__':main()
