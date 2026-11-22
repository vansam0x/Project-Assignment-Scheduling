#ifndef PROJECT_SCHEDULING_HPP
#define PROJECT_SCHEDULING_HPP

#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <numeric>
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace scheduling {

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
    std::vector<int> duration;
    std::vector<Time> release;
    std::vector<std::vector<int>> predecessors;
    std::vector<std::vector<int>> successors;
    std::vector<std::vector<AssignmentOption>> options;
    std::vector<bool> eligible;
    std::vector<int> topologicalOrder;

    static Problem read(std::istream& input) {
        Problem problem;
        int edgeCount;
        if (!(input >> problem.jobCount >> edgeCount) || problem.jobCount < 1 || edgeCount < 0) {
            throw std::runtime_error("Invalid job/edge count");
        }
        const int n = problem.jobCount;
        problem.predecessors.resize(n);
        problem.successors.resize(n);
        for (int edge = 0; edge < edgeCount; ++edge) {
            int before, after;
            if (!(input >> before >> after) || before < 1 || before > n || after < 1 || after > n) {
                throw std::runtime_error("Invalid precedence edge");
            }
            --before;
            --after;
            problem.predecessors[after].push_back(before);
            problem.successors[before].push_back(after);
        }
        problem.duration.resize(n);
        for (int& value : problem.duration) {
            if (!(input >> value) || value < 1) {
                throw std::runtime_error("Invalid duration");
            }
        }
        if (!(input >> problem.teamCount) || problem.teamCount < 1) {
            throw std::runtime_error("Invalid team count");
        }
        problem.release.resize(problem.teamCount);
        for (Time& value : problem.release) {
            if (!(input >> value) || value < 1) {
                throw std::runtime_error("Invalid release time");
            }
        }
        int optionCount;
        if (!(input >> optionCount) || optionCount < 0) {
            throw std::runtime_error("Invalid assignment count");
        }
        problem.options.resize(n);
        for (int index = 0; index < optionCount; ++index) {
            int job, team;
            Cost cost;
            if (!(input >> job >> team >> cost) || job < 1 || job > n || team < 1 ||
                team > problem.teamCount) {
                throw std::runtime_error("Invalid assignment");
            }
            problem.options[job - 1].push_back({team - 1, cost});
        }
        std::string extra;
        if (input >> extra) {
            throw std::runtime_error("Unexpected trailing input");
        }
        problem.selectEligibleJobs();
        return problem;
    }

private:
    void selectEligibleJobs() {
        std::vector<int> remaining(jobCount);
        std::queue<int> ready;
        eligible.assign(jobCount, false);
        for (int job = 0; job < jobCount; ++job) {
            remaining[job] = static_cast<int>(predecessors[job].size());
            if (remaining[job] == 0) {
                ready.push(job);
            }
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
            if (eligible[job]) {
                topologicalOrder.push_back(job);
            }
            for (int successor : successors[job]) {
                if (--remaining[successor] == 0) {
                    ready.push(successor);
                }
            }
        }
    }
};

struct Schedule {
    std::vector<int> order;
    std::vector<int> team;
    std::vector<Time> start;
    Time makespan = 0;
    Cost cost = 0;

    bool betterThan(const Schedule& other) const {
        return std::tie(makespan, cost) < std::tie(other.makespan, other.cost);
    }

    void write(std::ostream& output) const {
        output << order.size() << '\n';
        for (int job : order) {
            output << job + 1 << ' ' << team[job] + 1 << ' ' << start[job] << '\n';
        }
    }
};

enum class RepairPolicy { EarliestFinish, Cheapest, RandomizedFinish };

class ScheduleDecoder {
public:
    ScheduleDecoder(const Problem& problem, std::mt19937& random)
        : problem_(problem), random_(random) {}

