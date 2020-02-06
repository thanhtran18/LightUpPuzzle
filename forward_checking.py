import argparse
import sys
from typing import List
import random
# import light_up_puzzle
import library
import time
import copy

wall_values = {'0', '1', '2', '3', '4'}
num_nodes = 0


def check_edge_corner(puzzle: List[List[str]], r: int, c: int) -> int:
    status = 0
    if r == 0 or r == len(puzzle) - 1:  # edge
        status += 1
    if c == 0 or c == len(puzzle[0]) - 1:  # edge, status = 2 if it's a corner
        status += 1
    return status


def get_total_potential_adjacent(puzzle, r: int, c: int) -> int:
    rows, cols, count = len(puzzle), len(puzzle[0]), 0

    if r > 0 and isinstance(puzzle[r-1][c], int) and puzzle[r-1][c] >= 2:
        count += 1
    if r < rows-1 and isinstance(puzzle[r+1][c], int) and puzzle[r+1][c] >= 2:
        count += 1
    if c > 0 and isinstance(puzzle[r][c-1], int) and puzzle[r][c-1] >= 2:
        count += 1
    if c < cols-1 and isinstance(puzzle[r][c+1], int) and puzzle[r][c+1] >= 2:
        count += 1
    return count


def prioritize_bulbs(puzzle, r: int, c: int):
    moving_r = r - 1
    while moving_r >= 0 and isinstance(puzzle[moving_r][c], int):
        puzzle[moving_r][c] = puzzle[moving_r][c] % 2
        moving_r -= 1

    moving_r = r + 1
    while moving_r < len(puzzle)-1 and isinstance(puzzle[moving_r][c], int):
        puzzle[moving_r][c] = puzzle[moving_r][c] % 2
        moving_r += 1

    moving_c = c - 1
    while moving_c >= 0 and isinstance(puzzle[r][moving_c], int):
        puzzle[r][moving_c] = puzzle[r][moving_c] % 2
        moving_c -= 1

    moving_c = c + 1
    while moving_c < len(puzzle[r])-1 and isinstance(puzzle[r][moving_c], int):
        puzzle[r][moving_c] = puzzle[r][moving_c] % 2
        moving_c += 1


def prioritize_walls(puzzle, r, c):
    moving_r = r - 1
    if r > 0 and isinstance(puzzle[moving_r][c], int):
        puzzle[moving_r][c] = int(puzzle[moving_r][c]/2)*2
        if puzzle[moving_r][c] == 2:
            prioritize_bulbs(puzzle, moving_r, c)

    moving_r = r + 1
    if r < len(puzzle)-1 and isinstance(puzzle[moving_r][c], int):
        puzzle[moving_r][c] = int(puzzle[moving_r][c]/2) * 2
        if puzzle[moving_r][c] == 2:
            prioritize_bulbs(puzzle, moving_r, c)

    moving_c = c - 1
    if c > 0 and isinstance(puzzle[r][moving_c], int):
        puzzle[r][moving_c] = int(puzzle[r][moving_c]/2) * 2
        if puzzle[r][moving_c] == 2:
            prioritize_bulbs(puzzle, r, moving_c)

    moving_c = c + 1
    if c < len(puzzle[0])-1 and isinstance(puzzle[r][moving_c], int):
        puzzle[r][moving_c] = int(puzzle[r][moving_c]/2) * 2
        if puzzle[r][moving_c] == 2:
            prioritize_bulbs(puzzle, r, moving_c)


def generate_potential_bulbs_to_wall(puzzle, r: int, c: int) -> int:
    num_bulbs = 0
    if r > 0 and isinstance(puzzle[r-1][c], int) and puzzle[r-1][c] >= 2:
        num_bulbs += 1
    if r < len(puzzle)-1 and isinstance(puzzle[r+1][c], int) and puzzle[r+1][c] >= 2:
        num_bulbs += 1
    if c > 0 and isinstance(puzzle[r][c-1], int) and puzzle[r][c-1] >= 2:
        num_bulbs += 1
    if c < len(puzzle[0])-1 and isinstance(puzzle[r][c+1], int) and puzzle[r][c+1] >= 2:
        num_bulbs += 1
    return num_bulbs


