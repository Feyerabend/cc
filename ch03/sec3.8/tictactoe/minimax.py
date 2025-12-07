import math

# constants
EMPTY = 0
PLAYER_X = 1
PLAYER_O = -1

def print_board(board):
    """Prints the Tic-Tac-Toe board."""
    for i in range(3):
        row = ""
        for j in range(3):
            if board[i][j] == PLAYER_X:
                row += "X "
            elif board[i][j] == PLAYER_O:
                row += "O "
            else:
                row += "- "
        print(row)
    print()

def is_winner(board, player):
    """Check if the given player has won."""
    for i in range(3):
        # check rows and columns
        if all(board[i][j] == player for j in range(3)) or all(board[j][i] == player for j in range(3)):
            return True
    # check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False

def is_full(board):
    """Check if the board is full."""
    return all(board[i][j] != EMPTY for i in range(3) for j in range(3))

def minimax(board, depth, is_maximizing):
    """Minimax algorithm to evaluate the best move for the maximizing player."""
    if is_winner(board, PLAYER_X):
        return 1  # X wins
    if is_winner(board, PLAYER_O):
        return -1  # O wins
    if is_full(board):
        return 0  # draw

    if is_maximizing:
        best_score = -math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == EMPTY:
                    board[i][j] = PLAYER_X  # make the move for X
                    score = minimax(board, depth + 1, False)  # minimize for O
                    board[i][j] = EMPTY  # undo move
                    best_score = max(score, best_score)
        return best_score
    else:
        best_score = math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == EMPTY:
                    board[i][j] = PLAYER_O  # make the move for O
                    score = minimax(board, depth + 1, True)  # maximize for X
                    board[i][j] = EMPTY  # undo move
                    best_score = min(score, best_score)
        return best_score

def best_move(board):
    """Returns the best move for the AI (Player X)."""
    best_score = -math.inf
    move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == EMPTY:
                board[i][j] = PLAYER_X  # make move for X
                score = minimax(board, 0, False)  # minimize for O
                board[i][j] = EMPTY  # undo move
                if score > best_score:
                    best_score = score
                    move = (i, j)
    return move

board = [
    [PLAYER_X, PLAYER_O, EMPTY],
    [PLAYER_X, PLAYER_O, EMPTY],
    [EMPTY, EMPTY, EMPTY]
]

print_board(board)
move = best_move(board)
print(f"Best move for X is at position {move}")
