from containers import Board, SubContainer
from move import Move


class Sudoku:
    __slots__ = '_board'

    def __init__(self, filename):
        self._board = Board.fromCSV(filename)

    def solve(self):
        # this must initially be something the first iteration of the board can't be so the loop runs at least once
        boardHash = 0
        while True:
            if (nextHash := hash(self._board)) == boardHash:
                break
            boardHash = nextHash

            if move := self.findSingleOptionCell():
                self._executeMove(move)
            elif move := self.findSingleOptionRow():
                self._executeMove(move)
            elif move := self.findSingleOptionColumn():
                self._executeMove(move)
            elif move := self.findSingleOptionSection():
                self._executeMove(move)

    @staticmethod
    def _executeMove(move: Move):
        """Logic to handle making a move, including printing any messages explaining the move."""
        move()

    def findSingleOptionCell(self) -> Move | None:
        """Look for cells that can only be a single value and return that move."""

        for cellNumber in self._board.order:
            cell = self._board[cellNumber]
            if cell.count == 1:
                value = cell.possibilities.index(True) + 1
                return self._board.setCellMoves(cell.numbers.row, cell.numbers.column, value)

        return None

    def _findSingleOptionContainer(self, containers: list[SubContainer]) -> Move | None:
        for container in containers:
            if container.finished:
                continue

            for number in range(1, 10):
                containerPossibilities = [cell[number] for cell in container]
                if containerPossibilities.count(True) == 1:
                    _index = containerPossibilities.index(True)
                    cell = container[_index]
                    return self._board.setCellMoves(cell.numbers.row, cell.numbers.column, number)

        return None

    def findSingleOptionRow(self) -> Move | None:
        return self._findSingleOptionContainer(self._board.rows)

    def findSingleOptionColumn(self) -> Move | None:
        return self._findSingleOptionContainer(self._board.columns)

    def findSingleOptionSection(self) -> Move | None:
        return self._findSingleOptionContainer(self._board.sections)

    @property
    def board(self) -> Board:
        return self._board


def validateBoard(board: Board) -> bool:
    correctList = [i for i in range(1, 10)]

    # validate rows
    for row in board.rows:
        numberInRow = [cell.value for cell in row]
        if sorted(numberInRow) != correctList:
            return False

    # validate columns
    for column in board.columns:
        numberInColumn = [cell.value for cell in column]
        if sorted(numberInColumn) != correctList:
            return False

    # validate sections
    for section in board.sections:
        numberInSection = [cell.value for cell in section]
        if sorted(numberInSection) != correctList:
            return False

    return True
