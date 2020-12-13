# ===============================================================================
# Imports
# ===============================================================================
import math

import abstract
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP
import time
from collections import defaultdict

# ===============================================================================
# Globals
# ===============================================================================

PAWN_WEIGHT = 5
PAWN_HALF_WEIGHT = 7
KING_WEIGHT = 10


# ===============================================================================
# Player
# ===============================================================================

class Player(abstract.AbstractPlayer):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)
        self.clock = time.process_time()

        # We are simply providing (remaining time / remaining turns) for each turn in round.
        # Taking a spare time of 0.05 seconds.
        self.turns_remaining_in_round = self.k
        self.time_remaining_in_round = self.time_per_k_turns
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

    def get_move(self, game_state, possible_moves):
        self.clock = time.process_time()
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        if len(possible_moves) == 1:
            return possible_moves[0]

        current_depth = 1
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything
        minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time,
                                              self.selective_deepening_criterion)

        # Iterative deepening until the time runs out.
        while True:

            print('going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}'.format(
                current_depth,
                self.time_for_current_move - (time.process_time() - self.clock),
                prev_alpha,
                best_move))

            try:
                (alpha, move), run_time = run_with_limited_time(
                    minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {},
                    self.time_for_current_move - (time.process_time() - self.clock))
            except (ExceededTimeError, MemoryError):
                print('no more time, achieved depth {}'.format(current_depth))
                break

            if self.no_more_time():
                print('no more time')
                break

            prev_alpha = alpha
            best_move = move

            if alpha == INFINITY:
                print('the move: {} will guarantee victory.'.format(best_move))
                break

            if alpha == -INFINITY:
                print('all is lost')
                break

            current_depth += 1

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.process_time() - self.clock)
        return best_move

    def utility(self, state):
        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY
        if state.turns_since_last_jump >= MAX_TURNS_NO_JUMP:
            return 0

        red_score = 0
        black_score = 0
        black_pawn = 0
        red_pawn = 0
        black_king = 0
        red_king = 0
        for location in state.board:
            loc_val = state.board[location]
            if loc_val != EM:
                if loc_val == 'r' and location[0] > 3:
                    red_score += PAWN_HALF_WEIGHT
                    red_pawn += 1
                if loc_val == 'r' and location[0] <= 3:
                    red_score += PAWN_WEIGHT
                    red_pawn += 1
                if loc_val == 'b' and location[0] < 3:
                    black_score += PAWN_HALF_WEIGHT
                    black_pawn += 1
                if loc_val == 'b' and location[0] >= 3:
                    black_score += PAWN_WEIGHT
                    black_pawn += 1
                if loc_val == 'B':
                    black_score += KING_WEIGHT
                    black_king += 1
                if loc_val == 'R':
                    red_score += KING_WEIGHT
                    red_king += 1

        if self.color == 'red':
            my_u = red_score
            op_u = black_score
        else:
            my_u = black_score
            op_u = red_score

        if my_u == 0:
            # I have no tools left
            return -INFINITY
        elif op_u == 0:
            # The opponent has no tools left
            return INFINITY
        if red_pawn == 0 and black_pawn == 0:
            if self.color == 'red':
                king = 'R'
                opp_king = 'B'
            else:
                king = 'B'
                opp_king = 'R'
            for location in state.board:
                total_dist = 0
                if state.board[location] == king:
                    for l in state.board:
                        if state.board[location] == opp_king:
                            total_dist += math.sqrt(((location[0] - l[0]) ** 2) + ((location[1] - l[1]) ** 2))

            if self.color == 'red' and red_king > black_king or self.color == 'black' and black_king > red_king:
                return 1/total_dist
            else:
                total_dist
        else:
            return my_u - op_u

    def selective_deepening_criterion(self, state):
        # Simple player does not selectively deepen into certain nodes.
        return False

    def no_more_time(self):
        return (time.process_time() - self.clock) >= self.time_for_current_move

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'simple')

# c:\python35\python.exe run_game.py 3 3 3 y simple_player random_player
