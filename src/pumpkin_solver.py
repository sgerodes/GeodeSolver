from z3 import Int, Solver, IntVector, And, If, Implies, Sum, ForAll, Or


def flatten(grid: list[IntVector]):
    return [cell for row in grid for cell in row]


# Return minimum of a vector; error if empty
def min_(vector: IntVector):
    minimum = vector[0]
    for val in vector[1:]:
        minimum = If(val < minimum, val, minimum)
    return minimum


# Return maximum of a vector; error if empty
def max_(vector: IntVector):
    maximum = vector[0]
    for val in vector[1:]:
        maximum = If(val > maximum, val, maximum)
    return maximum


def parse_input(input_: str):
    # TODO: Split this up in separate functions if possible

    # Morph input
    split_input = input_.replace('p', '1').replace('o', '2').splitlines()
    height = len(split_input)
    width = len(split_input[0])

    # Grid of pumpkin coordinates
    pumpkin_grid = [IntVector(f'cell__{row}', width) for row in range(height)]

    # Set each pumpkin grid value to the appropriate value from the input
    pumpkin_grid_instance_c = [pumpkin_grid[row][col] == int(split_input[row][col])
                               for row in range(height)
                               for col in range(width)]

    # Each cell contains a value in {0, 1, 2}
    # 0 = empty, 1 = pumpkin, 2 = obsidian
    pumpkin_grid_legal_values_c = [And(0 <= pumpkin_grid[row][col], pumpkin_grid[row][col] <= 2)
                                   for row in range(height)
                                   for col in range(width)]

    # Grid of blanket coordinates
    # Blanket is for some reason what the slime/honey structures are named
    blanket_grid = [IntVector(f'blanket__{row}', width) for row in range(height)]

    # Each cell contains a value in {0, 1, 2}
    # 0 = empty, 1 = slime, 2 = honey
    blanket_grid_legal_values_c = [And(0 <= blanket_grid[row][col], blanket_grid[row][col] <= 2)
                                   for row in range(height)
                                   for col in range(width)]

    # Set the coordinates corresponding to obsidian (= 2) to be illegal for blankets
    blanket_grid_no_obsidian = [Implies(pumpkin_grid[row][col] == 2,  # if obsidian
                                        blanket_grid[row][col] == 0)  # then no blanket
                                for row in range(height)
                                for col in range(width)]

    # Grid of group number that a coordinate is part of
    group_grid = [IntVector(f'group__{row}', width) for row in range(height)]

    # Total number of groups that exist
    group_total_number = Int('group_total_number')

    # Legal values that group grid coordinates can have
    group_grid_legal_values_c = [If(blanket_grid[row][col] != 0,  # If there is slime or honey
                                    And(0 <= group_grid[row][col],
                                        group_grid[row][col] <= group_total_number),  # Then it can't be group -1
                                    group_grid[row][col] == -1)  # Else it is group -1
                                 for row in range(height)
                                 for col in range(width)]

    # Make neighbouring blanket blocks of the same kind (slime/honey) part of the same group
    group_neighbour_c = [Implies(blanket_grid[row][col] != 0,  # If a grid has a honey or slime block on it
                                 # Then for each neighbour, if it has the same honey or slime value,
                                 #                          then the left neighbour has the same group
                                 #                          else it has a different group
                                 And([If(blanket_grid[row + rowmod][col + colmod] == blanket_grid[row][col],
                                         group_grid[row + rowmod][col + colmod] == group_grid[row][col],  # same group
                                         group_grid[row + rowmod][col + colmod] != group_grid[row][col])  # diff group
                                      for rowmod, colmod in [(-1, 0), (1, 0), (0, -1), (0, 1)]]))
                         for row in range(1, height - 1)  # Range and height force the constraints to be in bounds
                         for col in range(1, width - 1)]

    # Creating groups alone isn't enough
    # We need to ensure that all blocks within a group can reach all other groups
    # To achieve this, we state that one of the blocks in a group can be the 'source' block, with a distance of 0
    # to itself.
    # All other blocks in the group have to have a neighbour from the same group with a lower distance value
    # than the block has itself.
    # This way, recursively, everything has a path to lead back to the source block, and it is asserted that
    # all blocks within a group connect to each other

    # Initialize the distance grid
    group_source_distance_grid = [IntVector(f'group_source_distance__{row}', width) for row in range(height)]

    # We need a constraint to actually have group_total_number equal the maximum group value that exists in
    # the group grid
    group_total_number_c = group_total_number == max_(flatten(group_grid))

    # Because currently everything is slow, we limit the group size to 10 for now
    group_max_based_on_pumpkins_c = group_total_number <= 10

    # Make sure that there are no groups which don't exist on the group grid
    group_number = Int('group_number')
    group_sequence_c = ForAll(group_number,
                              Implies(And(0 <= group_number,
                                          # For all groups within range 0, and the total number of groups
                                          group_number <= group_total_number),
                                      Or([group_grid[row][col] == group_number  # Or there is a group_grid cell
                                          for row in range(height)  # with the same group number
                                          for col in range(width)
                                          ])))

    # Each group can only consist of 4 to 12 slime or honey blocks
    group_size_c = ForAll(group_number,
                          Implies(And(0 <= group_number,
                                      group_number <= group_total_number),
                                  And([And(4 <= Sum(If(group_grid[row][col] == group_number, 1, 0)),
                                           Sum(If(group_grid[row][col] == group_number, 1, 0)) <= 12)
                                       for row in range(height)
                                       for col in range(width)
                                       ])))

    # Every group must be connected.
    # To check this, we introduce two constraints
    # For group_connected_c, we state that for each cell, it must either have a distance of 0 to 'the source',
    # or a neighbouring cell of the same group must have a lower distance.
    #
    # For group_single_source_distance_c, we state that each group must have exactly one cell with a distance of 0
    #
    # Both requirements combined should assert that all blocks within a group are connected

    group_connected_c = [Or(group_source_distance_grid[row][col] == 0,
                            And(group_grid[row + rowmod][col + colmod] == group_grid[row][col],
                                group_source_distance_grid[row + rowmod][col + colmod]
                                < group_source_distance_grid[row][col]))
                         for row in range(1, height - 1)
                         for col in range(1, width - 1)
                         for rowmod, colmod in [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Modifiers to get neighbours
                         ]

    # Each group can only have one source distance
    group_single_source_distance_c = ForAll(group_number,
                                            Implies(And(0 <= group_number,
                                                        group_number <= group_total_number),
                                                    Sum([If(And(group_grid[row][col] == group_number,
                                                                group_source_distance_grid[row][col] == 0),
                                                            1, 0)
                                                         for row in range(height)
                                                         for col in range(width)]
                                                        ) == 1
                                                    ))

    # Ensure that all 93 (hardcoded as of yet) pumpkins are covered.
    # As soon as the 4 <= group size <= 12 constraint is implemented, this will have to be lowered for proper results
    maximize_pumpkin_coverage = Sum([If(And(pumpkin_grid[row][col] == 1, blanket_grid[row][col] >= 1), 1, 0)
                                     for row in range(height)
                                     for col in range(width)]) >= 93

    s = Solver()
    s.append(pumpkin_grid_instance_c)
    s.append(pumpkin_grid_legal_values_c)
    s.append(blanket_grid_legal_values_c)
    s.append(blanket_grid_no_obsidian)
    s.append(group_grid_legal_values_c)
    s.append(group_neighbour_c)
    s.append(group_total_number_c)
    s.append(group_max_based_on_pumpkins_c)
    s.append(group_sequence_c)
    s.append(group_size_c)
    s.append(group_connected_c)
    s.append(group_single_source_distance_c)
    s.append(maximize_pumpkin_coverage)

    print('Constraints generated, starting solve')
    print(s.check())
    model = s.model()
    print(model)
