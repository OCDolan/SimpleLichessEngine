class BaseEngine:

    def __init__(self, board):
        self.board = board

    # Implement the following functions

    def do_move(self):
        """
        Uses the self.board chess.Board object, and gives out the chosen move in UCI
        :return:
        """
        raise NotImplementedError
