from src.cell import Cell


class Group:

    def __init__(self):
        self.group_nr: int = -1
        self.cells: set[Cell] = set()

    def add_cell(self, cell: Cell):
        self.cells.add(cell)
