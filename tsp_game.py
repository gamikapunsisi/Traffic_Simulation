import random
import time
import sqlite3
import itertools
from typing import List, Tuple, Dict, Optional
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np


class TSPAlgorithm(ABC):
    """Abstract base class for TSP algorithms"""
    
    @abstractmethod
    def solve(self, distance_matrix: List[List[int]], start_city: int, cities_to_visit: List[int]) -> Tuple[List[int], int, float]:
        """
        Solve TSP problem
        Returns: (route, total_distance, execution_time)
        """
        pass
    
    @abstractmethod
    def get_complexity(self) -> str:
        """Return time complexity of the algorithm"""
        pass


class BruteForceAlgorithm(TSPAlgorithm):
    """Brute Force TSP Algorithm - O(n!)"""
    
    def solve(self, distance_matrix: List[List[int]], start_city: int, cities_to_visit: List[int]) -> Tuple[List[int], int, float]:
        start_time = time.time()
        
        if len(cities_to_visit) > 8:  # Limit for performance
            raise ValueError("Brute force limited to 8 cities for performance")
        
        min_distance = float('inf')
        best_route = []
        
        # Generate all permutations of cities to visit
        for perm in itertools.permutations(cities_to_visit):
            route = [start_city] + list(perm) + [start_city]
            distance = self._calculate_route_distance(distance_matrix, route)
            
            if distance < min_distance:
                min_distance = distance
                best_route = route
        
        execution_time = time.time() - start_time
        return best_route, min_distance, execution_time
    
    def _calculate_route_distance(self, distance_matrix: List[List[int]], route: List[int]) -> int:
        """Calculate total distance for a given route"""
        total_distance = 0
        for i in range(len(route) - 1):
            total_distance += distance_matrix[route[i]][route[i + 1]]
        return total_distance
    
    def get_complexity(self) -> str:
        return "O(n!) - Factorial time complexity"


class NearestNeighborAlgorithm(TSPAlgorithm):
    """Nearest Neighbor Heuristic - O(n²)"""
    
    def solve(self, distance_matrix: List[List[int]], start_city: int, cities_to_visit: List[int]) -> Tuple[List[int], int, float]:
        start_time = time.time()
        
        route = [start_city]
        unvisited = cities_to_visit.copy()
        current_city = start_city
        total_distance = 0
        
        while unvisited:
            nearest_city = min(unvisited, key=lambda city: distance_matrix[current_city][city])
            total_distance += distance_matrix[current_city][nearest_city]
            route.append(nearest_city)
            unvisited.remove(nearest_city)
            current_city = nearest_city
        
        # Return to start city
        total_distance += distance_matrix[current_city][start_city]
        route.append(start_city)
        
        execution_time = time.time() - start_time
        return route, total_distance, execution_time
    
    def get_complexity(self) -> str:
        return "O(n²) - Quadratic time complexity"


class DynamicProgrammingAlgorithm(TSPAlgorithm):
    """Dynamic Programming (Held-Karp) Algorithm - O(n²2ⁿ)"""
    
    def solve(self, distance_matrix: List[List[int]], start_city: int, cities_to_visit: List[int]) -> Tuple[List[int], int, float]:
        start_time = time.time()
        
        if len(cities_to_visit) > 15:  # Limit for performance
            raise ValueError("Dynamic programming limited to 15 cities for performance")
        
        n = len(cities_to_visit)
        all_cities = [start_city] + cities_to_visit
        
        # Create city index mapping
        city_indices = {city: i for i, city in enumerate(all_cities)}
        
        # DP table: dp[mask][i] = minimum cost to visit cities in mask ending at city i
        dp = {}
        parent = {}
        
        # Base case: start from home city
        dp[(1, 0)] = 0
        
        # Fill DP table
        for mask in range(1, 1 << (n + 1)):
            for u in range(n + 1):
                if not (mask & (1 << u)):
                    continue
                
                prev_mask = mask ^ (1 << u)
                if prev_mask == 0:
                    continue
                
                min_cost = float('inf')
                best_prev = -1
                
                for v in range(n + 1):
                    if prev_mask & (1 << v):
                        cost = dp.get((prev_mask, v), float('inf')) + distance_matrix[all_cities[v]][all_cities[u]]
                        if cost < min_cost:
                            min_cost = cost
                            best_prev = v
                
                if min_cost != float('inf'):
                    dp[(mask, u)] = min_cost
                    parent[(mask, u)] = best_prev
        
        # Find minimum cost to return to start
        final_mask = (1 << (n + 1)) - 1
        min_cost = float('inf')
        last_city = -1
        
        for i in range(1, n + 1):
            cost = dp.get((final_mask ^ 1, i), float('inf')) + distance_matrix[all_cities[i]][all_cities[0]]
            if cost < min_cost:
                min_cost = cost
                last_city = i
        
        # Reconstruct path
        route = self._reconstruct_path(parent, final_mask ^ 1, last_city, all_cities)
        route.append(all_cities[0])  # Return to start
        
        execution_time = time.time() - start_time
        return route, min_cost, execution_time
    
    def _reconstruct_path(self, parent: Dict, mask: int, last: int, all_cities: List[int]) -> List[int]:
        """Reconstruct the optimal path"""
        if mask == 1:
            return [all_cities[0]]
        
        prev = parent.get((mask, last), -1)
        if prev == -1:
            return [all_cities[0]]
        
        path = self._reconstruct_path(parent, mask ^ (1 << last), prev, all_cities)
        path.append(all_cities[last])
        return path
    
    def get_complexity(self) -> str:
        return "O(n²2ⁿ) - Exponential time complexity with polynomial factor"


