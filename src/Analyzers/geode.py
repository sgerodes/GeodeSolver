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
        self.natural_clusters = self.compute_natural_clusters()
        self.generate_group_grid()
        self.populate_bridges()
        self.reset_groups()

        # self.average_isolation()
        # self.heuristic_placement()

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
            cell.reachable_pumpkins = 0

            current_distance = 0
            current_cells = {cell}

            while len(current_cells) > 0:
                total_distance += current_distance * len([cell for cell in current_cells
                                                          if cell.projected_block == GeodeEnum.PUMPKIN
                                                          and not cell.has_group])
                cell.reachable_pumpkins += len([cell for cell in current_cells
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
                cell.average_block_distance = total_distance / cell.reachable_pumpkins
            except ZeroDivisionError:
                cell.average_block_distance = float('inf')
            if cell.reachable_pumpkins <= MAX_GROUP_SIZE:  # If it only visited less than MAX range blocks, add 50 so the algorithm has to get it
                cell.average_block_distance = 60 - cell.reachable_pumpkins

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

    def compute_natural_clusters(self) -> list[set[Cell]]:
        # Returns a list of the natural clusters of pumpkins that already can naturally reach each other.
        # If every pumpkin can reach every pumpkin, then there's only one cluster
        # If there's also a 1x1 group that can't reach any other pumpkin, then there are two, etc.
        undiscovered_cells = set(cell for cell in self.cells() if cell.projected_block == GeodeEnum.PUMPKIN)

        clusters = []

        while len(undiscovered_cells) != 0:
            # Pick an arbitrary cell
            source_cell = next(iter(undiscovered_cells))
            visited_cells = set()
            current_cells = {source_cell}

            while len(current_cells) > 0:
                visited_cells |= current_cells

                # BFS
                current_cells = {cell
                                 for edge in current_cells
                                 for cell in edge.neighbours(self.grid)
                                 if cell not in visited_cells
                                 and cell.projected_block != GeodeEnum.OBSIDIAN}
            undiscovered_cells -= visited_cells
            clusters.append({cell for cell in visited_cells if cell.projected_block == GeodeEnum.PUMPKIN})
        self.pretty_print_projection()
        return clusters

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
                except IndexError:
                    break

                # If we encounter a bridge that can't connect to anything meaningful, we skip it
                if (cell.projected_block == GeodeEnum.BRIDGE
                    and not any((True for neighbour in cell.neighbours(self.grid)
                                 if neighbour.projected_block == GeodeEnum.PUMPKIN and not neighbour.has_group))):
                    visited_blocks.add(cell)
                    continue

                isolated_pumpkins_old = self.isolated_pumpkins()
                isolation_reachable_pumpkins_old = sum((cell.reachable_pumpkins for cell in isolated_pumpkins_old))
                cell.group_nr = group_nr
                self.groups[group_nr].add_cell(cell)
                self.average_isolation()
                # self.pretty_print_merged()
                # self.pretty_print_average_distance()
                visited_blocks.add(cell)

                # If we block off more blocks than we can absorb, don't place the block
                isolated_pumpkins_new = self.isolated_pumpkins()
                isolation_reachable_pumpkins_new = sum((cell.reachable_pumpkins for cell in isolated_pumpkins_old))
                if len(isolated_pumpkins_new) - len(isolated_pumpkins_old) > MAX_GROUP_SIZE - len(self.groups[group_nr].cells):
                    cell.group_nr = -1
                    self.groups[group_nr].cells.remove(cell)
                    continue

                # if isolation_reachable_pumpkins_old - isolation_reachable_pumpkins_new > 0
                #
                # if (sum((1 for cell in self.cells() if cell.projected_block == GeodeEnum.PUMPKIN)) < MAX_GROUP_SIZE
                #         and ):
                #     pass
                # If less than 12 pumpkins are left,
                # and these pumpkins are broken up
                # and not all pumpkins can be consumed by the current group
                # and all pumpkins that are left can reach each other
                # then don't place the block

                # During the computation of the isolation metric we also make a set of clusters consisting of blocks
                # that can all reach each other without traversing bedrock and blocks with groupos
                # When placing a block, if it leads to n new clusters, we know that the block breaks up
                # an existing cluster into 1 + n clusters

                # We take the difference between the old set of clusters and the new set of clusters:
                # original - new = the cluster that was split up
                # new - original = the clusters it was split up into
                #
                # For the neighbours of the newly added block, we check if the entire clusters can be added to the
                # current group
                #
                # To do this, we first make a cheap check: if the size of the old cluster - 1 is less than or equal
                # to the number of blocks that can still be added to the current group, we commit to placing the
                # block.
                # If that's not the case, we have to check how many blocks it takes to reach all blocks in the clusters.
                # This is because there may be bridges that are not needed to reach all pumpkins
                # If all bridges in the new clusters are reachable within the remaining group size, we also commit
                # to placing the block.
                #
                # If not all bridges can be reached, then the refined number of required blocks to reach all pumpkin
                # blocks per cluster has to be considered.
                # If the total number of required blocks is less than the group size, we decide not to place the block
                # and instead make a group of the entire old cluster.
                # If the total number of required blocks is more than the group size, we determine whether it's possible
                # to add all pumpkins from a cluster to the current group such that the other cluster can form its own
                # group if its size is less than the MAX_GROUP_SIZE.
                # If that's not possible, and one of the clusters requires more than MAX_GROUP_SIZE blocks to reach
                # all pumpkins, we can add some of those blocks to the current group to hopefully reduce the required
                # number of blocks to equal or below MAX_GROUP_SIZE
                # If none of these conditions apply, there is nothing that can be done to improve the situation

                # To check how many blocks it takes to reach all pumpkins in a cluster, we have to eliminate useless
                # bridges.
                # To check if a bridge is useless (i.e. all pumpkins that were reachable are still reachable after
                # disabling the bridge), we can run BFS with one bridge disabled each time and see if all pumpkins
                # are still reachable
                # Before running BFS for all bridges, we can instead make some optimizations that are faster to compute.

                # 1. For all pumpkins with only one neighbour where the neighbour is a bridge, the bridge is mandatory
                # 2. For all bridges with only one neighbour, the bridge is useless
                # 3. For the newly created clusters, if only one of the neighbours of the added block is part of the
                #    cluster, then trace a path from that neighbour until it branches or until all pumpkins are found.
                #    All bridges on this path are mandatory.
                #    # Optimization: For the 'forced' path, you can always explore pumpkins before bridges
                #                    If BFS runs end up being necessary you run those starting from the first
                #                    branching point.

                # If there are still bridges for which the state is undetermined, then you first run a BFS from the
                # final block of the mandatory path to determine the distances to all remaining pumpkins.
                # Then, for all undetermined bridges, you mark the bridge as unnecessary, run the BFS again from the
                # final block. If the distance to any of the pumpkins increases (possibly to infinite), the bridge
                # is necessary.
                # This doesn't necessarily achieve the optimal layout but can't massively mess up
                # Over-optimization: You can make subclusters while determining the distance to the remaining
                #                    pumpkins to decrease the BFS search space


                # At this point, we commit to placing the block.
                # We recompute the priority for everything in the queue since the priority changed after
                # adding a block and recomputing the isolation factor
                q.recompute_all(lambda x: Cell.priority(x, self.grid))

                for neighbour in (neighbour for neighbour in cell.neighbours(self.grid)
                                  if neighbour.projected_block in [GeodeEnum.PUMPKIN, GeodeEnum.BRIDGE]
                                  and not neighbour.has_group
                                  and neighbour not in visited_blocks):
                    q.add(neighbour, neighbour.priority(self.grid))

    def cells(self) -> Iterator[Cell]:
        return (self.grid[row][col]
                for row in range(len(self.grid))
                for col in range(len(self.grid[0])))

    def isolated_pumpkins(self) -> list[Cell]:
        return [cell
                for cell in self.cells()
                if cell.average_block_distance >= 50
                and cell.projected_block == GeodeEnum.PUMPKIN]

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
