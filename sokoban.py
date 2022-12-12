from itertools import combinations
from typing import Iterable, Generator, Hashable, Union, Set, FrozenSet, Optional

from coord import Coord

COMPASS = {
    'N': Coord(0, -1),
    'S': Coord(0, 1),
    'E': Coord(1, 0),
    'W': Coord(-1, 0),
}


class Sokoban:
    def __init__(self, robot: Coord, boxes: Union[Set, FrozenSet], storage: Union[Set, FrozenSet],
                 obstacles: Union[Set, FrozenSet], X: int = None, Y: int = None) -> None:
        """
        The constructor for the initial Sokoban puzzle
        :param robot: Robot starting position
        :param boxes: Boxes starting position
        :param storage: Storage starting positions
        :param obstacles: Obstacles starting position
        :param X: Max X for the puzzle
        :param Y: Max Y for the puzzle
        """

        # Init for each type of object on the board
        self.storage = frozenset(storage)
        self.obstacles = frozenset(obstacles)

        # Store the initial game state
        self.initialGameState = GameState(robot, boxes)

        # Get max X and Y for easy printing
        self.X = X if X is not None else max(self.obstacles, key=lambda c: c.x).x
        self.Y = Y if Y is not None else max(self.obstacles, key=lambda c: c.y).y

    def successors(self, state: 'GameState') -> Set['GameState']:
        """
        Checks all directions and returns legal move directions and their corresponding game state
        :return: All legal successor game states
        """
        return {successor for successor in state.nextMoves() if self.isLegal(successor)}

    def isLegal(self, state: 'GameState') -> bool:
        """
        Checks that a game state is legal
        :param state: State to be checked
        :return: Boolean if legal
        """
        if state.robot in self.obstacles:
            return False
        for box in state.boxes:
            if box in self.obstacles:
                return False
        return len(state.boxes) == len(self.initialGameState.boxes)

    def isWon(self, state: 'GameState') -> bool:
        """
        Checks if a game state has won
        :param state: State to be checked
        :return: True if the game is won else False
        """
        return self.isLegal(state) and state.boxes - self.storage == set()

    def solutions(self) -> Generator['GameState', None, None]:
        """
        Generates winning moves
        :return: Yields each possible winning game state and the leading move
        """
        boxStates = set(frozenset(boxes) for boxes in combinations(self.storage, len(self.initialGameState.boxes)))

        for boxes in boxStates:
            for box in boxes:
                for direction, coord in COMPASS.items():
                    robot = box - coord

                    if {robot, robot - coord} & (self.obstacles | boxes):
                        continue

                    final = GameState(robot, boxes, reverse=True)
                    yield GameState(robot - coord, {*(boxes - {box}), robot}, final, direction, True)

    @staticmethod
    def getStateFromString(state: str) -> 'Sokoban':
        """
        Load a game state from a string
        :param state: The state of the game from a string
        """
        robot = ()
        storage = set()
        obstacles = set()
        boxes = set()
        X = 0
        Y = 0

        for y, line in enumerate(state.split('\n')):
            for x, char in enumerate(line):
                if char == 'R':
                    robot = Coord(x, y)
                elif char == 'S':
                    storage.add(Coord(x, y))
                elif char == 'O':
                    obstacles.add(Coord(x, y))
                elif char == 'B':
                    boxes.add(Coord(x, y))
                X = max(X, x)
            Y = y

        if len(boxes) == len(storage) + 1:
            storage.add(robot)

        return Sokoban(robot=robot, storage=storage, obstacles=obstacles, boxes=boxes, X=X, Y=Y)

    def toStringWithState(self, state: 'GameState') -> str:
        """
        Returns the game and game state as a printable string
        :param state: The given game state
        :return: A string of the game state
        """
        S = []
        for y in range(self.Y + 1):
            S.append([])
            for x in range(self.X + 1):
                if Coord(x, y) == state.robot:
                    S[-1].append("R")
                elif Coord(x, y) in state.boxes:
                    S[-1].append("B")
                elif Coord(x, y) in self.storage:
                    S[-1].append("S")
                elif Coord(x, y) in self.obstacles:
                    S[-1].append("O")
                else:
                    S[-1].append(" ")

        S.append([state.direction if state.direction is not None else "No direction"])
        return '\n'.join(''.join(line) for line in S)

    def printLine(self, y: int, gameState: Optional['GameState'] = None) -> str:
        """
        Returns a single line of a given game state
        :param y: The line number
        :param gameState: The given game state
        :return: A string containing the given line
        """
        gameState = self.initialGameState if gameState is None else gameState
        S = []
        for x in range(self.X + 1):
            if Coord(x, y) == gameState.robot:
                S.append("R")
            elif Coord(x, y) in gameState.boxes:
                S.append("B")
            elif Coord(x, y) in self.storage:
                S.append("S")
            elif Coord(x, y) in self.obstacles:
                S.append("O")
            else:
                S.append(" ")
        return ''.join(S)

    def compareGameStates(self, gameStates: Iterable['GameState'], sep: str = " "*5, highlighter: str = "*"*8):
        """
        Returns a series of game states adjacent to each other in string form
        :param gameStates: A series of game states
        :param sep: The seperator between game states
        :param highlighter: Highlights when states are different
        :return: A string of adjacent gamestates
        """
        S = []
        if len(set(gameStates)) > 1:
            S.append(highlighter)
        for y in range(self.Y + 1):
            S.append([])
            for state in gameStates:
                S[-1].append(self.printLine(y, state))
            S[-1] = sep.join(S[-1])
        return '\n'.join(S)

    def __str__(self) -> str:
        S = []
        for y in range(self.Y + 1):
            S.append(self.printLine(y))

        S.append(["No direction"])
        return '\n'.join(''.join(line) for line in S)

    def __repr__(self) -> str:
        return f"Sokoban(robot={self.initialGameState.robot}, boxes={self.initialGameState.boxes}, " \
               + f"storage={self.storage}, obstacles={self.obstacles}, X={self.X}, Y={self.Y})"


