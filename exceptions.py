class CellValueNotPossible(Exception):
    def __init__(self, msg: str, value: int, *args):
        self.value = value
        super().__init__(msg, *args)


class CellValueContradiction(Exception):
    pass
