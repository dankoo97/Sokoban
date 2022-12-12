from typing import Hashable, Union, Optional


class Coord:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: 'Coord') -> 'Coord':
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Coord') -> 'Coord':
        return Coord(self.x - other.x, self.y - other.y)

    def __hash__(self) -> Hashable:
        return hash((self.x, self.y))

    def __eq__(self, other: 'Coord') -> bool:
        return self.x == other.x and self.y == other.y

    def __lt__(self, other: 'Coord') -> bool:
        return self.y < other.y if self.x == other.x else self.x < other.x

    def __str__(self) -> str:
        return f"{self.x}, {self.y}"

    def __repr__(self) -> str:
        return f"Coord(x={self.x}, y={self.y})"

    def distance(self, other: Optional['Coord'] = None, distanceType: Optional[str] = None) -> Union[int, float]:
        other = Coord(0, 0) if other is None else other
        distanceType = 'manhattan' if distanceType is None else distanceType

        if distanceType == 'manhattan':
            x = abs(self.x - other.x)
            y = abs(self.y - other.y)
            return x + y
        if distanceType == 'euclidean':
            x = abs(self.x - other.x)
            y = abs(self.y - other.y)
            return pow(x * x + y * y, 1 / 2)
        return 0
