from Field import Field


class Sudoku:

    def __init__(self, filename):
        self.board = self.read_sudoku(filename)

    def __str__(self):
        output = "╔═══════╦═══════╦═══════╗\n"
        # iterate through rows
        for i in range(9):
            if i == 3 or i == 6:
                output += "╠═══════╬═══════╬═══════╣\n"
            output += "║ "
            # iterate through columns
            for j in range(9):
                if j == 3 or j == 6:
                    output += "║ "
                output += str(self.board[i][j]) + " "
            output += "║\n"
        output += "╚═══════╩═══════╩═══════╝\n"
        return output

    @staticmethod
    def read_sudoku(filename):
        """
        Read in a sudoku file
        @param filename: Sudoku filename
        @return: A 9x9 grid of Fields where each field is initialized with all its neighbor fields
        """
        assert filename is not None and filename != "", "Invalid filename"
        # Setup 9x9 grid
        grid = [[Field for _ in range(9)] for _ in range(9)]

        try:
            with open(filename, "r") as file:
                for row, line in enumerate(file):
                    for col_index, char in enumerate(line):
                        if char == '\n':
                            continue
                        if int(char) == 0:
                            grid[row][col_index] = Field()
                        else:
                            grid[row][col_index] = Field(int(char))

        except FileNotFoundError:
            print("Error opening file: " + filename)

        Sudoku.add_neighbours(grid)
        return grid

    @staticmethod
    def add_neighbours(grid):
        """
        Adds a list of neighbors to each field
        @param grid: 9x9 list of Fields
        """
        for row in range(9):
            for col in range(9):
                field: Field = grid[row][col]  # Current field for which neighbors are being set
                neighbors: set[Field] = set()  # Set to hold unique neighbors

                # Check horizontal neighbors
                for x in range(9):
                    if x != col:
                        neighbors.add(grid[row][x])

                # Check vertical neighbors
                for y in range(9):
                    if y != row:
                        neighbors.add(grid[y][col])

                # Divide and round to integer downwards and multiply by 3 to get range of this subgrid
                subgrid_start_row = row // 3 * 3
                subgrid_start_col = col // 3 * 3
                for y in range(subgrid_start_row, subgrid_start_row + 3):
                    for x in range(subgrid_start_col, subgrid_start_col + 3):
                        if (y != row or x != col):
                            neighbors.add(grid[y][x])

                field.set_neighbours(list(neighbors))
                print(
                    f"Field ({row}, {col}) has {len(neighbors)} neighbors set.")  # Debugging statement to verify neighbors

    def board_to_string(self):

        output = ""
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                output += self.board[row][col].get_value()
            output += "\n"
        return output

    def get_board(self):
        return self.board