def check_curr_state(puzzle, non_assigned_cells) -> bool:
    # if a cell can be a bulb or empty, mark it as 3
    for r in range(len(puzzle)):
        for c in range(len(puzzle[r])):
            value = len(puzzle)*r + c
            if value in non_assigned_cells:
                puzzle[r][c] = 3

    # if a cell cannot be a bulb, mark it as 1.
    for r in range(len(puzzle)):
        for c in range(len(puzzle[r])):
            if puzzle[r][c] == 'b':
                prioritize_bulbs(puzzle, r, c)

    # if a cell cannot be empty but can be a bulb, mark it as 2, mark it as 0 if it can't be neither
    for r in range(len(puzzle)):
        for c in range(len(puzzle[r])):
            if puzzle[r][c] in wall_values:
                num_adj_bulbs = count_adjacent_bulbs(puzzle, r, c)
                potential_bulbs = generate_potential_bulbs_to_wall(puzzle, r, c)

                cell_status = check_edge_corner(puzzle, r, c)

                require_bulbs = int(puzzle[r][c]) - num_adj_bulbs - cell_status
                if require_bulbs == potential_bulbs:
                    prioritize_walls(puzzle, r, c)

    result = True
    for r in range(len(puzzle)):
        for c in range(len(puzzle[r])):
            if isinstance(puzzle[r][c], int):
                if puzzle[r][c] == 0:
                    result = False
                puzzle[r][c] = '_'
    return result


def is_inside(puzzle: List[List[str]], r: int, c: int) -> bool:
    return 0 <= r < len(puzzle) and 0 <= c < len(puzzle[0])


def can_bulb_be_here(puzzle: List[List[str]], r: int, c: int) -> bool:
    delta_r = [-1, 1, 0, 0]
    delta_c = [0, 0, -1, 1]
    for i in range(len(delta_c)):
        moving_r = r + delta_r[i]
        moving_c = c + delta_c[i]

        if is_inside(puzzle, moving_r, moving_c) and puzzle[moving_r][moving_c] in wall_values:
            if count_adjacent_bulbs(puzzle, moving_r, moving_c) > int(puzzle[moving_r][moving_c]):
                return False

        while is_inside(puzzle, moving_r, moving_c) and not puzzle[moving_r][moving_c] in wall_values:
            if puzzle[moving_r][moving_c] == 'b':  # adjacent bulbs
                return False
            moving_r += delta_r[i]
            moving_c += delta_c[i]
    return True


def forward_checking(puzzle: List[List[str]], domain, empty_cells, heuristic: str):
    global num_nodes
    num_nodes += 1
    if num_nodes < 10000:
        if num_nodes % 3 == 0:
            print('\rProcessing.', end='')
        if num_nodes % 3 == 1:
            print('\rProcessing..', end='')
        if num_nodes % 3 == 2:
            print('\rProcessing...', end='')
    if num_nodes % 10000 == 0:
        print('\rAlready processed {} nodes.'.format(num_nodes), end='')
    if num_nodes == 5000000:
        return 'Too many nodes. Timeout'
    if is_puzzle_solved(puzzle):
        return puzzle
    if len(empty_cells) == 0 and check_curr_state(puzzle, empty_cells):
        return 'backtrack'

    chosen_cells, chosen_cell = [], []
    # check the input to see what heuristic should be used
    if heuristic == 'most_constrained':
        chosen_cells = find_most_constrained(puzzle, empty_cells)
    elif heuristic == 'most_constraining':
        chosen_cells = find_most_constraining(puzzle, empty_cells)
    elif heuristic == 'hybrid':
        chosen_cells = hybrid_heuristic(puzzle, empty_cells)
    else:
        print('Heuristic must be either "most_constrained", "most_constraining" or "hybrid"')
    if len(chosen_cells) >= 1:
        chosen_cell = chosen_cells[random.randint(0, len(chosen_cells) - 1)]

    empty_cells.remove(chosen_cell)

    r, c = chosen_cell[0], chosen_cell[1]
    for val in domain:
        puzzle[r][c] = val
        if (val != '_' and can_bulb_be_here(puzzle, r, c)) or val == '_':
            result = forward_checking(puzzle, domain, empty_cells, heuristic)
            if result != 'backtrack':
                return result

    empty_cells.append(chosen_cell)
    return 'backtrack'