    Schedule decode(const std::vector<int>& order, const std::vector<int>& preferredTeam,
                    RepairPolicy policy = RepairPolicy::EarliestFinish) {
        Schedule schedule;
        const int n = problem_.jobCount;
        schedule.team.assign(n, -1);
        schedule.start.assign(n, 0);
        std::vector<int> rank(n, n), remaining(n);
        std::vector<Time> finish(n, 0), available = problem_.release;
        for (int index = 0; index < static_cast<int>(order.size()); ++index) {
            rank[order[index]] = index;
        }
        using RankedJob = std::pair<int, int>;
        std::priority_queue<RankedJob, std::vector<RankedJob>, std::greater<RankedJob>> ready;
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
                earliest = std::max(earliest, finish[predecessor]);
            }
            auto bestScore = std::make_tuple(std::numeric_limits<Time>::max(), Cost{0}, 0);
            Time chosenStart = 0;
            Cost chosenCost = 0;
            int chosenTeam = -1;
            for (const auto& option : problem_.options[job]) {
                if (preferredTeam[job] >= 0 && preferredTeam[job] != option.team) {
                    continue;
                }
                const Time start = std::max(earliest, available[option.team]);
                Time primary = policy == RepairPolicy::Cheapest ? option.cost
                                                               : start + problem_.duration[job];
                if (policy == RepairPolicy::RandomizedFinish) {
                    primary += random_() % (problem_.duration[job] + 1);
                }
                const Cost secondary = policy == RepairPolicy::Cheapest
                                           ? start + problem_.duration[job]
                                           : option.cost;
                const auto score = std::make_tuple(primary, secondary, option.team);
                if (score < bestScore) {
                    bestScore = score;
                    chosenTeam = option.team;
                    chosenStart = start;
                    chosenCost = option.cost;
                }
            }
            if (chosenTeam < 0) {
                throw std::runtime_error("Decoder could not assign an eligible job");
            }
            schedule.team[job] = chosenTeam;
            schedule.start[job] = chosenStart;
            finish[job] = chosenStart + problem_.duration[job];
            available[chosenTeam] = finish[job];
            schedule.makespan = std::max(schedule.makespan, finish[job]);
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
    std::mt19937& random_;
};

class HeuristicSolver {
public:
    HeuristicSolver(const Problem& problem, unsigned seed)
        : problem_(problem), random_(seed), decoder_(problem, random_),
          unassigned_(problem.jobCount, -1) {}
    virtual ~HeuristicSolver() = default;
    virtual Schedule solve(int iterations) = 0;

protected:
    const Problem& problem_;
    std::mt19937 random_;
    ScheduleDecoder decoder_;
    std::vector<int> unassigned_;

    Schedule greedy() {
        return decoder_.decode(problem_.topologicalOrder, unassigned_);
    }

    bool accept(const Schedule& candidate, const Schedule& current, const Schedule& best,
                int iteration, int iterations) {
        const double temperature = std::max(
            0.01, best.makespan * 0.05 * (1.0 - double(iteration) / std::max(1, iterations)));
        double delta = double(candidate.makespan) - double(current.makespan);
        if (delta == 0) {
            delta = (double(candidate.cost) - double(current.cost)) /
                    std::max(1.0, std::abs(double(current.cost)));
        }
        return std::uniform_real_distribution<double>(0, 1)(random_) <
               std::exp(-std::max(0.0, delta) / temperature);
    }
};

class GreedySolver : public HeuristicSolver {
public:
    using HeuristicSolver::HeuristicSolver;
    Schedule solve(int /*iterations*/) override { return greedy(); }
};

class PrioritySolver : public HeuristicSolver {
public:
    PrioritySolver(const Problem& problem, unsigned seed, bool criticalPath)
        : HeuristicSolver(problem, seed), criticalPath_(criticalPath) {}

    Schedule solve(int /*iterations*/) override {
        std::vector<int> order = problem_.topologicalOrder;
        std::vector<Time> priority(problem_.jobCount, 0);
        for (auto it = order.rbegin(); it != order.rend(); ++it) {
            const int job = *it;
            priority[job] = problem_.duration[job];
            if (criticalPath_) {
                Time longestSuccessor = 0;
                for (int successor : problem_.successors[job]) {
                    if (problem_.eligible[successor]) {
                        longestSuccessor = std::max(longestSuccessor, priority[successor]);
                    }
                }
                priority[job] += longestSuccessor;
            }
        }
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) {
            return priority[a] > priority[b];
        });
        return decoder_.decode(order, unassigned_);
    }

private:
    bool criticalPath_;
};

