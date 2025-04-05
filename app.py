from flask import Flask, render_template, jsonify, request
import chess
from stockfish import Stockfish
import threading
import time

app = Flask(__name__)
board = chess.Board()  # Initialize a chess board

# Initialize Stockfish engine
try:
    stockfish = Stockfish(path="./stockfish-windows-x86-64-avx2.exe", 
                          parameters={"Threads": 2, "Skill Level": 15})
    engine_available = True
except Exception as e:
    print(f"Error initializing Stockfish: {e}")
    engine_available = False

# Store the latest moves
latest_moves = {
    "user_move": None,
    "engine_move": None,
    "timestamp": None
}

# Lock for thread safety
move_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_fen')
def get_fen():
    """Return the current FEN notation of the chess board"""
    return jsonify({"fen": board.fen()})

@app.route('/submit_move', methods=['POST'])
def submit_move():
    """
    Process a move submitted by the user and generate an engine response.
    
    Expected JSON payload:
    {
        "move": "e2e4"  # UCI format move
    }
    
    Returns:
    {
        "success": true/false,
        "opponent_move": "e7e5",  # Engine's response move
        "fen": "current board FEN"
    }
    """
    global latest_moves
    
    data = request.get_json()
    if not data or 'move' not in data:
        return jsonify({"success": False, "message": "No move provided"}), 400
    
    move_uci = data['move']
    
    try:
        # Process user's move
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            # Apply user's move to the board
            board.push(move)
            
            # Update latest moves
            with move_lock:
                latest_moves["user_move"] = move_uci
                latest_moves["timestamp"] = time.time()
            
            # Generate engine response if engine is available
            opponent_move = None
            if engine_available and not board.is_game_over():
                # Update Stockfish with current position
                stockfish.set_fen_position(board.fen())
                # Get best move from engine
                best_move = stockfish.get_best_move()
                
                if best_move:
                    # Apply engine's move to the board
                    engine_move = chess.Move.from_uci(best_move)
                    board.push(engine_move)
                    opponent_move = best_move
                    
                    # Update latest moves with engine's move
                    with move_lock:
                        latest_moves["engine_move"] = best_move
            
            return jsonify({
                "success": True,
                "opponent_move": opponent_move,
                "fen": board.fen(),
                "game_over": board.is_game_over(),
                "check": board.is_check()
            })
        else:
            return jsonify({"success": False, "message": "Illegal move"}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid move format"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/get_move')
def get_move():
    """
    Return the latest move made by the engine.
    
    Returns:
    {
        "move": "e7e5",  # Latest engine move
        "user_move": "e2e4",  # Latest user move
        "timestamp": 1234567890.123  # When the move was made
    }
    """
    with move_lock:
        return jsonify({
            "move": latest_moves["engine_move"],
            "user_move": latest_moves["user_move"],
            "timestamp": latest_moves["timestamp"]
        })

@app.route('/reset_game', methods=['POST'])
def reset_game():
    """Reset the chess game to the starting position"""
    global board, latest_moves
    
    board = chess.Board()
    
    # Reset latest moves
    with move_lock:
        latest_moves = {
            "user_move": None,
            "engine_move": None,
            "timestamp": None
        }
    
    # Reset Stockfish if available
    if engine_available:
        stockfish.set_position([])
    
    return jsonify({"success": True, "fen": board.fen()})

if __name__ == '__main__':
    app.run(debug=True)

