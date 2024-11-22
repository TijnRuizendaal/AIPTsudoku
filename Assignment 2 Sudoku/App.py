import os
import csv
import copy
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from Game import Game
from Sudoku import Sudoku

# Folder containing Sudoku puzzles
sudoku_folder = os.path.join(os.path.dirname(__file__), "Sudokus")
output_file = os.path.join(os.path.dirname(__file__), "Sudoku_Complexity_Results.csv")

class App:

    @staticmethod
    def solve_sudoku(sudoku_file, use_mrv_ac3=False, use_degree_ac3=False, use_mrv_backtracking=False, use_degree_backtracking=False):
        """
        Solves a Sudoku puzzle using specified heuristics and tracks complexity.
        """
        # Preprocess the Sudoku once and use it for all combinations
        original_sudoku = Sudoku(sudoku_file)
        preprocessed_sudoku = copy.deepcopy(original_sudoku)

        game = Game(
            preprocessed_sudoku,
            feedback=False,  # Disable feedback for efficiency
            enable_preprocessing=False,  # Keep preprocessing disabled
            use_mrv_ac3=use_mrv_ac3,
            use_degree_ac3=use_degree_ac3,
            use_mrv_backtracking=use_mrv_backtracking,
            use_degree_backtracking=use_degree_backtracking
        )
        start_time = time.time()
        solved = False
        try:
            solved = game.solve()
        except TimeoutError:
            pass
        finally:
            end_time = time.time()
            # If solving takes longer than 20 seconds, return not solved with constraint checks up to that point
            if end_time - start_time > 20:
                solved = False

        complexity = (
            game.constraint_checks / game.empty_cells if game.empty_cells > 0 else "N/A"
        )
        return {
            "Sudoku File": os.path.basename(sudoku_file),
            "MRV AC3": use_mrv_ac3,
            "Degree AC3": use_degree_ac3,
            "MRV Backtracking": use_mrv_backtracking,
            "Degree Backtracking": use_degree_backtracking,
            "Empty Cells": game.empty_cells,
            "Constraint Checks": game.constraint_checks,
            "Complexity": round(complexity, 4) if isinstance(complexity, float) else complexity,
            "Solved": solved,
        }

    @staticmethod
    def test_all_sudokus_parallel():
        """
        Tests all Sudoku files with heuristic combinations in parallel and limits each test to 20 seconds.
        """
        results = []

        # Define heuristic combinations for testing
        heuristics = [
            # Combination Name, use_mrv_ac3, use_degree_ac3, use_mrv_backtracking, use_degree_backtracking
            ("All Heuristics (MRV & Degree for both AC3 and Backtracking)", True, True, True, True),
            ("MRV for AC3, Degree for Backtracking", True, False, False, True),
            ("Degree for AC3, MRV for Backtracking", False, True, True, False),
            ("MRV & Degree for AC3, None for Backtracking", True, True, False, False),
            ("None for AC3, MRV & Degree for Backtracking", False, False, True, True),
            ("MRV AC3 & Backtracking", True, False, True, False),
            ("Degree AC3 & Backtracking", False, True, False, True),
            ("MRV for AC3 and Backtracking", True, False, True, False),
            ("Degree for AC3 and Backtracking", False, True, False, True)
        ]

        tasks = []
        for filename in os.listdir(sudoku_folder):
            sudoku_path = os.path.join(sudoku_folder, filename)
            if os.path.isfile(sudoku_path) and filename.endswith(".txt"):
                for heuristic_name, use_mrv_ac3, use_degree_ac3, use_mrv_backtracking, use_degree_backtracking in heuristics:
                    tasks.append((sudoku_path, heuristic_name, use_mrv_ac3, use_degree_ac3, use_mrv_backtracking, use_degree_backtracking))

        with ProcessPoolExecutor() as executor:
            future_to_task = {executor.submit(App.process_task, task): task for task in tasks}

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result(timeout=20)
                except TimeoutError:
                    result = {
                        "Sudoku File": os.path.basename(task[0]),
                        "Combination": task[1],
                        "MRV AC3": task[2],
                        "Degree AC3": task[3],
                        "MRV Backtracking": task[4],
                        "Degree Backtracking": task[5],
                        "Empty Cells": "N/A",
                        "Constraint Checks": task[4].constraint_checks if hasattr(task[4], 'constraint_checks') else "N/A",
                        "Complexity": "N/A",
                        "Solved": False
                    }
                results.append(result)
                print(f"Testing Sudoku: {result['Sudoku File']} with Heuristic: {result['Combination']}, Solved: {result['Solved']}, Constraint Checks: {result['Constraint Checks']}")

        # Save results to a CSV file
        with open(output_file, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            # Write header
            writer.writerow([
                "Sudoku File",
                "Heuristic Combination",
                "AC3 Heuristics Used",
                "Backtracking Heuristics Used",
                "Total Heuristics",
                "MRV AC3",
                "Degree AC3",
                "MRV Backtracking",
                "Degree Backtracking",
                "Empty Cells",
                "Constraint Checks",
                "Complexity",
                "Solved"
            ])
            # Write results
            for result in results:
                writer.writerow([
                    result["Sudoku File"],
                    result["Combination"],
                    f"MRV: {result['MRV AC3']}, Degree: {result['Degree AC3']}",
                    f"MRV: {result['MRV Backtracking']}, Degree: {result['Degree Backtracking']}",
                    sum([result['MRV AC3'], result['Degree AC3'], result['MRV Backtracking'], result['Degree Backtracking']]),
                    result["MRV AC3"],
                    result["Degree AC3"],
                    result["MRV Backtracking"],
                    result["Degree Backtracking"],
                    result["Empty Cells"],
                    result["Constraint Checks"],
                    result["Complexity"],
                    result["Solved"]
                ])

        print(f"\nAll tests completed. Results saved to {output_file}")

    @staticmethod
    def process_task(task):
        sudoku_path, heuristic_name, use_mrv_ac3, use_degree_ac3, use_mrv_backtracking, use_degree_backtracking = task
        result = App.solve_sudoku(sudoku_path, use_mrv_ac3, use_degree_ac3, use_mrv_backtracking, use_degree_backtracking)
        result["Combination"] = heuristic_name
        return result

    @staticmethod
    def start():
        while True:
            print("Choose an option:")
            print("1. Solve a specific Sudoku file")
            print("2. Test all Sudoku files in parallel")
            choice = input("Enter choice (1-2): ")
            print("\n")

            if choice == '1':
                file_num = input("Enter Sudoku file (1-5): ")
                print("\n")

                file = None
                for filename in os.listdir(sudoku_folder):
                    if file_num in filename:
                        file = filename
                        break
                if file is not None:
                    result = App.solve_sudoku(os.path.join(sudoku_folder, file))
                    print(f"Solved: {result['Solved']}, Complexity: {result['Complexity']}")
                else:
                    print("Invalid choice")
            elif choice == '2':
                App.test_all_sudokus_parallel()
            else:
                print("Invalid choice")

            continue_input = input("Continue? (yes/no): ")
            if continue_input.lower() != 'yes':
                break

if __name__ == "__main__":
    App.start()