class GameState:
    def __init__(self, robot: Coord, boxes: Union[Set, FrozenSet], parent: Optional['GameState'] = None,
                 direction: Optional[str] = None, reverse: Optional[bool] = None, pathCost: int = 0) -> None:
        """
        Represents a game state of Sokoban
        :param robot: The robot's position
        :param boxes: A set of box locations
        :param parent: The parent game state
        :param direction: The direction from parent game state
        :param reverse: If the direction of this state should be reversed (searching from the solution to initial)
        """
        self.robot = robot
        self.boxes = frozenset(b for b in boxes)
        self.parent = parent if parent is not None else None
        self.direction = direction if direction is not None else None
        self.pathLen = pathCost
        self.reverse = bool(reverse)

    def nextMoves(self) -> Generator['GameState', None, None]:
        """
        Generates all states from a move in each direction
        :return: All successor game states
        """
        if not self.reverse:
            for direction, coord in COMPASS.items():

                # Move a direction
                robot = self.robot + coord

                # If the bot moves a box
                if robot in self.boxes:
                    box = robot + coord
                    boxes = {*(self.boxes - {robot}), box}
                else:
                    boxes = self.boxes

                yield GameState(robot, boxes, self, direction, pathCost=self.pathLen+1)
        else:
            for direction, coord in COMPASS.items():

                # Move a direction
                robot = self.robot - coord
                moved = self.robot + coord

                # Robot cannot move from a box
                if robot in self.boxes:
                    continue

                # If the robot could have moved a box
                if moved in self.boxes:
                    boxes = {*(self.boxes - {moved}), self.robot}
                    yield GameState(robot, boxes, self, direction, True, pathCost=self.pathLen+1)

                yield GameState(robot, self.boxes, self, direction, True, pathCost=self.pathLen+1)

    def getPath(self) -> Iterable['GameState']:
        """
        Gets the path of a game state from an initial state recursively
        :return: A game state's parents path along with itself in a list
        """

        # Avoid recursion as big puzzles and non-optimal paths can be very large
        if not self.reverse:
            path = []
            current = self
            while current:
                path.append(current)
                current = current.parent
            return reversed(path)
        else:
            path = []
            current = self
            while current:
                path.append(current)
                current = current.parent
            return path

    # For memoization
    def __eq__(self, other: 'GameState') -> bool:
        return self.robot == other.robot and not (self.boxes ^ other.boxes)

    def __ne__(self, other: 'GameState') -> bool:
        return self.robot != other.robot or self.boxes ^ other.boxes

    def __lt__(self, other: 'GameState') -> bool:
        if self.robot != other.robot:
            return self.robot < other.robot
        return sum(box.distance() for box in self.boxes) < sum(box.distance() for box in other.boxes)

    def __hash__(self) -> Hashable:
        return hash((self.robot, self.boxes))

    def __repr__(self) -> str:
        return f"GameState(robot={self.robot.__repr__()}, boxes={self.boxes})"
