import requests
from stockfish import Stockfish

def is_server_running(url="http://127.0.0.1:5000"):
    """
    Checks if the Flask server is running.
    Returns:
        bool: True if the server is running, False otherwise.
    """
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def initialize_stockfish():
    """
    Initialize the Stockfish chess engine.
    Returns:
        Stockfish: An instance of the Stockfish chess engine.
    """
    stockfish = Stockfish(path="./stockfish-windows-x86-64-avx2.exe", 
                          parameters={"Threads": 2, "Skill Level": 20})
    stockfish.set_position([])  # Start with a new game
    return stockfish

def display_board(stockfish):
    """
    Displays the current chessboard position in a character-based format.
    Uses '.' for empty spaces and FEN notation for pieces.
    """
    fen = stockfish.get_fen_position()
    board, _ = fen.split(" ", 1)  # Get the board part of the FEN string
    rows = board.split("/")  # Each row is separated by '/'

    print("\nCurrent Board Position:")
    for row in rows:
        formatted_row = ''.join(c if not c.isdigit() else '.' * int(c) for c in row)
        print(' '.join(formatted_row))  # Add spaces for better readability
    print("\n")

def send_fen_to_server(fen, move):
    """
    Sends the current FEN notation along with the move to the Flask server.
    """
    url = "http://127.0.0.1:5000/set_fen"
    data = {"fen": fen, "move": move}
    try:
        response = requests.post(url, json=data)
        print("Server Response:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error sending FEN to server:", e)

def get_opponent_move():
    """
    Fetches the latest move from the web interface.
    Returns:
        str: The opponent's move in UCI format, or None if no move is available.
    """
    url = "http://127.0.0.1:5000/get_move"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("move", None)
    except requests.exceptions.RequestException as e:
        print("Error fetching opponent move:", e)
    return None

def play_move(stockfish, move, online_mode):
    """
    Plays a move in the Stockfish engine.
    Parameters:
        stockfish (Stockfish): The Stockfish instance.
        move (str): The move in UCI format (e.g., "e2e4").
        online_mode (bool): Whether to send updates to the server.
    Returns:
        bool: True if the move is valid, False otherwise.
    """
    if stockfish.is_move_correct(move):
        stockfish.make_moves_from_current_position([move])
        return True
    else:
        return False

def get_best_move(stockfish):
    """
    Gets the best move from the Stockfish engine.
    Returns:
        str: The best move in UCI format.
    """
    return stockfish.get_best_move()

if __name__ == "__main__":
    # Check if the server is running
    online_mode = is_server_running()
    if online_mode:
        print("Running in ONLINE mode: FEN will be sent to the server.")
    else:
        print("Running in OFFLINE mode: No server connection detected.")

    # Initialize the Stockfish engine
    stockfish = initialize_stockfish()

    print("Welcome to Stockfish Chess Engine!")
    print("You can make moves in UCI format (e.g., 'e2e4'). Type 'exit' to quit.\n")

    while True:
        # Display the current board
        display_board(stockfish)

        # Get the opponent's move from the web interface
        user_move = get_opponent_move()
        if not user_move:
            user_move = input("Opponent's move (in UCI format): ").strip().lower()

        if user_move == "exit":
            print("Exiting the game. Goodbye!")
            break

        # Validate and play the opponent's move
        if not play_move(stockfish, user_move, online_mode):
            print(f"Invalid move: {user_move}. Try again.")
            continue

        # Display opponent's move
        print(f"Opponent played: {user_move}")

        # Send updated FEN after opponent's move
        if online_mode:
            send_fen_to_server(stockfish.get_fen_position(), user_move)

        # Get and play Stockfish's best move
        best_move = get_best_move(stockfish)
        if best_move:
            print(f"Stockfish's move: {best_move}")
            play_move(stockfish, best_move, online_mode)

            # Send updated FEN after Stockfish's move
            if online_mode:
                send_fen_to_server(stockfish.get_fen_position(), best_move)
        else:
            print("No valid moves available. The game is over.")
            break
