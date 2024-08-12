from components import Board, SubContainer


class Sudoku:
    __slots__ = '_board', '_rows', '_columns', '_sections'

    def __init__(self, filename):
        self._board = Board(filename)
        self._rows = [SubContainer(self._board, 'row', i) for i in range(1, 10)]
        self._columns = [SubContainer(self._board, 'column', i) for i in range(1, 10)]
        self._sections = [SubContainer(self._board, 'section', i) for i in range(1, 10)]

        self.setPossibilities()

    @staticmethod
    def _sectionFromRowColumn(row: int, column: int) -> int:
        return ((row // 3) * 3) + (column // 3)

    def setPossibilities(self):
        """Iterates through every cell and every number and sets any cell possibility values
        that are false due to the existence of a number in the same row, column, or section.
        If any part of a cell is changed on the board, the function is recursively called
        until there are no changes on the board."""

        initialHash = hash(self._board)
        for row in range(0, 9):
            for column in range(0, 9):
                for number in range(1, 10):
                    sectionNumber = self._sectionFromRowColumn(row, column)
                    if number in self._rows[row] or \
                        number in self._columns[column] or \
                            number in self._sections[sectionNumber]:
                        self._board.cells[row][column][number] = False
                        # self._board.cells[row][column].cantBe(number)

        if hash(self._board) != initialHash:
            return self.setPossibilities()

    @property
    def board(self) -> Board:
        return self._board
