import random

from engine_base import BaseEngine


# Here's a dumb example of a real Engine
class RandomEngine(BaseEngine):

    def do_move(self):
        return random.choice(list(self.board.legal_moves))
