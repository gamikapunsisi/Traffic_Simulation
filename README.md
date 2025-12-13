```markdown
# Traffic Simulation Game (Python)

This is a small Python project implementing the "Traffic simulation Problem".

Features:
- Random-capacity directed traffic network (capacities 5–15).
- draws the graph and asks the player to guess the max flow from A → T.
- Two independent max-flow algorithms: Edmonds–Karp and Dinic (implemented from scratch).
- Times each algorithm and records data in a normalized SQLite database.
- Unit tests for algorithms.

How to run:
1. Create a virtualenv and install requirements:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Run the app:
   python app.py

3. Run tests:
   python -m unittest tests/test_maxflow.py

4 . check SQLLite DB Table:
      python view_db.py

Database:
- The DB file `traffic_game.db` is created in the working directory.
- Schema:
  - players(id, name)
  - games(id, player_id, guess, correct_flow, is_correct, played_at)
  - algorithm_times(id, game_id, algorithm, time_ms)

Notes:
- Validation: player name required, guess must be a non-negative integer.
- Exception handling: validation errors shown to user; algorithm/DB exceptions appended to results area.
```