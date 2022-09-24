import statistics
from collections import defaultdict
from typing import Callable, Iterator

from src.Enums.geode_enum import GeodeEnum
from src.Utils.collections.queue_extensions import PrioritySet
from src.cell import Cell
from src.group import Group

MAX_GROUP_SIZE = 12


class Geode:

    def __init__(self, geode_grid: list[list[GeodeEnum]]):
        self.grid: list[list[Cell]] = geode_grid
        self.groups: defaultdict[int, Group] = defaultdict(Group)
        self.generate_group_grid()
        self.populate_bridges()
        self.reset_groups()
        self.average_isolation()
        self.heuristic_placement()

    def generate_group_grid(self):
        for cell in self.cells():
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
        for cell in cell.neighbours(self.grid):
            self.init_cell_group(group_nr, cell)

    def populate_bridges(self):
        for group in self.groups.values():
            for cell in (neighbour
                         for group_cell in group.cells
                         for neighbour in group_cell.neighbours(self.grid)):
                if (cell.projected_block == GeodeEnum.AIR and
                        any(neighbour.group_nr not in [-1, group.group_nr]
                            for neighbour in cell.neighbours(self.grid))):
                    cell.projected_block = GeodeEnum.BRIDGE

    def find_shortest_paths(self):
        # Uses Floyd-Warshall

        # shortest path is always initialized to infinity using the defaultdict

        # initialize distances to self at 0 for non-obsidian
        for block in (cell for cell in self.cells() if cell.projected_block != GeodeEnum.OBSIDIAN):
            block.shortest_path_dict |= {block: 0}
            for neighbour in block.neighbours(self.grid):
                if (neighbour.projected_block == GeodeEnum.OBSIDIAN
                        or neighbour.group_nr != -1):
                    block.shortest_path_dict[neighbour] = float('inf')
                    neighbour.shortest_path_dict[block] = float('inf')
                block.shortest_path_dict[neighbour] = 1

        # Floyd Warshall magic for non-obsidian
        iterator_ = [cell for cell in self.cells()
                     if cell.projected_block != GeodeEnum.OBSIDIAN or cell.group_nr != -1]
        for cell_i in iterator_:
            print(cell_i.row)
            for cell_j in iterator_:
                for cell_k in iterator_:
                    dist = cell_i.shortest_path_dict[cell_k] + cell_k.shortest_path_dict[cell_j]
                    if cell_i.shortest_path_dict[cell_j] > dist:
                        cell_i.shortest_path_dict[cell_j] = dist
                        cell_j.shortest_path_dict[cell_i] = dist

    def average_isolation(self):
        for cell in self.cells():
            cell.average_block_distance = float('inf')

        for cell in self.cells():
            if cell.projected_block == GeodeEnum.OBSIDIAN or cell.has_group:
                cell.average_block_distance = float('inf')
                continue

            # Breadth first search, not storing any distances but just the average distance
            total_distance = 0.0
            visited_cells = set()
            visited_cell_count = 0

            current_distance = 0
            current_cells = {cell}

            while len(current_cells) > 0:
                total_distance += current_distance * len([cell for cell in current_cells
                                                          if cell.projected_block == GeodeEnum.PUMPKIN
                                                          and not cell.has_group])
                visited_cell_count += len([cell for cell in current_cells
                                           if cell.projected_block == GeodeEnum.PUMPKIN
                                           and not cell.has_group])
                visited_cells |= current_cells

                new_cells = {cell
                             for edge in current_cells
                             for cell in edge.neighbours(self.grid)
                             if cell not in visited_cells
                             and cell.projected_block != GeodeEnum.OBSIDIAN
                             and not cell.has_group}

                current_cells = new_cells
                current_distance += 1
            try:
                cell.average_block_distance = total_distance / visited_cell_count
            except ZeroDivisionError:
                cell.average_block_distance = float('inf')
            if visited_cell_count <= MAX_GROUP_SIZE:  # If it only visited less than MAX range blocks, add 50 so the algorithm has to get it
                cell.average_block_distance = 60 - visited_cell_count

    def compute_isolation(self):
        for block in self.cells():
            if block.projected_block == GeodeEnum.OBSIDIAN:
                block.average_block_distance = float('inf')
            else:
                block.average_block_distance = statistics.mean((
                    distance
                    for cell, distance in block.shortest_path_dict.items()
                    if cell.projected_block == GeodeEnum.PUMPKIN and block.shortest_path_dict[cell] != float('inf')
                ))

    def reset_groups(self):
        # Reset groups
        for block in self.cells():
            block.group_nr = -1
        self.groups.clear()

    def heuristic_placement(self):
        self.reset_groups()

        while any(not block.has_group
                  for block in self.cells()
                  if block.projected_block == GeodeEnum.PUMPKIN):
            source_block = max((block for block in self.cells()
                                if block.projected_block == GeodeEnum.PUMPKIN and not block.has_group),
                               key=lambda x: x.average_block_distance)
            q = PrioritySet()
            q.add(source_block, 0)
            visited_blocks = set()
            group_nr = len(self.groups)
            while len(self.groups[group_nr].cells) < MAX_GROUP_SIZE:
                try:
                    cell: Cell = q.get()
                    # If there's only one node left to add, don't add bridges
                    if MAX_GROUP_SIZE - len(self.groups[group_nr].cells) == 1:
                        while cell.projected_block == GeodeEnum.BRIDGE:
                            visited_blocks.add(cell)
                            cell = q.get()

                    # If we encounter a bridge that can't connect to anything meaningful, we skip it
                    if (cell.projected_block == GeodeEnum.BRIDGE
                        and not any((True for neighbour in cell.neighbours(self.grid)
                                     if neighbour.projected_block == GeodeEnum.PUMPKIN and not neighbour.has_group))):
                        visited_blocks.add(cell)
                        continue

                except IndexError:
                    break

                isolation_count = self.nr_of_isolated_blocks()
                cell.group_nr = group_nr
                self.groups[group_nr].add_cell(cell)
                self.average_isolation()
                # self.pretty_print_merged()
                # self.pretty_print_average_distance()
                visited_blocks.add(cell)
                # If we block off more blocks than we can absorb, don't place the block
                if self.nr_of_isolated_blocks() - isolation_count > MAX_GROUP_SIZE - len(self.groups[group_nr].cells):
                    cell.group_nr = -1
                    self.groups[group_nr].cells.remove(cell)
                    continue

                for neighbour in (neighbour for neighbour in cell.neighbours(self.grid)
                                  if neighbour.projected_block in [GeodeEnum.PUMPKIN, GeodeEnum.BRIDGE]
                                  and not neighbour.has_group
                                  and neighbour not in visited_blocks):
                    priority = -neighbour.average_block_distance if neighbour.projected_block == GeodeEnum.PUMPKIN \
                               else -max((neighbour2.average_block_distance
                                          for neighbour2 in neighbour.neighbours(self.grid)
                                          if neighbour2.projected_block == GeodeEnum.PUMPKIN),
                                         default=neighbour.average_block_distance)
                    q.add(neighbour, (priority, neighbour))

    def cells(self) -> Iterator[Cell]:
        return (self.grid[row][col]
                for row in range(len(self.grid))
                for col in range(len(self.grid[0])))

    def nr_of_isolated_blocks(self) -> int:
        return sum(1
                   for cell in self.cells()
                   if cell.average_block_distance >= 50
                   and cell.projected_block == GeodeEnum.PUMPKIN)

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
