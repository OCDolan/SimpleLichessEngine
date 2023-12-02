# SimpleLichessConnector

## Install
Clone the repo and use the typical `python3 -m pip install -r requirements.txt` to install all the requirements

## Setup
Copy [example_config.py](example_config.py) to `config.py` and fill in the values as described in the file.

## Use
Run one of the below example scripts to have a play.

* Use [example_challenge_player_and_play.py](example_challenge_player_and_play.py) will connect to lichess and send a request to the target player from `config.py`
Once the target player has accepted, then game will start, and the bot will start making moves using your engine.

* Use [example_accept_challenge_and_play.py](example_accept_challenge_and_play.py) if a player has challenged the bot account, and you wish to accept the players
challenge.

* Use [example_resume_ongoing_game.py](example_resume_ongoing_game.py) to do exactly what it says.

For more functions available, take a look at [lichess_connector.py](lichess_connector.py).
