import re

from exceptions import CellValueContradiction, CellValueNotPossible


class Cell:
    __slots__ = '_possibilities', '_count', '_value'

    def __init__(self, value: int = 0):
        if value == 0:
            self._count = 9
            self._value = 0
            self._possibilities = [True] * 9
        elif 0 < value < 10:
            self._count = 0
            self._value = value
            self._possibilities = [False] * 9
            # self._possibilities[value - 1] = True
        else:
            raise ValueError(f'cell value must be in 1 to 9 inclusive, not {value}')

    @property
    def count(self) -> int:
        return self._count

    @property
    def value(self) -> int:
        return self._value

    @property
    def possibilities(self) -> list[bool]:
        return [value for value in self._possibilities]

    @value.setter
    def value(self, _value: int) -> None:
        if self._value:
            if self._value != _value:
                raise CellValueContradiction(f'cell already is set to {self._value}, cannot set to {_value}')
            else:
                return
        if not self._possibilities[_value - 1]:
            raise CellValueNotPossible(f'cell cannot be {_value}', _value)

        self._value = _value
        self._possibilities = [False] * 9
        self._count = 0

    def __getitem__(self, number: int) -> int:
        return self._possibilities[number - 1]

    def __setitem__(self, number: int, value: bool) -> None:
        if self._value:
            return

        value = bool(value)
        if value:
            if not self._possibilities[number - 1]:
                self._count += 1
                self._possibilities[number - 1] = True
        else:
            if self._possibilities[number - 1]:
                self._count -= 1
                self._possibilities[number - 1] = False
                if self._count == 1:
                    cellValueIndex = self._possibilities.index(True)
                    self.value = cellValueIndex + 1

    def __hash__(self) -> int:
        return hash((tuple(self._possibilities), self._count, self._value))


class Board:
    """Basically a wrapper class around the cell array."""
    __slots__ = '_cells'

    def __init__(self, filename):
        """default instantiation is a .csv with each row corresponding to each row of the puzzle"""
        self._cells = self._fromCSV(filename)

    @staticmethod
    def _fromCSV(filename) -> list[list[Cell]]:
        cells = []
        with open(filename, 'r') as file:
            for fileRow in file:
                fileRow = re.sub(r'\s+', '', fileRow)
                splitValues = fileRow.split(',')
                boardRow = [Cell(int(value)) for value in splitValues]
                cells.append(boardRow)

        return cells

    def getRow(self, number: int) -> list[Cell]:
        """Returns the nth row, starting from 1."""
        if number < 1 or number > 9:
            raise ValueError(f'number must be between 1 and 9 inclusive, not {number}')

        return self._cells[number - 1]

    def getColumn(self, number: int) -> list[Cell]:
        """Returns the nth column, starting from 1."""
        if number < 1 or number > 9:
            raise ValueError(f'number must be between 1 and 9 inclusive, not {number}')

        return [row[number - 1] for row in self._cells]

    def getSection(self, number: int) -> list[Cell]:
        """Returns the nth section, where 1 is top left, ascending move right and then down."""
        if number < 1 or number > 9:
            raise ValueError(f'number must be between 1 and 9 inclusive, not {number}')

        row = ((number - 1) // 3) * 3
        column = ((number - 1) % 3) * 3
        return [self._cells[row][column + i] for i in range(3)] + \
            [self._cells[row + 1][column + i] for i in range(3)] + \
            [self._cells[row + 2][column + i] for i in range(3)]

    @property
    def cells(self) -> list[list[Cell]]:
        return self._cells

    @staticmethod
    def _cellValueString(cell: Cell, number: int) -> str:
        if number == 0:
            return str(cell.value)

        return str(number) if cell[number] else ' '
        # return str(number) if cell.canBe(number) else ' '

    def _toStringChunk(self, row: list[Cell], start: int, stop: int, number: int) -> str:
        string = ''
        for column in range(start, stop):
            value = self._cellValueString(row[column], number)
            string += f' {value}'

        return string

    def toString(self, number=None) -> str:
        if number is None:
            number = 0

        string = ''
        for i, row in enumerate(self._cells, 1):
            string += self._toStringChunk(row, 0, 3, number)
            string += ' |'
            string += self._toStringChunk(row, 3, 6, number)
            string += ' |'
            string += self._toStringChunk(row, 6, 9, number)
            if i == 3 or i == 6:
                string += '\n-------+-------+------\n'
            else:
                string += '\n'

        return string.replace('0', ' ')

    def __hash__(self) -> int:
        cellsAsTuple = tuple((tuple(row) for row in self._cells))
        return hash(cellsAsTuple)


class SubContainer:
    __slots__ = '_cells', '_type', '_number'

    def __init__(self, board: Board, _type: str, number: int):
        """Type can be 'row', 'column', 'section'."""

        if _type == 'row':
            self._cells = board.getRow(number)
        elif _type == 'column':
            self._cells = board.getColumn(number)
        elif _type == 'section':
            self._cells = board.getSection(number)
        else:
            raise ValueError(f'container type must be "row", "column", or "section", not {_type}')

        self._type = _type
        self._number = number

    def __getitem__(self, number: int) -> Cell:
        if number < 1 or number > 9:
            raise ValueError(f'number must be between 1 and 9 inclusive, not {number}')

        return self._cells[number - 1]

    def finishedCount(self) -> int:
        len([cell.value for cell in self._cells if cell.value > 0])

    @property
    def finished(self) -> bool:
        return self.finishedCount() == 9

    def __contains__(self, item: int) -> bool:
        return any(cell.value == item for cell in self._cells)

    def __hash__(self) -> int:
        return hash((tuple(self._cells), self._type, self._number))
