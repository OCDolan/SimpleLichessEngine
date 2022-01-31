from lichess_connector import SimpleLichess
import config as config_file


if __name__ == "__main__":
    # Connect
    sl = SimpleLichess(config_file.my_username, config_file.token)
    sl.catch_engine_exceptions = True  # Use False for debugging your Chess Engine

    # Create a challenge with another player
    sl.create_challenge(config_file.target_user)

    # Wait for any challenge you have created to start
    sl.wait_for_game_start()

    # Import your engine!
    from engine_random import RandomEngine
    sl.set_engine(RandomEngine)

    # Plays the whole game from whatever the current state of the game is, untill finish
    sl.play_with_engine()

