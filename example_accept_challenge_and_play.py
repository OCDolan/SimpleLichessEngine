from lichess_connector import SimpleLichess
import config as config_file


if __name__ == "__main__":
    # Connect
    sl = SimpleLichess(config_file.my_username, config_file.token)
    sl.catch_engine_exceptions = True  # Use False for debugging your Chess Engine

    # Accept any challenge you have pending
    sl.accept_next_challenge()

    # Import your engine!
    from engine_random import RandomEngine
    sl.set_engine(RandomEngine)

    # Plays the whole game from whatever the current state of the game is, until finish
    sl.play_with_engine()
