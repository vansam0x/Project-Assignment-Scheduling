#include "../common/scheduling.hpp"

using namespace std;
using namespace scheduling;

class Scheduler {
public:
    Scheduler(const Problem& problem, unsigned seed)
        : problem_(problem), random_(seed), decoder_(problem, random_),
          unassigned_(problem.jobCount, -1) {}

    Schedule solve(const string& algorithm, int iterations) {
        if (algorithm == "greedy") return greedy();
        if (algorithm == "lpt") return priority(false);
        if (algorithm == "critical_path") return priority(true);
        if (algorithm == "multistart") return multiStart(iterations);
        if (algorithm == "sa") return anneal(iterations);
        if (algorithm == "alns") return alns(iterations);
        throw runtime_error("Unknown algorithm: " + algorithm);
    }

    Schedule greedy() {
        return decoder_.decode(problem_.topologicalOrder, unassigned_);
    }

    Schedule priority(bool criticalPath) {
        vector<int> order = problem_.topologicalOrder;
        vector<Time> priority(problem_.jobCount, 0);
        for (auto it = order.rbegin(); it != order.rend(); ++it) {
            const int job = *it;
            priority[job] = problem_.duration[job];
            if (criticalPath) {
                Time longestSuccessor = 0;
                for (int successor : problem_.successors[job]) {
                    if (problem_.eligible[successor]) {
                        longestSuccessor = max(longestSuccessor, priority[successor]);
                    }
                }
                priority[job] += longestSuccessor;
            }
        }
        stable_sort(order.begin(), order.end(), [&](int a, int b) {
            return priority[a] > priority[b];
        });
        return decoder_.decode(order, unassigned_);
    }

    Schedule multiStart(int iterations) {
        Schedule best = greedy();
        vector<int> order = problem_.topologicalOrder;
        for (int iteration = 0; iteration < iterations && !order.empty(); ++iteration) {
            shuffle(order.begin(), order.end(), random_);
            const auto policy = iteration % 3 == 0 ? RepairPolicy::RandomizedFinish
                                                   : RepairPolicy::EarliestFinish;
            Schedule candidate = decoder_.decode(order, unassigned_, policy);
            if (candidate.betterThan(best)) best = move(candidate);
        }
        return best;
    }

    Schedule anneal(int iterations) {
        Schedule current = greedy();
        Schedule best = current;
        for (int iteration = 0; iteration < iterations && !current.order.empty(); ++iteration) {
            vector<int> order = current.order;
            vector<int> preferred = current.team;
            const auto a = random_() % order.size();
            const auto b = random_() % order.size();
            swap(order[a], order[b]);
            preferred[order[a]] = -1;
            preferred[order[b]] = -1;
            const auto policy = static_cast<RepairPolicy>(random_() % 3);
            Schedule candidate = decoder_.decode(order, preferred, policy);
            if (candidate.betterThan(best)) best = candidate;
            if (candidate.betterThan(current) ||
                accept(candidate, current, best, iteration, iterations)) {
                current = move(candidate);
            }
        }
        return best;
    }

    Schedule alns(int iterations) {
        Schedule current = greedy();
        Schedule best = current;
        vector<double> weights(9, 1.0);
        for (int iteration = 0; iteration < iterations && !current.order.empty(); ++iteration) {
            discrete_distribution<int> select(weights.begin(), weights.end());
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
                reward = max(reward, 4.0);
            } else if (accept(candidate, current, best, iteration, iterations)) {
                current = candidate;
                reward = max(reward, 1.0);
            }
            weights[operation] = 0.9 * weights[operation] + 0.1 * reward;
        }
        return best;
    }

private:
    const Problem& problem_;
    mt19937 random_;
    ScheduleDecoder decoder_;
    vector<int> unassigned_;

    bool accept(const Schedule& candidate, const Schedule& current, const Schedule& best,
                int iteration, int iterations) {
        const double temperature = max(
            0.01, best.makespan * 0.05 * (1.0 - double(iteration) / max(1, iterations)));
        double delta = double(candidate.makespan) - double(current.makespan);
        if (delta == 0) {
            delta = (double(candidate.cost) - double(current.cost)) /
                    max(1.0, abs(double(current.cost)));
        }
        return uniform_real_distribution<double>(0, 1)(random_) <
               exp(-max(0.0, delta) / temperature);
    }

    Cost assignmentCost(const Schedule& schedule, int job) const {
        Cost cost = numeric_limits<Cost>::max();
        for (const auto& option : problem_.options[job]) {
            if (option.team == schedule.team[job]) cost = min(cost, option.cost);
        }
        return cost;
    }

    Schedule perturbAndRepair(const Schedule& current, int destroy, RepairPolicy repair) {
        vector<int> removed = current.order;
        if (destroy == 0) {
            shuffle(removed.begin(), removed.end(), random_);
        } else if (destroy == 1) {
            stable_sort(removed.begin(), removed.end(), [&](int a, int b) {
                return current.start[a] + problem_.duration[a] >
                       current.start[b] + problem_.duration[b];
            });
        } else {
            stable_sort(removed.begin(), removed.end(), [&](int a, int b) {
                return assignmentCost(current, a) > assignmentCost(current, b);
            });
        }
        const double fraction = 0.1 + 0.4 * (random_() % 1000) / 999.0;
        const int count = max(1, static_cast<int>(current.order.size() * fraction));
        removed.resize(count);
        vector<bool> erased(problem_.jobCount, false);
        vector<int> preferred = current.team;
        vector<int> order;
        for (int job : removed) {
            erased[job] = true;
            preferred[job] = -1;
        }
        for (int job : current.order) {
            if (!erased[job]) order.push_back(job);
        }
        shuffle(removed.begin(), removed.end(), random_);
        for (int job : removed) {
            order.insert(order.begin() + random_() % (order.size() + 1), job);
        }
        return decoder_.decode(order, preferred, repair);
    }
};

int main(int argc, char** argv) {
    try {
        if (argc < 2 || argc > 4) {
            throw runtime_error("Usage: heuristics algorithm [iterations >= 0] [seed]");
        }
        const string algorithm = argv[1];
        const int iterations = argc > 2 ? stoi(argv[2]) : 2000;
        const unsigned seed = argc > 3 ? stoul(argv[3]) : 1;
        if (iterations < 0) {
            throw runtime_error("Iterations must be nonnegative");
        }
        const auto problem = Problem::read(cin);
        Scheduler solver(problem, seed);
        const auto schedule = solver.solve(algorithm, iterations);
        schedule.write(cout);
        cerr << "algorithm=" << algorithm << " count=" << schedule.order.size()
                  << " makespan=" << schedule.makespan << " cost=" << schedule.cost
                  << " seed=" << seed << " iterations=" << iterations << '\n';
    } catch (const exception& error) {
        cerr << error.what() << '\n';
        return 2;
    }
    return 0;
}
