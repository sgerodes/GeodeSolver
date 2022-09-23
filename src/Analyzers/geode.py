import statistics
from collections import defaultdict
from queue import Empty
from typing import Callable

from src.Enums.geode_enum import GeodeEnum
from src.Utils.collections.queue_extensions import PrioritySet
from src.Utils.grid_utils import GridUtils
from src.cell import Cell
from src.group import Group


class Geode:

    def __init__(self, geode_grid: list[list[GeodeEnum]]):
        self.grid: list[list[Cell]] = geode_grid
        self.groups: defaultdict[int, Group] = defaultdict(Group)
        self.generate_group_grid()
        self.populate_bridges()
        self.find_shortest_paths()
        self.compute_isolation()
        self.pretty_print_shortest_distance(self.grid[4][9])
        self.pretty_print_average_distance()
        self.heuristic_placement()
        self.pretty_print_merged()

    def generate_group_grid(self):
        for cell in GridUtils.cells(self.grid):
            self.init_cell_group(len(self.groups), cell)
        for group_nr, group in self.groups.items():
            group.group_nr = group_nr

    def init_cell_group(self, group_nr: int, cell: Cell):
        # Base case, cell cannot have a group
        if cell.projected_block != GeodeEnum.PUMPKIN:
            return

        # Base case, cell has already been explored
        if cell.group_nr != -1:
            return

        # The cell is an ungrouped pumpkin, assign it to the group
        cell.group_nr = group_nr
        self.groups[group_nr].add_cell(cell)
        # Recursively update
        for cell in GridUtils.neighbours(self.grid, cell):
            self.init_cell_group(group_nr, cell)

    def populate_bridges(self):
        for group in self.groups.values():
            for cell in (neighbour
                         for group_cell in group.cells
                         for neighbour in GridUtils.neighbours(self.grid, group_cell)):
                if (cell.projected_block == GeodeEnum.AIR and
                        any(neighbour.group_nr not in [-1, group.group_nr]
                            for neighbour in GridUtils.neighbours(self.grid, cell))):
                    cell.projected_block = GeodeEnum.BRIDGE

    def find_shortest_paths(self):
        # Uses Floyd-Warshall

        # shortest path is always initialized to infinity using the defaultdict

        # initialize distances to self at 0 for non-obsidian
        for block in GridUtils.cells(self.grid):
            if block.projected_block == GeodeEnum.OBSIDIAN:
                continue
            block.shortest_path_dict |= {block: 0}
            for neighbour in GridUtils.neighbours(self.grid, block):
                if (neighbour.projected_block == GeodeEnum.OBSIDIAN
                        or neighbour.group_nr != -1):
                    block.shortest_path_dict[neighbour] = float('inf')
                    neighbour.shortest_path_dict[block] = float('inf')
                block.shortest_path_dict[neighbour] = 1

        # Floyd Warshall magic for non-obsidian
        iterator_ = [cell for cell in GridUtils.cells(self.grid)
                     if cell.projected_block != GeodeEnum.OBSIDIAN or cell.group_nr != -1]
        for cell_i in iterator_:
            print(cell_i.row)
            for cell_j in iterator_:
                for cell_k in iterator_:
                    dist = cell_i.shortest_path_dict[cell_k] + cell_k.shortest_path_dict[cell_j]
                    if cell_i.shortest_path_dict[cell_j] > dist:
                        cell_i.shortest_path_dict[cell_j] = dist
                        cell_j.shortest_path_dict[cell_i] = dist
            # if block.projected_block == GeodeEnum.OBSIDIAN:
            #     continue
            #
            # if block.row == 5 and block.col == 9:
            #     print('d')
            #
            # block.shortest_path_dict |= {block: 0}
            # for neighbour in GridUtils.neighbours(self.grid, block):
            #     if neighbour.projected_block == GeodeEnum.OBSIDIAN:
            #         continue
            #     for cell in list(neighbour.shortest_path_dict):
            #         shortest_distance = min(block.shortest_path_dict[cell], neighbour.shortest_path_dict[cell] + 1)
            #         block.shortest_path_dict[cell] = shortest_distance
            #         cell.shortest_path_dict[block] = shortest_distance
            #         if cell.shortest_path_dict[cell] == 0 and cell.projected_block == GeodeEnum.OBSIDIAN:
            #             print(f"Only {cell.row}:{cell.col} can save us now")
            #             cell = Cell()

    def compute_isolation(self):
        for block in GridUtils.cells(self.grid):
            if block.projected_block == GeodeEnum.OBSIDIAN:
                block.average_block_distance = float('inf')
            else:
                block.average_block_distance = statistics.mean((
                    distance
                    for cell, distance in block.shortest_path_dict.items() if cell.projected_block == GeodeEnum.PUMPKIN
                                                                              and block.shortest_path_dict[
                                                                                  cell] != float('inf')
                ))

    def heuristic_placement(self):
        # Reset groups
        for block in GridUtils.cells(self.grid):
            block.group_nr = -1
            block.average_block_distance  # TODO: do something sensible here when I don't have an 11 PM brain
        self.groups.clear()

        # For all
        while any(block.group_nr == -1
                  for block in GridUtils.cells(self.grid)
                  if block.projected_block == GeodeEnum.PUMPKIN):
            source_block = max((block for block in GridUtils.cells(self.grid)
                                if block.projected_block == GeodeEnum.PUMPKIN and block.group_nr == -1),
                               key=lambda x: x.average_block_distance)
            q = PrioritySet()
            q.add(source_block, 0)
            group_nr = len(self.groups)
            while len(self.groups[group_nr].cells) < 12:
                self.pretty_print_merged()
                try:
                    cell = q.get()
                except IndexError:
                    break

                cell.group_nr = group_nr
                self.groups[group_nr].add_cell(cell)

                for neighbour in (neighbour for neighbour in GridUtils.neighbours(self.grid, cell)
                                  if neighbour.projected_block in [GeodeEnum.PUMPKIN, GeodeEnum.BRIDGE]
                                  and neighbour.group_nr == -1):
                    q.add(neighbour, -neighbour.average_block_distance)
            self.find_shortest_paths()
            self.compute_isolation()

    def _pretty_print_grid(self, str_func: Callable[[Cell], str]):
        for row_val in self.grid:
            print(''.join((str_func(cell))
                          for cell in row_val))

    def pretty_print_group_grid(self):
        self._pretty_print_grid(Cell.group_str)

    def pretty_print_projection(self):
        self._pretty_print_grid(Cell.projected_str)

    def pretty_print_merged(self):
        self._pretty_print_grid(Cell.merged_str)

    def pretty_print_shortest_distance(self, cell: Cell):
        self._pretty_print_grid(lambda cell2: cell.distance_str(cell2))

    def pretty_print_average_distance(self):
        self._pretty_print_grid(Cell.isolation_str)
