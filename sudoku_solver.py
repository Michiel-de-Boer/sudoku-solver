#!/usr/bin/env python
# “If it was hard to write, it should be hard to read.”
#   - Anonymous cynic
import numpy as np

num_set = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def diff(li1, li2):
    return list(set(li1) - set(li2))


def invert(li):
    return diff(num_set, li)


class SolverDone(Exception):
    pass


class SolverStuck(Exception):
    pass


class SolverAlgorithmError(Exception):
    pass


class Cell():
    def __init__(self, row, col, val):
        self.row = row
        self.brow = row % 3
        self.col = col
        self.bcol = col % 3
        self.block = ((row // 3) * 3) + (col // 3)
        # print('(%i, %i) block = %i' % (self.row, self.col, self.block))
        self.val = val
        if self.val:
            self._possible = np.array([val], dtype=int)
        else:
            self._possible = np.array([], dtype=int)
            self._impossible = np.array([], dtype=int)

    def _poss_set(self, val):
        self._possible = np.array([], dtype=int)
        self._possible = np.append(self._possible, val)

    def poss_app(self, val):
        self._possible = np.append(self._possible, val)
        self._imposs_set(invert(self._possible))

    @property
    def possible(self):
        return self._possible

    @possible.setter
    def possible(self, val):
        self._poss_set(val)
        self._imposs_set(invert(self.possible))

    @property
    def solved(self):
        return len(self._possible) == 1

    def _imposs_set(self, val):
        self._impossible = np.array([], dtype=int)
        self._impossible = np.append(self._impossible, val)

    def imposs_app(self, val):
        self._impossible = np.append(self._impossible, val)
        self._poss_set(invert(self._impossible))

    @property
    def impossible(self):
        return self._impossible

    @impossible.setter
    def impossible(self, val):
        self._imposs_set(val)
        self._poss_set(invert(self.impossible))


class Response():
    valid = ('solved', 'result', 'loop_count', 'error')

    def __init__(self, **kw):
        for k, v in kw.items():
            if k not in self.valid: raise KeyError
            # print('key=', k, 'val=', v)
            self.__setattr__(k, v)


class Solver():
    def __init__(self, puzzle):
        self.puzzle = np.ndarray([9, 9], dtype=np.object)
        for row in range(9):
            for col in range(9):
                self.puzzle[row, col] = Cell(row, col, puzzle[row][col])

    def obj_to_num(self, ndarr_obj):
        return np.vectorize(lambda obj: obj.val)(ndarr_obj)

    '''
    if ndarr_obj.ndim == 1:
        #return np.asarray([obj.val for obj in ndarr_obj])
    
    elif ndarr_obj.ndim == 2:
        # FIXME !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # return np.asarray([obj.val for obj in ndarr_obj.flatten()])
        return np.vectorize(lambda obj: obj.val)(ndarr_obj)
        #row_len, col_len = ndarr_obj.shape
        #ndarr_num = np.ndarray([row_len, col_len], dtype=np.int)
        #for row in range(row_len):
        #    for col in range(col_len):
        #        ndarr_num[row, col] = ndarr_obj[row, col].val
    return ndarr_num
    '''

    def num_to_obj(self, ndarr_num):
        pass

    def get_row(self, row):
        return(self.puzzle[row])

    def get_row_val(self, row):
        row = self.obj_to_num(self.get_row(row))
        return row[row.nonzero()]

    def get_col(self, col):
        return(self.puzzle.T[col])

    def get_col_val(self, col):
        col = self.obj_to_num(self.get_col(col))
        return col[col.nonzero()]

    def block_get_base(self, block):
        rbase = (block // 3) * 3
        cbase = (block % 3) * 3
        return rbase, cbase

    def block_get_flat(self, block):
        rbase, cbase = self.block_get_base(block)
        return self.puzzle[rbase:rbase + 3, cbase:cbase + 3].flatten()

    def block_get(self, block):
        rbase, cbase = self.block_get_base(block)
        return self.puzzle[rbase:rbase + 3, cbase:cbase + 3]

    def block_iter(self, block):
        blk = self.block_get_flat(block)
        for cell in blk:
            yield(cell)

    def solution_valid(self, row, col, result):
        if not self.must_check_solution: return
        if self.check_against[row, col] != result:
            raise SolverAlgorithmError

    def compute_impossible(self, cell):
        row_not = self.get_row_val(cell.row)
        # row_not = self.puzzle_num[row][self.puzzle_num[row].nonzero()]
        col_not = self.get_col_val(cell.col)
        # col_not = self.puzzle_num.T[col][self.puzzle_num.T[col].nonzero()]
        blk_not = self.obj_to_num(self.block_get_flat(cell.block))
        blk_not = blk_not[blk_not.nonzero()]
        # blk_not = self.blk_not[self.blk_not.nonzero()]
        total_not = np.unique(np.concatenate([row_not, col_not, blk_not]))
        return total_not

    def is_cell_valid(self, cell):
        pass

    @property
    def solved(self):
        arr = self.obj_to_num(self.puzzle).flatten()
        if 0 not in arr:
            return True
        return False

    def block_scan(self, block, to_row=None, to_col=None):

            self.puzzle_num = self.obj_to_num(self.puzzle)
            self.slice_num = self.obj_to_num(self.block_get(block))

            # This iterates over a single 3x3 block, from top to bottom and from left to right
            for cell in self.block_iter(block):
                # Check this first, because cell.val might cause a continue,
                # causing the recursive code to skip past the stop.
                if cell.row == to_row and cell.col == to_col:
                    return
                if cell.val:
                    continue

                row, col = cell.row, cell.col

                '''
                # TODO: check if leading "self." is actually required for row_not, col_not, etc.
                # Collect all the values the cell in question can NOT have:
                # From the current row, the current column, and the current block
                self.row_not = self.puzzle_num[row][self.puzzle_num[row].nonzero()]
                # ndarray doesn't return a column when doing arr[:col]. Tilt it instead.
                self.col_not = self.puzzle_num.T[col][self.puzzle_num.T[col].nonzero()]
                self.blk_not = self.slice_num.flatten()
                self.blk_not = self.blk_not[self.blk_not.nonzero()]
                self.total_not = np.unique(np.concatenate([self.row_not, self.col_not, self.blk_not]))
                '''

                # cell.impossible = self.total_not
                cell.impossible = self.compute_impossible(cell)

                if cell.solved:
                    result = cell.possible[0]
                    self.solution_valid(row, col, result)
                    self.result_count += 1
                    self.puzzle_num[row, col] = result
                    self.slice_num[cell.brow, cell.bcol] = result
                    cell.val = result
                    # Going recursive
                    self.block_scan(block, to_row=cell.row, to_col=cell.col)

    def solve_logical(self):
        try:
            self.fail_count = 0
            for self.loop_counter in range(self.max_loops):
                if self.solved: raise SolverDone
                self.result_count = 0

                # Blocks are 3x3 grids inside the Sudoku. They are arranged as follows:
                #  0   1   2
                #  3   4   5
                #  6   7   8
                for block in range(9):
                    if self.solved: raise SolverDone
                    self.block_scan(block)

                    # Advanced check: see if any block-unique cell possible elements, e.g. the only one with 2 in
                    # [2,7,8]. If there are: these cells have been solved, because they are the only one in the block
                    # with that possibility. This takes care of cells which are solved by process of elimination.
                    # ("Hidden candidates")
                    concat = np.array([], dtype=int)
                    for cell in self.block_iter(block):
                        if cell.val: continue
                        concat = np.concatenate([concat, cell.possible])

                    uniq, counts = np.unique(concat, return_counts=True)
                    solutions = uniq[counts==1]

                    for solution in solutions:
                        for cell in self.block_iter(block):
                            if cell.val: continue
                            row, col = cell.row, cell.col

                            if solution in cell.possible:
                                self.solution_valid(row, col, solution)

                                self.result_count += 1
                                cell.possible = solution
                                cell.val = solution
                                break

                # It would be better if this actually checked if any cell's solutions had been altered rather
                # than a cell solved. More expert Sudoku solvers demonstrate that for advanced puzzels, there can
                # be several cycles without solves, just possibility reduction.
                if self.result_count:
                    self.fail_count = 0
                else:
                    self.fail_count += 1
                    if self.fail_count == 3:
                        raise SolverStuck

        except SolverDone:
            return Response(solved=True,
                            result=self.obj_to_num(self.puzzle).tolist(),
                            loop_count=self.loop_counter+1)

        except SolverStuck:
            # TODO: switch to backtracking algorithm to solve Sudoku puzzles from the 'diabolical' persuasion.
            return Response(solved=False,
                            result=self.obj_to_num(self.puzzle).tolist(),
                            loop_count=self.loop_counter+1,
                            error=1)

        except SolverAlgorithmError:
            # TODO: obtain backtrace and stuff it inside the response object.
            return Response(solved=False,
                            result=self.obj_to_num(self.puzzle).tolist(),
                            loop_count=self.loop_counter+1,
                            error=255)

    def solve_backtrack(self):
        def check_constraint(cell, val):
            # total_not = get_impossible(cell)
            if val in self.compute_impossible(cell): return False
            return True

        for cell in self.puzzle.flatten():
            if cell.val:
                cell.possible = cell.val
                cell.static = True
                # print(cell.static)
                continue
            cell.static = False
            cell.impossible = self.compute_impossible(cell)
            # print('%s, (%i, %i) %s' % (cell, cell.row, cell.col, cell.possible))
            cell.bt_ind = 0

        cells = self.puzzle.flatten()
        cell_ind = 0
        try:
            while True:
                if cell_ind == 81: raise SolverDone
                cell = cells[cell_ind]
                if cell.static:
                    cell_ind += 1
                    continue

                val_set = False
                for i in range(cell.bt_ind, len(cell.possible)):
                    if check_constraint(cell, cell.possible[i]):
                        cell.val = cell.possible[i]
                        cell.bt_ind = i
                        val_set = True
                        break
                if not val_set:
                    cell.bt_ind = 0
                    cell.val = 0
                    if cell_ind == 0:
                        continue
                    while True:
                        cell_ind -= 1
                        cell = cells[cell_ind]
                        if cell.static: continue
                        if cell.bt_ind == len(cell.possible) - 1:
                            cell.bt_ind = 0
                            cell.val = 0
                            continue
                        break
                    cell.bt_ind += 1
                    continue

                if cell_ind == 80: raise SolverDone
                cell_ind += 1
        except SolverDone:
            return Response(solved=True,
                            result=self.obj_to_num(self.puzzle).tolist(),
                            loop_count=0)

    def solve(self, max_loops=100, check_against=None, callback = None):
        self.max_loops = max_loops
        self.must_check_solution = False
        if check_against is not None:
            self.must_check_solution = True
            self.check_against = np.asarray(check_against, dtype=int)
        self.callback = callback

        print('Trying logical algorithm.')
        response = self.solve_logical()
        if response.solved:
            return response
        else:
            if response.error == 1:
                if self.callback is not None:
                    self.callback(response)
                print('Switching to backtracking algorithm.')
                response = self.solve_backtrack()
                if response.solved:
                    return response
                else:
                    exit(response.error)
            elif response.error == 255:
                print('Algorithm error.')


if __name__ == '__main__':
    sudoku_example_tuple = (
        (0, 0, 8, 9, 0, 0, 5, 0, 0),
        (2, 0, 0, 1, 0, 4, 0, 0, 6),
        (0, 9, 0, 0, 7, 5, 0, 0, 0),
        (0, 0, 0, 5, 0, 0, 2, 0, 0),
        (0, 5, 6, 0, 0, 1, 4, 0, 0),
        (0, 0, 0, 4, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 0, 0, 0, 0, 9),
        (1, 8, 0, 2, 0, 0, 6, 0, 0),
        (5, 2, 0, 0, 0, 0, 0, 0, 3)
    )

    # Using http://www.birot.hu/sudoku.php to validate
    # This can be passed in to check if the code errs when it
    #  thinks it has found a solution for a certain cell.
    sudoku_example_solution = (
        (7, 6, 8, 9, 3, 2, 5, 1, 4),
        (2, 3, 5, 1, 8, 4, 7, 9, 6),
        (4, 9, 1, 6, 7, 5, 3, 8, 2),
        (3, 1, 4, 5, 9, 7, 2, 6, 8),
        (9, 5, 6, 8, 2, 1, 4, 3, 7),
        (8, 7, 2, 4, 6, 3, 9, 5, 1),
        (6, 4, 7, 3, 5, 8, 1, 2, 9),
        (1, 8, 3, 2, 4, 9, 6, 7, 5),
        (5, 2, 9, 7, 1, 6, 8, 4, 3)
    )

    # To test passing in a 2D pure python array rather than a tuple
    # sudoku_example = []
    # for row in sudoku_example_tuple:
    #    sudoku_example.append(list(row))

    for row in sudoku_example_tuple:
        print(row)
    print()

    sudoku = Solver(sudoku_example_tuple)

    response = sudoku.solve_backtrack()
    # quit()

    # response = sudoku.solve(check_against=sudoku_example_solution)

    if response.solved:
        print('PUZZLE SOLVED! Number of loops: %i' % response.loop_count)
        for row in response.result:
            print(list(row))
    elif response.error == 1:
        print('PUZZLE SOLVER STUCK! Error: %i. Number of loops: %i.' % (response.error, response.loop_count))
        for row in response.result:
            print(list(row))
        exit(response.error)
    elif response.error == 255:
        print('PUZZLE SOLVER FAILED! Error: %i. Number of loops: %i.' % (response.error, response.loop_count))
        print('...Error in logical algorithm =(')
        exit(response.error)


