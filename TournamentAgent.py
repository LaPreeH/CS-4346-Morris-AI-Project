"""Tournament AI: python TournamentAgent.py input.txt output.txt depth W game

Optional final arguments: color W/B and phase opening/game. Defaults W/game.
The organizer must specify how turn and opening phase are communicated.
"""
import argparse
from morris_engine import search, validate

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('depth', type=int)
    parser.add_argument('color', choices=('W','B'), nargs='?', default='W')
    parser.add_argument('phase', choices=('opening','game'), nargs='?', default='game')
    args = parser.parse_args()
    with open(args.input_file, encoding='utf-8') as f:
        board = validate(f.read())
    outcome = search(board, args.depth, args.phase, args.color, alpha_beta=True, improved=True)
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(outcome.board + '\n')
    print('Board Position:', outcome.board)
    print('Positions evaluated by static estimation:', outcome.evaluations)
    print('MINIMAX estimate:', outcome.score)
