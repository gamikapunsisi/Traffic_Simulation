#!/usr/bin/env python3
"""
Traffic Simulation Game - Improved Version
Fixed issues and added comprehensive improvements
"""
import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import sqlite3
from datetime import datetime
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import matplotlib.pyplot as plt
import sys
from typing import Dict, Tuple, Optional

def log(msg):
    """Thread-safe logging with timestamp"""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stdout, flush=True)

# Graph topology
NODES = ["A", "B", "C", "D", "E", "F", "G", "H", "T"]
EDGES = [
    ("A", "B"), ("A", "C"), ("A", "D"),
    ("B", "E"), ("B", "F"),
    ("C", "E"), ("C", "F"),
    ("D", "F"),
    ("E", "G"), ("E", "H"),
    ("F", "H"),
    ("G", "T"), ("H", "T")
]

# Constants
MIN_CAPACITY = 5
MAX_CAPACITY = 15
MAX_GUESS_VALUE = 1000


def generate_random_capacity_graph() -> Dict[str, Dict[str, int]]:
    """Generate a random capacity graph with validation"""
    g = {u: {} for u in NODES}
    for u, v in EDGES:
        capacity = random.randint(MIN_CAPACITY, MAX_CAPACITY)
        g[u][v] = capacity
    return g


def build_networkx_graph(cap_graph: Dict[str, Dict[str, int]]) -> nx.DiGraph:
    """Build NetworkX graph from capacity dictionary"""
    G = nx.DiGraph()
    for n in NODES:
        G.add_node(n)
    for u, v in EDGES:
        if u in cap_graph and v in cap_graph[u]:
            G.add_edge(u, v, capacity=cap_graph[u][v])
    return G


# ============= MAX FLOW ALGORITHMS =============

def edmonds_karp_with_flows(graph: Dict, source: str, sink: str) -> Tuple[int, Dict]:
    """
    Edmonds-Karp algorithm returning max flow and flow dictionary
    
    Args:
        graph: Adjacency list with capacities
        source: Source node
        sink: Sink node
    
    Returns:
        Tuple of (max_flow, flow_dict) where flow_dict maps (u,v) -> flow
    """
    try:
        # Create residual graph
        residual = {u: dict(neighbors) for u, neighbors in graph.items()}
        flow_dict = {}
        
        # Initialize flow dictionary
        for u in graph:
            for v in graph[u]:
                flow_dict[(u, v)] = 0
        
        def bfs_find_path():
            """BFS to find augmenting path"""
            queue = [(source, [source])]
            visited = {source}
            
            while queue:
                node, path = queue.pop(0)
                
                if node == sink:
                    return path
                
                if node in residual:
                    for neighbor, capacity in residual[node].items():
                        if neighbor not in visited and capacity > 0:
                            visited.add(neighbor)
                            queue.append((neighbor, path + [neighbor]))
            
            return None
        
        max_flow = 0
        
        while True:
            path = bfs_find_path()
            if not path:
                break
            
            # Find minimum capacity along path
            flow = float('inf')
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                flow = min(flow, residual[u][v])
            
            # Update residual graph and flow
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                residual[u][v] -= flow
                if v not in residual:
                    residual[v] = {}
                residual[v][u] = residual[v].get(u, 0) + flow
                
                # Track actual flow on original edges
                if (u, v) in flow_dict:
                    flow_dict[(u, v)] += flow
            
            max_flow += flow
        
        return max_flow, flow_dict
    
    except Exception as e:
        log(f"Error in edmonds_karp_with_flows: {e}")
        raise


