import itertools
from enum import Enum

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cell import Cell


class ActionType(Enum):
    SET_VALUE = 0
    SET_POSSIBILITY = 1


class Action:
    __slots__ = '_type', '_cell', '_args', '_msg'

    def __init__(self, _type: ActionType, cell: 'Cell', xArgs: tuple, msg: str):
        self._type = _type
        self._cell = cell
        self._args = xArgs
        self._msg = msg

    def __call__(self):
        if self._type == ActionType.SET_VALUE:
            value = self._args[0]
            self._cell.value = value
        elif self._type == ActionType.SET_POSSIBILITY:
            number, value = self._args
            self._cell[number] = value

    @property
    def msg(self) -> str:
        return self._msg


class Move:
    __slots__ = '_actions'

    def __init__(self, actions: Action | list[Action]):
        if isinstance(actions, Action):
            self._actions = (actions,)
        else:
            self._actions = tuple(actions)

    def __call__(self):
        for action in self._actions:
            action()

    def __str__(self) -> str:
        return '\n'.join((action.msg for action in self._actions))

    @property
    def actions(self):
        return self._actions

    def join(self, *args) -> 'Move':
        return Move(itertools.chain(self._actions, *args))
