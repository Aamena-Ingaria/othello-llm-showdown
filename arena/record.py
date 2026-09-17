import logging
import os
import math
from datetime import datetime
from typing import List, Dict, Optional
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
except ImportError:
    MongoClient = None
    ConnectionFailure = None
    ServerSelectionTimeoutError = None



class Result:
    """
    Represents the result of a single game
    """

    def __init__(
        self,
        black_player: Optional[str] = None,
        white_player: Optional[str] = None,
        black_won: bool = False,
        white_won: bool = False,
        when: Optional[datetime] = None,
        black_score: int = 0,
        white_score: int = 0,
        # Backwards compatibility arguments
        red_player: Optional[str] = None,
        yellow_player: Optional[str] = None,
        red_won: Optional[bool] = None,
        yellow_won: Optional[bool] = None,
        **kwargs,
    ):
        self.black_player = black_player or red_player or "Unknown"
        self.white_player = white_player or yellow_player or "Unknown"
        self.black_won = black_won if black_won is not None else bool(red_won)
        self.white_won = white_won if white_won is not None else bool(yellow_won)
        self.when = when or datetime.now()
        self.black_score = black_score
        self.white_score = white_score

    # Backwards compatibility properties
    @property
    def red_player(self) -> str:
        return self.black_player

    @property
    def yellow_player(self) -> str:
        return self.white_player

    @property
    def red_won(self) -> bool:
        return self.black_won

    @property
    def yellow_won(self) -> bool:
        return self.white_won

    def to_dict(self) -> dict:
        return {
            "black_player": self.black_player,
            "white_player": self.white_player,
            "black_won": self.black_won,
            "white_won": self.white_won,
            "black_score": self.black_score,
            "white_score": self.white_score,
            "when": self.when,
            # Backwards compatibility in DB
            "red_player": self.black_player,
            "yellow_player": self.white_player,
            "red_won": self.black_won,
            "yellow_won": self.white_won,
        }


COLLECTION = "othello"


def _get_collection():
    """Helper function to get MongoDB collection with error handling"""
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if mongo_uri and MongoClient:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ismaster")
            db = client.outsmart
            return db[COLLECTION]
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return None
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        return None


def record_game(result: Result) -> bool:
    """
    Store the results in the database, if database is available.
    Returns True if successful, False if database is unavailable.
    """
    collection = _get_collection()
    if collection is None:
        return False

    game_dict = result.to_dict()

    try:
        collection.insert_one(game_dict)
        return True
    except Exception as e:
        logging.error("Failed to record a game in the database")
        logging.exception(e)
        return False


def get_games() -> List[Result]:
    """
    Return all games in the order that they were played.
    Returns empty list if database is unavailable.
    """
    collection = _get_collection()
    if collection is None:
        return []

    try:
        games = collection.find().sort("_id", 1)
        results = []
        for game in games:
            game.pop("_id", None)
            results.append(Result(**game))

        return results
    except Exception as e:
        logging.error("Error getting games")
        logging.exception(e)
        return []


class EloCalculator:
    def __init__(self, k_factor: float = 32, default_rating: int = 1000):
        """
        Initialize the ELO calculator.
        """
        self.k_factor = k_factor
        self.default_rating = default_rating
        self.ratings: Dict[str, float] = {}

    def get_player_rating(self, player: str) -> float:
        """Get a player's current rating, or default if they're new."""
        return self.ratings.get(player, self.default_rating)

    def calculate_expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate the expected score (win probability) for player A against player B.
        Uses the ELO formula: 1 / (1 + 10^((ratingB - ratingA)/400))
        """
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

    def update_ratings(
        self, player_a: str, player_b: str, score_a: float, score_b: float
    ) -> None:
        """
        Update ratings for two players based on their game outcome.
        """
        rating_a = self.get_player_rating(player_a)
        rating_b = self.get_player_rating(player_b)

        expected_a = self.calculate_expected_score(rating_a, rating_b)
        expected_b = 1 - expected_a

        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * (score_b - expected_b)

        self.ratings[player_a] = new_rating_a
        self.ratings[player_b] = new_rating_b


def calculate_elo_ratings(
    results: List[Result], exclude_self_play: bool = True
) -> Dict[str, float]:
    """
    Calculate final ELO ratings for all players based on a list of game results.
    """
    calculator = EloCalculator()

    for result in results:
        p1 = result.black_player
        p2 = result.white_player

        if exclude_self_play and p1 == p2:
            continue

        if result.black_won and not result.white_won:
            score_b, score_w = 1.0, 0.0
        elif result.white_won and not result.black_won:
            score_b, score_w = 0.0, 1.0
        else:
            score_b, score_w = 0.5, 0.5

        calculator.update_ratings(p1, p2, score_b, score_w)

    return calculator.ratings


def ratings() -> Dict[str, float]:
    """
    Return the ELO ratings from all prior games in the DB
    """
    games = get_games()
    return calculate_elo_ratings(games)
