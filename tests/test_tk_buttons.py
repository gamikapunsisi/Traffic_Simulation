import tkinter as tk
from tkinter import ttk

def on_submit():
    print("Submit button clicked")
    lbl.config(text="Submit clicked")

def on_new_round():
    print("New Round button clicked")
    lbl.config(text="New Round clicked")

root = tk.Tk()
root.geometry("400x200")
frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

name_lbl = ttk.Label(frame, text="Player name:")
name_lbl.pack(anchor="w")
name_entry = ttk.Entry(frame)
name_entry.pack(fill="x")

guess_lbl = ttk.Label(frame, text="Guess:")
guess_lbl.pack(anchor="w")
guess_entry = ttk.Entry(frame)
guess_entry.pack(fill="x")

btn_submit = ttk.Button(frame, text="Submit Guess & Run Algorithms", command=on_submit)
btn_submit.pack(fill="x", pady=(10,2))
btn_new = ttk.Button(frame, text="New Random Round", command=on_new_round)
btn_new.pack(fill="x")

lbl = ttk.Label(frame, text="No clicks yet")
lbl.pack(pady=(10,0))

root.mainloop()