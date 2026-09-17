from arena.board_view import to_svg
from typing import List, Tuple, Optional

BLACK = 1
WHITE = -1
EMPTY = 0

# Backwards compatibility aliases
RED = BLACK
YELLOW = WHITE

show = {EMPTY: "·", BLACK: "⚫", WHITE: "⚪"}
pieces = {EMPTY: "", BLACK: "black", WHITE: "white"}
simple = {EMPTY: ".", BLACK: "B", WHITE: "W"}
cols = "ABCDEFGH"
rows = "12345678"

DIRECTIONS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1)
]


class Board:
    """
    A class to represent an 8x8 Othello (Reversi) Board
    """

    def __init__(self):
        """
        Initialize the 8x8 board with the standard four center discs.
        Black moves first.
        """
        self.cells = [[EMPTY for _ in range(8)] for _ in range(8)]
        # Standard starting position:
        # D4 (x=3, y=3): White, E4 (x=4, y=3): Black
        # D5 (x=3, y=4): Black, E5 (x=4, y=4): White
        self.cells[3][3] = WHITE
        self.cells[3][4] = BLACK
        self.cells[4][3] = BLACK
        self.cells[4][4] = WHITE

        self.player = BLACK
        self.winner = EMPTY
        self.draw = False
        self.forfeit = False
        self.latest_x, self.latest_y = -1, -1
        self.latest_flips: List[Tuple[int, int]] = []
        self.passed = False

    def count(self, player: int) -> int:
        """
        Count the number of discs for the specified player
        """
        return sum(row.count(player) for row in self.cells)

    def score(self) -> Tuple[int, int]:
        """
        Return (black_count, white_count)
        """
        return self.count(BLACK), self.count(WHITE)

    @staticmethod
    def coord_to_str(x: int, y: int) -> str:
        """
        Convert (x, y) coordinates to algebraic notation, e.g. (2, 3) -> "C4"
        """
        return f"{cols[x]}{y + 1}"

    @staticmethod
    def str_to_coord(coord: str) -> Optional[Tuple[int, int]]:
        """
        Parse algebraic notation into (x, y), e.g. "C4" -> (2, 3).
        Returns None if invalid.
        """
        coord = coord.strip().upper()
        if len(coord) == 2 and coord[0] in cols and coord[1] in rows:
            return cols.index(coord[0]), rows.index(coord[1])
        return None

    def get_flips_in_dir(self, x: int, y: int, dx: int, dy: int, player: int) -> List[Tuple[int, int]]:
        """
        Return list of opponent coordinates that would be flipped in direction (dx, dy)
        if player places a disc at (x, y).
        """
        opponent = -1 * player
        flips = []
        cx, cy = x + dx, y + dy

        while 0 <= cx < 8 and 0 <= cy < 8 and self.cells[cy][cx] == opponent:
            flips.append((cx, cy))
            cx += dx
            cy += dy

        if 0 <= cx < 8 and 0 <= cy < 8 and self.cells[cy][cx] == player and len(flips) > 0:
            return flips
        return []

    def get_flips(self, x: int, y: int, player: Optional[int] = None) -> List[Tuple[int, int]]:
        """
        Return all discs that would be flipped if player places a disc at (x, y)
        """
        if player is None:
            player = self.player

        if not (0 <= x < 8 and 0 <= y < 8) or self.cells[y][x] != EMPTY:
            return []

        all_flips = []
        for dx, dy in DIRECTIONS:
            all_flips.extend(self.get_flips_in_dir(x, y, dx, dy, player))
        return all_flips

    def is_legal_move(self, x: int, y: int, player: Optional[int] = None) -> bool:
        """
        Check if placing a disc at (x, y) is a legal move
        """
        return len(self.get_flips(x, y, player)) > 0

    def legal_moves(self, player: Optional[int] = None) -> List[str]:
        """
        Return a list of algebraic coordinates for all legal moves for player.
        """
        if player is None:
            player = self.player

        moves = []
        for y in range(8):
            for x in range(8):
                if self.is_legal_move(x, y, player):
                    moves.append(self.coord_to_str(x, y))
        return moves

    def illegal_moves(self, player: Optional[int] = None) -> List[str]:
        """
        Return empty cells that are NOT legal moves (for prompt negative examples)
        """
        if player is None:
            player = self.player

        moves = []
        for y in range(8):
            for x in range(8):
                if self.cells[y][x] == EMPTY and not self.is_legal_move(x, y, player):
                    moves.append(self.coord_to_str(x, y))
        return moves

    def pass_turn(self):
        """
        Pass turn to the other player.
        If neither player can move, the game ends.
        """
        self.latest_x, self.latest_y = -1, -1
        self.latest_flips = []
        opponent = -1 * self.player

        if not self.legal_moves(opponent):
            # Neither player can move; game is over
            self._determine_winner()
        else:
            self.player = opponent
            self.passed = True

    def move(self, move_input):
        """
        Make a move on the board.
        move_input can be:
          - A string coordinate: "C4", "D3", or "PASS"
          - A tuple of (x, y)
          - An integer column index (if legacy call col)
        """
        self.passed = False

        # If move_input is string "PASS"
        if isinstance(move_input, str) and move_input.strip().upper() == "PASS":
            if len(self.legal_moves(self.player)) == 0:
                self.pass_turn()
                return self
            else:
                raise ValueError("Cannot pass when legal moves are available")

        # Parse coordinate
        if isinstance(move_input, str):
            coord = self.str_to_coord(move_input)
            if coord is None:
                raise ValueError(f"Invalid coordinate format: {move_input}")
            x, y = coord
        elif isinstance(move_input, (tuple, list)):
            x, y = move_input
        elif isinstance(move_input, int):
            # Legacy fallback: column index with first legal move in that column
            x = move_input
            legal_in_col = [
                self.str_to_coord(m) for m in self.legal_moves(self.player) if m.startswith(cols[x])
            ]
            if not legal_in_col or legal_in_col[0] is None:
                raise ValueError(f"No legal move in column {cols[x]}")
            x, y = legal_in_col[0]
        else:
            raise ValueError(f"Unsupported move input: {move_input}")

        flips = self.get_flips(x, y, self.player)
        if not flips:
            raise ValueError(f"Illegal move at {self.coord_to_str(x, y)}")

        # Place the disc and flip opponent discs
        self.cells[y][x] = self.player
        for fx, fy in flips:
            self.cells[fy][fx] = self.player

        self.latest_x, self.latest_y = x, y
        self.latest_flips = flips

        # Next player turn or game over check
        opponent = -1 * self.player
        if self.legal_moves(opponent):
            self.player = opponent
        elif self.legal_moves(self.player):
            # Opponent has no moves, current player moves again (opponent passes)
            self.passed = True
        else:
            # Neither player has legal moves; game ends
            self._determine_winner()

        return self

    def _determine_winner(self):
        """
        Count discs and determine the winner or draw
        """
        black_count, white_count = self.score()
        if black_count > white_count:
            self.winner = BLACK
        elif white_count > black_count:
            self.winner = WHITE
        else:
            self.draw = True

    def is_active(self) -> bool:
        """
        Return True if the game is still active
        """
        return self.winner == EMPTY and not self.draw

    def message(self) -> str:
        """
        A summary of the status
        """
        black_count, white_count = self.score()
        score_str = f"⚫ {black_count} - {white_count} ⚪"

        if self.winner and self.forfeit:
            loser = -1 * self.winner
            return (
                f"{show[self.winner]} ({pieces[self.winner].capitalize()}) wins after an illegal move "
                f"by {show[loser]} ({pieces[loser].capitalize()}) | Score: {score_str}"
            )
        elif self.winner:
            return (
                f"{show[self.winner]} ({pieces[self.winner].capitalize()}) wins! | Final Score: {score_str}"
            )
        elif self.draw:
            return f"The game is a draw! | Final Score: {score_str}"
        else:
            pass_notice = " (Opponent had no moves and passed)" if self.passed else ""
            return f"{show[self.player]} ({pieces[self.player].capitalize()}) to play{pass_notice} | Score: {score_str}"

    def __repr__(self) -> str:
        """
        ASCII visual representation
        """
        result = "  " + " ".join(cols) + "\n"
        for y in range(8):
            row_num = y + 1
            result += f"{row_num} "
            for x in range(8):
                result += show[self.cells[y][x]] + " "
            result += "\n"
        result += "\n" + self.message()
        return result

    def html(self) -> str:
        """
        Return an HTML representation
        """
        result = '<div style="text-align: center;font-family: monospace;font-size:20px">'
        result += self.__repr__().replace("\n", "<br/>").replace(" ", "&nbsp;")
        result += "</div>"
        return result

    def svg(self) -> str:
        """
        Return SVG representation of the board
        """
        return to_svg(self)

    def json(self) -> str:
        """
        Return a JSON representation of the board
        """
        result = "{\n"
        result += '    "Column names": ["A", "B", "C", "D", "E", "F", "G", "H"],\n'
        for y in range(8):
            row_num = y + 1
            result += f'    "Row {row_num}": ['
            for x in range(8):
                result += f'"{pieces[self.cells[y][x]]}", '
            result = result[:-2] + "],\n"
        result = result[:-2] + "\n}"
        return result

    def alternative(self) -> str:
        """
        Alternative clean ASCII board representation for LLM prompting
        """
        result = "  A B C D E F G H\n"
        for y in range(8):
            row_num = y + 1
            row_cells = [simple[self.cells[y][x]] for x in range(8)]
            result += f"{row_num} " + " ".join(row_cells) + "\n"
        return result
