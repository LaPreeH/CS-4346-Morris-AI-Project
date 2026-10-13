# CS4346 Morris AI Tournament

Python 3.10+; no third-party dependencies. All entry scripts expect:

```bash
python MiniMaxOpening.py board1.txt board2.txt 2
python ABGame.py board1.txt board2.txt 2
python TournamentAgent.py board1.txt board2.txt 3 B game
python -m unittest discover -v
```

The file `board1.txt` must contain exactly 23 `W`, `B` or `x` symbols.
Output file will contain the chosen successor board.

The 8 course-requested scripts each accept three positional arguments. Shared
logic is in `morris_engine.py`. The tournament script also accepts optional
color (`W` or `B`) and phase (`opening` or `game`), defaulting to W/game.
**Confirm the tournament protocol and per-move time limit with the instructor.**
The brief provided no time limit, input protocol, or opening placement counters.
Because piece counts alone cannot reveal how many pieces were previously
captured, opening phase cannot always be inferred correctly from board strings.

This program follows the handout's exact `GenerateRemove` instruction: if all
opposing pieces are already in mills, leave the board unchanged rather than
removing a mill piece. No repetition/draw rule was specified in the handout.

Depth counts plies (each individual player turn), not full turns. Move ordering
is by ascending board index, consistently across MINIMAX and ALPHA-BETA.
Scores for basic game evaluation are always White-oriented, including in the
Black programs; Black minimizes them. The improved evaluation is symmetric.

Note that a practical tournament agent may need iterative deepening and a
verified turn-time cutoff once the actual protocol is supplied.
