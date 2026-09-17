from arena.board import Board, BLACK, WHITE, RED, YELLOW
from arena.player import Player
from arena.record import get_games, Result, record_game, ratings
from datetime import datetime
from typing import List, Optional
from arena.llm import LLM


class Game:
    """
    A Game consists of an 8x8 Othello Board and 2 AI players
    """

    def __init__(
        self,
        model_black: Optional[str] = None,
        model_white: Optional[str] = None,
        # Backwards compatibility parameters
        model_red: Optional[str] = None,
        model_yellow: Optional[str] = None,
    ):
        """
        Initialize this Game; a new board, and new Player objects
        """
        black_model = model_black or model_red or LLM.all_model_names()[0]
        white_model = model_white or model_yellow or LLM.all_model_names()[1]

        self.board = Board()
        black_player = Player(black_model, BLACK)
        white_player = Player(white_model, WHITE)

        self.players = {
            BLACK: black_player,
            WHITE: white_player,
            # Backwards compatibility keys
            RED: black_player,
            YELLOW: white_player,
        }

    def reset(self):
        """
        Restart the game by resetting the board; keep players the same
        """
        self.board = Board()

    def move(self):
        """
        Make the next move. Delegate to the current player to make a move on this board.
        """
        if not self.is_active():
            return

        current_player = self.players[self.board.player]
        current_player.move(self.board)

    def is_active(self) -> bool:
        """
        Return True if the game hasn't yet ended
        """
        return self.board.is_active()

    def thoughts(self, player: int) -> str:
        """
        Return the inner thoughts of the given player
        """
        return self.players[player].thoughts()

    @staticmethod
    def get_games() -> List[Result]:
        """
        Return all the games stored in the db
        """
        return get_games()

    @staticmethod
    def get_ratings():
        """
        Return the ELO ratings of all players - filter out any models that are not supported
        """
        return {
            model: rating
            for model, rating in ratings().items()
            if model in LLM.all_supported_model_names()
        }

    def record(self):
        """
        Store the results of this game in the DB
        """
        black_player = self.players[BLACK].llm.model_name
        white_player = self.players[WHITE].llm.model_name
        black_won = self.board.winner == BLACK
        white_won = self.board.winner == WHITE
        black_score, white_score = self.board.score()

        result = Result(
            black_player=black_player,
            white_player=white_player,
            black_won=black_won,
            white_won=white_won,
            black_score=black_score,
            white_score=white_score,
            when=datetime.now(),
        )
        record_game(result)

    def run(self):
        """
        If being used outside gradio; move and print in a loop
        """
        while self.is_active():
            self.move()
            print(self.board)
