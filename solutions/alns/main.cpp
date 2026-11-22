#include "../common/scheduling.hpp"

int main(int argc, char** argv) {
    try {
        const int iterations = argc > 1 ? std::stoi(argv[1]) : 5000;
        const unsigned seed = argc > 2 ? std::stoul(argv[2]) : 1;
        if (iterations < 0 || argc > 3) {
            throw std::runtime_error("Usage: alns [iterations >= 0] [seed]");
        }
        const auto problem = scheduling::Problem::read(std::cin);
        scheduling::AlnsSolver solver(problem, seed);
        const auto schedule = solver.solve(iterations);
        schedule.write(std::cout);
        std::cerr << "count=" << schedule.order.size() << " makespan=" << schedule.makespan
                  << " cost=" << schedule.cost << " seed=" << seed
                  << " iterations=" << iterations << '\n';
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
    return 0;
}