class MultiStartSolver : public HeuristicSolver {
public:
    using HeuristicSolver::HeuristicSolver;
    Schedule solve(int iterations) override {
        Schedule best = greedy();
        std::vector<int> order = problem_.topologicalOrder;
        for (int iteration = 0; iteration < iterations && !order.empty(); ++iteration) {
            std::shuffle(order.begin(), order.end(), random_);
            const auto policy = iteration % 3 == 0 ? RepairPolicy::RandomizedFinish
                                                   : RepairPolicy::EarliestFinish;
            Schedule candidate = decoder_.decode(order, unassigned_, policy);
            if (candidate.betterThan(best)) {
                best = std::move(candidate);
            }
        }
        return best;
    }
};

class SimulatedAnnealingSolver : public HeuristicSolver {
public:
    using HeuristicSolver::HeuristicSolver;
    Schedule solve(int iterations) override {
        Schedule current = greedy();
        Schedule best = current;
        for (int iteration = 0; iteration < iterations && !current.order.empty(); ++iteration) {
            std::vector<int> order = current.order;
            std::vector<int> preferred = current.team;
            const auto a = random_() % order.size();
            const auto b = random_() % order.size();
            std::swap(order[a], order[b]);
            preferred[order[a]] = -1;
            preferred[order[b]] = -1;
            const auto policy = static_cast<RepairPolicy>(random_() % 3);
            Schedule candidate = decoder_.decode(order, preferred, policy);
            if (candidate.betterThan(best)) {
                best = candidate;
            }
            if (candidate.betterThan(current) ||
                accept(candidate, current, best, iteration, iterations)) {
                current = std::move(candidate);
            }
        }
        return best;
    }
};

class AlnsSolver : public HeuristicSolver {
public:
    using HeuristicSolver::HeuristicSolver;

    Schedule solve(int iterations) override {
        Schedule current = greedy();
        Schedule best = current;
        std::vector<double> weights(9, 1.0);
        for (int iteration = 0; iteration < iterations && !current.order.empty(); ++iteration) {
            std::discrete_distribution<int> select(weights.begin(), weights.end());
            const int operation = select(random_);
            const int destroy = operation / 3;
            const auto repair = static_cast<RepairPolicy>(operation % 3);
            Schedule candidate = perturbAndRepair(current, destroy, repair);
            double reward = 0.1;
            if (candidate.betterThan(best)) {
                best = candidate;
                reward = 8.0;
            }
            if (candidate.betterThan(current)) {
                current = candidate;
                reward = std::max(reward, 4.0);
            } else if (accept(candidate, current, best, iteration, iterations)) {
                current = candidate;
                reward = std::max(reward, 1.0);
            }
            weights[operation] = 0.9 * weights[operation] + 0.1 * reward;
        }
        return best;
    }

private:
    Cost assignmentCost(const Schedule& schedule, int job) const {
        Cost cost = std::numeric_limits<Cost>::max();
        for (const auto& option : problem_.options[job]) {
            if (option.team == schedule.team[job]) {
                cost = std::min(cost, option.cost);
            }
        }
        return cost;
    }

    Schedule perturbAndRepair(const Schedule& current, int destroy, RepairPolicy repair) {
        std::vector<int> removed = current.order;
        if (destroy == 0) {
            std::shuffle(removed.begin(), removed.end(), random_);
        } else if (destroy == 1) {
            std::stable_sort(removed.begin(), removed.end(), [&](int a, int b) {
                return current.start[a] + problem_.duration[a] >
                       current.start[b] + problem_.duration[b];
            });
        } else {
            std::stable_sort(removed.begin(), removed.end(), [&](int a, int b) {
                return assignmentCost(current, a) > assignmentCost(current, b);
            });
        }
        const double fraction = 0.1 + 0.4 * (random_() % 1000) / 999.0;
        const int count = std::max(1, static_cast<int>(current.order.size() * fraction));
        removed.resize(count);
        std::vector<bool> erased(problem_.jobCount, false);
        std::vector<int> preferred = current.team;
        std::vector<int> order;
        for (int job : removed) {
            erased[job] = true;
            preferred[job] = -1;
        }
        for (int job : current.order) {
            if (!erased[job]) {
                order.push_back(job);
            }
        }
        std::shuffle(removed.begin(), removed.end(), random_);
        for (int job : removed) {
            order.insert(order.begin() + random_() % (order.size() + 1), job);
        }
        return decoder_.decode(order, preferred, repair);
    }
};

} // namespace scheduling

#endif // PROJECT_SCHEDULING_HPP
