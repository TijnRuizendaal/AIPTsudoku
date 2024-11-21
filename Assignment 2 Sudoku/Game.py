from collections import deque
from Field import Field

class Game:
    def __init__(self, sudoku, use_mrv=True, use_degree_heuristic=True, feedback=True):
        """
        Initialize the Game class with optional heuristics and feedback.
        @param sudoku: The Sudoku puzzle to solve.
        @param use_mrv: Boolean indicating whether to use the MRV heuristic.
        @param use_degree_heuristic: Boolean indicating whether to use the Degree Heuristic.
        @param feedback: Boolean indicating whether to print detailed feedback.
        """
        self.sudoku = sudoku  # Reference to the Sudoku object
        self.use_mrv = use_mrv
        self.use_degree_heuristic = use_degree_heuristic
        self.feedback = feedback  # Feedback toggle
        self.queue = deque()  # Queue for AC-3
        self.preprocess_constraints()

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

    def solve(self) -> bool:
        """
        Solves the Sudoku puzzle using AC-3 algorithm and backtracking search.
        Provides feedback about the solving process if enabled.
        @return: True if the puzzle is solved, False otherwise.
        """
        if self.feedback:
            print("Starting AC-3 algorithm...")

        if not self.ac3():
            if self.feedback:
                print("AC-3 failed to solve the puzzle.")
            return False

        if self.is_fully_assigned():
            if self.feedback:
                print("Sudoku solved successfully with AC-3.")
            return True
        else:
            if self.feedback:
                print("AC-3 could not fully solve the puzzle. Proceeding with backtracking search...")
            return self.backtracking_search()

    def backtracking_search(self) -> bool:
        """
        Performs backtracking search to assign values to all fields.
        @return: True if a solution is found, False otherwise.
        """
        unassigned = self.get_unassigned_fields()
        if not unassigned:
            return True  # Puzzle solved

        # Apply MRV heuristic if enabled
        if self.use_mrv:
            field = min(unassigned, key=lambda f: f.get_domain_size())
        else:
            field = unassigned[0]

        for value in field.get_domain():
            if self.is_consistent(field, value):
                field.set_value(value)
                if self.backtracking_search():
                    return True
                field.set_value(0)  # Unassign the value during backtracking

        return False

    def get_unassigned_fields(self):
        return [field for row in self.sudoku.get_board() for field in row if not field.is_finalized()]

    def is_consistent(self, field, value) -> bool:
        """
        Checks if assigning 'value' to 'field' is consistent with the Sudoku rules.
        """
        for neighbor in field.get_neighbours():
            if neighbor.is_finalized() and neighbor.get_value() == value:
                return False
        return True

    def ac3(self) -> bool:
        """
        Applies the AC-3 algorithm to enforce arc consistency.
        Provides feedback about changes in domains.
        @return: True if arc consistency is achieved without domain wipeouts, False otherwise.
        """
        board = self.sudoku.get_board()
        self.queue = deque([(field, neighbor) for row in board for field in row for neighbor in field.get_neighbours()])

        while self.queue:
            xi, xj = self.queue.popleft()
            xi_row, xi_col = self.get_field_coordinates(xi)
            xj_row, xj_col = self.get_field_coordinates(xj)

            if self.feedback:
                print(f"Processing arc ({xi} at ({xi_row}, {xi_col}), {xj} at ({xj_row}, {xj_col}))")

            if self.revise(xi, xj):
                if self.feedback:
                    print(f"Revised domain for Field at ({xi_row}, {xi_col}): {xi.get_domain()}")

                if xi.get_domain_size() == 0:  # Domain wipeout
                    if self.feedback:
                        print(f"Domain wipeout at Field at ({xi_row}, {xi_col}).")
                    return False

                # Re-add all arcs involving xi except xj
                for xk in xi.get_other_neighbours(xj):
                    self.queue.append((xk, xi))

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

        # If xj is finalized, remove its value from xi's domain
        if xj.is_finalized():
            xj_value = xj.get_value()
            if xj_value in xi.get_domain():
                xi.remove_from_domain(xj_value)
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
