"""
Database Manager for Traffic Simulation Game
Handles all SQLite database operations
"""
import sqlite3
from typing import Dict, List
from datetime import datetime


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
            print("✓ Database initialized successfully")
        
        except sqlite3.Error as e:
            print(f"✗ Database initialization error: {e}")
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
            print(f"✓ Game result saved for {player_name}")
        
        except sqlite3.Error as e:
            print(f"✗ Database save error: {e}")
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
            print(f"✗ Database query error: {e}")
            return {}
        
        finally:
            conn.close()
    
    def get_all_game_results(self, limit: int = 100) -> List[Dict]:
        """Get recent game results"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    player_name,
                    guess,
                    correct_flow,
                    is_correct,
                    ek_time_ms,
                    dinic_time_ms,
                    round_number,
                    timestamp
                FROM game_results
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            
            games = []
            for row in results:
                games.append({
                    'playerName': row[0],
                    'guess': row[1],
                    'correctFlow': row[2],
                    'isCorrect': bool(row[3]),
                    'ekTime': round(row[4], 3),
                    'dinicTime': round(row[5], 3),
                    'round': row[6],
                    'timestamp': row[7]
                })
            
            return games
        
        except sqlite3.Error as e:
            print(f"✗ Database query error: {e}")
            return []
        
        finally:
            conn.close()
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by win rate"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    player_name,
                    COUNT(*) as total_games,
                    SUM(is_correct) as wins,
                    AVG(ek_time_ms) as avg_time
                FROM game_results
                GROUP BY player_name
                HAVING total_games >= 3
                ORDER BY (SUM(is_correct) * 1.0 / COUNT(*)) DESC, AVG(ek_time_ms) ASC
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
                    'avgTime': round(row[3], 3)
                })
            
            return leaderboard
        
        except sqlite3.Error as e:
            print(f"✗ Database query error: {e}")
            return []
        
        finally:
            conn.close()