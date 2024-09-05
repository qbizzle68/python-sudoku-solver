__all__ = ('Coordinate', 'Cell')


class Coordinate:
    """A data class that holds the coordinates of a cell position of the board. The class
    holds row, column, and box numbers of the position and can check equality of other
    Coordinates for comparing different cells. The class also supports the convertToBox
    static method to convert row and column values to a box number that other classes
    and modules can use."""

    __slots__ = '_row', '_column', '_box'

    def __init__(self, row: int, column: int):
        """Initializes a Coordinate object with the given row and column. Counting starts
        at 1, and the box number is computed from the row and column values."""

        self._row = row
        self._column = column
        self._box = self.convertToBox(row, column)

    @staticmethod
    def convertToBox(row: int, column: int) -> int:
        """Convert row and column numbers into a box number. All numbering starts a 1."""

        return (((row - 1) // 3) * 3) + ((column - 1) // 3) + 1

    @property
    def row(self) -> int:
        return self._row

    @property
    def column(self) -> int:
        return self._column

    @property
    def box(self) -> int:
        return self._box

    def __str__(self) -> str:
        return f'R{self._row}C{self._column}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._row}, {self._column})'

    def __eq__(self, other: 'Coordinate') -> bool:
        return self._row == other._row and self._column == other._column


class Cell:
    """Represents one fo the 81 cells on a Sudoku board. The Cell class provides mechanisms
    for tracking possible candidates as well as its value if/when it is determined. The class
    also is instantiated with a Coordinate object corresponding to the position of the cell
    in the board, which helps with introspection later distinguishing Cell objects from each
    other in memory."""

    __slots__ = '_candidates', '_count', '_value', '_coordinate'

    def __init__(self, value: int, coordinate: Coordinate):
        """Instantiate a Cell object corresponding to the cell at coordinate with initial value.
        If the cell is unfilled value should be 0."""

        if value == 0:
            self._count = 9
            self._value = 0
            self._candidates = [True] * 9
        elif 0 < value < 10:
            self._count = 0
            self._value = value
            self._candidates = [False] * 9
        else:
            raise ValueError(f'cell value must be in 1 to 9 inclusive, not {value}')

        self._coordinate = coordinate

    @property
    def count(self) -> int:
        """Return the number of candidates the cell can be."""
        return self._count

    @property
    def value(self) -> int:
        """Return the value of the cell. The value is 0 for an empty cell."""
        return self._value

    @value.setter
    def value(self, _value: int) -> None:
        """Sets the value of the cell to _value. All candidates are set to False and
        the count is set to 0."""

        self._value = _value
        self._candidates = [False] * 9
        self._count = 0

    @property
    def candidates(self) -> list[bool]:
        """Returns a list of boolean values where the ith value corresponds to the
        (i + 1)th candidate number.

        For example a Cell object whose only possible candidates are 2 and 7 would
        return [False, True, False, False, False, False, True, False, False].

        As an implementation detail the class keeps a running track of the count of
        possible candidates, which means editing the candidates variable without
        also updating the internal count variable would cause serious problems. To
        ensure the class doesn't break, a copy of the candidate array is returned
        here, so if you want to edit one of its values use self.__setitem__ instead."""

        return [value for value in self._candidates]

    @property
    def coordinate(self) -> Coordinate:
        """Return the coordinate object used during object construction."""
        return self._coordinate

    def __getitem__(self, number: int) -> bool:
        """Returns the boolean value corresponding to the candidate number. This is
        equivalent to self.candidates[number - 1]."""

        if number < 1 or number > 9:
            raise IndexError(f'number must be in 1 to 9 inclusive, not {number}')
        return self._candidates[number - 1]

    def __setitem__(self, number: int, value: bool):
        """Sets the possibility of the number candidate to value. This is equivalent
        to self.candidates[number - 1] = value, however that would not actually edit
        the candidate array within the class. This is due to an implementation detail,
        see the candidates property for more information."""

        if number < 1 or number > 9:
            raise ValueError(f'number must be in 1 to 9 inclusive, not {number}')
        value = bool(value)
        self._candidates[number - 1] = value
        self._count += 1 if value else -1

    def __hash__(self) -> int:
        return hash((tuple(self._candidates), self._count, self._value))

    def __eq__(self, other: 'Cell') -> bool:
        return self._coordinate == other._coordinate
