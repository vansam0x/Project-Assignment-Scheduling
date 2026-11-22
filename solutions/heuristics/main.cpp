#include "../common/scheduling.hpp"

#include <memory>

std::unique_ptr<scheduling::HeuristicSolver> makeSolver(const std::string& algorithm,
                                                      const scheduling::Problem& problem,
                                                      unsigned seed) {
    using namespace scheduling;
    if (algorithm == "greedy") {
        return std::make_unique<GreedySolver>(problem, seed);
    }
    if (algorithm == "lpt" || algorithm == "critical_path") {
        return std::make_unique<PrioritySolver>(problem, seed, algorithm == "critical_path");
    }
    if (algorithm == "multistart") {
        return std::make_unique<MultiStartSolver>(problem, seed);
    }
    if (algorithm == "sa") {
        return std::make_unique<SimulatedAnnealingSolver>(problem, seed);
    }
    if (algorithm == "alns") {
        return std::make_unique<AlnsSolver>(problem, seed);
    }
    throw std::runtime_error("Unknown algorithm: " + algorithm);
}

int main(int argc, char** argv) {
    try {
        if (argc < 2 || argc > 4) {
            throw std::runtime_error("Usage: heuristics algorithm [iterations >= 0] [seed]");
        }
        const std::string algorithm = argv[1];
        const int iterations = argc > 2 ? std::stoi(argv[2]) : 2000;
        const unsigned seed = argc > 3 ? std::stoul(argv[3]) : 1;
        if (iterations < 0) {
            throw std::runtime_error("Iterations must be nonnegative");
        }
        const auto problem = scheduling::Problem::read(std::cin);
        auto solver = makeSolver(algorithm, problem, seed);
        const auto schedule = solver->solve(iterations);
        schedule.write(std::cout);
        std::cerr << "algorithm=" << algorithm << " count=" << schedule.order.size()
                  << " makespan=" << schedule.makespan << " cost=" << schedule.cost
                  << " seed=" << seed << " iterations=" << iterations << '\n';
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
    return 0;
}
