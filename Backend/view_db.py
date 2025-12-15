"""
DB viewer for the Traffic Simulation DB (normalized + optional denormalized).

Tabs:
 - Attempts (joined players, game_rounds, algorithm_performance)
 - Players
 - Rounds
 - Performance
 - Denormalized (if game_results exists)

Features:
 - Refresh current tab
 - Copy selected row to clipboard
 - Export current tab to CSV
"""
import sqlite3
import sys
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional, Tuple, List, Any

DEFAULT_DB = "traffic_game.db"


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    return cur.fetchone() is not None


def fetch_attempts(conn: sqlite3.Connection, limit: Optional[int] = 500) -> List[Tuple[Any, ...]]:
    cur = conn.cursor()
    query = """
        SELECT
            ga.attempt_id,
            p.player_name,
            ga.guess,
            ga.correct_flow,
            ga.is_correct,
            gr.round_number,
            ga.attempt_timestamp
        FROM game_attempts ga
        JOIN players p ON ga.player_id = p.player_id
        LEFT JOIN game_rounds gr ON ga.round_id = gr.round_id
        ORDER BY ga.attempt_timestamp DESC
        {limit_clause}
    """.format(limit_clause=("LIMIT ?" if limit is not None else ""))
    params: Tuple = (limit,) if limit is not None else ()
    cur.execute(query, params)
    attempts = cur.fetchall()
    results = []
    for a in attempts:
        attempt_id = a["attempt_id"]
        cur.execute("""
            SELECT algorithm_name, execution_time_ms
            FROM algorithm_performance
            WHERE attempt_id = ?
        """, (attempt_id,))
        perf_rows = cur.fetchall()
        ek_time = None
        dinic_time = None
        for pr in perf_rows:
            name = pr["algorithm_name"]
            t = pr["execution_time_ms"]
            if name and name.lower().startswith("edmond"):
                ek_time = t
            elif name and name.lower().startswith("dinic"):
                dinic_time = t
        ek_time = ek_time if ek_time is not None else 0.0
        dinic_time = dinic_time if dinic_time is not None else 0.0
        results.append((
            attempt_id,
            a["player_name"],
            a["guess"],
            a["correct_flow"],
            bool(a["is_correct"]),
            ek_time,
            dinic_time,
            a["round_number"],
            a["attempt_timestamp"],
        ))
    return results


def fetch_players(conn: sqlite3.Connection) -> List[Tuple[Any, ...]]:
    cur = conn.cursor()
    cur.execute("SELECT player_id, player_name, created_at, last_played FROM players ORDER BY created_at DESC")
    return [ (r["player_id"], r["player_name"], r["created_at"], r["last_played"]) for r in cur.fetchall() ]


def fetch_rounds(conn: sqlite3.Connection) -> List[Tuple[Any, ...]]:
    cur = conn.cursor()
    cur.execute("SELECT round_id, round_number, graph_data, created_at FROM game_rounds ORDER BY created_at DESC")
    return [ (r["round_id"], r["round_number"], r["graph_data"], r["created_at"]) for r in cur.fetchall() ]


def fetch_performances(conn: sqlite3.Connection, limit: Optional[int] = 1000) -> List[Tuple[Any, ...]]:
    cur = conn.cursor()
    query = "SELECT performance_id, attempt_id, algorithm_name, execution_time_ms, flow_result FROM algorithm_performance ORDER BY performance_id DESC {limit_clause}"
    query = query.format(limit_clause=("LIMIT ?" if limit is not None else ""))
    params = (limit,) if limit is not None else ()
    cur.execute(query, params)
    return [ (r["performance_id"], r["attempt_id"], r["algorithm_name"], r["execution_time_ms"], r["flow_result"]) for r in cur.fetchall() ]


def fetch_denorm(conn: sqlite3.Connection, limit: Optional[int] = 500) -> List[Tuple[Any, ...]]:
    cur = conn.cursor()
    query = """
        SELECT id, player_name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms, round_number, timestamp
        FROM game_results
        ORDER BY timestamp DESC
        {limit_clause}
    """.format(limit_clause=("LIMIT ?" if limit is not None else ""))
    params = (limit,) if limit is not None else ()
    cur.execute(query, params)
    rows = cur.fetchall()
    return [ (r["id"], r["player_name"], r["guess"], r["correct_flow"], bool(r["is_correct"]), r["ek_time_ms"] or 0.0, r["dinic_time_ms"] or 0.0, r["round_number"], r["timestamp"]) for r in rows ]


