import copy
from typing import Union, Set, FrozenSet, Optional
import numpy as np

import algorithms
import sokoban
from coord import Coord
from sokoban import COMPASS

DEBUG = False


class Heuristic:
    name = "Dijkstra"
    description = "Assigns a uniform value to all game states"

    def __init__(self, robot: Coord, boxes: Union[Set, FrozenSet], storage: Union[Set, FrozenSet],
                 obstacles: Union[Set, FrozenSet]) -> None:
        """
        A uniform heuristic for Sokoban
        :param robot: The coord of the robot
        :param boxes: The set of boxes
        :param storage: The set of storage spaces
        :param obstacles: The set of obstacles
        """
        self.robot = robot
        self.boxes = boxes
        self.storage = storage
        self.obstacles = obstacles
        self.val = 0
        self.distanceHandler = DistanceHandler(self.storage)

    def __int__(self) -> int:
        return int(self.val)

    def update(self, robot: Optional[Coord] = None, boxes: Optional[Union[Set, FrozenSet]] = None,
               storage: Optional[Union[Set, FrozenSet]] = None, obstacles: Optional[Union[Set, FrozenSet]] = None):

        self._updateValues(robot, boxes, storage, obstacles)
        self.val = 0

    def _updateValues(self, robot: Optional[Coord] = None, boxes: Optional[Union[Set, FrozenSet]] = None,
                      storage: Optional[Union[Set, FrozenSet]] = None,
                      obstacles: Optional[Union[Set, FrozenSet]] = None):

        self.robot = self.robot if robot is None else robot
        self.boxes = self.boxes if boxes is None else boxes
        self.storage = self.storage if storage is None else storage
        self.obstacles = self.obstacles if obstacles is None else obstacles
        self.distanceHandler.addBox(*self.boxes)


class Manhattan(Heuristic):
    name = "Manhattan Distance"
    description = "Assigns a value equal to the sum of distance between each box and its closest storage spot"

    def __init__(self, robot: Coord, boxes: Union[Set, FrozenSet], storage: Union[Set, FrozenSet],
                 obstacles: Union[Set, FrozenSet]):

        super().__init__(robot, boxes, storage, obstacles)

        # Storage does not move so just keep track of the shortest path from any location
        self.distances = {}

        self.realDistance = RealDistance(sokoban.Sokoban(self.robot, self.boxes, storage, self.obstacles))

    def update(self, robot: Optional[Coord] = None, boxes: Optional[Union[Set, FrozenSet]] = None,
               storage: Optional[Union[Set, FrozenSet]] = None, obstacles: Optional[Union[Set, FrozenSet]] = None):

        self._updateValues(robot, boxes, storage, obstacles)

        for box in self.boxes - self.distances.keys():
            self.distances[box] = min(self.distanceHandler[box].values())

        self.val = sum(self.distances[box] for box in self.boxes)


class IsStuck(Heuristic):
    name = "Prevent Stuck Boxes"
    description = "Identifies \"stuck\" states and assigns an arbitrarily large value to them"

    maxValue = 9999999

    def __init__(self, robot: Coord, boxes: Union[Set, FrozenSet], storage: Union[Set, FrozenSet],
                 obstacles: Union[Set, FrozenSet]):

        super().__init__(robot, boxes, storage, obstacles)

        # Keep track of checked positions
        self.stuckSpots = set()
        self.checked = set()

    def update(self, robot: Optional[Coord] = None, boxes: Optional[Union[Set, FrozenSet]] = None,
               storage: Optional[Union[Set, FrozenSet]] = None, obstacles: Optional[Union[Set, FrozenSet]] = None):

        self._updateValues(robot, boxes, storage, obstacles)

        if self.boxes & self.stuckSpots:
            self.val = IsStuck.maxValue
            return

        for box in self.boxes - self.checked:
            obstacleTracker = set()
            for direction, coord in COMPASS.items():
                if box + coord in self.obstacles:
                    obstacleTracker.add(direction)

            if all((
                    box not in self.storage,
                    any(obstacleTracker >= corner for corner in (set('NE'), set('NW'), set('SE'), set('SW')))
            )):
                self.val = IsStuck.maxValue
                self.stuckSpots.add(box)
                self.checked.add(box)
                return
            else:
                self.checked.add(box)

        self.val = 0

    def stuckStates(self):
        return self.stuckSpots


