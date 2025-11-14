"""
SQLite DB helpers for the traffic game.
Normalized schema:
- players(id INTEGER PK, name TEXT UNIQUE)
- games(id INTEGER PK, player_id INTEGER, guess INTEGER, correct_flow INTEGER,
        is_correct INTEGER, played_at TEXT)
- algorithm_times(id INTEGER PK, game_id INTEGER, algorithm TEXT, time_ms REAL)

Provides init_db() and save_game_result() helpers.
"""
import sqlite3
from datetime import datetime

DB_FILE = "traffic_game.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY,
            player_id INTEGER,
            guess INTEGER,
            correct_flow INTEGER,
            is_correct INTEGER,
            played_at TEXT,
            FOREIGN KEY(player_id) REFERENCES players(id)
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS algorithm_times (
            id INTEGER PRIMARY KEY,
            game_id INTEGER,
            algorithm TEXT,
            time_ms REAL,
            FOREIGN KEY(game_id) REFERENCES games(id)
        );
        """)
        conn.commit()
    finally:
        conn.close()

def _get_or_create_player(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT id FROM players WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO players (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid

def save_game_result(name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms):
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        player_id = _get_or_create_player(conn, name)
        played_at = datetime.utcnow().isoformat()
        cur.execute(
            "INSERT INTO games (player_id, guess, correct_flow, is_correct, played_at) VALUES (?,?,?,?,?)",
            (player_id, guess, correct_flow, is_correct, played_at)
        )
        game_id = cur.lastrowid
        cur.execute("INSERT INTO algorithm_times (game_id, algorithm, time_ms) VALUES (?,?,?)",
                    (game_id, "Edmonds-Karp", ek_time_ms))
        cur.execute("INSERT INTO algorithm_times (game_id, algorithm, time_ms) VALUES (?,?,?)",
                    (game_id, "Dinic", dinic_time_ms))
        conn.commit()
    finally:
        conn.close()