def dinic(graph: Dict, source: str, sink: str) -> int:
    """
    Dinic's algorithm for max flow
    
    Args:
        graph: Adjacency list with capacities
        source: Source node
        sink: Sink node
    
    Returns:
        Maximum flow value
    """
    try:
        # Create residual graph
        residual = {u: dict(neighbors) for u, neighbors in graph.items()}
        
        def bfs_level():
            """Build level graph using BFS"""
            level = {source: 0}
            queue = [source]
            
            while queue:
                u = queue.pop(0)
                
                if u in residual:
                    for v, cap in residual[u].items():
                        if v not in level and cap > 0:
                            level[v] = level[u] + 1
                            queue.append(v)
            
            return level if sink in level else None
        
        def dfs_flow(u, pushed, level, start):
            """Send flow using DFS"""
            if u == sink:
                return pushed
            
            if u not in residual:
                return 0
            
            while start[u] < len(list(residual[u].keys())):
                neighbors = list(residual[u].keys())
                if start[u] >= len(neighbors):
                    break
                    
                v = neighbors[start[u]]
                cap = residual[u][v]
                
                if v in level and level[v] == level[u] + 1 and cap > 0:
                    flow = dfs_flow(v, min(pushed, cap), level, start)
                    
                    if flow > 0:
                        residual[u][v] -= flow
                        if v not in residual:
                            residual[v] = {}
                        residual[v][u] = residual[v].get(u, 0) + flow
                        return flow
                
                start[u] += 1
            
            return 0
        
        max_flow = 0
        
        while True:
            level = bfs_level()
            if not level:
                break
            
            start = {node: 0 for node in graph}
            
            while True:
                flow = dfs_flow(source, float('inf'), level, start)
                if flow == 0:
                    break
                max_flow += flow
        
        return max_flow
    
    except Exception as e:
        log(f"Error in dinic: {e}")
        raise