def count_adjacent_bulbs(puzzle: List[List[str]], r: int, c: int) -> int:
    num_bulbs = 0
    if r > 0 and puzzle[r-1][c] == 'b':
        num_bulbs += 1
    if r < len(puzzle)-1 and puzzle[r+1][c] == 'b':
        num_bulbs += 1
    if c > 0 and puzzle[r][c-1] == 'b':
        num_bulbs += 1
    if c < len(puzzle[0])-1 and puzzle[r][c+1] == 'b':
        num_bulbs += 1
    return num_bulbs


# check if the current solution is valid
def is_puzzle_solved(puzzle: List[List[str]]) -> bool:
    for r in range(len(puzzle)):
        for c in range(len(puzzle[r])):
            if puzzle[r][c] in wall_values and int(puzzle[r][c]) != count_adjacent_bulbs(puzzle, r, c):
                return False

    light_map_up(puzzle)

    print('\nBacktracking...')
    print_puzzle(puzzle)
    print("--------------")
    return is_map_lit_up_and_clean_map(puzzle)


def light_map_up(puzzle: List[List[str]]):
    for r in range(len(puzzle)):
        for c in range(len(puzzle[0])):
            if puzzle[r][c] == 'b':
                k = 1
                while r - k >= 0 and (puzzle[r-k][c] == '_' or puzzle[r - k][c] == '*'):
                    puzzle[r-k][c] = '*'
                    k += 1
                k = 1
                while r + k < len(puzzle) and (puzzle[r + k][c] == '_' or puzzle[r + k][c] == '*'):
                    puzzle[r + k][c] = '*'
                    k += 1
                k = 1
                while c - k >= 0 and (puzzle[r][c - k] == '_' or puzzle[r][c - k] == '*'):
                    puzzle[r][c - k] = '*'
                    k += 1
                k = 1
                while c + k < len(puzzle[r]) and (puzzle[r][c + k] == '_' or puzzle[r][c + k] == '*'):
                    puzzle[r][c + k] = '*'
                    k += 1


# given a bulb position, count the number of cells should be lit up in the corresponding row and column
def num_cells_should_be_lit(puzzle: List[List[str]], r: int, c: int) -> int:
    num_cells = 0
    row_up = r - 1
    while row_up >= 0 and (puzzle[row_up][c] == '_' or puzzle[row_up][c] == '*'):
        if puzzle[row_up][c] == '_':
            num_cells += 1
        row_up -= 1

    row_down = r + 1
    while row_down < len(puzzle) and (puzzle[row_down][c] == '_' or puzzle[row_down][c] == '*'):
        if puzzle[row_down][c] == '_':
            num_cells += 1
        row_down += 1

    col_left = c - 1
    while col_left >= 0 and (puzzle[r][col_left] == '_' or puzzle[r][col_left] == '*'):
        if puzzle[r][col_left] == '_':
            num_cells += 1
        col_left -= 1

    col_right = c + 1
    while col_right < len(puzzle[0]) and (puzzle[r][col_right] == '_' or puzzle[r][col_right] == '*'):
        if puzzle[r][col_right] == '_':
            num_cells += 1
        col_right += 1
    return num_cells


def count_walls_around(puzzle: List[List[str]], r: int, c: int) -> int:
    num_walls = 0
    if r > 0 and puzzle[r-1][c] in wall_values:
        num_walls += int(int(puzzle[r-1][c])/2 + 1)
    if r < len(puzzle)-1 and puzzle[r+1][c] in wall_values:
        num_walls += int(int(puzzle[r+1][c])/2 + 1)
    if c > 0 and puzzle[r][c-1] in wall_values:
        num_walls += int(int(puzzle[r][c-1])/2 + 1)
    if c < len(puzzle[0])-1 and puzzle[r][c+1] in wall_values:
        num_walls += int(int(puzzle[r][c+1])/2 + 1)
    return num_walls


