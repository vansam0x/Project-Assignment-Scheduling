"""Run actual OR-Tools/SCIP, greedy and ALNS experiments on every stress instance."""
import sys

from benchmark import main


if __name__ == '__main__':
    main(['--suite', 'stress', *sys.argv[1:]])
