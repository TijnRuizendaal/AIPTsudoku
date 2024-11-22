from collections import deque
import time


class Game:
    def __init__(self, sudoku, feedback=False, enable_preprocessing=True,
                 use_mrv_ac3=False, use_degree_ac3=False,
                 use_mrv_backtracking=False, use_degree_backtracking=False):
        """
        Initialize the Game class with optional heuristics and feedback.
        @param sudoku: The Sudoku puzzle to solve.
        @param feedback: Boolean indicating whether to print detailed feedback.
        @param enable_preprocessing: Boolean indicating whether to preprocess constraints.
        @param use_mrv_ac3: Boolean to enable MRV heuristic in AC-3.
        @param use_degree_ac3: Boolean to enable Degree Heuristic in AC-3.
        @param use_mrv_backtracking: Boolean to enable MRV heuristic in Backtracking.
        @param use_degree_backtracking: Boolean to enable Degree Heuristic in Backtracking.
        """
        self.sudoku = sudoku
        self.feedback = feedback
        self.enable_preprocessing = enable_preprocessing
        self.use_mrv_ac3 = use_mrv_ac3
        self.use_degree_ac3 = use_degree_ac3
        self.use_mrv_backtracking = use_mrv_backtracking
        self.use_degree_backtracking = use_degree_backtracking
        self.queue = deque()
        self.recursive_calls = 0
        self.constraint_checks = 0
        self.domain_reductions = 0
        self.assignments = 0
        self.start_time = None
        self.end_time = None
        self.empty_cells = sum(1 for row in sudoku.get_board() for field in row if not field.is_finalized())

        if self.enable_preprocessing:
            if self.feedback:
                print("Preprocessing constraints...")
            self.preprocess_constraints()

    def ac3(self) -> bool:
        """
        Applies the AC-3 algorithm to enforce arc consistency.
        Uses heuristics to prioritize arcs if enabled.
        """
        board = self.sudoku.get_board()
        self.queue = deque([(field, neighbor) for row in board for field in row for neighbor in field.get_neighbours()])

        while self.queue:
            xi, xj = self.queue.popleft()
            if self.revise(xi, xj):
                if xi.get_domain_size() == 0:  # Domain wipeout
                    return False

                # Re-add arcs involving xi
                neighbors = xi.get_other_neighbours(xj)
                if self.use_mrv_ac3:
                    neighbors = sorted(neighbors, key=lambda n: n.get_domain_size())
                if self.use_degree_ac3:
                    neighbors = sorted(
                        neighbors,
                        key=lambda n: len([nb for nb in n.get_neighbours() if not nb.is_finalized()]),
                        reverse=True
                    )
                for xk in neighbors:
                    self.queue.append((xk, xi))
        return True

    def backtracking_search(self) -> bool:
        """
        Performs backtracking search to assign values to all fields.
        Uses heuristics for variable selection if enabled.
        """
        self.recursive_calls += 1
        # Add a timeout check periodically
        if self.timeout and (time.time() - self.start_time) > self.timeout:
            raise TimeoutError("Solving exceeded time limit")
        unassigned = self.get_unassigned_fields()
        if not unassigned:
            return True

        field = unassigned[0]  # Default choice
        if self.use_mrv_backtracking:
            field = min(unassigned, key=lambda f: f.get_domain_size())
        if self.use_degree_backtracking:
            min_domain_size = field.get_domain_size()
            candidates = [f for f in unassigned if f.get_domain_size() == min_domain_size]
            field = max(candidates, key=lambda f: len([n for n in f.get_neighbours() if not n.is_finalized()]))

        for value in field.get_domain():
            self.constraint_checks += 1
            if self.is_consistent(field, value):
                field.set_value(value)
                self.assignments += 1
                if self.backtracking_search():
                    return True
                field.set_value(0)

        return False

    def preprocess_constraints(self):
        """
        Preprocess the Sudoku board by ensuring all domains are consistent with known values.
        This eliminates invalid values from the domains of non-finalized neighbors.
        """
        board = self.sudoku.get_board()

        for row in board:
            for field in row:
                if field.is_finalized():
                    value = field.get_value()
                    for neighbor in field.get_neighbours():
                        if not neighbor.is_finalized():
                            neighbor.remove_from_domain(value)
                            if self.feedback:
                                row_idx, col_idx = self.get_field_coordinates(neighbor)
                                print(f"Removed {value} from domain of Field at ({row_idx}, {col_idx})")

    def get_field_coordinates(self, field):
        """
        Retrieve the (row, col) coordinates of a given field in the Sudoku board.
        @param field: The Field object to locate.
        @return: A tuple (row, col) of the field's coordinates.
        """
        board = self.sudoku.get_board()
        for row_index, row in enumerate(board):
            if field in row:
                return row_index, row.index(field)
        return -1, -1  # Not found (should not happen)

    def solve(self, timeout=20) -> bool:
        """
        Solves the Sudoku puzzle using AC-3 algorithm and backtracking search.
        """
        self.start_time = time.time()  # Start the timer
        self.timeout = timeout

        if self.feedback:
            print("Starting AC-3 algorithm...")

        if not self.ac3():
            if self.feedback:
                print("AC-3 failed to solve the puzzle.")
                self.display_metrics()
            self.end_time = time.time()  # End the timer
            return False

        if self.is_fully_assigned():
            if self.feedback:
                print("Sudoku solved successfully with AC-3.")
                self.display_metrics()
            self.end_time = time.time()  # End the timer
            return True
        else:
            if self.feedback:
                print("AC-3 could not fully solve the puzzle. Proceeding with backtracking search...")
                self.display_metrics()
            result = self.backtracking_search()
            self.end_time = time.time()  # End the timer
            return result

    def get_unassigned_fields(self):
        return [field for row in self.sudoku.get_board() for field in row if not field.is_finalized()]

    def is_consistent(self, field, value) -> bool:
        """
        Checks if assigning 'value' to 'field' is consistent with the Sudoku rules.
        """
        for neighbor in field.get_neighbours():
            self.constraint_checks += 1  # Increment constraint check count
            if neighbor.is_finalized() and neighbor.get_value() == value:
                return False
        return True

    def revise(self, xi, xj) -> bool:
        """
        Revises the domain of xi to maintain arc consistency with xj.
        Only processes non-finalized fields.
        @param xi: The current field.
        @param xj: The neighboring field.
        @return: True if the domain of xi was revised, False otherwise.
        """
        revised = False
        if xi.is_finalized():
            return False

        if xj.is_finalized():
            xj_value = xj.get_value()
            if xj_value in xi.get_domain():
                xi.remove_from_domain(xj_value)
                self.domain_reductions += 1  # Increment domain reductions count
                revised = True
                if self.feedback:
                    xi_row, xi_col = self.get_field_coordinates(xi)
                    xj_row, xj_col = self.get_field_coordinates(xj)
                    print(
                        f"Removed {xj_value} from domain of Field at ({xi_row}, {xi_col}) because Field at ({xj_row}, {xj_col}) is finalized with {xj_value}")
        return revised

    def is_fully_assigned(self) -> bool:
        """
        Checks if all fields have been assigned a single value.
        @return: True if all fields are assigned, False otherwise.
        """
        board = self.sudoku.get_board()
        return all(field.is_finalized() for row in board for field in row)

    def display_metrics(self):
        total_time = self.end_time - self.start_time
        print("\nSolver Metrics:")
        print(f"Total Execution Time: {total_time:.6f} seconds")
        print(f"Total Recursive Calls: {self.recursive_calls}")
        print(f"Total Constraint Checks: {self.constraint_checks}")
        print(f"Total Domain Reductions: {self.domain_reductions}")
        print(f"Total Assignments Made: {self.assignments}")
        print(f"Empty cells at start: {self.empty_cells}")
        print(f"Constraints checked per empty cell: {self.constraint_checks / self.empty_cells}")

    def valid_solution(self) -> bool:
        """
        Checks the validity of a sudoku solution
        @return: true if the sudoku solution is correct, false otherwise
        """
        # Check each row
        for row in self.sudoku.get_board():
            values = [field.get_value() for field in row if field.get_value() != 0]
            if len(values) != len(set(values)):
                print(f"Invalid row: {self.sudoku.get_board().index(row)}")
                return False

        # Check each column
        for col_index in range(9):
            values = [self.sudoku.get_board()[row][col_index].get_value() for row in range(9) if
                      self.sudoku.get_board()[row][col_index].get_value() != 0]
            if len(values) != len(set(values)):
                print(f"Invalid column: {col_index}")
                return False

        # Check each 3x3 box
        for box_row in range(3):  # For each box generate box integer
            for box_col in range(3):
                values = []
                for row in range(3):
                    for col in range(3):
                        field = self.sudoku.get_board()[box_row * 3 + row][box_col * 3 + col]
                        if field.get_value() != 0:
                            values.append(field.get_value())
                if len(values) != len(set(values)):
                    print(f"Invalid box: ({box_row}, {box_col})")
                    return False

        return True

    def show_sudoku(self):
        """
        Displays the current state of the Sudoku puzzle.
        """
        print(self.sudoku)
