from arena.llm import LLM
from arena.board import pieces, cols, rows, BLACK, WHITE
import json
import random
import logging
import re

logger = logging.getLogger(__name__)


class Player:
    """
    This class represents one AI player in the game, and is responsible for managing the prompts
    Delegating to an LLM instance to connect to the LLM
    """

    def __init__(self, model: str, color: int):
        """
        Set up this instance for the given model and player color
        """
        self.color = color
        self.model = model
        self.llm = LLM.create(self.model)
        self.evaluation = ""
        self.threats = ""
        self.opportunities = ""
        self.strategy = ""

    def system(self, board, legal_moves: str, illegal_moves: str) -> str:
        """
        Return the system prompt for this move
        """
        my_color = pieces[self.color]
        opponent_color = pieces[-1 * self.color]
        return f"""You are a grandmaster playing the board game Othello (Reversi).
The game is played on an 8x8 board with columns A to H and rows 1 to 8.
A move is made by placing a disc of your color on an empty square to outflank (trap) one or more opponent discs in any straight line (horizontal, vertical, or diagonal) between your newly placed disc and another disc of your color. All trapped opponent discs flip to your color.
You are playing as {my_color} and your opponent is {opponent_color}.
You must choose a move from the list of legal moves: {legal_moves}. If no legal moves are available, respond with PASS.

You must respond in JSON strictly according to this spec:
{{
    "evaluation": "my assessment of the board position and material/positional control",
    "threats": "opponent corners, dangerous moves, or vulnerabilities to watch out for",
    "opportunities": "potential corner takes, stable discs, edge control, or high-value flips",
    "strategy": "my tactical calculation and reasoning behind my move",
    "move": "one coordinate from this list of legal moves: {legal_moves}"
}}

You must pick one of these exact moves for your move: {legal_moves}"""

    def user(self, board, legal_moves: str, illegal_moves: str) -> str:
        """
        Return the user prompt for this move
        """
        my_color = pieces[self.color]
        opponent_color = pieces[-1 * self.color]
        black_count, white_count = board.score()

        sample_choice = random.choice(board.legal_moves()) if board.legal_moves() else "PASS"

        return f"""It is your turn to make a move as {my_color}.
Current Score: Black: {black_count} | White: {white_count}

Here is the current board in JSON format (Row 1 at top, Row 8 at bottom):
{board.json()}

Visual representation of the board (. = empty, B = Black, W = White):
{board.alternative()}

Legal moves available to you:
{legal_moves}
{illegal_moves}

Your final response must be ONLY valid JSON matching this schema:
{{
    "evaluation": "my assessment of the board",
    "threats": "opponent threats",
    "opportunities": "opportunities and tactical targets",
    "strategy": "my plan and reasoning",
    "move": "{sample_choice}"
}}

Now make your decision. Pick one move from: {legal_moves}
"""

    def process_move(self, reply: str, board):
        """
        Interpret the reply and make the move; if the move is illegal, then the current player loses
        """
        try:
            # Extract JSON substring if wrapped in markdown or conversational text
            json_match = re.search(r"\{.*\}", reply, re.DOTALL)
            if json_match:
                reply = json_match.group(0)

            result = json.loads(reply)

            # Accept "move", "move_column", or "coordinate"
            move = result.get("move") or result.get("move_column") or result.get("coordinate") or ""
            move = str(move).strip().upper()

            # Clean any trailing punctuation
            move = move.strip(".,;:\"'")

            # Handle PASS
            if move == "PASS":
                if not board.legal_moves(board.player):
                    board.pass_turn()
                    self.evaluation = result.get("evaluation") or ""
                    self.threats = result.get("threats") or ""
                    self.opportunities = result.get("opportunities") or ""
                    self.strategy = result.get("strategy") or "Passed due to no legal moves."
                    return
                else:
                    raise ValueError("Cannot pass when legal moves exist")

            # Check if valid coordinate
            coord = board.str_to_coord(move)
            if coord is None:
                raise ValueError(f"Invalid coordinate: '{move}'")

            x, y = coord
            if not board.is_legal_move(x, y, board.player):
                raise ValueError(f"Illegal move {move} for player {pieces[board.player]}")

            board.move(move)

            self.evaluation = result.get("evaluation") or ""
            self.threats = result.get("threats") or ""
            self.opportunities = result.get("opportunities") or ""
            self.strategy = result.get("strategy") or ""

        except Exception as e:
            logger.error(f"Exception processing move: {e}")
            logger.error(f"Raw reply was: {reply}")
            board.forfeit = True
            board.winner = -1 * board.player

    def move(self, board):
        """
        Have the underlying LLM make a move, and process the result
        """
        legals = board.legal_moves(board.player)
        if not legals:
            # No legal moves available: pass turn
            board.pass_turn()
            self.evaluation = "No legal moves available."
            self.strategy = "Passed turn to opponent."
            return

        legal_moves_str = ", ".join(legals)
        illegal = board.illegal_moves(board.player)[:10]  # sample illegal moves for negative prompting
        if illegal:
            illegal_moves_str = (
                "\nDo NOT choose any non-flanking squares such as: " + ", ".join(illegal)
            )
        else:
            illegal_moves_str = ""

        system = self.system(board, legal_moves_str, illegal_moves_str)
        user = self.user(board, legal_moves_str, illegal_moves_str)
        reply = self.llm.send(system, user)
        self.process_move(reply, board)

    def thoughts(self) -> str:
        """
        Return HTML to describe the inner thoughts
        """
        result = '<div style="text-align: left; font-size: 14px; line-height: 1.5;"><br/>'
        result += f"<b style='color:#38bdf8;'>Evaluation:</b><br/>{self.evaluation}<br/><br/>"
        result += f"<b style='color:#f87171;'>Threats:</b><br/>{self.threats}<br/><br/>"
        result += f"<b style='color:#4ade80;'>Opportunities:</b><br/>{self.opportunities}<br/><br/>"
        result += f"<b style='color:#fbbf24;'>Strategy:</b><br/>{self.strategy}"
        result += "</div>"
        return result

    def switch_model(self, new_model_name: str):
        """
        Change the underlying LLM to the new model
        """
        self.model = new_model_name
        self.llm = LLM.create(new_model_name)
