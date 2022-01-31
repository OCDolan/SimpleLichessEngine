from lichess_connector import SimpleLichess
import config as config_file

# Connect
sl = SimpleLichess(config_file.my_username, config_file.token)
sl.catch_engine_exceptions = True  # Use False for debugging your Chess Engine

# Create a challenge with another player
# sl.create_challenge(config_file.target_user)

# Wait for any challenge you have created to start
# sl.wait_for_game_start()

# List all challenges you have created or are included in
# sl.list_challenges()

# Load the current game state as a board
# load_game_state_as_chess_board()

# Make a single move
# sl.make_move('a2b2')

# Accept any challenge you have pending
# sl.accept_next_challenge()

# Import your engine!
from engine_random import RandomEngine
sl.set_engine(RandomEngine)

# Do a single move using your engine. (Assumes it is already your turn, else will crash!)
# sl.do_engine_move()

# Plays the whole game from whatever the current state of the game is, untill finish
sl.play_with_engine()

