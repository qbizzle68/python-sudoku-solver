import itertools
from typing import Iterable

from cell import Coordinate, Cell
from containers import GenericIterable, CellContainer, House
from move import Move, Action, ActionType, MoveType

__all__ = ('dataArrayFromSS', 'dataArrayFromSDK', 'dataArrayFromSDX', 'dataArrayFromSDM', 'allEqual', 'Board')


def dataArrayFromSS(rawData: str) -> list[list[int]]:
    """Convert a raw string from a .ss file to a data array. Each line is a row
    represented by the column values with a period (.) representing unfilled cells.
    Every third column is separated by a pipe symbol (|) and every third row is
    separated by a row of hyphens (-).

    Example:
        ..7|..5|..3
        ..9|.6.|...
        36.|..8|2..
        -----------
        ..6|...|...
        51.|.8.|..9
        ...|..2|.4.
        -----------
        ...|5..|9..
        83.|.1.|..5
        7..|...|...
    """

    array = []
    dataRows = rawData.splitlines(keepends=False)
    for line in dataRows:
        if line.startswith('-'):
            continue
        processedLine = line.replace('.', '0').replace('|', '').rstrip()
        row = [int(char) for char in processedLine]
        array.append(row)

    return array


def dataArrayFromSDK(rawData: str) -> list[list[int]]:
    """Convert a raw data string representing a .sdk file to an integer data array.
    The first several lines may provide comments by starting the line with a '#'
    character. The puzzle is represented by rows of column values with periods (.)
    representing unfilled cells.

    Example:
        #ARuud
        #DA random puzzle created by SudoCue
        #CJust start plugging in the numbers
        #B03-08-2006
        #SSudoCue
        #LEasy
        #Uhttp://www.sudocue.net/
        2..1.5..3
        .54...71.
        .1.2.3.8.
        6.28.73.4
        .........
        1.53.98.6
        .2.7.1.6.
        .81...24.
        7..4.2..1
    """

    array = []
    dataRows = rawData.splitlines(keepends=False)
    for line in dataRows:
        if line.startswith('#'):
            continue

        processedLine = line.replace('.', '0')
        row = [int(char) for char in processedLine]
        array.append(row)

    return array


def dataArrayFromSDX(rawData: str) -> list[list[int]]:
    """Convert a raw data string representing a .sdx file to an integer data array.
    Each line contains groups of numbers separated by spaces where unfilled cells
    are seen as groups of candidates for the cell. A 'u' character can prefix a set
    cell to signal that it was set by a user.

    Example:
        2 679 6789 1 46789 5 469 9 3
        389 5 4 69 689 68 7 1 29
        9 1 679 2 4679 3 4569 8 59
        6 9 2 8 u1 7 3 59 4
        3489 3479 3789 56 2456 46 u1 2579 2579
        1 47 5 3 24 9 8 27 6
        3459 2 39 7 3589 1 59 6 589
        359 8 1 569 3569 6 2 4 579
        7 369 369 4 35689 2 59 359 1
    """

    array = []
    dataRows = rawData.splitlines(keepends=False)
    for line in dataRows:
        groups = line.split(' ')
        row = []
        for group in groups:
            group = group.replace('u', '')
            value = int(group) if len(group) == 1 else 0
            row.append(value)
        array.append(row)

    return array


def dataArrayFromSDM(rawData: str) -> list[list[int]]:
    """Convert a raw data string representing a line from a .sdm file to an integer
    data array. Each line is a run-on list of values from each row with a zero (0)
    representing an unfilled cell. Other characters (such as a period (.)) are also
    valid representations of empty cells.

    Example:
        016400000200009000400000062070230100100000003003087040960000005000800007000006820
    """

    return [[int(rawData[row * 9 + column]) for column in range(9)] for row in range(9)]


def allEqual(_list: Iterable) -> int:
    """If the iterable contains one or more occurrences of a unique value, that value is
    returned, otherwise 0 is returned."""

    _set = set(_list)
    return _set.pop() if len(_set) == 1 else 0


