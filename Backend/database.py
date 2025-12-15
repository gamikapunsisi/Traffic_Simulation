# """
# Database Manager for Traffic Simulation Game
# Handles all SQLite database operations
# """
# import sqlite3
# from typing import Dict, List
# from datetime import datetime


# class DatabaseManager:
#     """Handles all database operations"""
    
#     def __init__(self, db_name: str = "traffic_game.db"):
#         self.db_name = db_name
#         self.init_db()
    
#     def init_db(self):
#         """Initialize database with proper schema"""
#         try:
#             conn = sqlite3.connect(self.db_name)
#             cursor = conn.cursor()
            
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS game_results (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     player_name TEXT NOT NULL,
#                     guess INTEGER NOT NULL,
#                     correct_flow INTEGER NOT NULL,
#                     is_correct INTEGER NOT NULL,
#                     ek_time_ms REAL NOT NULL,
#                     dinic_time_ms REAL NOT NULL,
#                     round_number INTEGER,
#                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
            
#             conn.commit()
#             print("✓ Database initialized successfully")
        
#         except sqlite3.Error as e:
#             print(f"✗ Database initialization error: {e}")
#             raise
        
#         finally:
#             conn.close()
    
#     def save_game_result(self, player_name: str, guess: int, correct_flow: int,
#                         is_correct: int, ek_time_ms: float, dinic_time_ms: float,
#                         round_number: int = 1):
#         """Save game result to database"""
#         try:
#             conn = sqlite3.connect(self.db_name)
#             cursor = conn.cursor()
            
#             cursor.execute("""
#                 INSERT INTO game_results 
#                 (player_name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms, round_number)
#                 VALUES (?, ?, ?, ?, ?, ?, ?)
#             """, (player_name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms, round_number))
            
#             conn.commit()
#             print(f"✓ Game result saved for {player_name}")
        
#         except sqlite3.Error as e:
#             print(f"✗ Database save error: {e}")
#             raise
        
#         finally:
#             conn.close()
    
#     def get_player_stats(self, player_name: str) -> Dict:
#         """Get statistics for a specific player"""
#         try:
#             conn = sqlite3.connect(self.db_name)
#             cursor = conn.cursor()
            
#             cursor.execute("""
#                 SELECT 
#                     COUNT(*) as total_games,
#                     SUM(is_correct) as wins,
#                     AVG(ek_time_ms) as avg_ek_time,
#                     AVG(dinic_time_ms) as avg_dinic_time
#                 FROM game_results
#                 WHERE player_name = ?
#             """, (player_name,))
            
#             result = cursor.fetchone()
            
#             return {
#                 'total_games': result[0] or 0,
#                 'wins': result[1] or 0,
#                 'avg_ek_time': result[2] or 0,
#                 'avg_dinic_time': result[3] or 0
#             }
        
#         except sqlite3.Error as e:
#             print(f"✗ Database query error: {e}")
#             return {}
        
#         finally:
#             conn.close()
    
#     def get_all_game_results(self, limit: int = 100) -> List[Dict]:
#         """Get recent game results"""
#         try:
#             conn = sqlite3.connect(self.db_name)
#             cursor = conn.cursor()
            
#             cursor.execute("""
#                 SELECT 
#                     player_name,
#                     guess,
#                     correct_flow,
#                     is_correct,
#                     ek_time_ms,
#                     dinic_time_ms,
#                     round_number,
#                     timestamp
#                 FROM game_results
#                 ORDER BY timestamp DESC
#                 LIMIT ?
#             """, (limit,))
            
#             results = cursor.fetchall()
            
#             games = []
#             for row in results:
#                 games.append({
#                     'playerName': row[0],
#                     'guess': row[1],
#                     'correctFlow': row[2],
#                     'isCorrect': bool(row[3]),
#                     'ekTime': round(row[4], 3),
#                     'dinicTime': round(row[5], 3),
#                     'round': row[6],
#                     'timestamp': row[7]
#                 })
            
#             return games
        
#         except sqlite3.Error as e:
#             print(f"✗ Database query error: {e}")
#             return []
        
#         finally:
#             conn.close()
    
#     def get_leaderboard(self, limit: int = 10) -> List[Dict]:
#         """Get top players by win rate"""
#         try:
#             conn = sqlite3.connect(self.db_name)
#             cursor = conn.cursor()
            
#             cursor.execute("""
#                 SELECT 
#                     player_name,
#                     COUNT(*) as total_games,
#                     SUM(is_correct) as wins,
#                     AVG(ek_time_ms) as avg_time
#                 FROM game_results
#                 GROUP BY player_name
#                 HAVING total_games >= 3
#                 ORDER BY (SUM(is_correct) * 1.0 / COUNT(*)) DESC, AVG(ek_time_ms) ASC
#                 LIMIT ?
#             """, (limit,))
            
#             results = cursor.fetchall()
            
#             leaderboard = []
#             for row in results:
#                 win_rate = (row[2] / row[1]) * 100 if row[1] > 0 else 0
#                 leaderboard.append({
#                     'playerName': row[0],
#                     'totalGames': row[1],
#                     'wins': row[2],
#                     'winRate': round(win_rate, 1),
#                     'avgTime': round(row[3], 3)
#                 })
            
#             return leaderboard
        
#         except sqlite3.Error as e:
#             print(f"✗ Database query error: {e}")
#             return []
        
#         finally:
#             conn.close()

"""
Database Manager for Traffic Simulation Game (Normalized + Migration)

- Normalized schema:
  - players
  - game_rounds
  - game_attempts
  - algorithm_performance

- If an old denormalized table `game_results` is detected, this module will
  automatically migrate rows into the normalized schema and rename the old
  table to `game_results_denorm_backup_<timestamp>`.

Usage:
    from database import DatabaseManager
    db = DatabaseManager()  # default file: traffic_game.db
"""
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
import time
import os

class DatabaseManager:
    """Normalized database manager with automatic migration from old denormalized table."""
    def __init__(self, db_name: str = "traffic_game.db"):
        self.db_name = db_name
        self.init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Initialize normalized schema and migrate from old schema if present."""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Create normalized tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_played DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_rounds (
                    round_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_number INTEGER NOT NULL,
                    graph_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    round_id INTEGER,
                    guess INTEGER NOT NULL,
                    correct_flow INTEGER NOT NULL,
                    is_correct INTEGER NOT NULL,
                    attempt_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
                    FOREIGN KEY (round_id) REFERENCES game_rounds(round_id) ON DELETE SET NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS algorithm_performance (
                    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempt_id INTEGER NOT NULL,
                    algorithm_name TEXT NOT NULL,
                    execution_time_ms REAL NOT NULL,
                    flow_result INTEGER NOT NULL,
                    FOREIGN KEY (attempt_id) REFERENCES game_attempts(attempt_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_name ON players(player_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_player ON game_attempts(player_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_timestamp ON game_attempts(attempt_timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_attempt ON algorithm_performance(attempt_id)")

            conn.commit()

            # If old denormalized table exists, migrate it if migration hasn't already been done.
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_results'")
            if cursor.fetchone():
                # Check whether migration already occurred by seeing if game_attempts has rows
                cursor.execute("SELECT COUNT(*) FROM game_attempts")
                attempt_count = cursor.fetchone()[0]
                if attempt_count == 0:
                    self._migrate_old_table(conn)
                else:
                    # Already have attempts; skip migration
                    pass

            print("✓ Database (normalized) initialized successfully")
        except sqlite3.Error as e:
            print(f"✗ Database initialization error: {e}")
            raise
        finally:
            conn.close()

    def _migrate_old_table(self, conn: sqlite3.Connection):
        """Migrate rows from old `game_results` table into the normalized schema.
        After successful migration the old table is renamed for backup.
        """
        cursor = conn.cursor()
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_table = f"game_results_denorm_backup_{timestamp}"

        try:
            print("i) Detected old denormalized `game_results` table — starting migration...")
            # Read all rows from old table
            cursor.execute("""
                SELECT id, player_name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms, round_number, timestamp
                FROM game_results
                ORDER BY id ASC
            """)
            rows = cursor.fetchall()

            # Map player_name -> player_id
            player_cache: Dict[str, int] = {}

            def get_or_create_player_id(name: str) -> int:
                if name in player_cache:
                    return player_cache[name]
                cursor.execute("SELECT player_id FROM players WHERE player_name = ?", (name,))
                res = cursor.fetchone()
                if res:
                    pid = res[0]
                    cursor.execute("UPDATE players SET last_played = CURRENT_TIMESTAMP WHERE player_id = ?", (pid,))
                else:
                    cursor.execute("INSERT INTO players (player_name) VALUES (?)", (name,))
                    pid = cursor.lastrowid
                player_cache[name] = pid
                return pid

            # Migrate each row
            for r in rows:
                (old_id, player_name, guess, correct_flow, is_correct, ek_time_ms, dinic_time_ms, round_number, ts) = r

                player_id = get_or_create_player_id(player_name)

                # Create a round row (one per migrated row preserves original round_number)
                cursor.execute("""
                    INSERT INTO game_rounds (round_number, graph_data, created_at)
                    VALUES (?, NULL, ?)
                """, (round_number if round_number is not None else 1, ts if ts else datetime.utcnow()))
                round_id = cursor.lastrowid

                # Create attempt
                cursor.execute("""
                    INSERT INTO game_attempts (player_id, round_id, guess, correct_flow, is_correct, attempt_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (player_id, round_id, guess, correct_flow, is_correct, ts if ts else datetime.utcnow()))
                attempt_id = cursor.lastrowid

                # Create algorithm_performance rows for Edmonds-Karp and Dinic
                # Use ek_time_ms and dinic_time_ms; if either is NULL, store 0
                ek_ms = ek_time_ms if ek_time_ms is not None else 0.0
                dinic_ms = dinic_time_ms if dinic_time_ms is not None else 0.0

                cursor.execute("""
                    INSERT INTO algorithm_performance (attempt_id, algorithm_name, execution_time_ms, flow_result)
                    VALUES (?, 'Edmonds-Karp', ?, ?)
                """, (attempt_id, ek_ms, correct_flow))
                cursor.execute("""
                    INSERT INTO algorithm_performance (attempt_id, algorithm_name, execution_time_ms, flow_result)
                    VALUES (?, 'Dinic', ?, ?)
                """, (attempt_id, dinic_ms, correct_flow))

            # Rename old table for backup (do not DROP automatically)
            cursor.execute(f"ALTER TABLE game_results RENAME TO {backup_table}")
            conn.commit()
            print(f"✓ Migration complete — old table renamed to `{backup_table}`. Keep it until you verify data.")
        except sqlite3.Error as e:
            conn.rollback()
            print(f"✗ Migration failed: {e}")
            raise

    def get_or_create_player(self, player_name: str) -> int:
        """Get existing player_id or create new player (updates last_played)."""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT player_id FROM players WHERE player_name = ?", (player_name,))
            result = cursor.fetchone()
            if result:
                player_id = result[0]
                cursor.execute("UPDATE players SET last_played = CURRENT_TIMESTAMP WHERE player_id = ?", (player_id,))
            else:
                cursor.execute("INSERT INTO players (player_name) VALUES (?)", (player_name,))
                player_id = cursor.lastrowid
            conn.commit()
            return player_id
        finally:
            conn.close()

    def save_game_result(self, player_name: str, guess: int, correct_flow: int,
                        is_correct: int, ek_time_ms: float, dinic_time_ms: float,
                        round_number: int = 1, graph_data: Optional[str] = None):
        """Save a game result using normalized schema."""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            player_id = self.get_or_create_player(player_name)

            # Create round entry (store graph_data if provided)
            cursor.execute("INSERT INTO game_rounds (round_number, graph_data) VALUES (?, ?)",
                           (round_number, graph_data))
            round_id = cursor.lastrowid

            # Create game attempt
            cursor.execute("""
                INSERT INTO game_attempts (player_id, round_id, guess, correct_flow, is_correct)
                VALUES (?, ?, ?, ?, ?)
            """, (player_id, round_id, guess, correct_flow, is_correct))
            attempt_id = cursor.lastrowid

            # Save algorithm performances
            cursor.execute("""
                INSERT INTO algorithm_performance (attempt_id, algorithm_name, execution_time_ms, flow_result)
                VALUES (?, 'Edmonds-Karp', ?, ?)
            """, (attempt_id, ek_time_ms, correct_flow))

            cursor.execute("""
                INSERT INTO algorithm_performance (attempt_id, algorithm_name, execution_time_ms, flow_result)
                VALUES (?, 'Dinic', ?, ?)
            """, (attempt_id, dinic_time_ms, correct_flow))

            conn.commit()
            print(f"✓ Game result saved for {player_name}")
        except sqlite3.Error as e:
            conn.rollback()
            print(f"✗ Database save error: {e}")
            raise
        finally:
            conn.close()

    def get_player_stats(self, player_name: str) -> Dict:
        """Get statistics for a specific player."""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    p.player_id,
                    COUNT(ga.attempt_id) as total_games,
                    SUM(ga.is_correct) as wins
                FROM players p
                LEFT JOIN game_attempts ga ON p.player_id = ga.player_id
                WHERE p.player_name = ?
                GROUP BY p.player_id
            """, (player_name,))
            result = cursor.fetchone()
            if not result:
                return {'total_games': 0, 'wins': 0, 'avg_ek_time': 0, 'avg_dinic_time': 0}
            player_id = result[0]
            cursor.execute("""
                SELECT ap.algorithm_name, AVG(ap.execution_time_ms) as avg_time
                FROM algorithm_performance ap
                JOIN game_attempts ga ON ap.attempt_id = ga.attempt_id
                WHERE ga.player_id = ?
                GROUP BY ap.algorithm_name
            """, (player_id,))
            algo_stats = {row[0]: row[1] for row in cursor.fetchall()}
            return {
                'total_games': result[1],
                'wins': result[2] or 0,
                'avg_ek_time': algo_stats.get('Edmonds-Karp', 0),
                'avg_dinic_time': algo_stats.get('Dinic', 0)
            }
        finally:
            conn.close()

    def get_all_game_results(self, limit: int = 100) -> List[Dict]:
        """Get recent game results (joined from normalized tables)."""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    p.player_name, ga.guess, ga.correct_flow, ga.is_correct,
                    ga.attempt_timestamp, gr.round_number, ga.attempt_id
                FROM game_attempts ga
                JOIN players p ON ga.player_id = p.player_id
                LEFT JOIN game_rounds gr ON ga.round_id = gr.round_id
                ORDER BY ga.attempt_timestamp DESC
                LIMIT ?
            """, (limit,))
            attempts = cursor.fetchall()
            games = []
            for row in attempts:
                attempt_id = row[6]
                cursor.execute("""
                    SELECT algorithm_name, execution_time_ms
                    FROM algorithm_performance WHERE attempt_id = ?
                """, (attempt_id,))
                algo_data = {r[0]: r[1] for r in cursor.fetchall()}
                games.append({
                    'playerName': row[0],
                    'guess': row[1],
                    'correctFlow': row[2],
                    'isCorrect': bool(row[3]),
                    'timestamp': row[4],
                    'round': row[5],
                    'ekTime': round(algo_data.get('Edmonds-Karp', 0) or 0, 3),
                    'dinicTime': round(algo_data.get('Dinic', 0) or 0, 3)
                })
            return games
        finally:
            conn.close()

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by win rate."""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    p.player_name,
                    COUNT(ga.attempt_id) as total_games,
                    SUM(ga.is_correct) as wins,
                    AVG(CASE WHEN ap.algorithm_name = 'Edmonds-Karp' 
                        THEN ap.execution_time_ms END) as avg_ek_time
                FROM players p
                JOIN game_attempts ga ON p.player_id = ga.player_id
                LEFT JOIN algorithm_performance ap ON ga.attempt_id = ap.attempt_id
                GROUP BY p.player_id, p.player_name
                HAVING total_games >= 3
                ORDER BY (SUM(ga.is_correct) * 1.0 / COUNT(ga.attempt_id)) DESC, avg_ek_time ASC
                LIMIT ?
            """, (limit,))
            results = cursor.fetchall()
            leaderboard = []
            for row in results:
                win_rate = (row[2] / row[1]) * 100 if row[1] > 0 else 0
                leaderboard.append({
                    'playerName': row[0],
                    'totalGames': row[1],
                    'wins': row[2],
                    'winRate': round(win_rate, 1),
                    'avgTime': round(row[3], 3) if row[3] else 0
                })
            return leaderboard
        finally:
            conn.close()