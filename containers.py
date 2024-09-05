import itertools
from collections.abc import Generator
from enum import IntEnum
from typing import TypeVar, Sequence, Iterator, Generic

from cell import Cell

__all__ = ('GenericIterable', 'House', 'CellContainer')

T = TypeVar("T")
SequenceBuffer = Sequence[T] | Sequence[Sequence[T]]


class GenericIterable(Generic[T]):
    __slots__ = '_buffer'

    def __init__(self, buffer: SequenceBuffer):

        if isinstance(buffer, Generator):
            self._buffer = tuple(buffer)
        else:
            self._buffer = buffer

    def __getitem__(self, index: int) -> Sequence[T] | T:
        """Returns the nth element of a container with counting starting at 1."""

        item = self._buffer[index - 1]

        if isinstance(item, Sequence):
            if issubclass(type(item), self.__class__):
                return item
            return self.__class__(item)
        else:
            return item

    def __iter__(self) -> Iterator[T]:
        """Returns an iterator of the buffer."""
        return iter(self._buffer)

    def __len__(self) -> int:
        """Returns the length of the underlying memory buffer."""
        return len(self._buffer)

    @property
    def buffer(self) -> SequenceBuffer:
        """Returns the underlying data buffer."""
        return self._buffer

    def squash(self) -> 'GenericIterable[Cell]':
        """Return a single dimensional 'squashed' version of the buffer for
        simple iteration of all values."""

        flattenedChain = itertools.chain(*tuple(self._buffer))
        return self.__class__(tuple(flattenedChain))


class House(GenericIterable[Cell]):
    """A subclass of GenericIterable with added functionalities to support behavior specific
    to a fixed length sequence of Cell objects. Specifically, a House object is a GenericIterable
    object with exactly 9 Cells as its contents. In addition to these restrictions, the
    class also supports properties for quickly determining the state of the cells in the
    house, as well as metadata about the house like its type and number."""

    __slots__ = '_type', '_number'

    def __init__(self, arrayReference: Sequence[Cell], _type: str, number: int):
        """Instantiate the underlying buffer to be arrayReference, and set internal metadata
        with the _type and number arguments. The _type parameter should be one of 'row',
        'column', or 'box', while number should be the number of said type (box starts counting
        in the upper left and moves left to right then top to bottom)."""

        super().__init__(arrayReference)
        self._type = _type
        self._number = number

    @property
    def count(self) -> int:
        """Returns the number of cells that have a filled value (i.e. a non-zero value)."""

        return len([cell.value for cell in self._buffer if cell.value > 0])

    @property
    def finished(self) -> bool:
        """Returns True if and only if the count of the object is equal to 9."""

        return self.count == 9

    @property
    def type(self) -> str:
        """Returns the 'type' of house, whichever was used as the '_type' argument during construction."""

        return self._type

    @property
    def number(self) -> int:
        """Returns the number associated with this house as given via the 'number' argument during construction."""

        return self._number

    def __contains__(self, number: int) -> bool:
        """Returns True if a Cell in the buffer is equal to number."""

        return any(cell.value == number for cell in self._buffer)

    def __hash__(self) -> int:
        return hash((tuple(self._buffer), self._type, self._number))


class CellContainer(GenericIterable):
    """A subclass of GenericIterable, the CellContainer doesn't provide any further
    functionality, but represents a more concrete version of a container of Cells for
    general usage. The type can be used for a representation of a rigid construct, such
    as a 9x9 array of Cells representing the Sudoku Board, or as an intermediate container
    for iterating over while computing a more complex computation."""
    pass


class LockedCandidateType(IntEnum):
    TYPE1 = 1
    TYPE2 = 2


class LockedCandidates:
    __slots__ = '_lockedByHouse', '_lockedInHouse', '_type'

    def __init__(self, _type: LockedCandidateType, lockedBy: House, lockedIn: House):
        self._lockedByHouse = lockedBy
        self._lockedInHouse = lockedIn
        self._type = _type

    @property
    def lockedBy(self) -> House:
        return self._lockedByHouse

    @property
    def lockedIn(self) -> House:
        return self._lockedInHouse

    @property
    def type(self) -> LockedCandidateType:
        return self._type
