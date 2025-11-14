#!/usr/bin/env python3
"""
Traffic Simulation Game (Tkinter UI)
- Displays the network graph with random capacities per round
- Asks player for name and max-flow guess from A -> T
- Computes max flow using Edmonds-Karp and Dinic, times both
- Saves correct answers and timing information to SQLite DB
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
from maxflow import edmonds_karp, dinic
from db import init_db, save_game_result
import threading
import statistics
import matplotlib.pyplot as plt

# Graph topology as per the problem (directed)
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
    g = {}
    for u in NODES:
        g[u] = {}
    for u,v in EDGES:
        cap = random.randint(5,15)
        g[u][v] = cap
    return g

def build_networkx_graph(cap_graph):
    G = nx.DiGraph()
    for n in NODES:
        G.add_node(n)
    for u,v in EDGES:
        G.add_edge(u,v,capacity=cap_graph[u][v])
    return G

class TrafficGameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traffic Simulation Game")
        self.geometry("1000x700")
        init_db()  # ensure DB is ready
        self.current_graph = generate_random_capacity_graph()
        self.round = 1
        self.history_times = []  # list of (ek_time_ms, dinic_time_ms)
        self._build_ui()

    def _build_ui(self):
        # Left: canvas with network graph
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(6,6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=left)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # Prevent canvas from grabbing keyboard focus at startup
        try:
            self.canvas.get_tk_widget().configure(takefocus=0)
        except Exception:
            pass

        # Right: controls
        right = ttk.Frame(self, width=300)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        lbl = ttk.Label(right, text="Player name:")
        lbl.pack(anchor=tk.W, pady=(10,0))
        self.name_entry = ttk.Entry(right)
        self.name_entry.pack(fill=tk.X, padx=2)

        lbl2 = ttk.Label(right, text="Enter your max-flow guess (A → T):")
        lbl2.pack(anchor=tk.W, pady=(10,0))
        self.guess_entry = ttk.Entry(right)
        self.guess_entry.pack(fill=tk.X, padx=2)

        # Live-validate guess to digits only (allows empty string)
        vcmd = (self.register(self._validate_guess), '%P')
        self.guess_entry.config(validate='key', validatecommand=vcmd)

        # Bind Enter to submit for quick keyboard use
        self.name_entry.bind('<Return>', lambda e: self.on_submit())
        self.guess_entry.bind('<Return>', lambda e: self.on_submit())

        self.play_btn = ttk.Button(right, text="Submit Guess & Run Algorithms", command=self.on_submit)
        self.play_btn.pack(fill=tk.X, pady=(10,0))

        self.next_round_btn = ttk.Button(right, text="New Random Round", command=self.new_round)
        self.next_round_btn.pack(fill=tk.X, pady=(5,0))

        self.results_text = tk.Text(right, height=18, width=40, state=tk.DISABLED)
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(10,0))

        # Bottom: timing chart button
        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.chart_btn = ttk.Button(bottom, text="Show Timing Chart (Rounds)", command=self.show_timing_chart)
        self.chart_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.status_var = tk.StringVar(value=f"Round {self.round}")
        status = ttk.Label(bottom, textvariable=self.status_var)
        status.pack(side=tk.RIGHT, padx=5)

        # Ensure entries are enabled and set initial focus to name
        self.name_entry.config(state='normal', takefocus=1)
        self.guess_entry.config(state='normal', takefocus=1)
        self.name_entry.focus_set()

        self.draw_graph()

    def _validate_guess(self, proposed):
        # Allow empty (so user can delete) or a string of digits (non-negative integers)
        if proposed == "":
            return True
        return proposed.isdigit()

    def draw_graph(self):
        self.ax.clear()
        G = build_networkx_graph(self.current_graph)
        pos = {
            "A":(0,0.5),"B":(1,0.8),"C":(1,0.5),"D":(1,0.2),
            "E":(2,0.8),"F":(2,0.3),"G":(3,0.7),"H":(3,0.25),"T":(4,0.5)
        }
        edge_labels = {(u,v):str(self.current_graph[u][v]) for u,v in EDGES}
        nx.draw(G, pos, ax=self.ax, with_labels=True, node_size=900, node_color="#ffd966")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=self.ax)
        self.ax.set_title(f"Traffic Network (Round {self.round})")
        self.canvas.draw()
        # After drawing, ensure focus returns to name entry so typing works immediately
        try:
            self.name_entry.focus_set()
        except Exception:
            pass

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
        # Extra safety: ensure entries are enabled
        try:
            if self.name_entry.cget('state') != 'normal':
                self.name_entry.config(state='normal')
            if self.guess_entry.cget('state') != 'normal':
                self.guess_entry.config(state='normal')
        except Exception:
            pass

        try:
            name, guess = self.validate_inputs()
        except Exception as e:
            messagebox.showerror("Validation error", str(e))
            return

        # Run algorithms on a worker thread to avoid UI block
        self.play_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._compute_and_handle, args=(name, guess), daemon=True)
        thread.start()

    def _compute_and_handle(self, name, guess):
        try:
            # Compute Edmonds-Karp
            graph_copy = {u:dict(vs) for u,vs in self.current_graph.items()}
            t0 = time.perf_counter()
            ek_flow = edmonds_karp(graph_copy, "A", "T")
            t1 = time.perf_counter()
            ek_ms = (t1 - t0) * 1000

            # Compute Dinic
            graph_copy2 = {u:dict(vs) for u,vs in self.current_graph.items()}
            t2 = time.perf_counter()
            dinic_flow = dinic(graph_copy2, "A", "T")
            t3 = time.perf_counter()
            dinic_ms = (t3 - t2) * 1000

            # Save times for round chart
            self.history_times.append((ek_ms, dinic_ms))

            correct_flow = ek_flow
            alg_disagree = False
            if dinic_flow != ek_flow:
                # Algorithms disagree; prefer max of both as the "correct" but indicate disagreement
                alg_disagree = True
                correct_flow = max(ek_flow, dinic_flow)

            is_correct = (guess == correct_flow)

            # Save to DB only if correct
            if is_correct:
                save_game_result(name=name, guess=guess, correct_flow=correct_flow,
                                 is_correct=1, ek_time_ms=ek_ms, dinic_time_ms=dinic_ms)
            else:
                # still save the attempt (is_correct=0)
                save_game_result(name=name, guess=guess, correct_flow=correct_flow,
                                 is_correct=0, ek_time_ms=ek_ms, dinic_time_ms=dinic_ms)

            # Update UI
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

            self._append_results("\n".join(result_lines) + "\n" + "-"*40 + "\n")
        except Exception as e:
            self._append_results(f"Error during computation: {e}\n")
        finally:
            # re-enable button and keep focus for convenience
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
        self.current_graph = generate_random_capacity_graph()
        self.round += 1
        self.status_var.set(f"Round {self.round}")
        self.draw_graph()

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
    app = TrafficGameApp()
    app.mainloop()