def count_adjacent_lit_cells(puzzle: List[List[str]], r, c) -> int:
    count = 0
    if r > 0 and puzzle[r-1][c] == '*':
        count += 1
    if r < len(puzzle)-1 and puzzle[r+1][c] == '*':
        count += 1
    if c > 0 and puzzle[r][c-1] == '*':
        count += 1
    if c < len(puzzle[0])-1 and puzzle[r][c+1] == '*':
        count += 1
    if puzzle[r][c] == '*':
        count += 3
    return count


def is_map_lit_up_and_clean_map(puzzle: List[List[str]]) -> bool:
    lit_up = True
    for r in range(len(puzzle)):
        for c in range(len(puzzle[r])):
            if puzzle[r][c] == '_':  # the solution is not valid
                lit_up = False
            elif puzzle[r][c] == '*':
                puzzle[r][c] = '_'

    return lit_up


def find_most_constrained(puzzle: List[List[str]], empty_cells: List[List[int]]):
    curr_most_constrained = (-1, [])
    light_map_up(puzzle)

    for cell in empty_cells:
        num_walls = count_walls_around(puzzle, cell[0], cell[1])
        # check to see if a cell is in an edge, or corner
        location = check_edge_corner(puzzle, cell[0], cell[1])
        adj_lit_cells = count_adjacent_lit_cells(puzzle, cell[0], cell[1])

        constraints = num_walls + location + adj_lit_cells

        # randomly pick one to pick if the constraints of this cell is the same as the current most constrained
        if constraints == curr_most_constrained[0]:
            curr_most_constrained[1].append(cell)
        if constraints > curr_most_constrained[0]:
            curr_most_constrained = (constraints, [cell])

    is_map_lit_up_and_clean_map(puzzle)
    return curr_most_constrained[1]


def find_most_constraining(puzzle: List[List[str]], empty_cells: List[List[int]]):
    cells = []
    max_count = 0

    light_map_up(puzzle)

    for cell in empty_cells:
        to_be_lit_up = num_cells_should_be_lit(puzzle, cell[0], cell[1])
        if to_be_lit_up > max_count:
            cells = [cell]
            max_count = to_be_lit_up
        elif to_be_lit_up == max_count:
            cells.append(cell)
    is_map_lit_up_and_clean_map(puzzle)
    return cells


# this is a combination of most constrained and most constraining heuristics, with most constraining heuristic acts as a
# tie breaker for most constrained heuristic.
def hybrid_heuristic(puzzle: List[List[str]], empty_cells: List[List[int]]):
    chosen_cells = find_most_constrained(puzzle, empty_cells)
    # when there is a tie between multiple empty cells
    if len(chosen_cells) > 1:
        chosen_cells = find_most_constraining(puzzle, chosen_cells)
    is_map_lit_up_and_clean_map(puzzle)
    return chosen_cells


def get_empty_cells(puzzle: List[List[str]]) -> List[List[int]]:
    empty_cells = []
    for r in range(len(puzzle)):
        for c in range(len(puzzle[r])):
            if puzzle[r][c] == '_':
                empty_cells.append([r, c])
    return empty_cells


def place_must_have_bulbs(puzzle: List[List[str]], empty_cells: List[List[int]]) -> List[List[int]]:
    stop = False
    count = 0
    while not stop:
        count += 1
        # stop = False
        new_bulb_placed = False
        for wall in library.valid_wall:

            sure_variable = library.generate_valid_neighbours(wall[0], wall[1], len(puzzle), puzzle)
            count_bulbs = 0
            count_empty_cells = 0
            count_stars = 0
            for var in sure_variable:
                if puzzle[var[0]][var[1]] == 'b':
                    count_bulbs += 1
                elif puzzle[var[0]][var[1]] == '_':
                    count_empty_cells += 1
                elif puzzle[var[0]][var[1]] == '*':
                    count_stars += 1
            if count_empty_cells > 0 and count_empty_cells == int(puzzle[wall[0]][wall[1]]) - count_bulbs:
                for var in sure_variable:
                    if puzzle[var[0]][var[1]] == '_':
                        puzzle[var[0]][var[1]] = 'b'
                        empty_cells.remove(var)
                # stop = True
                new_bulb_placed = True
                light_map_up(puzzle)
        if not new_bulb_placed:
            stop = True

    variables = copy.deepcopy(empty_cells)
    for cell in variables:
        if puzzle[cell[0]][cell[1]] == '*':
            empty_cells.remove(cell)
    print(count)
    return empty_cells


