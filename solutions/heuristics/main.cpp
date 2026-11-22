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