class Board:
    __slots__ = '_cells', '_rows', '_columns', '_boxes'  # , '_order'

    def __init__(self, array: list[list[int]]):
        """Instantiate the Board with initial values in array as rows of columns. Any
        empty cell should be equal to 0."""

        self._cells = self._convertDataToCells(array)
        self._setHouses()
        self._setInitialCandidates()
        
    @staticmethod
    def _convertDataToCells(array: list[list[int]]) -> CellContainer:
        """Convert a 2D array of integers into an array of Cell objects."""

        if len(array) != 9:
            raise ValueError(f'array must be of length 9, not {len(array)}')

        cells = []
        for i, row in enumerate(array, 1):
            if len(row) != 9:
                raise ValueError(f'row {i} of array must be of length 9, not {len(row)}')
            cellRow = [Cell(number, Coordinate(i, j)) for j, number in enumerate(row, 1)]
            cells.append(cellRow)

        return CellContainer(cells)

    def _setHouses(self):
        """Set the house arrays for the puzzle."""

        rows = [[], [], [], [], [], [], [], [], []]
        columns = [[], [], [], [], [], [], [], [], []]
        boxes = [[], [], [], [], [], [], [], [], []]
        for i, cell in enumerate(self._cells.squash()):
            rows[cell.coordinate.row - 1].append(cell)
            columns[cell.coordinate.column - 1].append(cell)
            boxes[cell.coordinate.box - 1].append(cell)

        self._rows = GenericIterable(House(row, 'row', i) for i, row in enumerate(rows, 1))
        self._columns = GenericIterable(House(column, 'column', i) for i, column in enumerate(columns, 1))
        self._boxes = GenericIterable(House(box, 'box', i) for i, box in enumerate(boxes, 1))

    def _setInitialCandidates(self):
        """Sets the initial candidate values for each cell."""

        for row in range(1, 10):
            for column in range(1, 10):
                for number in range(1, 10):
                    sectionNumber = Coordinate.convertToBox(row, column)
                    if number in self._rows[row] or \
                        number in self._columns[column] or \
                            number in self._boxes[sectionNumber]:
                        self._cells[row][column][number] = False

    @classmethod
    def fromFile(cls, filename: str) -> 'Board':
        """Read contents of a file and convert the data to a Board object. The file must
        end in a valid Sudoku file format: .sdk, .sdx, .sdm, and .ss. The file suffix
        determines how each file is parsed so the file extension must match the format
        of the data within the file."""

        with open(filename, 'r') as file:
            data = file.read()

        if not data:
            raise IOError(f'Error reading from {filename}.')

        if filename.endswith('.sdk'):
            array = dataArrayFromSDK(data)
        elif filename.endswith('.sdx'):
            array = dataArrayFromSDX(data)
        elif filename.endswith('.sdm'):
            # we only take the first line if there are many
            firstLine = data.split('\n', 1)[0]
            array = dataArrayFromSDM(firstLine)
        elif filename.endswith('.ss'):
            array = dataArrayFromSS(data)
        else:
            raise ValueError(f'Unknown Sudoku file format ({filename}).')

        board = object.__new__(cls)
        board.__init__(array)

        return board

    @classmethod
    def fromCollection(cls, filename: str, number: int) -> 'Board':
        """Read the nth puzzle from a list of puzzles with a .ss file format at
        filename. If there are less than number of puzzles ValueError is raised."""

        with open(filename, 'r') as file:
            data = file.readlines()

        if not data:
            raise IOError(f'Error reading from {filename}.')

        if len(data) < number:
            raise ValueError(f'Only {len(data)} puzzles found in {filename}, can\'t access puzzle {number}')

        array = dataArrayFromSDM(data[number - 1].rstrip())
        board = object.__new__(cls)
        board.__init__(array)

        return board

    @property
    def cells(self) -> GenericIterable[GenericIterable[Cell]]:
        """Return the memory buffer of Cells."""
        return self._cells

    @property
    def rows(self) -> GenericIterable[House]:
        """Return the container of rows of the Board."""
        return self._rows

    @property
    def columns(self) -> GenericIterable[House]:
        """Return the container of columns of the Board."""
        return self._columns

    @property
    def boxes(self) -> GenericIterable[House]:
        """Return the container of boxes of the Board."""
        return self._boxes

    @staticmethod
    def _cellValueString(cell: Cell, number: int) -> str:
        """Find the textual value of the cell, either the string representation of
        the number or a space."""

        if number == 0:
            return str(cell.value)

        return str(number) if cell[number] else ' '

    def toString(self, number=None) -> str:
        """Creates the string representation by formatting the Board. If number is None
        or 0 the overall values will be shown, otherwise each cell that is a candidate
        of number will show number and the rest will be empty."""

        if number is None:
            number = 0

        string = ''
        for i, cell in enumerate(self._cells.squash(), 1):
            value = self._cellValueString(cell, number)
            string += f' {value}'
            if i % 3 == 0 and i % 9 != 0:
                string += ' |'
            if i == 27 or i == 54:
                string += '\n-------+-------+------\n'
            elif i % 9 == 0:
                string += '\n'

        return string.replace('0', ' ')

    def _getStringLine(self, row: int, line: int) -> str:
        """Generate a line of the detailed output string. Row is the row of the puzzle we
        are creating the string for and line is the line in that row. Each row has three,
        lines: the first display the candidates for 1, 2, and 3; the second display the
        candidates for 4, 5, 6, and the third display the candidates for 7, 8, 9. If the
        cell is filled, each candidate slot will contain the cell value to make it obvious
        the cell is filled."""

        offset = (line - 1) * 3
        string = ''
        for i, cell in enumerate(self._rows[row], 1):
            if cell.value:
                string += ''.join(f'{cell.value} ' for _ in range(3))
            else:
                for j in range(1, 4):
                    candidate = offset + j
                    string += f'{candidate} ' if cell[candidate] else '  '
            if i < 9:
                string += '|| ' if i % 3 == 0 else '| '

        return string

    def _getStringRow(self, row: int) -> str:
        """Get the three candidate lines for a single row in creating the detailed
        string of the board."""

        string = ''
        for i, line in enumerate(range(1, 4), 1):
            string += self._getStringLine(row, line)
            string += '\n'

        return string

    def __str__(self) -> str:
        """Create a detailed string representation of the current board state. Each
        cell contains the possible candidates of that cell unless the cell is already
        filled, in which case every candidate slot will be filled with the cell value
        to ensure it is obvious that cell is filled at first glance."""

        string = ''
        for rowNumber in range(1, 10):
            string += self._getStringRow(rowNumber)
            if rowNumber < 9:
                if rowNumber % 3 == 0:
                    string += '========================================================================\n'
                else:
                    string += '------------------------------------------------------------------------\n'

        # there's a trailing new line character we don't want to force on anyone
        return string[:-1]

    def __repr__(self) -> str:
        """Create a .sdm formatted string of the current state of the board."""

        numbers = (str(cell.value) for cell in self._cells.squash())
        return ''.join(numbers)

    def __hash__(self) -> int:
        return hash((tuple(self._rows), tuple(self._columns), tuple(self._boxes)))

    def __getitem__(self, coordinate: Coordinate) -> Cell:
        """Return the Cell whose coordinates match those in coordinate."""
        return self._cells[coordinate.row][coordinate.column]

    def getPeerCells(self, cells: Cell | list[Cell]) -> GenericIterable[Cell]:
        """Return the common peer cells of every cell in cells. If cell can be a single Cell
        object or a list of Cell objects."""

        if isinstance(cells, Cell):
            cells = [cells]

        boxNumber = allEqual(cell.coordinate.box for cell in cells)
        rowNumber = allEqual(cell.coordinate.row for cell in cells)
        columnNumber = allEqual(cell.coordinate.column for cell in cells)

        def key(cell: Cell) -> bool:
            return cell.coordinate.box == boxNumber or cell.coordinate.row == rowNumber \
                   or cell.coordinate.column == columnNumber

        peerCells = [cell for cell in self._cells.squash() if key(cell) and cell not in cells]

        return GenericIterable(peerCells)

    def setCellMove(self, _type: MoveType, coordinate: Coordinate, value: int, msg: str) -> Move:
        """Compiles all Action objects associated with setting the cell at row and column
        to value and returns them in a Move object. This includes flipping the candidate
        values for peer cells as well. The msg argument is used to instantiate the Move
        object."""

        cell = self._cells[coordinate.row][coordinate.column]

        def _isPossible(_cell, _value):
            return _cell[_value]

        peerCells = self.getPeerCells(cell)
        secondaryActions = self.removeCandidateValues(peerCells, value, _isPossible)
        action = Action(ActionType.SET_VALUE, cell, value)

        return Move(_type, [action] + secondaryActions, msg)

    def setCell(self, coordinate: Coordinate, value: int) -> None:
        """Create a Move object to set coordinate to value similar to what is returned
        from Board.setCellMove() and execute the move. This doesn't return anything and
        is simple an ease of use function for also adjusting candidates when setting a
        cell value."""

        move = self.setCellMove(MoveType.GENERAL, coordinate, value, '')
        move()

    @staticmethod
    def removeCandidateValues(cells: GenericIterable[Cell], value: int, key: callable) -> list[Action]:
        """Builds a Move object from all actions needed to remove the candidate value from
        every cell in cells where key(cell, value) is True."""

        actions = []
        for cell in cells:
            if key(cell, value):
                action = Action(ActionType.REMOVE_CANDIDATE, cell, value)
                actions.append(action)

        return actions

    def convertToStringFormat(self, extension: str) -> str:
        """Create a string representative of a specific sudoku puzzle file format. The
        possible extension values are sdk, sdx, sdm, ss."""

        if extension == 'sdk':
            rows = (''.join(str(cell.value) for cell in cellRow) for cellRow in self._cells)
            return '\n'.join(rows).replace('0', '.')
        elif extension == 'sdx':
            # todo: this can't infer if any values a user set as of now
            allCandidates = tuple(str(i) for i in range(1, 10))

            rows = []
            for cellRow in self._cells:
                rowStrings = []
                for cell in cellRow:
                    if cell.value:
                        cellString = str(cell.value)
                    else:
                        candidateString = sorted(itertools.compress(allCandidates, cell.candidates))
                        cellString = ''.join(candidateString)
                    rowStrings.append(cellString)
                rows.append(' '.join(rowStrings))

            return '\n'.join(rows)
        elif extension == 'sdm':
            return self.__repr__()
        elif extension == 'ss':
            skimmedVersion = self.convertToStringFormat('sdk').splitlines(keepends=True)
            # todo: use some text buffer to build this first
            sdmString = ''
            for rowNumber, row in enumerate(skimmedVersion, 1):
                for columnNumber, value in enumerate(row, 1):
                    sdmString += value
                    if columnNumber == 3 or columnNumber == 6:
                        sdmString += '|'
                if rowNumber == 3 or rowNumber == 6:
                    sdmString += '-----------\n'
            return sdmString
        else:
            raise ValueError(f'Invalid extension type {extension}')

    def export(self, filename: str) -> None:
        """Export the current board state to filename using the corresponding format
        based on the file extension provided. Possible values are the same for
        Board.convertToStringFormat()."""

        fileParts = filename.rsplit('.', 1)
        if len(fileParts) < 2:
            raise ValueError(f'File path does not have an extension: {filename}')

        extension = fileParts[-1]
        boardString = self.convertToStringFormat(extension)

        with open(filename, 'w') as file:
            file.write(boardString)
