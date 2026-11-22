#ifndef PROJECT_SCHEDULING_HPP
#define PROJECT_SCHEDULING_HPP

#include <bits/stdc++.h>

namespace scheduling {

using namespace std;

using Time = long long;
using Cost = long long;

struct AssignmentOption {
    int team;
    Cost cost;
};

class Problem {
public:
    int jobCount = 0;
    int teamCount = 0;
    vector<int> duration;
    vector<Time> release;
    vector<vector<int>> predecessors;
    vector<vector<int>> successors;
    vector<vector<AssignmentOption>> options;
    vector<bool> eligible;
    vector<int> topologicalOrder;

    static Problem read(istream& input) {
        Problem problem;
        int edgeCount;
        if (!(input >> problem.jobCount >> edgeCount) || problem.jobCount < 1 || edgeCount < 0) {
            throw runtime_error("Invalid job/edge count");
        }
        const int n = problem.jobCount;
        problem.predecessors.resize(n);
        problem.successors.resize(n);
        for (int edge = 0; edge < edgeCount; ++edge) {
            int before, after;
            if (!(input >> before >> after) || before < 1 || before > n || after < 1 || after > n) {
                throw runtime_error("Invalid precedence edge");
            }
            --before;
            --after;
            problem.predecessors[after].push_back(before);
            problem.successors[before].push_back(after);
        }
        problem.duration.resize(n);
        for (int& value : problem.duration) {
            if (!(input >> value) || value < 1) throw runtime_error("Invalid duration");
        }
        if (!(input >> problem.teamCount) || problem.teamCount < 1) {
            throw runtime_error("Invalid team count");
        }
        problem.release.resize(problem.teamCount);
        for (Time& value : problem.release) {
            if (!(input >> value) || value < 1) throw runtime_error("Invalid release time");
        }
        int optionCount;
        if (!(input >> optionCount) || optionCount < 0) {
            throw runtime_error("Invalid assignment count");
        }
        problem.options.resize(n);
        for (int index = 0; index < optionCount; ++index) {
            int job, team;
            Cost cost;
            if (!(input >> job >> team >> cost) || job < 1 || job > n || team < 1 ||
                team > problem.teamCount) {
                throw runtime_error("Invalid assignment");
            }
            problem.options[job - 1].push_back({team - 1, cost});
        }
        string extra;
        if (input >> extra) throw runtime_error("Unexpected trailing input");
        problem.selectEligibleJobs();
        return problem;
    }

private:
    void selectEligibleJobs() {
        vector<int> remaining(jobCount);
        queue<int> ready;
        eligible.assign(jobCount, false);
        for (int job = 0; job < jobCount; ++job) {
            remaining[job] = static_cast<int>(predecessors[job].size());
            if (remaining[job] == 0) ready.push(job);
        }
        // Unvisited cycles and their descendants cannot be selected. Missing
        // assignment options propagate exclusion along the topological traversal.
        while (!ready.empty()) {
            const int job = ready.front();
            ready.pop();
            eligible[job] = !options[job].empty();
            for (int predecessor : predecessors[job]) {
                eligible[job] = eligible[job] && eligible[predecessor];
            }
            if (eligible[job]) topologicalOrder.push_back(job);
            for (int successor : successors[job]) {
                if (--remaining[successor] == 0) ready.push(successor);
            }
        }
    }
};

struct Schedule {
    vector<int> order;
    vector<int> team;
    vector<Time> start;
    Time makespan = 0;
    Cost cost = 0;

    bool betterThan(const Schedule& other) const {
        return tie(makespan, cost) < tie(other.makespan, other.cost);
    }

    void write(ostream& output) const {
        output << order.size() << '\n';
        for (int job : order) {
            output << job + 1 << ' ' << team[job] + 1 << ' ' << start[job] << '\n';
        }
    }
};

enum class RepairPolicy { EarliestFinish, Cheapest, RandomizedFinish };

class ScheduleDecoder {
public:
    ScheduleDecoder(const Problem& problem, mt19937& random)
        : problem_(problem), random_(random) {}

    Schedule decode(const vector<int>& order, const vector<int>& preferredTeam,
                    RepairPolicy policy = RepairPolicy::EarliestFinish) {
        Schedule schedule;
        const int n = problem_.jobCount;
        schedule.team.assign(n, -1);
        schedule.start.assign(n, 0);
        vector<int> rank(n, n), remaining(n);
        vector<Time> finish(n, 0), available = problem_.release;
        for (int index = 0; index < static_cast<int>(order.size()); ++index) {
            rank[order[index]] = index;
        }
        using RankedJob = pair<int, int>;
        priority_queue<RankedJob, vector<RankedJob>, greater<RankedJob>> ready;
        for (int job : problem_.topologicalOrder) {
            remaining[job] = static_cast<int>(problem_.predecessors[job].size());
            if (remaining[job] == 0) {
                ready.push({rank[job], job});
            }
        }
        while (!ready.empty()) {
            const int job = ready.top().second;
            ready.pop();
            Time earliest = 0;
            for (int predecessor : problem_.predecessors[job]) {
                earliest = max(earliest, finish[predecessor]);
            }
            auto bestScore = make_tuple(numeric_limits<Time>::max(), Cost{0}, 0);
            Time chosenStart = 0;
            Cost chosenCost = 0;
            int chosenTeam = -1;
            for (const auto& option : problem_.options[job]) {
                if (preferredTeam[job] >= 0 && preferredTeam[job] != option.team) continue;
                const Time start = max(earliest, available[option.team]);
                Time primary = policy == RepairPolicy::Cheapest ? option.cost
                                                               : start + problem_.duration[job];
                if (policy == RepairPolicy::RandomizedFinish) {
                    primary += random_() % (problem_.duration[job] + 1);
                }
                const Cost secondary = policy == RepairPolicy::Cheapest
                                           ? start + problem_.duration[job]
                                           : option.cost;
                const auto score = make_tuple(primary, secondary, option.team);
                if (score < bestScore) {
                    bestScore = score;
                    chosenTeam = option.team;
                    chosenStart = start;
                    chosenCost = option.cost;
                }
            }
            if (chosenTeam < 0) {
                throw runtime_error("Decoder could not assign an eligible job");
            }
            schedule.team[job] = chosenTeam;
            schedule.start[job] = chosenStart;
            finish[job] = chosenStart + problem_.duration[job];
            available[chosenTeam] = finish[job];
            schedule.makespan = max(schedule.makespan, finish[job]);
            schedule.cost += chosenCost;
            schedule.order.push_back(job);
            for (int successor : problem_.successors[job]) {
                if (problem_.eligible[successor] && --remaining[successor] == 0) {
                    ready.push({rank[successor], successor});
                }
            }
        }
        return schedule;
    }

private:
    const Problem& problem_;
    mt19937& random_;
};


} // namespace scheduling

#endif // PROJECT_SCHEDULING_HPP
