"""
Flask Backend for Traffic Simulation Game
Main API server with CORS support
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from algorithms import edmonds_karp_with_flows, dinic, generate_random_capacity_graph
from database import DatabaseManager

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize database
db = DatabaseManager()

# Store current game state (in production, use sessions or Redis)
game_state = {
    'current_graph': generate_random_capacity_graph(),
    'round': 1
}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Traffic Simulation API is running'})


@app.route('/api/new-game', methods=['GET'])
def new_game():
    """Generate a new traffic network graph"""
    try:
        game_state['current_graph'] = generate_random_capacity_graph()
        game_state['round'] += 1
        
        # Convert graph to serializable format
        graph_data = {
            'nodes': ["A", "B", "C", "D", "E", "F", "G", "H", "T"],
            'edges': [],
            'round': game_state['round']
        }
        
        for u in game_state['current_graph']:
            for v, capacity in game_state['current_graph'][u].items():
                graph_data['edges'].append({
                    'source': u,
                    'target': v,
                    'capacity': capacity
                })
        
        return jsonify({
            'success': True,
            'graph': graph_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/current-graph', methods=['GET'])
def get_current_graph():
    """Get the current graph without generating a new one"""
    try:
        graph_data = {
            'nodes': ["A", "B", "C", "D", "E", "F", "G", "H", "T"],
            'edges': [],
            'round': game_state['round']
        }
        
        for u in game_state['current_graph']:
            for v, capacity in game_state['current_graph'][u].items():
                graph_data['edges'].append({
                    'source': u,
                    'target': v,
                    'capacity': capacity
                })
        
        return jsonify({
            'success': True,
            'graph': graph_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/submit-guess', methods=['POST'])
def submit_guess():
    """Process player's guess and compute max flow"""
    try:
        data = request.get_json()
        
        # Validate input
        player_name = data.get('playerName', '').strip()
        guess = data.get('guess')
        
        if not player_name:
            return jsonify({
                'success': False,
                'error': 'Player name is required'
            }), 400
        
        if guess is None or not isinstance(guess, int):
            return jsonify({
                'success': False,
                'error': 'Valid guess is required'
            }), 400
        
        if guess < 0:
            return jsonify({
                'success': False,
                'error': 'Guess must be non-negative'
            }), 400
        
        # Create graph copies
        graph_ek = {u: dict(vs) for u, vs in game_state['current_graph'].items()}
        graph_dinic = {u: dict(vs) for u, vs in game_state['current_graph'].items()}
        
        # Compute with Edmonds-Karp
        t0 = time.perf_counter()
        ek_flow, ek_flow_dict = edmonds_karp_with_flows(graph_ek, "A", "T")
        t1 = time.perf_counter()
        ek_time_ms = (t1 - t0) * 1000
        
        # Compute with Dinic
        t2 = time.perf_counter()
        dinic_flow = dinic(graph_dinic, "A", "T")
        t3 = time.perf_counter()
        dinic_time_ms = (t3 - t2) * 1000
        
        # Determine correctness
        algorithms_agree = (ek_flow == dinic_flow)
        correct_flow = ek_flow
        
        if not algorithms_agree:
            print(f"WARNING: Algorithms disagree! EK={ek_flow}, Dinic={dinic_flow}")
            correct_flow = max(ek_flow, dinic_flow)
        
        is_correct = (guess == correct_flow)
        
        # Save to database
        db.save_game_result(
            player_name=player_name,
            guess=guess,
            correct_flow=correct_flow,
            is_correct=1 if is_correct else 0,
            ek_time_ms=ek_time_ms,
            dinic_time_ms=dinic_time_ms,
            round_number=game_state['round']
        )
        
        # Format flow dictionary for frontend
        flow_data = []
        for (u, v), flow in ek_flow_dict.items():
            if flow > 0:
                flow_data.append({
                    'source': u,
                    'target': v,
                    'flow': flow
                })
        
        return jsonify({
            'success': True,
            'result': {
                'isCorrect': is_correct,
                'correctFlow': correct_flow,
                'ekFlow': ek_flow,
                'dinicFlow': dinic_flow,
                'ekTime': round(ek_time_ms, 3),
                'dinicTime': round(dinic_time_ms, 3),
                'algorithmsAgree': algorithms_agree,
                'flowData': flow_data
            }
        })
    
    except Exception as e:
        print(f"Error in submit_guess: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/player-stats/<player_name>', methods=['GET'])
def get_player_stats(player_name):
    """Get statistics for a specific player"""
    try:
        stats = db.get_player_stats(player_name)
        
        if stats['total_games'] == 0:
            return jsonify({
                'success': True,
                'stats': None,
                'message': 'No games found for this player'
            })
        
        win_rate = (stats['wins'] / stats['total_games']) * 100 if stats['total_games'] > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'totalGames': stats['total_games'],
                'wins': stats['wins'],
                'winRate': round(win_rate, 1),
                'avgEkTime': round(stats['avg_ek_time'], 3),
                'avgDinicTime': round(stats['avg_dinic_time'], 3)
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/all-stats', methods=['GET'])
def get_all_stats():
    """Get all game statistics"""
    try:
        all_stats = db.get_all_game_results()
        
        return jsonify({
            'success': True,
            'games': all_stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Traffic Simulation API Server Starting...")
    print("=" * 60)
    print("Backend running on: http://localhost:5000")
    print("Frontend should connect to: http://localhost:5000/api")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)