import threading
from abc import ABC, abstractmethod
from datetime import datetime
from heapq import heappush, heappop
from math import factorial
from typing import Optional, Type, Tuple, FrozenSet, Set

from heuristic import Heuristic, IsStuck
from sokoban import Sokoban, GameState


class Algorithm(ABC):
    name = "Base"

    def __init__(self, game: Sokoban, heuristics: FrozenSet[Type[Heuristic]], reverse: Optional[bool] = None):
        f"""
        The {self.name} algorithm
        :param game: An instance of the game
        :param heuristics: The used heuristics
        :param reverse: Whether to reverse and find the starting position from the solution
        """

        self.game = game
        if bool(reverse):
            self.boxes = game.storage
            self.storage = game.initialGameState.boxes
        else:
            self.boxes = game.initialGameState.boxes
            self.storage = game.storage

        self.robot = game.initialGameState.robot
        self.obstacles = game.obstacles
        self.heuristics = {
            h: h(robot=self.robot, boxes=self.boxes, storage=self.storage, obstacles=self.obstacles)
            for h in heuristics
        }
        self.fringe = []

    @abstractmethod
    def push(self, val: GameState) -> None:
        pass

    @abstractmethod
    def pop(self) -> GameState:
        pass

    @abstractmethod
    def peek(self) -> Tuple[int, GameState]:
        pass

    def __bool__(self):
        return bool(self.fringe)

    def __len__(self):
        return len(self.fringe)


class BFS(Algorithm):
    name = "Breadth First Search"

    def push(self, val: GameState) -> None:
        self.fringe.append(val)

    def pop(self) -> GameState:
        return self.fringe.pop(0)

    def peek(self) -> Tuple[int, GameState]:
        return self.fringe[0].pathLen, self.fringe[0]


class DFS(Algorithm):
    name = "Depth First Search"

    def push(self, val: GameState) -> None:
        self.fringe.append(val)

    def pop(self) -> GameState:
        return self.fringe.pop(-1)

    def peek(self) -> Tuple[int, GameState]:
        return self.fringe[-1].pathLen, self.fringe[-1]


class GreedyBest(Algorithm):
    name = "Greedy Best Search"

    def push(self, val: GameState) -> None:
        hSum = 0
        for h in self.heuristics.values():
            h.update(robot=val.robot, boxes=val.boxes, storage=self.storage, obstacles=self.obstacles)
            hSum += int(h)

        heappush(self.fringe, (hSum, val))

    def pop(self) -> GameState:
        _, state = heappop(self.fringe)
        return state

    def peek(self) -> Tuple[int, GameState]:
        return self.fringe[0]


class AStar(Algorithm):
    name = "A*"

    def push(self, val: GameState) -> None:
        hSum = 0
        for h in self.heuristics.values():
            h.update(robot=val.robot, boxes=val.boxes, storage=self.storage, obstacles=self.obstacles)
            hSum += int(h)

        heappush(self.fringe, (hSum + val.pathLen, val))

    def pop(self):
        _, state = heappop(self.fringe)
        return state

    def peek(self) -> Tuple[int, GameState]:
        return self.fringe[0]


class SearchPattern(threading.Thread):

    def __init__(self, game: Sokoban, algorithm: Type[Algorithm], heuristics: Set[Type[Heuristic]],
                 bidirectional: bool = None, maxFringeSize: int = None) -> None:
        """
        A modular search pattern
        :param game: An instance of Sokoban
        :param algorithm: The algorithm used (ie. A*)
        :param heuristics: The heuristics used if any
        :param bidirectional: Whether to search bidirectionally
        :param maxFringeSize: A max fringe size, -1 indicates infinite
        :return: A list of game states indicated the found solution
        """
        super().__init__(
            target=self.searchPattern,
        )
        self.game = game
        self.algorithm = algorithm
        self.heuristics = frozenset(heuristics)
        self.bidirectional = bool(bidirectional)
        self.maxFringeSize = -1 if maxFringeSize is None else maxFringeSize
        self._return = None
        self.path = []
        self.stats = {}

    def finish(self, start):
        self.stats['Total Time'] = datetime.now() - start
        self.stats['Solved'] = True
        self.stats['Path Length'] = len(self.path)

        self.stats['Average Time per Unique State'] = self.stats['Total Time'] / self.stats['Unique States Searched']

    def searchPattern(self):
        start = datetime.now()
        self.stats = {
            'Solved': False,
            'Unique States Searched': 0,
            'Upper Bound of Unique States': (len(self.game.storage) + 1) * factorial((self.game.X - 1) * (self.game.Y - 1)) //
                                            (factorial(len(self.game.storage) + 1)
                                             * factorial((self.game.X - 1) * (self.game.Y - 1) - (len(self.game.storage) + 1))),
            'Max Fringe Size': 1,
            'Total Time': 0,
            'Path Length': 0,
            'Used Algorithm': self.algorithm.name,
            'Used Heuristic': ', '.join(h.name for h in self.heuristics),
            'Directionality': "One-directional" if not self.bidirectional else "Bidirectional",
        }

        directions = {
            'forward': (self.algorithm(self.game, self.heuristics), {}),
        }
        directions['forward'][0].push(self.game.initialGameState)

        checked = {}

        if self.bidirectional:
            # Backwards cannot ever actually get stuck in a corner, Distance to box is troublesome backwards
            for solution in self.game.solutions():
                directions[str(solution)] = (self.algorithm(self.game, self.heuristics - {IsStuck}, reverse=True), {})
                directions[str(solution)][0].push(solution)

        try:
            while all((
                    directions['forward'][0],
                    not self.bidirectional or len(directions) > 1,
                    self.maxFringeSize == -1 or sum(len(directions[d][0]) for d in directions) < self.maxFringeSize
            )):

                removed = set()
                for d in directions:
                    try:
                        current = directions[d][0].pop()
                        while current in directions[d][1] and directions[d][1][current] < current.pathLen:
                            current = directions[d][0].pop()
                    except IndexError:
                        removed.add(d)
                        continue

                    self.stats['Unique States Searched'] += 1

                    if len(directions) == 1 and self.game.isWon(current):
                        self.path = tuple(current.getPath())

                        self.finish(start)
                        return

                    if current in checked and any((
                            d == 'forward' and current not in directions['forward'][1],
                            d != 'forward' and current in directions['forward'][1],
                    )):

                        if d == 'forward':
                            self.path = (*current.getPath()[:-1], *checked[current].getPath())
                        else:
                            self.path = (*checked[current].getPath()[:-1], *current.getPath())

                        self.finish(start)
                        return

                    if current in checked:
                        checked[current] = min(current, checked[current], key=lambda state: state.pathLen)
                    else:
                        checked[current] = current

                    directions[d][1][current] = current.pathLen

                    for successor in self.game.successors(current):
                        if successor not in directions[d][1]:
                            directions[d][0].push(successor)

                    self.stats['Max Fringe Size'] = max((
                        sum(len(directions[other][0]) for other in directions),
                        self.stats['Max Fringe Size']
                    ))
                for d in removed:
                    del directions[d]
        except KeyboardInterrupt:
            pass
        finally:
            # If we quit early or complete without solving
            if not self.stats['Total Time']:
                self.stats['Total Time'] = datetime.now() - start

            self.stats['Average Time per Unique State'] = self.stats['Total Time'] / self.stats[
                'Unique States Searched']


