"""Shared search engine for the 23-location Morris variant.

Board order (0..22) follows the instructor handout. Search scores are from
White's perspective for the classic functions; the root can be either color.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import inf
from time import monotonic

NEIGHBORS = (
    (1, 3, 8), (0, 2, 4), (1, 5, 13), (0, 4, 6, 9),
    (1, 3, 5), (2, 4, 7, 12), (3, 7, 10), (5, 6, 11),
    (0, 9, 20), (3, 8, 10, 17), (6, 9, 14), (7, 12, 16),
    (5, 11, 13, 19), (2, 12, 22), (10, 15, 17),
    (14, 16, 18), (11, 15, 19), (9, 14, 18, 20),
    (15, 17, 19, 21), (12, 16, 18, 22), (8, 17, 21),
    (18, 20, 22), (13, 19, 21),
)
MILLS = (
    (0,1,2),(0,3,6),(0,8,20),
    (2,5,7),(2,13,22),(3,4,5),(3,9,17),
    (5,12,19),(6,10,14),(7,11,16),
    (8,9,10),(11,12,13),(14,15,16),
    (14,17,20),(15,18,21),(16,19,22),
    (17,18,19),(20,21,22),
)
MILLS_AT = tuple(tuple(m for m in MILLS if i in m) for i in range(23))


def validate(board: str) -> str:
    board = board.strip()
    if len(board) != 23 or any(c not in 'WBx' for c in board):
        raise ValueError('Board must be exactly 23 characters from W, B, x.')
    return board


def opposite(player: str) -> str:
    return 'B' if player == 'W' else 'W'


def close_mill(board: str, location: int) -> bool:
    color = board[location]
    return color != 'x' and any(all(board[j] == color for j in mill) for mill in MILLS_AT[location])


def replace(board: str, index: int, piece: str) -> str:
    return board[:index] + piece + board[index+1:]


def with_capture(board: str, player: str) -> list[str]:
    opponent = opposite(player)
    removable = [i for i,c in enumerate(board) if c == opponent and not close_mill(board,i)]
    # The instructor explicitly says to retain the board unchanged if every
    # opposing piece is in a mill. This differs from common Morris rules.
    if not removable:
        return [board]
    return [replace(board, i, 'x') for i in removable]


def legal_moves(board: str, player: str, phase: str) -> list[str]:
    """Generate all successor board strings in deterministic location order."""
    result = []
    if phase == 'opening':
        for destination, piece in enumerate(board):
            if piece != 'x':
                continue
            moved = replace(board, destination, player)
            result.extend(with_capture(moved, player) if close_mill(moved, destination) else [moved])
    elif phase == 'game':
        count = board.count(player)
        for source, piece in enumerate(board):
            if piece != player:
                continue
            targets = range(23) if count == 3 else NEIGHBORS[source]
            for destination in targets:
                if board[destination] != 'x':
                    continue
                moved = replace(replace(board, source, 'x'), destination, player)
                result.extend(with_capture(moved, player) if close_mill(moved, destination) else [moved])
    else:
        raise ValueError("phase must be 'opening' or 'game'")
    return result


def original_evaluation(board: str, phase: str) -> int:
    white = board.count('W')
    black = board.count('B')
    if phase == 'opening':
        return white - black
    if black <= 2:
        return 10000
    if white <= 2:
        return -10000
    black_moves = len(legal_moves(board, 'B', 'game'))
    if black_moves == 0:
        return 10000
    return 1000 * (white - black) - black_moves


def mill_counts(board: str, color: str) -> tuple[int,int]:
    """Completed mills and two-in-line mills with a vacant third location."""
    completed = threats = 0
    for mill in MILLS:
        chars = [board[i] for i in mill]
        if chars.count(color) == 3:
            completed += 1
        elif chars.count(color) == 2 and chars.count('x') == 1:
            threats += 1
    return completed, threats


def improved_evaluation(board: str, phase: str) -> int:
    """Symmetric heuristic: positive scores favor White."""
    w = board.count('W')
    b = board.count('B')
    if phase == 'game':
        if b <= 2:
            return 100000
        if w <= 2:
            return -100000
    wm, wt = mill_counts(board, 'W')
    bm, bt = mill_counts(board, 'B')
    piece_weight, mill_weight, threat_weight = ((100, 45, 24) if phase == 'opening'
                                                else (1000, 90, 35))
    score = (piece_weight * (w-b) + mill_weight * (wm-bm)
             + threat_weight * (wt-bt))
    if phase == 'game':
        white_moves = len(legal_moves(board, 'W', 'game'))
        black_moves = len(legal_moves(board, 'B', 'game'))
        if not black_moves:
            return 100000
        if not white_moves:
            return -100000
        score += 3 * (white_moves - black_moves)
        blocked_w = sum(all(board[n]!='x' for n in NEIGHBORS[i]) for i,c in enumerate(board) if c == 'W') if w > 3 else 0
        blocked_b = sum(all(board[n]!='x' for n in NEIGHBORS[i]) for i,c in enumerate(board) if c == 'B') if b > 3 else 0
        score += 15 * (blocked_b - blocked_w)
    else:
        # Valuable highly-connected sites support more future placements.
        score += 3 * sum((len(NEIGHBORS[i]) if c=='W' else -len(NEIGHBORS[i]) if c=='B' else 0)
                         for i,c in enumerate(board))
    return score


@dataclass
class Result:
    board: str
    score: int
    evaluations: int


def search(board: str, depth: int, phase: str = 'game', color: str = 'W',
           alpha_beta: bool = False, improved: bool = False,
           deadline: float | None = None) -> Result:
    """Depth-limited MINIMAX/ALPHA-BETA, keeping the first equal-score move."""
    validate(board)
    if color not in 'WB' or phase not in ('opening','game') or depth < 0:
        raise ValueError('Invalid color, phase or depth')
    evaluator = improved_evaluation if improved else original_evaluation
    leaves = 0

    def check_time():
        if deadline is not None and monotonic() >= deadline:
            raise TimeoutError("Search time limit exceeded")
    
    def visit(position: str, remaining: int, turn: str, alpha: float, beta: float) -> int:
        nonlocal leaves

        check_time()
        if remaining == 0:
            leaves += 1
            return evaluator(position, phase)
        options = legal_moves(position, turn, phase)
        if not options:
            if phase == 'game':
                # A blocked player loses, independent of which turn it is.
                return -100000 if turn == 'W' else 100000
            leaves += 1
            return evaluator(position, phase)
        maximize = turn == 'W'
        best = -inf if maximize else inf
        for next_position in options:
            value = visit(next_position, remaining - 1, opposite(turn), alpha, beta)
            if maximize:
                best = max(best, value)
                alpha = max(alpha, best)
            else:
                best = min(best, value)
                beta = min(beta, best)
            if alpha_beta and alpha >= beta:
                break
        return int(best)

    if depth == 0:
        return Result(board, visit(board, 0, color, -inf, inf), leaves)
    options = legal_moves(board, color, phase)
    if not options:
        score = visit(board, depth, color, -inf, inf)
        return Result(board, score, leaves)
    maximizing = color == 'W'
    best = -inf if maximizing else inf
    chosen = options[0]
    alpha, beta = -inf, inf
    for next_board in options:
        score = visit(next_board, depth-1, opposite(color), alpha, beta)
        if (score > best if maximizing else score < best):
            best, chosen = score, next_board
        if maximizing:
            alpha = max(alpha, best)
        else:
            beta = min(beta, best)
        # Do not prematurely prune root: retain deterministic optimal tie-break.
    return Result(chosen, int(best), leaves)


def main(phase: str, color: str = 'W', alpha_beta: bool = False, improved: bool = False):
    import argparse
    parser = argparse.ArgumentParser(description='23-position Morris AI')
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('depth', type=int)
    args = parser.parse_args()
    with open(args.input_file, encoding='utf-8') as f:
        board = validate(f.read())
    result = search(board, args.depth, phase, color, alpha_beta, improved)
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(result.board + '\n')
    print(f'Board Position: {result.board}')
    print(f'Positions evaluated by static estimation: {result.evaluations}')
    print(f'MINIMAX estimate: {result.score}')

def main(phase: str, color: str = 'W', alpha_beta: bool = False, improved: bool = False):
    import argparse
    parser = argparse.ArgumentParser(description='23-position Morris AI')
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('depth', type=int)
    args = parser.parse_args()
    with open(args.input_file, encoding='utf-8') as f:
        board = validate(f.read())
    result = search(board, args.depth, phase, color, alpha_beta, improved)
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(result.board + '\n')
    print(f'Board Position: {result.board}')
    print(f'Positions evaluated by static estimation: {result.evaluations}')
    print(f'MINIMAX estimate: {result.score}')


def timed_search(board: str, color: str, phase: str, seconds: float = 30.0,
                 maximum_depth: int = 20) -> Result:
    """Iterative-deepening alpha-beta; return last fully searched legal choice."""
    validate(board)
    if seconds <= 0 or maximum_depth < 1:
        raise ValueError("seconds and maximum_depth must be positive")
    moves = legal_moves(board, color, phase)
    if not moves:
        raise ValueError("No legal move exists for the selected player and phase")
    deadline = monotonic() + seconds
    best = Result(moves[0], improved_evaluation(moves[0], phase), 0)
    for depth in range(1, maximum_depth + 1):
        if monotonic() >= deadline:
            break
        try:
            completed = search(board, depth, phase, color,
                               alpha_beta=True, improved=True, deadline=deadline)
        except TimeoutError:
            break
        best = completed
    return best
