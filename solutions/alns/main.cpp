#include <limits>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <numeric>
#include <queue>
#include <random>
#include <tuple>
#include <vector>
using namespace std;
using ll = long long;
struct Sol { vector<int> order, team; vector<ll> start; ll span=0, cost=0; };
int main(int argc,char**argv){
    int iterations=argc>1?stoi(argv[1]):5000;
    unsigned seed=argc>2?stoul(argv[2]):1;
    if(iterations<0) return 2;
    mt19937 rng(seed);
    int n,q,m,k; if(!(cin>>n>>q)||n<1) return 2;
    vector<vector<int>> pred(n),succ(n);
    vector<int> indeg(n),d(n);
    for(int e=0,a,b;e<q;e++){cin>>a>>b; --a;--b;pred[b].push_back(a);succ[a].push_back(b);indeg[b]++;}
    for(auto&v:d)cin>>v;
    cin>>m; vector<ll> release(m);for(auto&v:release)cin>>v;
    cin>>k; vector<vector<pair<int,ll>>> options(n);
    for(int e=0,i,j;e<k;e++){ll c;cin>>i>>j>>c;options[i-1].push_back({j-1,c});}
    // Kahn elimination also excludes cycles and their descendants. Missing teams
    // propagate exclusion to successors. All remaining jobs can be scheduled.
    queue<int> ready;for(int i=0;i<n;i++)if(!indeg[i])ready.push(i);
    vector<int> valid(n,0),topo;
    while(!ready.empty()){
        int i=ready.front();ready.pop();valid[i]=!options[i].empty();
        for(int p:pred[i])valid[i]&=valid[p];
        if(valid[i])topo.push_back(i);
        for(int b:succ[i])if(--indeg[b]==0)ready.push(b);
    }
    auto decode=[&](const vector<int>&order,const vector<int>&prefs,int mode){
        Sol sol;sol.team.assign(n,-1);sol.start.assign(n,0);
        vector<int> rank(n,n),left(n);vector<ll> finish(n,0),available=release;
        for(int z=0;z<(int)order.size();z++)rank[order[z]]=z;
        priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>> heap;
        for(int i:topo){left[i]=pred[i].size();if(!left[i])heap.push({rank[i],i});}
        while(!heap.empty()){
            int i=heap.top().second;heap.pop();ll earliest=0;
            for(int p:pred[i])earliest=max(earliest,finish[p]);
            tuple<ll,ll,int> best={numeric_limits<ll>::max(),0,0};
            ll start=0,cost=0;int team=-1;
            for(auto [j,c]:options[i]){
                if(prefs[i]>=0&&prefs[i]!=j)continue;
                ll t=max(earliest,available[j]);
                // Three repair policies: earliest finish, cheapest, randomized finish.
                ll first=mode==1?c:t+d[i];
                if(mode==2)first+=rng()%(d[i]+1);
                auto score=make_tuple(first,mode==1?t+d[i]:c,j);
                if(score<best){best=score;team=j;start=t;cost=c;}
            }
            sol.team[i]=team;sol.start[i]=start;finish[i]=start+d[i];available[team]=finish[i];
            sol.span=max(sol.span,finish[i]);sol.cost+=cost;sol.order.push_back(i);
            for(int b:succ[i])if(valid[b]&&--left[b]==0)heap.push({rank[b],b});
        }
        return sol;
    };
    vector<int> none(n,-1);Sol current=decode(topo,none,0),best=current;
    vector<double> weights(9,1.0);
    for(int it=0;it<iterations&&!topo.empty();it++){
        discrete_distribution<int> select(weights.begin(),weights.end());int op=select(rng),destroy=op/3,repair=op%3;
        vector<int> removed=current.order;
        if(destroy==0)shuffle(removed.begin(),removed.end(),rng);
        if(destroy==1)stable_sort(removed.begin(),removed.end(),[&](int a,int b){return current.start[a]+d[a]>current.start[b]+d[b];});
        if(destroy==2)stable_sort(removed.begin(),removed.end(),[&](int a,int b){
            auto c=[&](int i){ll v=numeric_limits<ll>::max();for(auto [j,c]:options[i])if(j==current.team[i])v=min(v,c);return v;};return c(a)>c(b);
        });
        int count=max(1,(int)(topo.size()*(0.1+0.4*(rng()%1000)/999.0)));
        removed.resize(count);vector<int> erased(n,0),prefs=current.team,order;
        for(int i:removed){erased[i]=1;prefs[i]=-1;}
        for(int i:current.order)if(!erased[i])order.push_back(i);
        shuffle(removed.begin(),removed.end(),rng);
        for(int i:removed)order.insert(order.begin()+rng()%(order.size()+1),i);
        Sol candidate=decode(order,prefs,repair);
        auto key=[](const Sol&s){return make_pair(s.span,s.cost);};
        double reward=0.1;
        if(key(candidate)<key(best)){best=candidate;reward=8;}
        if(key(candidate)<key(current)){current=candidate;reward=max(reward,4.0);}
        else {
            double temperature=max(0.01,best.span*0.05*(1.0-double(it)/max(1,iterations)));
            double delta=candidate.span-current.span;
            // A cost worsening at equal makespan may be accepted for exploration.
            if(delta==0)delta=double(candidate.cost-current.cost)/max(1.0,abs(double(current.cost)));
            if(uniform_real_distribution<double>(0,1)(rng)<exp(-max(0.0,delta)/temperature)){current=candidate;reward=max(reward,1.0);}
        }
        weights[op]=0.9*weights[op]+0.1*reward;
    }
    cout<<best.order.size()<<'\n';for(int i:best.order)cout<<i+1<<' '<<best.team[i]+1<<' '<<best.start[i]<<'\n';
    cerr<<"count="<<best.order.size()<<" makespan="<<best.span<<" cost="<<best.cost<<" seed="<<seed<<" iterations="<<iterations<<'\n';
}
