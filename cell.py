import itertools


class CellNumbers:
    __slots__ = '_row', '_column', '_section'

    def __init__(self, row: int, column: int):
        self._row = row
        self._column = column
        self._section = self.rowColumnToSection(row, column)

    @staticmethod
    def rowColumnToSection(row: int, column: int) -> int:
        return ((row // 3) * 3) + (column // 3)

    @property
    def row(self) -> int:
        return self._row

    @property
    def column(self) -> int:
        return self._column

    @property
    def section(self) -> int:
        return self._section

    def __repr__(self) -> str:
        return f'CellNumbers({self._row}, {self._column})'

    def __eq__(self, other: 'CellNumbers') -> bool:
        return self._row == other._row and self._column == other._column


class BoardOrder:
    __slots__ = '_order'

    def __init__(self):
        self._order = tuple(tuple(CellNumbers(row, column) for column in range(1, 10)) for row in range(1, 10))

    def __getitem__(self, row: int) -> tuple[CellNumbers]:
        return self._order[row]

    def __iter__(self):
        return itertools.chain(*self._order)


class Cell:
    __slots__ = '_possibilities', '_count', '_value', '_cellNumbers'

    def __init__(self, value: int, numbers: CellNumbers):
        if value == 0:
            self._count = 9
            self._value = 0
            self._possibilities = [True] * 9
        elif 0 < value < 10:
            self._count = 0
            self._value = value
            self._possibilities = [False] * 9
        else:
            raise ValueError(f'cell value must be in 1 to 9 inclusive, not {value}')

        self._cellNumbers = numbers

    @property
    def count(self) -> int:
        return self._count

    @property
    def value(self) -> int:
        return self._value

    @property
    def possibilities(self) -> list[bool]:
        return [value for value in self._possibilities]

    @property
    def numbers(self):
        return self._cellNumbers

    def __getitem__(self, number: int) -> bool:
        if number < 1 or number > 9:
            raise ValueError(f'number must be in 1 to 9 inclusive, not {number}')
        return self._possibilities[number - 1]

    def __setitem__(self, number: int, value: bool):
        if number < 1 or number > 9:
            raise ValueError(f'number must be in 1 to 9 inclusive, not {number}')
        value = bool(value)
        self._possibilities[number - 1] = value
        self._count += 1 if value else -1

    @value.setter
    def value(self, _value: int) -> None:
        self._value = _value
        self._possibilities = [False] * 9
        self._count = 0

    def __hash__(self) -> int:
        return hash((tuple(self._possibilities), self._count, self._value))

    def __eq__(self, other: 'Cell') -> bool:
        return self._cellNumbers == other._cellNumbers
