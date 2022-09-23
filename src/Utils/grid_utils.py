from typing import TypeVar, Any, Iterator

from src.cell import Cell
from src.group import Group

T = TypeVar('T')


class GridUtils:

    @staticmethod
    def init_grid(grid: list[list[Any]], default: T) -> list[list[T]]:
        # instantiate an empty grid of the same size as the given grid assuming a uniform size
        return [[default for _ in range(len(grid[0]))]
                for _ in range(len(grid))]

    @staticmethod
    def cells(grid: list[list[Cell]]) -> Iterator[Cell]:
        return (grid[row][col]
                for row in range(len(grid))
                for col in range(len(grid[0])))

    @staticmethod
    def neighbours(grid: list[list[T]], cell: Cell) -> list[Cell]:
        row = cell.row
        col = cell.col
        row_len = len(grid)
        col_len = len(grid[0])

        return [grid[row + row_][col + col_]
                for row_, col_ in [(-1, 0), (0, -1), (1, 0), (0, 1)]
                if 0 <= row + row_ < row_len and 0 <= col + col_ < col_len]
