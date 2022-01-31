import requests
import json
import random
import time

import chess


from engine_random import BaseEngine


class LichessApiError(Exception):
    pass


class LichessGenericError(Exception):
    pass


###############################################################################
# python-chess functions
# https://python-chess.readthedocs.io/en/latest/index.html
###############################################################################

def convert_moves_to_board(moves):
    board = chess.Board()
    for move in moves:
        if move != '':
            board.push_san(move)
    return board

###############################################################################
# SimpleLichess Class
###############################################################################

class SimpleLichess:

    def __init__(self, username, token):
        self.username = username
        self.token = token

        self.url = 'https://lichess.org/api'
        self.default_headers = {'Authorization': f'Bearer {token}',
                                'Content type': 'application/json'}

        self.session = requests.Session()  # Create a session
        self.session.headers = {'Authorization': f'Bearer {token}',
                                'Content type': 'application/json'}

        self.streaming_response = {}

        self.catch_engine_exceptions = True
        self.verbose = False

        self.current_game_id = None
        self.engine = None
        self.added_move_time_delay = 0

    ###########################################################################
    # General functions for the Lichess API
    # https://lichess.org/api
    ###########################################################################

    @staticmethod
    def handle_return(resp):
        if resp.status_code == 200:
            return resp.json()
        else:
            raise LichessApiError(resp.text)

    def get_stream_events(self, endpoint='stream/event'):
        if self.streaming_response.get(endpoint, None) is not None:
            raise LichessGenericError("Another thread is already reading the streaming events!")

        self.streaming_response[endpoint] = self.session.get(f'{self.url}/{endpoint}', stream=True)
        try:
            for line in self.streaming_response[endpoint].iter_lines():
                if line == b'':
                    print("Received Empty response")
                    continue
                yield json.loads(line)
        except AttributeError as e:
            if "'NoneType' object has no attribute 'readline'" in str(e):
                # Expected this if stream is closed
                return

    def close_stream_events(self, endpoint):
        if self.streaming_response[endpoint] is not None:
            self.streaming_response[endpoint].close()
            self.streaming_response[endpoint] = None

    ###########################################################################
    # Miscelaneous functions for SimpleLichess class
    ###########################################################################

    def set_engine(self, engine):
        if list(engine.__bases__)[0] == BaseEngine \
                and 'do_move' in dir(engine):
            self.engine = engine
        else:
            raise AttributeError("Engine supplied does not work")

    ###########################################################################
    # Challenges
    # https://lichess.org/api#tag/Challenges
    ###########################################################################

    def create_challenge(self, opponent_username) :
        url = f'{self.url}/challenge/{opponent_username}'
        resp = self.session.post(
            url,
            params={'username': 'GlitchyMammal',
                    'rated': False,
                    'clock.limit': 300,
                    'clock.increment': 0,
                    'variant': 'standard'})
        return self.handle_return(resp)

    def accept_challenge(self, id=None):
        """
        :param id: If not given, will accept an open challenge
        :return:
        """
        if id is None:
            # Find an open challenge and accept it
            challenges_received = self.list_challenges_received()
            if not challenges_received:
                raise LichessGenericError("No Challenges to Accept")
            else:
                # At least one challenge recieved - Accept the first
                id = challenges_received[0]['id']

        resp = self.session.post(f'{self.url}/challenge/{id}/accept')
        ret = self.handle_return(resp)
        self.current_game_id = id
        return ret

    def list_challenges(self):
        """
        Lists all challenges
        :return:
        """
        resp = self.session.get(f'{self.url}/challenge')
        return self.handle_return(resp)

    def list_challenges_received(self):
        """
        Lists all challenges other users have challenged you
        :return:
        """
        resp = self.session.get(f'{self.url}/challenge')
        return self.handle_return(resp)['in']

    def list_challenges_created(self):
        """
        Lists all challenges you have given to other users
        :return:
        """
        resp = self.session.get(f'{self.url}/challenge')
        return self.handle_return(resp)['out']

    def accept_next_challenge(self):
        """
        Open a stream, and wait for a challenge, and accept the first one found
        :return:
        """
        for event in self.get_stream_events():
            if event['type'] == 'challenge':
                self.accept_challenge(event['challenge']['id'])
                self.close_stream_events('stream/event')

    ###########################################################################
    # Games
    # https://lichess.org/api#tag/Games
    ###########################################################################

    def wait_for_game_start(self, game_id=None):
        """
        Blocks until game is started
        :param game_id:
        :return: ID of started game
        """
        for event in self.get_stream_events():
            if event['type'] == 'gameStart':
                if game_id is None or (game_id == event['game']['id']):
                    return event['game']['id']
        time.sleep(1)

    def get_ongoing_games(self):
        resp = self.session.get(f'{self.url}/account/playing')
        return self.handle_return(resp)

    def load_ongoing_game(self, game_id=None):
        if game_id is None:
            game_id = self.current_game_id
        if game_id is None:
            game_id = self.get_ongoing_games()['nowPlaying'][0]['gameId']
        self.current_game_id = game_id

    def get_bot_game_full_state(self, game_id=None):
        self.load_ongoing_game(game_id=game_id)
        endpoint = f'bot/game/stream/{self.current_game_id}'
        for event in self.get_stream_events(endpoint):
            if event['type'] == 'gameFull':
                self.close_stream_events(endpoint)
                return event

    def load_game_state_as_chess_board(self):
        game = self.get_bot_game_full_state()
        # Check for for expected API content
        if self.get_bot_game_full_state()['state']['type'] != 'gameState':
            raise LichessGenericError("Unknown API state")

        return convert_moves_to_board(game['state']['moves'].split(' '))

    def make_move(self, move):
        """
        Send the move to lichess
        :param move: The move to play, in UCI format
            example: "e2e4"
        :return:
        """
        resp = self.session.post(f'{self.url}/bot/game/{self.current_game_id}/move/{move}')
        return self.handle_return(resp)

    def make_board_move(self, board):
        """
        Takes a chess.Board type and uploads the most recent move
        :return:
        """
        return self.make_move(board.peek().uci())

    ###########################################################################
    # Engine - Lichess interaction
    ###########################################################################

    def do_engine_move(self, board=None):
        """
        Use the engine provided (self.engine) and tell it to do the next move on lichess
        :param board: chess.Board object
        :return:
        """
        # Get the board if not given
        if board is None:
            board = self.load_game_state_as_chess_board()

        # Firstly see if there are any valid moves, and exit if not
        if not list(board.legal_moves):
            return

        # Since we need to take a turn, Wait if required to give lichess
        # a time to catch its breath so we don't hit the API throttle
        time.sleep(self.added_move_time_delay)

        # And now we count anything after here as engine time
        engine_timer_start = time.time()

        # Start the engine!
        eng = self.engine(board)

        try:
            requested_move = eng.do_move()
            engine_timer_stop = time.time()
            if requested_move not in list(board.legal_moves):
                print(f"Valid moves: {str(list(board.legal_moves))}")
                raise ValueError(f"{requested_move} - Not a valid move!")
        except Exception as e:
            engine_timer_stop = time.time()
            if self.catch_engine_exceptions:
                print(e)
            else:
                raise e
            # Bot was unable to find a valid move - perform a random move
            requested_move = random.choice(list(board.legal_moves))

        engine_time_ms = round(1000*(engine_timer_stop - engine_timer_start))
        print(f"Time taken in engine: {engine_time_ms}ms")

        self.make_move(requested_move)

    @staticmethod
    def get_moves(moves):
        return [t for t in moves.split(' ') if t != '']

    def play_with_engine(self, game_id=None):

        self.load_ongoing_game(game_id=game_id)
        endpoint = f'bot/game/stream/{self.current_game_id}'

        events = self.get_stream_events(endpoint)

        # The first element is the current game (gameFull)
        # https://lichess.org/api#operation/botGameStream
        full_game = next(events)
        # Find out if engine is white or black
        is_engine_white = full_game['white']['id'].lower() == self.username.lower()

        # Also, if this function is started when it's the engine turn, we need to know,
        # as we don't get an event yet
        turns = self.get_moves(full_game['state']['moves'])
        is_white_turn = (len(turns) % 2) == 0
        if is_engine_white == is_white_turn:
            # If (engine is white and white turn) or (engine is black and black turn)
            board = convert_moves_to_board(turns)
            self.do_engine_move(board=board)

        # Now for the remaining (and future events)
        for event in events:
            if event['type'] == 'gameState':
                turns = self.get_moves(event['moves'])
                is_white_turn = (len(turns) % 2) == 0
                if is_engine_white == is_white_turn:
                    # If (engine is white and white turn) or (engine is black and black turn)
                    board = convert_moves_to_board(turns)
                    self.do_engine_move(board=board)
                else:
                    pass  # Event says it's not your turn, go to the next event
