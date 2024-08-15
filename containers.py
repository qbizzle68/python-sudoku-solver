import itertools
import re

from cell import CellNumbers, BoardOrder, Cell
from move import Move, Action, ActionType


class SubContainer:
    __slots__ = '_cells', '_type', '_number'

    def __init__(self, arrayReference: list[Cell], _type: str, number: int):
        if len(arrayReference) != 9:
            raise ValueError(f'length of array must be 9, not {len(arrayReference)}')
        self._cells = arrayReference
        self._type = _type
        self._number = number

    def __getitem__(self, item: int) -> Cell:
        return self._cells[item]

    def __iter__(self):
        return iter(self._cells)

    @property
    def count(self) -> int:
        return len([cell.value for cell in self._cells if cell.value > 0])

    @property
    def finished(self) -> bool:
        return self.count == 9

    @property
    def type(self) -> str:
        return self._type

    @property
    def number(self) -> int:
        return self._number

    def __contains__(self, number: int) -> bool:
        return any(cell.value == number for cell in self._cells)

    def __hash__(self) -> int:
        return hash((tuple(self._cells), self._type, self._number))


class Board:
    __slots__ = '_cells', '_rows', '_columns', '_sections', '_order'

    def __init__(self, array: list[list[int]]):
        if len(array) != 9:
            raise ValueError(f'array must be of length 9, not {len(array)}')

        self._cells = []
        for i, row in enumerate(array):
            if len(row) != 9:
                raise ValueError(f'row {i} of array must be of length 9, not {len(row)}')
            cellRow = []
            for j, number in enumerate(row):
                cellNumbers = CellNumbers(i, j)
                cellRow.append(Cell(number, cellNumbers))
            self._cells.append(cellRow)

        self._rows = []
        self._columns = []
        self._sections = []
        self._setContainers()
        self._setInitialPossibilities()
        self._order = BoardOrder()

    def _setContainers(self):
        for i in range(9):
            #   rows
            row = self._cells[i]
            self._rows.append(SubContainer(row, 'row', i))
            #   columns
            column = [row[i] for row in self._cells]
            self._columns.append(SubContainer(column, 'column', i))
            #   sections
            row = (i // 3) * 3
            column = (i % 3) * 3
            sectionArray = [self._cells[row][column + i] for i in range(3)] + \
                [self._cells[row + 1][column + i] for i in range(3)] + \
                [self._cells[row + 2][column + i] for i in range(3)]
            self._sections.append(SubContainer(sectionArray, 'section', i))

    @staticmethod
    def _sectionFromRowColumn(row: int, column: int) -> int:
        return ((row // 3) * 3) + (column // 3)

    def _setInitialPossibilities(self):
        for row in range(0, 9):
            for column in range(0, 9):
                for number in range(1, 10):
                    sectionNumber = self._sectionFromRowColumn(row, column)
                    if number in self._rows[row] or \
                        number in self._columns[column] or \
                            number in self._sections[sectionNumber]:
                        self._cells[row][column][number] = False

    @classmethod
    def fromCSV(cls, filename: str) -> 'Board':
        board = object.__new__(cls)

        array = []
        with open(filename, 'r') as file:
            for fileRow in file:
                fileRow = re.sub(r'\s+', '', fileRow)
                splitValues = fileRow.split(',')
                boardRow = [int(value) for value in splitValues]
                array.append(boardRow)

        board.__init__(array)
        return board

    @property
    def cells(self) -> list[list[Cell]]:
        return self._cells

    @property
    def rows(self) -> list[SubContainer]:
        return self._rows

    @property
    def columns(self) -> list[SubContainer]:
        return self._columns

    @property
    def sections(self) -> list[SubContainer]:
        return self._sections

    @property
    def order(self) -> BoardOrder:
        return self._order

    @staticmethod
    def _cellValueString(cell: Cell, number: int) -> str:
        if number == 0:
            return str(cell.value)

        return str(number) if cell[number] else ' '

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
        return hash((tuple(self._rows), tuple(self._columns), tuple(self._sections)))

    def __getitem__(self, item: CellNumbers) -> Cell:
        return self._cells[item.row - 1][item.column - 1]

    def _getCoCells(self, cellNumbers: CellNumbers) -> list[Cell]:
        rowCells = (_cell for _cell in self._rows[cellNumbers.row] if _cell.numbers != cellNumbers)
        columnCells = (_cell for _cell in self._columns[cellNumbers.column] if _cell.numbers != cellNumbers)
        sectionCells = (_cell for _cell in self._sections[cellNumbers.section] if _cell.numbers.row != cellNumbers.row
                        and _cell.numbers.column != cellNumbers.column)

        return itertools.chain(rowCells, columnCells, sectionCells)

    def setCellMoves(self, row: int, column: int, value: int) -> Move:
        # it may be best to pass the actual Cell into here, not sure yet
        cell = self._cells[row][column]

        def _isPossible(_cell, _value):
            return _cell[_value]

        setAction = Action(ActionType.SET_VALUE, cell, (value,),
                           f'Set cell ({row}, {column}) to {value}.')
        setMove = Move(setAction)

        coCells = self._getCoCells(cell.numbers)
        coMove = self.removePossibleValues(coCells, value, _isPossible)

        return setMove.join(coMove.actions)

    @staticmethod
    def removePossibleValues(subContainer: itertools.chain[Cell], value: int, key) -> Move:
        actions = []
        for cell in subContainer:
            if key(cell, value):
                actions.append(
                    Action(
                        ActionType.SET_POSSIBILITY,
                        cell,
                        (value, False),
                        f'Remove possibility of {value} from ({cell.numbers.row}, {cell.numbers.column})'
                    )
                )

        return Move(actions)
