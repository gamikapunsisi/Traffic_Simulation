import sqlite3
import tkinter as tk
from tkinter import ttk

def show_db_popup():
    conn = sqlite3.connect("traffic_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM game_results")
    rows = cursor.fetchall()
    conn.close()

    # Create window
    root = tk.Tk()
    root.title("Game Results")
    root.geometry("900x400")

    columns = (
        "ID", "Player", "Guess", "Correct Flow", "Is Correct",
        "EK Time (ms)", "Dinic Time (ms)", "Round", "Timestamp"
    )

    tree = ttk.Treeview(root, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    for row in rows:
        tree.insert("", tk.END, values=row)

    tree.pack(expand=True, fill="both")

    root.mainloop()

show_db_popup()
