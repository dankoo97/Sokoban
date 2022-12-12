import threading
from itertools import zip_longest
import sys
from sys import argv
from time import sleep
from typing import Type, Optional, Set
import os

from sokoban import Sokoban
import algorithms
import heuristic


def solve(game: Sokoban, algorithm: Type[algorithms.Algorithm],
          heuristics: Optional[Set[Type[heuristic.Heuristic]]] = None,
          **algorithmParameters) -> algorithms.SearchPattern:
    """
    Solves a game with a given algorithm
    :param game: The game instance
    :param algorithm: The given algorithm
    :param heuristics: The given heuristics to try
    :param algorithmParameters: Additional parameters to pass to the algorithm
    :return: The resulting game states from the algorithm, empty if unsolved
    """
    algorithmParameters = {} if algorithmParameters is None else algorithmParameters
    heuristics = heuristics if heuristics is not None else frozenset()
    return algorithms.SearchPattern(game, algorithm, heuristics, **algorithmParameters)


def animate(result, game, speed):
    """
    Animate a game
    :param game: An instance of the game
    :param result: The resulting solution path
    :param speed: Frames per second
    :return: A simple console animation of the game result
    """
    if not result:
        print(game)
        print("No solution")
        return

    for state in result:
        if os.name in ('nt', 'dos'):
            # windows
            os.system('cls')
        else:
            # linux
            os.system('clear')

        print(game.toStringWithState(state) + "\n\n")
        sleep(1/speed)


def handleCmdLineArgs(args):
    """
    Handles command line arguments
    :param args: sys.argv
    :return: Returns a dict that states how the program should be run
    """

    results = {
        'input': args[1],
        'output': None,
        'animate': False,
        'animationSpeed': 3,
        'algorithms': [],
        'compare': False,
        'maxFringe': -1,
    }

    for arg in args[2:]:
        arg = arg.lower()
        if '=' in arg:
            key, value = arg.split('=')

            if key == 'algorithm':
                results['algorithms'].append((value, set()))

            elif key in results:
                results[key] = value

        else:
            if arg == 'animate':
                results['animate'] = True

            elif arg == 'compare':
                results['compare'] = True

            else:
                results['algorithms'][-1][1].add(arg)

    return results


algorithmsDict = {
    'astar': algorithms.AStar,
    'bfs': algorithms.BFS,
    'dfs': algorithms.DFS,
    'greedybest': algorithms.GreedyBest,
}

heuristicDict = {
    'isstuck': heuristic.IsStuck,
    'manhattan': heuristic.Manhattan,
    'tobox': heuristic.DistanceToBox,
    'minmatch': heuristic.MinMatch,
}


if __name__ == '__main__':
    args = handleCmdLineArgs(argv)
    args['output'] = open(args['output'], 'w') if args['output'] is not None else sys.stdout
    with open(args['input'], "r") as gameFile:
        gameStr = gameFile.read()

    myGame = Sokoban.getStateFromString(gameStr)
    maxFringe = int(args['maxFringe'])

    solutions = {}
    animationLock = threading.Lock()

    for algo, options in args['algorithms']:
        algorithm = algorithmsDict[algo]
        bidirectional = 'bidirectional' in options
        heuristics = {heuristicDict[h] for h in options if h in heuristicDict}

        t = algorithms.SearchPattern(myGame, algorithm, heuristics, bidirectional, maxFringe)

        solutions[t.name] = t
        t.searchPattern()
        # solutions[t.name].start()

    # for t in solutions:
    #     solutions[t].join()

    if args['animate']:
        solutionStates = [solutions[sol].path for sol in solutions if solutions[sol].path]
        for state in solutionStates:
            animate(state, myGame, args['animationSpeed'])

    if args['compare']:
        # Take all completed paths
        solutionStates = [solutions[sol].path for sol in solutions if solutions[sol].path]
        for i, states in enumerate(zip_longest(*solutionStates, fillvalue=min(solutionStates, key=len)[-1])):
            print(i, file=args['output'])
            print(myGame.compareGameStates(states), end='\n\n', file=args['output'])

    for sol in solutions:
        print(file=args['output'])
        for name, val in solutions[sol].stats.items():
            print(f"{name}: {val}", file=args['output'])

    args['output'].close()