def format_timestamp(ts) -> str:
    if ts is None:
        return ""
    if isinstance(ts, str):
        return ts
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts).isoformat(sep=' ')
        except Exception:
            return str(ts)
    try:
        return ts.isoformat(sep=' ')
    except Exception:
        return str(ts)


class TableTab:
    def __init__(self, parent, columns: Tuple[str, ...]):
        self.frame = ttk.Frame(parent)
        self.columns = columns
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.vsb = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        for col in columns:
            self.tree.heading(col, text=col)
            # default width; caller may adjust after creation
            self.tree.column(col, width=120, anchor=tk.CENTER)

    def clear(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def insert_rows(self, rows: List[Tuple[Any, ...]], formatters=None):
        self.clear()
        fmt = formatters or (lambda v, i: v)
        for r in rows:
            vals = []
            for i, v in enumerate(r):
                vals.append(fmt(v, i))
            self.tree.insert("", tk.END, values=tuple(vals))


def export_to_csv(columns: Tuple[str, ...], rows: List[Tuple[Any, ...]], title_hint: str):
    if not rows:
        messagebox.showinfo("Export", "No rows to export.")
        return
    fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")], initialfile=f"{title_hint}.csv")
    if not fpath:
        return
    try:
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for r in rows:
                writer.writerow(r)
        messagebox.showinfo("Export", f"Exported {len(rows)} rows to {fpath}")
    except Exception as e:
        messagebox.showerror("Export error", str(e))


def build_ui(db_path: str):
    try:
        conn = connect(db_path)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("DB Error", f"Unable to open database '{db_path}':\n{e}")
        return

    has_attempts = table_exists(conn, "game_attempts")
    has_players = table_exists(conn, "players")
    has_rounds = table_exists(conn, "game_rounds")
    has_performance = table_exists(conn, "algorithm_performance")
    has_denorm = table_exists(conn, "game_results")

    root = tk.Tk()
    root.title(f"DB Viewer — {db_path}")
    root.geometry("1200x700")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=6, pady=6)

    tabs = {}
    data_cache = {}  # store last fetched rows for export

    # Attempts tab
    if has_attempts and has_players:
        cols_attempts = ("ID", "Player", "Guess", "Correct Flow", "Is Correct", "EK Time (ms)", "Dinic Time (ms)", "Round", "Timestamp")
        tab_attempts = TableTab(nb, cols_attempts)
        # tweak widths
        tab_attempts.tree.column("ID", width=70, anchor=tk.CENTER)
        tab_attempts.tree.column("Player", width=240, anchor=tk.W)
        tab_attempts.tree.column("EK Time (ms)", width=130, anchor=tk.E)
        tab_attempts.tree.column("Dinic Time (ms)", width=130, anchor=tk.E)
        nb.add(tab_attempts.frame, text="Attempts")
        tabs["Attempts"] = (tab_attempts, lambda: fetch_attempts(conn, limit=200))
    else:
        # if attempts not normalized but denorm exists we skip this tab
        pass

    # Players tab
    if has_players:
        cols_players = ("Player ID", "Player Name", "Created At", "Last Played")
        tab_players = TableTab(nb, cols_players)
        tab_players.tree.column("Player Name", width=300, anchor=tk.W)
        nb.add(tab_players.frame, text="Players")
        tabs["Players"] = (tab_players, lambda: fetch_players(conn))

    # Rounds tab
    if has_rounds:
        cols_rounds = ("Round ID", "Round Number", "Graph Data", "Created At")
        tab_rounds = TableTab(nb, cols_rounds)
        tab_rounds.tree.column("Graph Data", width=400, anchor=tk.W)
        nb.add(tab_rounds.frame, text="Rounds")
        tabs["Rounds"] = (tab_rounds, lambda: fetch_rounds(conn))

    # Performance tab
    if has_performance:
        cols_perf = ("Perf ID", "Attempt ID", "Algorithm", "Execution Time (ms)", "Flow Result")
        tab_perf = TableTab(nb, cols_perf)
        tab_perf.tree.column("Algorithm", width=180, anchor=tk.W)
        tab_perf.tree.column("Execution Time (ms)", width=160, anchor=tk.E)
        nb.add(tab_perf.frame, text="Performance")
        tabs["Performance"] = (tab_perf, lambda: fetch_performances(conn, limit=1000))

    # Denormalized tab (fallback)
    if has_denorm:
        cols_denorm = ("ID", "Player", "Guess", "Correct Flow", "Is Correct", "EK Time (ms)", "Dinic Time (ms)", "Round", "Timestamp")
        tab_denorm = TableTab(nb, cols_denorm)
        tab_denorm.tree.column("Player", width=240, anchor=tk.W)
        nb.add(tab_denorm.frame, text="Denormalized")
        tabs["Denormalized"] = (tab_denorm, lambda: fetch_denorm(conn, limit=500))

    if not tabs:
        conn.close()
        root.withdraw()
        messagebox.showerror("DB Error", "No recognized tables found in DB (players/game_attempts or game_results).")
        return

    # Controls frame
    ctrl = ttk.Frame(root)
    ctrl.pack(fill="x", padx=6, pady=(0,6))

    status_var = tk.StringVar(value=f"DB: {db_path}")
    status_label = ttk.Label(ctrl, textvariable=status_var)
    status_label.pack(side="left")

    def refresh_current():
        current = nb.tab(nb.select(), "text")
        tab_obj, fetcher = tabs[current]
        try:
            rows = fetcher()
            data_cache[current] = rows
            # Formatting function for insert: convert booleans and timestamps
            def fmt(v, i):
                # For Attempts/Denorm we want formatting of booleans/times and rounding times
                if isinstance(v, bool):
                    return "Yes" if v else "No"
                if isinstance(v, float) and (i == 5 or i == 6):  # EK/Dinic times columns index differs per tab shape
                    return f"{round(v, 3):.3f}"
                if isinstance(v, (int,)) and (i == 0):
                    return v
                if i == len(tab_obj.columns) - 1:  # timestamp column
                    return format_timestamp(v)
                return v
            # Better: build specific formatters per tab by name
            if current == "Attempts":
                def fmt_attempts(v, i):
                    if i == 4:
                        return "Yes" if v else "No"
                    if i in (5,6):
                        return f"{round(v or 0, 3):.3f}"
                    if i == 8:
                        return format_timestamp(v)
                    return v
                tab_obj.insert_rows(rows, formatters=fmt_attempts)
            elif current == "Denormalized":
                def fmt_den(v, i):
                    if i == 4:
                        return "Yes" if v else "No"
                    if i in (5,6):
                        return f"{round(v or 0, 3):.3f}"
                    if i == 8:
                        return format_timestamp(v)
                    return v
                tab_obj.insert_rows(rows, formatters=fmt_den)
            elif current == "Players":
                def fmt_players(v, i):
                    if i in (2,3):
                        return format_timestamp(v)
                    return v
                tab_obj.insert_rows(rows, formatters=fmt_players)
            elif current == "Rounds":
                def fmt_rounds(v, i):
                    if i == 3:
                        return format_timestamp(v)
                    return v
                tab_obj.insert_rows(rows, formatters=fmt_rounds)
            elif current == "Performance":
                def fmt_perf(v, i):
                    if i == 3:
                        return f"{round(v or 0, 3):.3f}"
                    return v
                tab_obj.insert_rows(rows, formatters=fmt_perf)
            else:
                tab_obj.insert_rows(rows)
            status_var.set(f"DB: {db_path}  —  {current}: {len(rows)} rows")
        except Exception as e:
            messagebox.showerror("Read error", str(e))

    def copy_selected():
        current = nb.tab(nb.select(), "text")
        tab_obj, _ = tabs[current]
        sel = tab_obj.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Please select a row to copy.")
            return
        vals = tab_obj.tree.item(sel[0], "values")
        root.clipboard_clear()
        root.clipboard_append(str(vals))
        messagebox.showinfo("Copied", "Selected row copied to clipboard.")

    def export_current():
        current = nb.tab(nb.select(), "text")
        cols = tabs[current][0].columns
        rows = data_cache.get(current, [])
        export_to_csv(cols, rows, title_hint=current.lower())

    refresh_btn = ttk.Button(ctrl, text="Refresh", command=refresh_current)
    refresh_btn.pack(side="left", padx=6)
    copy_btn = ttk.Button(ctrl, text="Copy Selected", command=copy_selected)
    copy_btn.pack(side="left")
    export_btn = ttk.Button(ctrl, text="Export CSV", command=export_current)
    export_btn.pack(side="left", padx=(6,0))
    close_btn = ttk.Button(ctrl, text="Close", command=root.destroy)
    close_btn.pack(side="right")

    # Initial load for first tab
    refresh_current()

    root.mainloop()
    conn.close()


if __name__ == "__main__":
    db_path = DEFAULT_DB
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    build_ui(db_path)