class DistanceToBox(Heuristic):
    name = "Distance from Robot to nearest Box"
    description = "Assigns a value equal to the distance from the robot to the nearest box"

    def update(self, robot: Optional[Coord] = None, boxes: Optional[Union[Set, FrozenSet]] = None,
               storage: Optional[Union[Set, FrozenSet]] = None, obstacles: Optional[Union[Set, FrozenSet]] = None):

        self._updateValues(robot, boxes, storage, obstacles)
        self.val = min(self.robot.distance(box) for box in self.boxes) - 1


class MinMatch(Heuristic):
    name = "Minimum matching from boxes to storage"
    description = "Match boxes to storage with the minimum total distance using the Hungarian Algorithm"
    source = "https://en.wikipedia.org/wiki/Hungarian_algorithm"

    def __init__(self, robot: Coord, boxes: Union[Set, FrozenSet], storage: Union[Set, FrozenSet],
                 obstacles: Union[Set, FrozenSet]):

        super().__init__(robot, boxes, storage, obstacles)
        self.storage = tuple(self.storage)
        self.boxClose = {}
        self.solved = {}

        self.realDistance = RealDistance(sokoban.Sokoban(self.robot, self.boxes, storage, self.obstacles))

    def _updateValues(self, robot: Optional[Coord] = None, boxes: Optional[Union[Set, FrozenSet]] = None,
                      storage: Optional[Union[Set, FrozenSet]] = None,
                      obstacles: Optional[Union[Set, FrozenSet]] = None):
        super()._updateValues(robot, boxes, None, obstacles)

        for box in self.boxes - self.boxClose.keys():
            # Store the boxes and storage as rows and perform the first step and store the value
            # self.boxClose[box] = np.array([self.realDistance.getVal(robot, box, store) for store in self.storage])
            self.boxClose[box] = np.array([box.distance(store) for store in self.storage])

    def __coverMinimum(self, boxStorageMatrix):
        starred, primed, rows, cols = set(), set(), set(), set()
        starredRows, starredCols, primedRows, primedCols = {}, {}, {}, {}

        while len(starred) < len(self.storage):
            restart = False

            for rowNum, row in enumerate(boxStorageMatrix):
                for colNum, value in enumerate(row):
                    if Coord(colNum, rowNum) in starred and rowNum not in rows:
                        cols.add(colNum)

                        if DEBUG:
                            print()
                            print('eep')
                            print(f"cols: {cols}, rows: {rows}")
                            print(f"starred: {starred}")
                            print(f"primed: {primed}")
                            print(boxStorageMatrix)

                    elif value == 0 and rowNum not in starredRows and colNum not in starredCols:
                        star = Coord(colNum, rowNum)
                        starred.add(star)
                        starredCols[star.x] = star
                        starredRows[star.y] = star
                        cols.add(star.x)

                        if DEBUG:
                            print()
                            print('a')
                            print(f"cols: {cols}, rows: {rows}")
                            print(f"starred: {starred}")
                            print(f"primed: {primed}")
                            print(boxStorageMatrix)

            for rowNum, row in enumerate(boxStorageMatrix):
                for colNum, value in enumerate(row):
                    if value == 0 and rowNum in starredRows and colNum not in cols and rowNum not in rows:
                        prime = Coord(colNum, rowNum)
                        primed.add(prime)
                        primedCols[prime.x] = prime
                        primedRows[prime.y] = prime

                        cols.remove(starredRows[prime.y].x)
                        rows.add(prime.y)

                        if DEBUG:
                            print()
                            print('b')
                            print(f"cols: {cols}, rows: {rows}")
                            print(f"starred: {starred}")
                            print(f"primed: {primed}")
                            print(boxStorageMatrix)

                        restart = True
                        break

                    elif value == 0 and rowNum not in starredRows and colNum not in cols and rowNum not in rows:
                        prime = Coord(colNum, rowNum)
                        primed.add(prime)
                        primedCols[prime.x] = prime
                        primedRows[prime.y] = prime

                        zeros = {prime}
                        while prime.x in starredCols:
                            star = starredCols[prime.x]
                            prime = primedRows[star.y]
                            zeros |= {star, prime}

                        for zero in zeros:
                            if zero in starred:
                                starred.remove(zero)
                            else:
                                primed.remove(zero)
                                starred.add(zero)
                                starredCols[zero.x] = zero
                                starredRows[zero.y] = zero

                        rows, cols = set(), set()

                        if DEBUG:
                            print()
                            print('c')
                            print(f"cols: {cols}, rows: {rows}")
                            print(f"starred: {starred}")
                            print(f"primed: {primed}")
                            print(boxStorageMatrix)

                        restart = True
                        break
                if restart:
                    break

            if len(starred) == len(self.storage):
                return starred

            if restart:
                continue

            smallest = 9999999999
            for rowNum, row in enumerate(boxStorageMatrix):
                for colNum, value in enumerate(row):
                    if rowNum not in rows and colNum not in cols:
                        smallest = min((smallest, value))

            if DEBUG:
                print(starred)
                print(cols, rows)
                print(smallest)

            for rowNum, row in enumerate(boxStorageMatrix):
                for colNum, value in enumerate(row):
                    if rowNum in rows and colNum in cols:
                        boxStorageMatrix[rowNum, colNum] += smallest
                    elif rowNum not in rows and colNum not in cols:
                        boxStorageMatrix[rowNum, colNum] -= smallest

            starred, primed, cols, rows = set(), set(), set(), set()
            starredRows, starredCols, primedRows, primedCols = {}, {}, {}, {}

            if DEBUG:
                print()
                print('d')
                print(smallest)
                print(boxStorageMatrix)

        return starred

    def update(self, robot: Optional[Coord] = None, boxes: Optional[Union[Set, FrozenSet]] = None,
               storage: Optional[Union[Set, FrozenSet]] = None, obstacles: Optional[Union[Set, FrozenSet]] = None):

        self._updateValues(robot=robot, boxes=boxes, storage=storage, obstacles=obstacles)

        if frozenset(self.boxes) in self.solved:
            self.val = self.solved[frozenset(self.boxes)]
            return

        boxStorageMatrix = None

        # Create a matrix
        for box in self.boxes:
            if boxStorageMatrix is None:
                boxStorageMatrix = self.boxClose[box]
            else:
                boxStorageMatrix = np.vstack((boxStorageMatrix, self.boxClose[box]))

        original = copy.deepcopy(boxStorageMatrix)

        # reduce rows
        for row in boxStorageMatrix:
            row -= row.min()

        if DEBUG:
            print()
            print()
            print(original)
            print(boxStorageMatrix)

        # Reduce columns
        for i in range(len(self.storage)):
            delta = boxStorageMatrix[..., i].min()
            boxStorageMatrix[..., i] -= delta

        if DEBUG:
            print(boxStorageMatrix)

        starred = self.__coverMinimum(boxStorageMatrix)

        self.val = 0
        for star in starred:
            self.val += original[star.y, star.x]
        self.solved[self.boxes] = self.val


class DistanceHandler:
    def __init__(self, storage: FrozenSet[Coord]):
        self.storage = storage
        self.distances = {}

    def addBox(self, *boxes):
        for box in boxes:
            if box not in self.distances:
                self.distances[box] = {store: box.distance(store) for store in self.storage}

    def __getitem__(self, item):
        return self.distances[item]


class RealDistance:
    def __init__(self, game: sokoban.Sokoban):
        self.obstacles = game.obstacles
        self.storage = game.storage
        self.miniSolve = {}

    def getVal(self, robot, box, store):
        if (robot, box, store) in self.miniSolve:
            return self.miniSolve[(robot, box, store)]

        game = sokoban.Sokoban(robot, {box}, {store}, self.obstacles)
        result = algorithms.SearchPattern(game, algorithms.BFS, set(), True)
        result.searchPattern()
        if not result.stats['Solved']:
            self.miniSolve[(robot, box, store)] = 999999
            return self.miniSolve[(robot, box, store)]
        for state in result.path:
            # Only 1 loop
            for b in state.boxes:
                self.miniSolve[(state.robot, b, store)] = state.pathLen
        return self.miniSolve[(robot, box, store)]
