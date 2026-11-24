#include "../common/scheduling.hpp"

using namespace std;
using namespace scheduling;

void checkpoint(const Schedule& schedule) {
    if (!getenv("SCHEDULING_PROGRESS")) return;
    cerr << "SCHEDULE_BEGIN\n";
    schedule.write(cerr);
    cerr << "SCHEDULE_END\n" << flush;
}

class AlnsSolver {
public:
    AlnsSolver(const Problem& problem, unsigned seed, double seconds = 0)
        : problem_(problem), random_(seed), decoder_(problem, random_),
          unassigned_(problem.jobCount, -1), seconds_(seconds),
          started_(chrono::steady_clock::now()) {
        if (const char* value = getenv("SCHEDULING_DEADLINE")) deadline_ = stod(value);
    }

    Schedule alns(int iterations) {
        Schedule current = greedy();
        Schedule best = current;
        checkpoint(best);
        vector<double> weights(9, 1.0);
        for (int iteration = 0; iteration < iterations && !current.order.empty() && !expired();
             ++iteration) {
            discrete_distribution<int> select(weights.begin(), weights.end());
            const int operation = select(random_);
            const int destroy = operation / 3;
            const auto repair = static_cast<RepairPolicy>(operation % 3);
            Schedule candidate = perturbAndRepair(current, destroy, repair);
            double reward = 0.1;
            if (candidate.betterThan(best)) {
                best = candidate;
                checkpoint(best);
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
    double seconds_;
    double deadline_ = 0;
    chrono::steady_clock::time_point started_;

    double elapsed() const {
        return chrono::duration<double>(chrono::steady_clock::now() - started_).count();
    }

    bool expired() const {
        if (deadline_ > 0) {
            timespec now;
            clock_gettime(CLOCK_MONOTONIC, &now);
            if (now.tv_sec + now.tv_nsec * 1e-9 >= deadline_) return true;
        }
        return seconds_ > 0 && elapsed() >= seconds_;
    }

    Schedule greedy() {
        return decoder_.decode(problem_.topologicalOrder, unassigned_);
    }

    bool accept(const Schedule& candidate, const Schedule& current, const Schedule& best,
                int iteration, int iterations) {
        const double progress = seconds_ > 0 ? min(1.0, elapsed() / seconds_)
                                            : double(iteration) / max(1, iterations);
        const double temperature = max(0.01, best.makespan * 0.05 * (1.0 - progress));
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
        const int iterations = argc > 1 ? stoi(argv[1]) : 5000;
        const unsigned seed = argc > 2 ? stoul(argv[2]) : 1;
        if (iterations < 0 || argc > 4) {
            throw runtime_error("Usage: alns [iterations >= 0] [seed] [seconds > 0]");
        }
        const double seconds = argc > 3 ? stod(argv[3]) : 0;
        if (argc > 3 && seconds <= 0) throw runtime_error("Seconds must be positive");
        const auto problem = Problem::read(cin);
        AlnsSolver solver(problem, seed, seconds);
        const auto schedule = solver.alns(iterations);
        schedule.write(cout);
        cerr << "count=" << schedule.order.size() << " makespan=" << schedule.makespan
                  << " cost=" << schedule.cost << " seed=" << seed
                  << " iterations=" << iterations << '\n';
    } catch (const exception& error) {
        cerr << error.what() << '\n';
        return 2;
    }
    return 0;
}