class GameDatabase:
    """Database manager for game results"""
    
    def __init__(self, db_name: str = "tsp_game.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Game results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                home_city CHAR(1) NOT NULL,
                selected_cities TEXT NOT NULL,
                shortest_route TEXT NOT NULL,
                total_distance INTEGER NOT NULL,
                algorithm_used TEXT NOT NULL,
                execution_time REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Algorithm performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS algorithm_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                algorithm_name TEXT NOT NULL,
                num_cities INTEGER NOT NULL,
                execution_time REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_game_result(self, player_name: str, home_city: str, selected_cities: List[str], 
                        route: List[int], distance: int, algorithm: str, exec_time: float):
        """Save game result to database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cities_str = ','.join(selected_cities)
        route_str = ','.join(map(str, route))
        
        cursor.execute('''
            INSERT INTO game_results 
            (player_name, home_city, selected_cities, shortest_route, total_distance, algorithm_used, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (player_name, home_city, cities_str, route_str, distance, algorithm, exec_time))
        
        conn.commit()
        conn.close()
    
    def save_algorithm_performance(self, algorithm_name: str, num_cities: int, exec_time: float):
        """Save algorithm performance metrics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO algorithm_performance (algorithm_name, num_cities, execution_time)
            VALUES (?, ?, ?)
        ''', (algorithm_name, num_cities, exec_time))
        
        conn.commit()
        conn.close()


class TSPGameGUI:
    """Graphical User Interface for TSP Game"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Traveling Salesman Problem Game")
        self.root.geometry("800x600")
        
        self.cities = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        self.distance_matrix = []
        self.home_city = None
        self.selected_cities = []
        
        self.algorithms = {
            'Brute Force': BruteForceAlgorithm(),
            'Nearest Neighbor': NearestNeighborAlgorithm(),
            'Dynamic Programming': DynamicProgrammingAlgorithm()
        }
        
        self.database = GameDatabase()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Traveling Salesman Problem Game", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Player name
        ttk.Label(main_frame, text="Player Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.player_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.player_name_var, width=30).grid(row=1, column=1, pady=5)
        
        # Start new game button
        ttk.Button(main_frame, text="Start New Game", command=self.start_new_game).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Game info frame
        self.game_frame = ttk.LabelFrame(main_frame, text="Game Information", padding="10")
        self.game_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Home city display
        self.home_city_label = ttk.Label(self.game_frame, text="Home City: Not set")
        self.home_city_label.grid(row=0, column=0, sticky=tk.W)
        
        # Cities selection frame
        cities_frame = ttk.LabelFrame(main_frame, text="Select Cities to Visit", padding="10")
        cities_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.city_vars = {}
        for i, city in enumerate(self.cities):
            var = tk.BooleanVar()
            self.city_vars[city] = var
            ttk.Checkbutton(cities_frame, text=f"City {city}", variable=var).grid(row=i//5, column=i%5, sticky=tk.W, padx=5, pady=2)
        
        # Algorithm selection
        algo_frame = ttk.LabelFrame(main_frame, text="Algorithm Selection", padding="10")
        algo_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.algorithm_var = tk.StringVar(value="Nearest Neighbor")
        for i, algo_name in enumerate(self.algorithms.keys()):
            ttk.Radiobutton(algo_frame, text=algo_name, variable=self.algorithm_var, 
                          value=algo_name).grid(row=i//3, column=i%3, sticky=tk.W, padx=10)
        
        # Solve button
        ttk.Button(main_frame, text="Solve TSP", command=self.solve_tsp).grid(row=6, column=0, columnspan=2, pady=10)
        
        # Results frame
        self.results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        self.results_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Results text
        self.results_text = tk.Text(self.results_frame, height=8, width=80)
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def start_new_game(self):
        """Start a new game round"""
        try:
            if not self.player_name_var.get().strip():
                messagebox.showerror("Error", "Please enter your name")
                return
            
            # Generate random distance matrix
            self.distance_matrix = self.generate_distance_matrix()
            
            # Choose random home city
            self.home_city = random.choice(self.cities)
            self.home_city_label.config(text=f"Home City: {self.home_city}")
            
            # Reset city selections
            for var in self.city_vars.values():
                var.set(False)
            
            # Clear results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"New game started!\nHome City: {self.home_city}\n")
            self.results_text.insert(tk.END, "Select cities to visit and choose an algorithm.\n\n")
            
            messagebox.showinfo("New Game", f"New game started!\nHome City: {self.home_city}\nSelect cities to visit.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start new game: {str(e)}")
    
    def generate_distance_matrix(self) -> List[List[int]]:
        """Generate random symmetric distance matrix"""
        n = len(self.cities)
        matrix = [[0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                distance = random.randint(50, 100)
                matrix[i][j] = distance
                matrix[j][i] = distance
        
        return matrix
    
    def solve_tsp(self):
        """Solve TSP with selected algorithm"""
        try:
            # Validation
            if not self.player_name_var.get().strip():
                messagebox.showerror("Error", "Please enter your name")
                return
            
            if self.home_city is None:
                messagebox.showerror("Error", "Please start a new game first")
                return
            
            # Get selected cities
            selected_cities = [city for city, var in self.city_vars.items() if var.get()]
            
            if not selected_cities:
                messagebox.showerror("Error", "Please select at least one city to visit")
                return
            
            if self.home_city in selected_cities:
                messagebox.showerror("Error", "Home city cannot be in the cities to visit")
                return
            
            # Convert city names to indices
            home_index = self.cities.index(self.home_city)
            city_indices = [self.cities.index(city) for city in selected_cities]
            
            # Get selected algorithm
            algorithm_name = self.algorithm_var.get()
            algorithm = self.algorithms[algorithm_name]
            
            # Solve TSP
            self.results_text.insert(tk.END, f"\nSolving with {algorithm_name}...\n")
            self.root.update()
            
            route, distance, exec_time = algorithm.solve(self.distance_matrix, home_index, city_indices)
            
            # Convert route back to city names
            route_cities = [self.cities[i] for i in route]
            
            # Display results
            self.display_results(algorithm_name, route_cities, distance, exec_time, algorithm.get_complexity())
            
            # Save to database
            self.database.save_game_result(
                self.player_name_var.get(),
                self.home_city,
                selected_cities,
                route,
                distance,
                algorithm_name,
                exec_time
            )
            
            self.database.save_algorithm_performance(algorithm_name, len(selected_cities), exec_time)
            
            messagebox.showinfo("Success", "TSP solved and results saved!")
        
        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to solve TSP: {str(e)}")
    
    def display_results(self, algorithm_name: str, route: List[str], distance: int, 
                       exec_time: float, complexity: str):
        """Display TSP solution results"""
        self.results_text.insert(tk.END, f"\n{'='*50}\n")
        self.results_text.insert(tk.END, f"Algorithm: {algorithm_name}\n")
        self.results_text.insert(tk.END, f"Complexity: {complexity}\n")
        self.results_text.insert(tk.END, f"Optimal Route: {' -> '.join(route)}\n")
        self.results_text.insert(tk.END, f"Total Distance: {distance} km\n")
        self.results_text.insert(tk.END, f"Execution Time: {exec_time:.6f} seconds\n")
        self.results_text.insert(tk.END, f"{'='*50}\n")
        
        # Auto-scroll to bottom
        self.results_text.see(tk.END)
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Main function to run the TSP game"""
    try:
        app = TSPGameGUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")


if __name__ == "__main__":
    main()