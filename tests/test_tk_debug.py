import tkinter as tk
from tkinter import ttk, messagebox
import sys
import time

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stdout, flush=True)

def on_submit():
    log("on_submit() invoked")
    messagebox.showinfo("Debug", "Submit button handler ran")
    lbl.config(text="Submit clicked")

def on_new_round():
    log("on_new_round() invoked")
    messagebox.showinfo("Debug", "New Round button handler ran")
    lbl.config(text="New Round clicked")

def on_any_click(event):
    widget = event.widget
    log(f"Global click at ({event.x},{event.y}) on widget: {widget} type={type(widget)}")
    # show what currently has focus
    focused = root.focus_get()
    log(f"Focus widget: {focused} ({type(focused)})")

root = tk.Tk()
root.geometry("500x260")
root.title("Tk Debug Test")

frame = ttk.Frame(root, padding=8)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Player name:").pack(anchor="w")
name_entry = ttk.Entry(frame)
name_entry.pack(fill="x")

ttk.Label(frame, text="Guess:").pack(anchor="w", pady=(6,0))
guess_entry = ttk.Entry(frame)
guess_entry.pack(fill="x")

btn_submit = ttk.Button(frame, text="Submit Guess & Run Algorithms", command=on_submit)
btn_submit.pack(fill="x", pady=(12,2))

btn_new = ttk.Button(frame, text="New Random Round", command=on_new_round)
btn_new.pack(fill="x")

lbl = ttk.Label(frame, text="No clicks yet", foreground="blue")
lbl.pack(pady=(12,0))

# Bind a global click handler on the top-level to see clicks anywhere
root.bind_all("<Button-1>", on_any_click, add="+")

# Also bind a mouse-press on the buttons themselves to check binding delivery
btn_submit.bind("<Button-1>", lambda e: log("btn_submit received <Button-1> event"), add="+")
btn_new.bind("<Button-1>", lambda e: log("btn_new received <Button-1> event"), add="+")

# Print initial state
log("Starting Tk Debug Test")
log(f"Button submit state: {btn_submit.cget('state')}")
log(f"Button new state: {btn_new.cget('state')}")
log("Please click the Submit and New Round buttons now.")

# Set focus to name entry
name_entry.focus_set()

root.mainloop()
log("Mainloop exited")