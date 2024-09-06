import itertools
import os
import sys
from typing import Generator

from board import *
from containers import *
from move import *
# noinspection PyUnresolvedReferences
from cell import *


class NoMovesFound(Exception):
    pass


_NAKED_TUPLE_TYPES = [
    None, None,
    MoveType.NAKED_PAIR,
    MoveType.NAKED_TRIPLE,
    MoveType.NAKED_QUAD,
]


_LOCKED_TUPLE_TYPES = [
    None, None,
    MoveType.LOCKED_PAIR,
    MoveType.LOCKED_TRIPLE,
    MoveType.LOCKED_QUAD
]


_HIDDEN_TUPLE_TYPES = [
    None, None,
    MoveType.HIDDEN_PAIR,
    MoveType.HIDDEN_TRIPLE,
    MoveType.HIDDEN_QUAD
]


class SudokuSolver:
    """The SudokuSolver class handles finding all steps for solving the Sudoku puzzle. The
    SudokuSolver.solve() method lets the solver handle solving the puzzle to completion, or
    the global next() method can be used to continually get the next move and solve the
    puzzle step by step."""

    __slots__ = '_board', '_executionOrder'

    def __init__(self, filename: str):
        self._board = Board.fromFile(filename)

        self._executionOrder = (
            self.findNakedSingles,
            self.findHiddenSingles,
            self.findFullHouses,
            self.findLockedCandidatesType1,
            self.findLockedCandidatesType2,
            self.findNakedDisjointSets,
            self.findHiddenDisjointSets,
        )

    def __str__(self) -> str:
        """Returns a string representation of the current state of the board. This does not show
        any possibilities and is mostly a shorthand of SudokuSolver.board.toString(0)."""

        return self._board.toString(0)

    def solve(self, details: bool = False) -> bool:
        """Solve the puzzle by finding each step and executing the necessary moves until
        the puzzle is fully solved. If details is True the message property of each Move
        object is printed before executing said Move. Returns the value of
        validateBoard(self.board)."""

        for move in self:
            if move:
                if details:
                    print(move.message)
                self._executeMove(move)
            else:
                raise NoMovesFound('No more moves found in this puzzle.')

        # adds a blank line between details and finished puzzle
        if details:
            print('\n', end='')

        return validateBoard(self._board)

    def findCurrentMoves(self) -> list[Move]:
        """Return a list of all possible moves with the board's current state. If no moves are
        found an empty list is returned instead of """

        # noinspection PyArgumentList
        moveLists = [_function(single=False) for _function in self._executionOrder]

        return list(itertools.chain.from_iterable(moveLists))

    @staticmethod
    def _executeMove(move: Move):
        """Logic to handle making a move, including printing any messages explaining the move."""

        move()

    def __iter__(self) -> 'SudokuSolver':
        """Don't call this without calling the Move objects returned by __next__ inbetween
        each iteration, otherwise the same Move will be returned by __next__ and you will
        run an infinite loop. As an implementation detail, this method just returns the
        SudokuSolver instance, so a separate iterator does not actually need to be created
        to iterate over the moves, and next() can just be called directly if so desired."""

        return self

    def __next__(self) -> Move:
        """Find and return the next Move to the current board state. If __call__ of any Move
        is not invoked before another call to __next__ the same move will be returned. This
        can result in infinite loops if using in a generator expression among other things.

        Since the class __iter__ method just returns the SudokuSolver instance, any class
        iterator is the same object as its SudokuSolver instance, so this method can be directly
        called with the builtin 'next' function without creating an iterator if required."""

        if validateBoard(self._board):
            raise StopIteration()

        for _function in self._executionOrder:
            move = _function()
            if move:
                return move

    def findNakedSingles(self, single: bool = True) -> Move | None:
        """Find cells that have only a single candidate."""

        moves = []
        for cell in self._board.cells.squash():
            if cell.count == 1:
                value = cell.candidates.index(True) + 1
                message = getMoveMessage(MoveType.NAKED_SINGLE, coordinate=cell.coordinate, value=value)
                move = self._board.setCellMove(MoveType.NAKED_SINGLE, cell.coordinate, value, message)

                if single:
                    return move
                else:
                    moves.append(move)

        if single:
            return None
        else:
            return moves

    def _findHiddenSinglesExec(self, houses: GenericIterable[House], single: bool) -> Move | list[Move] | None:
        """Logic for finding an individual cell in a container that is the only possibility of
        a number. Returns either the first Move found or None if none is found and single is True,
        otherwise returns a list of all moves found."""

        moves = []
        for house in houses:
            if house.finished:
                continue

            for candidate in range(1, 10):
                houseCandidates = [cell[candidate] for cell in house]
                if houseCandidates.count(True) == 1:
                    _index = houseCandidates.index(True) + 1
                    cell = house[_index]
                    message = getMoveMessage(MoveType.HIDDEN_SINGLE, coordinate=cell.coordinate, value=candidate)
                    move = self._board.setCellMove(MoveType.HIDDEN_SINGLE, cell.coordinate, candidate, message)

                    if single:
                        return move
                    else:
                        moves.append(move)

        if single:
            return None
        else:
            return moves

    def findHiddenSingles(self, single: bool = True) -> Move | list[Move] | None:
        """Find the only cell of a house that can be a candidate. Return only a single Move
        if single is True otherwise return an iterable of possible moves."""

        if single:
            move = self._findHiddenSinglesExec(self._board.rows, True)
            if move is not None:
                return move
            move = self._findHiddenSinglesExec(self._board.columns, True)
            if move is not None:
                return move
            return self._findHiddenSinglesExec(self._board.boxes, True)

        rowMoves = self._findHiddenSinglesExec(self._board.rows, False)
        columnMoves = self._findHiddenSinglesExec(self._board.columns, False)
        boxMoves = self._findHiddenSinglesExec(self._board.boxes, False)

        return list(itertools.chain(rowMoves, columnMoves, boxMoves))

    def _findFullHousesExec(self, houses: GenericIterable[House], single: bool) -> Move | list[Move] | None:
        """Logic for finding full house situations on the board. If single is True the
        first full house case is found unless none are found then None is returned. If
        single is False return a list of all cases found."""

        moves = []
        for house in houses:
            unfilledHouses = list(itertools.filterfalse(lambda o: o.value, house))
            if len(unfilledHouses) == 1:
                cell = unfilledHouses[0]
                value = cell.candidates.index(True) + 1
                message = getMoveMessage(MoveType.FULL_HOUSE, house=house, coordinate=cell.coordinate, value=value)
                move = self._board.setCellMove(MoveType.FULL_HOUSE, cell.coordinate, value, message)

                if single:
                    return move
                else:
                    moves.append(move)

        if single:
            return None
        else:
            return moves

    def findFullHouses(self, single: bool = True) -> Move | list[Move] | None:
        """Check each house for a single remaining unfilled cell and return the first
        Move found if single is True. If single False return a list of all full house
        moves currently found on the board."""

        if single:
            move = self._findFullHousesExec(self._board.rows, True)
            if move:
                return move
            move = self._findFullHousesExec(self._board.columns, True)
            if move:
                return move
            return self._findFullHousesExec(self._board.boxes, True)

        rowMoves = self._findFullHousesExec(self._board.rows, False)
        columnMoves = self._findFullHousesExec(self._board.columns, False)
        boxMoves = self._findFullHousesExec(self._board.boxes, False)

        return list(itertools.chain(rowMoves, columnMoves, boxMoves))

    def _areCandidatesLocked(self, cells: GenericIterable) -> '(House, House) | None':
        """If all cells in cells lie in an intersection of a box and a row or column,
        return the box and column, otherwise return None. This does not differentiate
        between type 1 and type 2 locked candidates, if the cells are filtered from a
        box the results are for type 1, if they are filtered from a row or column they
        are type 2."""

        boxNumbers = [cell.coordinate.box for cell in cells]
        rowNumbers = [cell.coordinate.row for cell in cells]
        columnNumbers = [cell.coordinate.column for cell in cells]

        lockedBox = allEqual(boxNumbers)
        lockedRow = allEqual(rowNumbers)
        lockedColumn = allEqual(columnNumbers)

        if lockedBox and lockedRow:
            return self._board.boxes[lockedBox], self._board.rows[lockedRow]
        elif lockedBox and lockedColumn:
            return self._board.boxes[lockedBox], self._board.columns[lockedColumn]

        return None

    def _findLockedCandidatesExec(self, house: House, _type: MoveType) -> Generator[Move, None, None]:
        """Generator function for finding locked candidates in house. _type should be used
        to distinguish between type 1 and type 2 locked candidates as it will be forwarded
        to the Move constructor."""

        for candidate in range(1, 10):
            candidateCells = [cell for cell in house if cell[candidate]]
            if len(candidateCells) < 2:
                continue

            isLocked = self._areCandidatesLocked(candidateCells)
            if isLocked is not None:
                box, line = isLocked

                peerCells = self._board.getPeerCells(candidateCells)
                if not peerCells:
                    continue

                actions = self.board.removeCandidateValues(peerCells, candidate, lambda o, v: o[v])
                if not actions:
                    continue

                lockedIn = line if _type == MoveType.LOCKED_CANDIDATES1 else box
                message = getMoveMessage(_type, lockedIn=lockedIn,
                                         lockedBy=house, candidate=candidate)
                yield Move(_type, actions, message)

    def findLockedCandidatesType1(self, single: bool = True) -> Move | list[Move] | None:
        """Find locked candidates of type 1 and return the corresponding Move to eliminate any
        extra candidates in the locked row/column. If single is True return the first move found
        or None if no move can be found, otherwise return a list of (if any) possible moves."""

        moves = []
        for box in self._board.boxes:
            if box.finished:
                continue

            for move in self._findLockedCandidatesExec(box, MoveType.LOCKED_CANDIDATES1):
                if single:
                    return move
                else:
                    moves.append(move)

        return None if single else moves

    def findLockedCandidatesType2(self, single: bool = True) -> Move | list[Move] | None:
        """Find locked candidates of type 2 and return the corresponding Move to eliminate any
        extra candidates in the locked box. If single is True return the first move found or
        None if no move can be found, otherwise return a list of (if any) possible moves."""

        moves = []
        for house in itertools.chain(self._board.rows, self._board.columns):
            if house.finished:
                continue

            for move in self._findLockedCandidatesExec(house, MoveType.LOCKED_CANDIDATES2):
                if single:
                    return move
                else:
                    moves.append(move)

        return None if single else moves

    def findNakedDisjointSets(self, single: bool = True) -> Move | list[Move] | None:
        """Find any naked disjoint sets in the puzzle. Only sets upto quads are searched for, as a
        smaller complementary hidden disjoint set also exists. If single is True return a single
        Move if it exists otherwise return None. If single is False return a list of Moves (if
        any exist)."""

        moves = []
        for house in itertools.chain(self._board.rows, self._board.columns, self._board.boxes):
            if house.finished:
                continue

            unfilledCells = GenericIterable(cell for cell in house if not cell.value)
            if len(unfilledCells) < 2:
                continue

            endRange = min(len(unfilledCells), 5)
            for combinationLength in range(2, endRange):
                for combination in itertools.combinations(unfilledCells, combinationLength):
                    cumulativeCandidates = ([i for i in range(1, 10) if cell[i]] for cell in combination)
                    discreteCandidates = set(itertools.chain.from_iterable(cumulativeCandidates))

                    if len(discreteCandidates) == combinationLength:
                        peerCells = self._board.getPeerCells(combination)
                        if not peerCells:
                            continue

                        # having actions/candidate list in order is more visually pleasing
                        sortedCandidates = sorted(discreteCandidates)
                        foldedActions = (self._board.removeCandidateValues(peerCells, candidate, lambda o, v: o[v])
                                         for candidate in sortedCandidates)
                        actions = list(itertools.chain.from_iterable(foldedActions))
                        if not actions:
                            continue

                        if self._areCandidatesLocked(combination):
                            moveType = _LOCKED_TUPLE_TYPES[combinationLength]
                        else:
                            moveType = _NAKED_TUPLE_TYPES[combinationLength]

                        candidates = ', '.join(str(candidate) for candidate in sortedCandidates)
                        cells = ', '.join(str(cell.coordinate) for cell in combination)
                        message = getMoveMessage(moveType, candidates=candidates, cells=cells)
                        move = Move(moveType, actions, message)
                        if single:
                            return move
                        else:
                            moves.append(move)

        return None if single else moves

    def findHiddenDisjointSets(self, single: bool = True) -> Move | list[Move] | None:
        """Returns any hidden disjoint sets in the puzzle. A hidden tuple larger than a quad is
        not looked for, as if it existed it would have a smaller complementary naked disjoint set.
        If single is True return a single Move object or None if there isn't a move with the
        current board state, otherwise return a list of Moves (if they exist)."""

        # todo: if there are naked singles a lot of these get triggered. it may behoove us to
        #   make sure we don't include any sets with a naked single
        moves = []
        for house in itertools.chain(self._board.rows, self._board.columns, self._board.boxes):
            if house.finished:
                continue

            unfilledCells = GenericIterable(cell for cell in house if not cell.value)
            if len(unfilledCells) < 2:
                continue

            houseCandidates = list(set(range(1, 10)) ^ set([cell.value for cell in house if cell.value]))
            for combinationLength in range(2, min(len(unfilledCells), 5)):
                for combination in itertools.combinations(houseCandidates, combinationLength):
                    cumulativeCells = ([cell for cell in unfilledCells if cell[candidate]] for candidate in combination)
                    discreteCells = set(itertools.chain.from_iterable(cumulativeCells))

                    if len(discreteCells) == combinationLength:

                        sortedCandidates = sorted(combination)
                        disjointCandidates = (i for i in houseCandidates if i not in sortedCandidates)
                        foldedActions = (self._board.removeCandidateValues(discreteCells, candidate, lambda o, v: o[v])
                                         for candidate in disjointCandidates)
                        actions = list(itertools.chain.from_iterable(foldedActions))
                        if not actions:
                            continue

                        moveType = _HIDDEN_TUPLE_TYPES[combinationLength]
                        candidates = ', '.join(str(candidate) for candidate in sortedCandidates)
                        cells = ', '.join(str(cell.coordinate) for cell in discreteCells)
                        message = getMoveMessage(moveType, candidates=candidates, cells=cells)
                        move = Move(moveType, actions, message)
                        if single:
                            return move
                        else:
                            moves.append(move)

        return None if single else moves

    @property
    def board(self) -> Board:
        return self._board


def validateBoard(board: Board) -> bool:
    """Validates each number occurs only a single time in each row, column, and section of
    a game board."""

    correctList = [i for i in range(1, 10)]

    for house in itertools.chain(board.rows, board.columns, board.boxes):
        houseValues = [cell.value for cell in house]
        if sorted(houseValues) != correctList:
            return False

    return True


def main():
    filename = sys.argv[1]
    if not os.path.exists:
        raise FileExistsError(f'file path {filename} does not exist')

    # this will be handled by argparse in the future
    if len(sys.argv) > 2:
        detailsArg = sys.argv[2]
        if detailsArg == '--details' or detailsArg == '-d':
            details = True
        else:
            print('Unknown argument', detailsArg)
            return 1
    else:
        details = False

    solver = SudokuSolver(filename)

    try:
        solver.solve(details=details)
    except NoMovesFound:
        print(solver)
        print('No more moves found.')
        return 1

    print(solver)
    if not validateBoard(solver.board):
        print('Finished board invalid!')
    else:
        print('Finished successfully!')

    return 0


if __name__ == '__main__':
    exit(main())
