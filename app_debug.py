#!/usr/bin/env python3
"""
Instrumented Traffic Simulation Game (DEBUG) with flow-path visualization.

- Uses edmonds_karp_with_flows to obtain per-edge flow assignment
- Draws edges with color/width proportional to flow and labels "flow/cap"
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
from maxflow import edmonds_karp, edmonds_karp_with_flows, dinic
from db import init_db, save_game_result
import threading
import matplotlib.pyplot as plt
import sys

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stdout, flush=True)

# Graph topology
NODES = ["A","B","C","D","E","F","G","H","T"]
EDGES = [
    ("A","B"), ("A","C"), ("A","D"),
    ("B","E"), ("B","F"),
    ("C","E"), ("C","F"),
    ("D","F"),
    ("E","G"), ("E","H"),
    ("F","H"),
    ("G","T"), ("H","T")
]

def generate_random_capacity_graph():
    g = {u: {} for u in NODES}
    for u,v in EDGES:
        g[u][v] = random.randint(5,15)
    return g

def build_networkx_graph(cap_graph):
    G = nx.DiGraph()
    for n in NODES:
        G.add_node(n)
    for u,v in EDGES:
        G.add_edge(u,v,capacity=cap_graph[u][v])
    return G

class TrafficGameDebugApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traffic Simulation Game (DEBUG)")
        self.geometry("1000x700")
        init_db()
        self.current_graph = generate_random_capacity_graph()
        self.round = 1
        self.history_times = []
        self._build_ui()
        # Global click logger
        self.bind_all("<Button-1>", self._on_any_click, add="+")

    def _build_ui(self):
        # Left: canvas
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(6,6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=left)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        try:
            self.canvas.get_tk_widget().configure(takefocus=0)
        except Exception:
            pass

        # Right: controls
        right = ttk.Frame(self, width=320)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(right, text="Player name:").pack(anchor=tk.W, pady=(10,0))
        self.name_entry = ttk.Entry(right)
        self.name_entry.pack(fill=tk.X, padx=2)

        ttk.Label(right, text="Enter your max-flow guess (A → T):").pack(anchor=tk.W, pady=(10,0))
        self.guess_entry = ttk.Entry(right)
        self.guess_entry.pack(fill=tk.X, padx=2)

        # Bindings & validation
        self.guess_entry.config(validate='key', validatecommand=(self.register(self._validate_guess), '%P'))
        self.name_entry.bind('<Return>', lambda e: self.on_submit())
        self.guess_entry.bind('<Return>', lambda e: self.on_submit())

        self.play_btn = ttk.Button(right, text="Submit Guess & Run Algorithms", command=self.on_submit)
        self.play_btn.pack(fill=tk.X, pady=(10,0))
        self.play_btn.bind("<Button-1>", lambda e: log("play_btn received <Button-1>"), add="+")

        self.next_round_btn = ttk.Button(right, text="New Random Round", command=self.new_round)
        self.next_round_btn.pack(fill=tk.X, pady=(5,0))
        self.next_round_btn.bind("<Button-1>", lambda e: log("next_round_btn received <Button-1>"), add="+")

        self.results_text = tk.Text(right, height=18, width=40, state=tk.DISABLED)
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(10,0))

        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.chart_btn = ttk.Button(bottom, text="Show Timing Chart (Rounds)", command=self.show_timing_chart)
        self.chart_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.status_var = tk.StringVar(value=f"Round {self.round}")
        ttk.Label(bottom, textvariable=self.status_var).pack(side=tk.RIGHT, padx=5)

        # focus
        self.name_entry.focus_set()
        self.draw_graph()

    def _on_any_click(self, event):
        widget = event.widget
        log(f"Global click at ({event.x},{event.y}) on widget: {widget} type={type(widget)}")
        focused = self.focus_get()
        log(f"Focus widget: {focused} ({type(focused) if focused else 'None'})")

    def _validate_guess(self, proposed):
        if proposed == "":
            return True
        return proposed.isdigit()

    def draw_graph(self, flow_dict=None):
        """
        Draw network. If flow_dict provided (mapping (u,v)->flow), highlight edges carrying flow.
        """
        self.ax.clear()
        G = build_networkx_graph(self.current_graph)
        pos = {
            "A":(0,0.5),"B":(1,0.8),"C":(1,0.5),"D":(1,0.2),
            "E":(2,0.8),"F":(2,0.3),"G":(3,0.7),"H":(3,0.25),"T":(4,0.5)
        }

        # Prepare edge colors, widths, and labels
        edge_colors = []
        edge_widths = []
        edge_labels = {}
        # maximum possible flow on an edge for sensible scaling
        max_cap = max(self.current_graph[u][v] for u,v in EDGES)

        for u,v in EDGES:
            cap = self.current_graph[u][v]
            flow = 0
            if flow_dict and (u,v) in flow_dict:
                flow = flow_dict[(u,v)]
            # color red if carries flow, gray otherwise
            color = '#d9534f' if flow > 0 else '#777777'
            width = 1.0 + (flow / max(1, max_cap)) * 6.0  # scale width
            edge_colors.append(color)
            edge_widths.append(width)
            edge_labels[(u,v)] = f"{flow}/{cap}"

        # draw nodes
        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_size=900, node_color="#ffd966")
        nx.draw_networkx_labels(G, pos, ax=self.ax)

        # draw edges with colors and widths
        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color=edge_colors, width=edge_widths, arrowsize=20)
        # draw edge labels showing flow/capacity
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=self.ax, font_color='black')

        title = f"Traffic Network (Round {self.round})"
        if flow_dict:
            title += " — flow shown as flow/cap"
        self.ax.set_title(title)
        self.canvas.draw()

    def validate_inputs(self):
        name = self.name_entry.get().strip()
        if not name:
            raise ValueError("Player name cannot be empty.")
        guess_s = self.guess_entry.get().strip()
        if not guess_s:
            raise ValueError("Please enter a numeric guess for max flow.")
        try:
            guess = int(guess_s)
        except ValueError:
            raise ValueError("Guess must be an integer.")
        if guess < 0:
            raise ValueError("Guess must be non-negative.")
        return name, guess

    def on_submit(self):
        log("on_submit() called")
        try:
            if self.name_entry.cget('state') != 'normal':
                self.name_entry.config(state='normal')
            if self.guess_entry.cget('state') != 'normal':
                self.guess_entry.config(state='normal')
        except Exception as e:
            log(f"Error ensuring entries enabled: {e}")

        try:
            name, guess = self.validate_inputs()
        except Exception as e:
            log(f"Validation error: {e}")
            messagebox.showerror("Validation error", str(e))
            return

        log(f"Inputs validated: name={name!r}, guess={guess}")
        self.play_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._compute_and_handle, args=(name, guess), daemon=True)
        thread.start()

    def _compute_and_handle(self, name, guess):
        log("_compute_and_handle started")
        try:
            # Use the Edmonds-Karp variant that also returns flows per edge
            graph_copy = {u:dict(vs) for u,vs in self.current_graph.items()}
            t0 = time.perf_counter()
            ek_flow, ek_flow_dict = edmonds_karp_with_flows(graph_copy, "A", "T")
            t1 = time.perf_counter()
            ek_ms = (t1 - t0) * 1000

            # Also time Dinic for comparison (flow only)
            graph_copy2 = {u:dict(vs) for u,vs in self.current_graph.items()}
            t2 = time.perf_counter()
            dinic_flow = dinic(graph_copy2, "A", "T")
            t3 = time.perf_counter()
            dinic_ms = (t3 - t2) * 1000

            log(f"Computed flows ek={ek_flow}, dinic={dinic_flow}; times ek={ek_ms:.2f}ms dinic={dinic_ms:.2f}ms")
            self.history_times.append((ek_ms, dinic_ms))

            correct_flow = ek_flow
            alg_disagree = False
            if dinic_flow != ek_flow:
                alg_disagree = True
                correct_flow = max(ek_flow, dinic_flow)

            is_correct = (guess == correct_flow)

            save_game_result(name=name, guess=guess, correct_flow=correct_flow,
                             is_correct=(1 if is_correct else 0),
                             ek_time_ms=ek_ms, dinic_time_ms=dinic_ms)
            log("Saved game result to DB")

            result_lines = [
                f"Player: {name}",
                f"Your guess: {guess}",
                f"Edmonds-Karp flow: {ek_flow} | time: {ek_ms:.2f} ms",
                f"Dinic flow: {dinic_flow} | time: {dinic_ms:.2f} ms",
            ]
            if alg_disagree:
                result_lines.append("Warning: algorithms returned different values. Using max for correctness.")
            if is_correct:
                result_lines.append("Result: YOU WIN! Correct answer saved to database.")
            else:
                result_lines.append("Result: You LOSE. Correct max flow is " + str(correct_flow))

            # Append text results
            self._append_results("\n".join(result_lines) + "\n" + "-"*40 + "\n")

            # Update visualization on the main thread: draw flows using ek_flow_dict
            def update_viz():
                self.draw_graph(flow_dict=ek_flow_dict)
            self.after(0, update_viz)

        except Exception as e:
            log(f"Exception during compute: {e}")
            self._append_results(f"Error during computation: {e}\n")
        finally:
            log("_compute_and_handle finished")
            def finish_ui():
                self.play_btn.config(state=tk.NORMAL)
                try:
                    self.name_entry.focus_set()
                except Exception:
                    pass
            self.after(0, finish_ui)

    def _append_results(self, text):
        def _ui():
            self.results_text.config(state=tk.NORMAL)
            self.results_text.insert(tk.END, text)
            self.results_text.see(tk.END)
            self.results_text.config(state=tk.DISABLED)
        self.after(0, _ui)

    def new_round(self):
        log("new_round() called")
        self.current_graph = generate_random_capacity_graph()
        self.round += 1
        self.status_var.set(f"Round {self.round}")
        # draw without flow overlay (fresh capacities)
        self.draw_graph(flow_dict=None)
        log("new_round() finished")

    def show_timing_chart(self):
        if not self.history_times:
            messagebox.showinfo("No data", "No timing data yet — play some rounds first.")
            return
        ek_times = [t[0] for t in self.history_times]
        dinic_times = [t[1] for t in self.history_times]
        rounds = list(range(1, len(ek_times)+1))
        plt.figure(figsize=(8,4))
        plt.plot(rounds, ek_times, marker='o', label='Edmonds-Karp (ms)')
        plt.plot(rounds, dinic_times, marker='o', label='Dinic (ms)')
        plt.xlabel("Round")
        plt.ylabel("Time (ms)")
        plt.title("Algorithm Times per Round")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    log("Starting TrafficGameDebugApp (with flow visualization)")
    app = TrafficGameDebugApp()
    app.mainloop()
    log("App mainloop exited")