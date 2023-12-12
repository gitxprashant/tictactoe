from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Game state variables
players = [None, None]
current_player = 0
board = [""] * 9
game_in_progress = True

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tic Tac Toe</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }

            h1 {
                color: #333;
            }

            #container {
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            #playerNumber {
                margin-bottom: 10px;
            }

            #board {
                display: grid;
                grid-template-columns: repeat(3, 100px);
                gap: 5px;
                margin-top: 20px;
            }

            .cell {
                width: 100px;
                height: 100px;
                border: 1px solid #ccc;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>Tic Tac Toe</h1>
            <p id="playerNumber"></p>
            <div id="board"></div>
            <p id="message"></p>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.2.0/socket.io.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.4.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const boardElement = document.getElementById('board');
                const messageElement = document.getElementById('message');
                let currentPlayer;

                const socket = io();

                socket.on('player_number', (data) => {
                    currentPlayer = data.playerNumber - 1;
                    document.getElementById('playerNumber').textContent = `You are player ${data.playerNumber}`;
                });

                socket.on('start_game', (data) => {
                    updateBoard(data);
                    messageElement.textContent = '';
                });

                socket.on('update_board', (data) => {
                    currentPlayer = data.currentPlayer;
                    updateBoard(data);
                    messageElement.textContent = '';
                });

                socket.on('invalid_move', (data) => {
                    messageElement.textContent = data.message;
                });

                socket.on('game_over', (data) => {
                    messageElement.textContent = data.message;
                });

                // Function to update the board on the client side
                function updateBoard(data) {
                    const cells = document.querySelectorAll('.cell');

                    cells.forEach((cell, index) => {
                        cell.textContent = data.board[index];
                    });

                    // Enable or disable cell clicks based on the game state
                    cells.forEach((cell, index) => {
                        cell.style.pointerEvents = data.board[index] === "" && data.currentPlayer === currentPlayer ? 'auto' : 'none';
                    });
                }

                // Function to send a move to the server
                function makeMove(move) {
                    socket.emit('make_move', { 'move': move, 'playerNumber': currentPlayer + 1 });
                }

                // Populate the initial board
                for (let i = 0; i < 9; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    cell.addEventListener('click', () => makeMove(i));
                    boardElement.appendChild(cell);
                }
            });
        </script>
    </body>
    </html>
    """)

@socketio.on('connect')
def handle_connect():
    global current_player, board
    player_number = len([p for p in players if p is not None]) + 1

    if player_number <= 2:
        players[player_number - 1] = request.sid

    emit('player_number', {'playerNumber': player_number})

    if player_number == 2:
        emit('start_game', {'board': board, 'currentPlayer': current_player}, room=players[0])
        emit('start_game', {'board': board, 'currentPlayer': current_player}, room=players[1])

@socketio.on('make_move')
def handle_make_move(data):
    global current_player, game_in_progress
    if not game_in_progress:
        return

    move = int(data['move'])
    player_number = data['playerNumber']

    if not (0 <= move < 9) or board[move] != "" or player_number != current_player + 1 or request.sid != players[current_player]:
        emit('invalid_move', {'message': f"Player {current_player + 1}'s turn"}, room=request.sid)
        return

    board[move] = 'X' if current_player == 0 else 'O'
    current_player = 1 - current_player

    emit('update_board', {'board': board, 'currentPlayer': current_player}, room=players[0])
    emit('update_board', {'board': board, 'currentPlayer': current_player}, room=players[1])

    check_game_state()

def check_game_state():
    global game_in_progress
    winner = check_winner()
    if winner:
        emit('game_over', {'message': f"Player {winner} wins!"})
        game_in_progress = False
    elif "" not in board:
        emit('game_over', {'message': "It's a draw!"})
        game_in_progress = False

def check_winner():
    # Check rows
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] != "":
            return board[i]

    # Check columns
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] != "":
            return board[i]

    # Check diagonals
    if board[0] == board[4] == board[8] != "":
        return board[0]
    if board[2] == board[4] == board[6] != "":
        return board[2]

    return ""

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