# place bulbs in places that must be bulbs
def pre_process(puzzle: List[List[str]], empty_cells: List[List[int]]):
    # stop = False
    # count = 0
    # while not stop:
    #     count += 1
    #     # stop = False
    #     new_bulb_placed = False
    #     for wall in library.valid_wall:
    #
    #         sure_variable = library.generate_valid_neighbours(wall[0], wall[1], len(puzzle), puzzle)
    #         count_bulbs = 0
    #         count_empty_cells = 0
    #         count_stars = 0
    #         for var in sure_variable:
    #             if puzzle[var[0]][var[1]] == 'b':
    #                 count_bulbs += 1
    #             elif puzzle[var[0]][var[1]] == '_':
    #                 count_empty_cells += 1
    #             elif puzzle[var[0]][var[1]] == '*':
    #                 count_stars += 1
    #         if count_empty_cells > 0 and count_empty_cells == int(puzzle[wall[0]][wall[1]]) - count_bulbs:
    #             for var in sure_variable:
    #                 if puzzle[var[0]][var[1]] == '_':
    #                     puzzle[var[0]][var[1]] = 'b'
    #                     empty_cells.remove(var)
    #             # stop = True
    #             new_bulb_placed = True
    #             light_map_up(puzzle)
    #     if not new_bulb_placed:
    #         stop = True
    #
    # variables = copy.deepcopy(empty_cells)
    # for cell in variables:
    #     if puzzle[cell[0]][cell[1]] == '*':
    #         empty_cells.remove(cell)
    empty_cells = place_must_have_bulbs(puzzle, empty_cells)
    remove_zero_wall_neighbours(puzzle, empty_cells)

    print_puzzle(puzzle)
    # print(count)
    is_map_lit_up_and_clean_map(puzzle)


def remove_zero_wall_neighbours(puzzle: List[List[str]], empty_cells: List[List[int]]):
    invalid_neighbours = []
    # remove all neighbours of a zero wall
    for x in range(len(library.invalid_wall)):
        invalid_neighbours.extend(library.generate_valid_neighbours(library.invalid_wall[x][0],
                                                            library.invalid_wall[x][1], len(puzzle), puzzle))
    for x in range(len(invalid_neighbours)):
        # for y in range(len(empty_cells)):
        #     if empty_cells[y][1] == invalid_neighbours[x]:
        if invalid_neighbours[x] in empty_cells:
            empty_cells.remove(invalid_neighbours[x])
                # break


def solve(puzzle: List[List[str]], heuristic: str):
    domain = ('b', '_')
    non_assigned = get_empty_cells(puzzle)
    pre_process(puzzle, non_assigned)
    print("*****")
    print(heuristic)
    return forward_checking(puzzle, domain, non_assigned, heuristic)


def print_puzzle(puzzle: List[List[str]]):
    for r in range(len(puzzle)):
        for c in range(len(puzzle[0])):
            print(puzzle[r][c], end=' ')
        print()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--heuristic', action='store', dest='heuristic', type=str, default='most_constrained')

    arguments = arg_parser.parse_args(argv)

    # TODO: add different input reading methods and heuristic detection
    puzzle = library.read_puzzle()
    # print(type(puzzle))
    starting_time = time.time()
    solution = solve(puzzle, arguments.heuristic)
    ending_time = time.time()
    if solution == 'Too many nodes. Timeout':
        print('Too many nodes. Timeout.\nIt took {} seconds.'.format(ending_time - starting_time))
    else:
        print_puzzle(solution)
        print('*** Done! ***')
        print("The puzzle was solved in {} seconds.".format(ending_time - starting_time))
    print('Visited {} nodes.'.format(num_nodes))


if __name__ == '__main__':
    main()