# ============= DATABASE MODULE =============

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_name: str = "traffic_game.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Initialize database with proper schema"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    guess INTEGER NOT NULL,
                    correct_flow INTEGER NOT NULL,
                    is_correct INTEGER NOT NULL,
                    ek_time_ms REAL NOT NULL,
                    dinic_time_ms REAL NOT NULL,
                    round_number INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            log("Database initialized successfully")
        
        except sqlite3.Error as e:
            log(f"Database initialization error: {e}")
            raise
        
        finally:
            conn.close()
    
    def save_game_result(self, player_name: str, guess: int, correct_flow: int,
                        is_correct: int, ek_time_ms: float, dinic_time_ms: float,
                        round_number: int = 1):
        """Save game result to database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO game_results 
                (player_name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms, round_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (player_name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms, round_number))
            
            conn.commit()
            log(f"Game result saved for {player_name}")
        
        except sqlite3.Error as e:
            log(f"Database save error: {e}")
            raise
        
        finally:
            conn.close()
    
    def get_player_stats(self, player_name: str) -> Dict:
        """Get statistics for a specific player"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_games,
                    SUM(is_correct) as wins,
                    AVG(ek_time_ms) as avg_ek_time,
                    AVG(dinic_time_ms) as avg_dinic_time
                FROM game_results
                WHERE player_name = ?
            """, (player_name,))
            
            result = cursor.fetchone()
            
            return {
                'total_games': result[0] or 0,
                'wins': result[1] or 0,
                'avg_ek_time': result[2] or 0,
                'avg_dinic_time': result[3] or 0
            }
        
        except sqlite3.Error as e:
            log(f"Database query error: {e}")
            return {}
        
        finally:
            conn.close()


# ============= MAIN APPLICATION =============

class TrafficGameApp(tk.Tk):
    """Main application window for Traffic Simulation Game"""
    
    def __init__(self):
        super().__init__()
        self.title("Traffic Simulation Game")
        self.geometry("1200x750")
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Game state
        self.current_graph = generate_random_capacity_graph()
        self.round = 1
        self.history_times = []
        self.is_processing = False
        
        # Build UI
        self._build_ui()
        
        # Initial draw
        self.draw_graph()
        
        # Set protocol for window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _build_ui(self):
        """Build the user interface"""
        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Graph visualization
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 7))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Right panel: Controls
        right_panel = ttk.Frame(main_container, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        right_panel.pack_propagate(False)
        
        # Title
        title_label = ttk.Label(right_panel, text="Traffic Flow Challenge",
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Player name section
        name_frame = ttk.LabelFrame(right_panel, text="Player Information", padding=10)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Player Name:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(name_frame, font=('Arial', 10))
        self.name_entry.pack(fill=tk.X, pady=(5, 0))
        self.name_entry.bind('<Return>', lambda e: self.guess_entry.focus_set())
        
        # Guess section
        guess_frame = ttk.LabelFrame(right_panel, text="Your Guess", padding=10)
        guess_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(guess_frame, text="Maximum Flow (A → T):").pack(anchor=tk.W)
        
        # Validation for numeric input
        vcmd = (self.register(self._validate_numeric_input), '%P')
        self.guess_entry = ttk.Entry(guess_frame, font=('Arial', 10),
                                     validate='key', validatecommand=vcmd)
        self.guess_entry.pack(fill=tk.X, pady=(5, 0))
        self.guess_entry.bind('<Return>', lambda e: self.on_submit())
        
        # Action buttons
        button_frame = ttk.Frame(right_panel)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.submit_btn = ttk.Button(button_frame, text="Submit Guess",
                                     command=self.on_submit)
        self.submit_btn.pack(fill=tk.X, pady=(0, 5))
        
        self.new_round_btn = ttk.Button(button_frame, text="New Round",
                                        command=self.new_round)
        self.new_round_btn.pack(fill=tk.X, pady=(0, 5))
        
        self.stats_btn = ttk.Button(button_frame, text="View Player Stats",
                                    command=self.show_player_stats)
        self.stats_btn.pack(fill=tk.X)
        
        # Results display
        results_frame = ttk.LabelFrame(right_panel, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollbar for results
        scroll = ttk.Scrollbar(results_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(results_frame, wrap=tk.WORD, height=15,
                                   yscrollcommand=scroll.set, font=('Courier', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.results_text.yview)
        
        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.status_var = tk.StringVar(value=f"Round {self.round} | Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        ttk.Button(status_frame, text="Show Timing Chart",
                  command=self.show_timing_chart).pack(side=tk.RIGHT)
        
        # Set focus
        self.name_entry.focus_set()
    
    def _validate_numeric_input(self, value: str) -> bool:
        """Validate that input is numeric"""
        if value == "":
            return True
        try:
            num = int(value)
            return 0 <= num <= MAX_GUESS_VALUE
        except ValueError:
            return False
    
    def draw_graph(self, flow_dict: Optional[Dict] = None):
        """
        Draw the traffic network graph
        
        Args:
            flow_dict: Optional dictionary mapping (u,v) -> flow value
        """
        try:
            self.ax.clear()
            G = build_networkx_graph(self.current_graph)
            
            # Node positions (optimized layout)
            pos = {
                "A": (0, 0.5), "B": (1, 0.8), "C": (1, 0.5), "D": (1, 0.2),
                "E": (2, 0.8), "F": (2, 0.3), "G": (3, 0.7), "H": (3, 0.25),
                "T": (4, 0.5)
            }
            
            # Calculate edge properties
            edge_colors = []
            edge_widths = []
            edge_labels = {}
            
            max_cap = max(self.current_graph[u][v] for u, v in EDGES)
            
            for u, v in EDGES:
                cap = self.current_graph[u][v]
                flow = 0
                
                if flow_dict and (u, v) in flow_dict:
                    flow = flow_dict[(u, v)]
                
                # Color based on flow utilization
                if flow > 0:
                    utilization = flow / cap
                    if utilization > 0.8:
                        color = '#d9534f'  # Red for high utilization
                    elif utilization > 0.5:
                        color = '#f0ad4e'  # Orange for medium
                    else:
                        color = '#5bc0de'  # Blue for low
                else:
                    color = '#999999'  # Gray for no flow
                
                edge_colors.append(color)
                
                # Width based on flow
                width = 1.5 + (flow / max(1, max_cap)) * 5.0
                edge_widths.append(width)
                
                # Label
                if flow_dict:
                    edge_labels[(u, v)] = f"{flow}/{cap}"
                else:
                    edge_labels[(u, v)] = f"{cap}"
            
            # Draw nodes
            node_colors = ['#90EE90' if n == 'A' else '#FFB6C1' if n == 'T' else '#FFD700' 
                          for n in G.nodes()]
            
            nx.draw_networkx_nodes(G, pos, ax=self.ax, node_size=1000,
                                  node_color=node_colors, edgecolors='black', linewidths=2)
            
            # Draw node labels
            nx.draw_networkx_labels(G, pos, ax=self.ax, font_size=12, font_weight='bold')
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color=edge_colors,
                                  width=edge_widths, arrowsize=20,
                                  connectionstyle='arc3,rad=0.1')
            
            # Draw edge labels
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                        ax=self.ax, font_size=8, font_color='black',
                                        bbox=dict(boxstyle='round,pad=0.3', 
                                                facecolor='white', edgecolor='gray', alpha=0.8))
            
            # Title
            title = f"Traffic Network - Round {self.round}"
            if flow_dict:
                title += " (Flow Distribution)"
            
            self.ax.set_title(title, fontsize=14, fontweight='bold')
            self.ax.axis('off')
            
            self.canvas.draw()
        
        except Exception as e:
            log(f"Error drawing graph: {e}")
            messagebox.showerror("Drawing Error", f"Failed to draw graph: {str(e)}")
    
    def validate_inputs(self) -> Tuple[str, int]:
        """
        Validate user inputs
        
        Returns:
            Tuple of (player_name, guess)
        
        Raises:
            ValueError: If validation fails
        """
        name = self.name_entry.get().strip()
        
        if not name:
            raise ValueError("Player name cannot be empty")
        
        if len(name) > 50:
            raise ValueError("Player name must be 50 characters or less")
        
        guess_str = self.guess_entry.get().strip()
        
        if not guess_str:
            raise ValueError("Please enter your guess for maximum flow")
        
        try:
            guess = int(guess_str)
        except ValueError:
            raise ValueError("Guess must be a valid integer")
        
        if guess < 0:
            raise ValueError("Guess must be non-negative")
        
        if guess > MAX_GUESS_VALUE:
            raise ValueError(f"Guess must be {MAX_GUESS_VALUE} or less")
        
        return name, guess
    
    def on_submit(self):
        """Handle guess submission"""
        if self.is_processing:
            messagebox.showwarning("Processing", "Please wait for current computation to complete")
            return
        
        try:
            name, guess = self.validate_inputs()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return
        
        log(f"Processing submission: name={name}, guess={guess}")
        
        # Disable inputs during processing
        self.is_processing = True
        self.submit_btn.config(state=tk.DISABLED)
        self.new_round_btn.config(state=tk.DISABLED)
        self.status_var.set("Computing maximum flow...")
        
        # Run computation in separate thread
        thread = threading.Thread(target=self._compute_max_flow,
                                 args=(name, guess), daemon=True)
        thread.start()
    
    def _compute_max_flow(self, name: str, guess: int):
        """
        Compute maximum flow using both algorithms
        
        Args:
            name: Player name
            guess: Player's guess
        """
        try:
            # Create graph copies for each algorithm
            graph_ek = {u: dict(vs) for u, vs in self.current_graph.items()}
            graph_dinic = {u: dict(vs) for u, vs in self.current_graph.items()}
            
            # Edmonds-Karp with flow tracking
            t0 = time.perf_counter()
            ek_flow, ek_flow_dict = edmonds_karp_with_flows(graph_ek, "A", "T")
            t1 = time.perf_counter()
            ek_time_ms = (t1 - t0) * 1000
            
            # Dinic's algorithm
            t2 = time.perf_counter()
            dinic_flow = dinic(graph_dinic, "A", "T")
            t3 = time.perf_counter()
            dinic_time_ms = (t3 - t2) * 1000
            
            log(f"Flows computed: EK={ek_flow}, Dinic={dinic_flow}")
            log(f"Times: EK={ek_time_ms:.3f}ms, Dinic={dinic_time_ms:.3f}ms")
            
            # Store timing data
            self.history_times.append((ek_time_ms, dinic_time_ms))
            
            # Determine correctness
            algorithms_agree = (ek_flow == dinic_flow)
            correct_flow = ek_flow  # Use EK as reference
            
            if not algorithms_agree:
                log(f"WARNING: Algorithms disagree! EK={ek_flow}, Dinic={dinic_flow}")
                correct_flow = max(ek_flow, dinic_flow)
            
            is_correct = (guess == correct_flow)
            
            # Save to database
            self.db.save_game_result(
                player_name=name,
                guess=guess,
                correct_flow=correct_flow,
                is_correct=1 if is_correct else 0,
                ek_time_ms=ek_time_ms,
                dinic_time_ms=dinic_time_ms,
                round_number=self.round
            )
            
            # Prepare result message
            result_lines = [
                f"{'='*40}",
                f"ROUND {self.round} RESULTS",
                f"{'='*40}",
                f"Player: {name}",
                f"Your Guess: {guess}",
                f"",
                f"Algorithm Results:",
                f"  Edmonds-Karp: {ek_flow} (Time: {ek_time_ms:.3f} ms)",
                f"  Dinic: {dinic_flow} (Time: {dinic_time_ms:.3f} ms)",
                f""
            ]
            
            if not algorithms_agree:
                result_lines.append("⚠ WARNING: Algorithms produced different results!")
                result_lines.append(f"Using maximum value: {correct_flow}")
                result_lines.append("")
            
            if is_correct:
                result_lines.append("🎉 CORRECT! You win this round!")
                result_lines.append("Your answer has been saved to the database.")
            else:
                result_lines.append("❌ INCORRECT!")
                result_lines.append(f"Correct maximum flow: {correct_flow}")
            
            result_lines.append(f"{'='*40}\n")
            
            result_text = "\n".join(result_lines)
            
            # Update UI on main thread
            self.after(0, lambda: self._display_results(result_text, ek_flow_dict, is_correct))
        
        except Exception as e:
            log(f"Error during computation: {e}")
            error_msg = f"Error during computation: {str(e)}\n"
            self.after(0, lambda: self._display_results(error_msg, None, False))
        
        finally:
            # Re-enable UI
            self.after(0, self._finish_processing)
    
    def _display_results(self, text: str, flow_dict: Optional[Dict], is_correct: bool):
        """Display results in UI"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, text)
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)
        
        # Update graph with flow visualization
        if flow_dict:
            self.draw_graph(flow_dict=flow_dict)
        
        # Show result dialog
        if is_correct:
            messagebox.showinfo("Congratulations!", "You correctly identified the maximum flow!")
        else:
            messagebox.showinfo("Try Again", "Your guess was incorrect. Better luck next time!")
    
    def _finish_processing(self):
        """Re-enable UI after processing"""
        self.is_processing = False
        self.submit_btn.config(state=tk.NORMAL)
        self.new_round_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Round {self.round} | Ready")
        self.name_entry.focus_set()
    
    def new_round(self):
        """Start a new round with a fresh graph"""
        if self.is_processing:
            messagebox.showwarning("Processing", "Please wait for current computation to complete")
            return
        
        self.current_graph = generate_random_capacity_graph()
        self.round += 1
        self.status_var.set(f"Round {self.round} | Ready")
        
        # Clear guess entry
        self.guess_entry.delete(0, tk.END)
        
        # Redraw graph without flow
        self.draw_graph(flow_dict=None)
        
        log(f"New round started: Round {self.round}")
    
    def show_player_stats(self):
        """Show statistics for current player"""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("No Player", "Please enter a player name first")
            return
        
        stats = self.db.get_player_stats(name)
        
        if stats['total_games'] == 0:
            messagebox.showinfo("No Data", f"No game history found for player: {name}")
            return
        
        win_rate = (stats['wins'] / stats['total_games']) * 100 if stats['total_games'] > 0 else 0
        
        message = f"""
Player Statistics for: {name}

Total Games Played: {stats['total_games']}
Games Won: {stats['wins']}
Win Rate: {win_rate:.1f}%

Average Algorithm Times:
  Edmonds-Karp: {stats['avg_ek_time']:.3f} ms
  Dinic: {stats['avg_dinic_time']:.3f} ms
        """
        
        messagebox.showinfo("Player Statistics", message.strip())
    
    def show_timing_chart(self):
        """Display timing comparison chart"""
        if not self.history_times:
            messagebox.showinfo("No Data", "No timing data available. Play some rounds first!")
            return
        
        try:
            ek_times = [t[0] for t in self.history_times]
            dinic_times = [t[1] for t in self.history_times]
            rounds = list(range(1, len(self.history_times) + 1))
            
            plt.figure(figsize=(10, 6))
            plt.plot(rounds, ek_times, marker='o', label='Edmonds-Karp', linewidth=2)
            plt.plot(rounds, dinic_times, marker='s', label="Dinic's Algorithm", linewidth=2)
            
            plt.xlabel("Round Number", fontsize=12)
            plt.ylabel("Computation Time (ms)", fontsize=12)
            plt.title("Algorithm Performance Comparison", fontsize=14, fontweight='bold')
            plt.legend(fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
        
        except Exception as e:
            log(f"Error showing chart: {e}")
            messagebox.showerror("Chart Error", f"Failed to display chart: {str(e)}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_processing:
            if not messagebox.askokcancel("Processing", 
                "Computation in progress. Are you sure you want to quit?"):
                return
        
        self.destroy()


# ============= MAIN ENTRY POINT =============

def main():
    """Main entry point"""
    try:
        log("Starting Traffic Simulation Game")
        app = TrafficGameApp()
        app.mainloop()
        log("Application closed")
    except Exception as e:
        log(f"Fatal error: {e}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")


if __name__ == "__main__":
    main()