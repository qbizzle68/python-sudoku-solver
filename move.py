import itertools
from enum import IntEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cell import Cell, Coordinate

__all__ = ('ActionType', 'MoveType', 'getMoveMessage', 'Action', 'Move')


class ActionType(IntEnum):
    SET_VALUE = 0
    ADD_CANDIDATE = 1
    REMOVE_CANDIDATE = 2
    SET_CANDIDATE = 3


_ACTION_MESSAGES = [
    'Set {coordinate} value to {value}',
    'Add {value} as candidate to {coordinate}',
    'Remove {value} as candidate to {coordinate}',
]


class MoveType(IntEnum):
    GENERAL = 0
    NAKED_SINGLE = 1
    HIDDEN_SINGLE = 2
    FULL_HOUSE = 3
    LOCKED_CANDIDATES1 = 4
    LOCKED_CANDIDATES2 = 5
    NAKED_PAIR = 6
    NAKED_TRIPLE = 7
    NAKED_QUAD = 8
    LOCKED_PAIR = 9
    LOCKED_TRIPLE = 10
    LOCKED_QUAD = 11
    HIDDEN_PAIR = 12
    HIDDEN_TRIPLE = 13
    HIDDEN_QUAD = 14
    XWING = 15
    SWORDFISH = 16
    JELLYFISH = 17


_MOVE_MESSAGES = [
    '',
    'Naked single; cell = {coordinate}; value = {value};',
    'Hidden single; cell = {coordinate}; value = {value};',
    'Full house; house = {house.type} {house.number}; cell = {coordinate}; value = {value};',
    'Locked candidates type 1; candidate = {candidate}; locked in {lockedIn.type} {lockedIn.number}; locked by '
    '{lockedBy.type} {lockedBy.number};',
    'Locked candidates type 2; candidate = {candidate}; locked in {lockedIn.type} {lockedIn.number}; locked by '
    '{lockedBy.type} {lockedBy.number};',
    'Naked pair; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'Naked triple; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'Naked quad; candidates = {{{candidates}}}; cells = {{{cells}}},',
    'Locked pair; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'Locked triple; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'Locked quad; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'Hidden pair; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'Hidden triple; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'Hidden quad; candidates = {{{candidates}}}; cells = {{{cells}}}',
    'X-Wing; candidate = {candidate}; row = {{{rows}}}; columns = {{{columns}}}',
    'Swordfish; candidate = {candidate}; row = {{{rows}}}; columns = {{{columns}}}',
    'Jellyfish; candidate = {candidate}; row = {{{rows}}}; columns = {{{columns}}}',
]


def getMoveMessage(_type: MoveType, **kwargs) -> str:
    """Curate the message to describe a move based on its MoveType."""
    return _MOVE_MESSAGES[_type].format(**kwargs)


class Action:
    __slots__ = '_type', '_cell', '_candidate', '_msg'

    def __init__(self, _type: ActionType, cell: 'Cell', candidate: int):
        self._type = _type
        self._cell = cell
        self._candidate = candidate
        self._msg = self._getActionMessage(self._type, self._cell.coordinate, self._candidate)

    def __call__(self) -> None:
        if self._type == ActionType.SET_VALUE:
            self._cell.value = self._candidate
        elif self._type == ActionType.ADD_CANDIDATE:
            self._cell[self._candidate] = True
        elif self._type == ActionType.REMOVE_CANDIDATE:
            self._cell[self._candidate] = False

    @staticmethod
    def _getActionMessage(_type: ActionType, coordinate: 'Coordinate', value: int) -> str:
        """Curate the message to describe an action based on its ActionType."""
        return _ACTION_MESSAGES[_type].format(coordinate=coordinate, value=value)

    @property
    def msg(self) -> str:
        return self._msg


class Move:
    __slots__ = '_type', '_msg', '_actions'

    def __init__(self, _type: MoveType, actions: Action | list[Action], msg: str = ''):
        if isinstance(actions, Action):
            self._actions = (actions,)
        else:
            self._actions = tuple(actions)

        self._type = _type
        self._msg = msg

    def __call__(self):
        for action in self._actions:
            action()

    def __str__(self) -> str:
        rtn = self._msg + '\n' + '\n'.join((action.msg for action in self._actions))
        return rtn.replace('\n', '\n - ')

    @property
    def actions(self):
        return self._actions

    @property
    def message(self) -> str:
        return self._msg

    def join(self, *args) -> 'Move':
        """Join one or more iterables of actions to this Move. This action returns a new
        Move object, but it will resemble this Move, only differing in the additional
        Action objects used to instantiate the new value."""

        joinedActions = itertools.chain(self._actions, *args)
        return Move(self._type, joinedActions, self._msg)
