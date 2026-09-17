"""
Comprehensive unit tests for Othello game implementation
"""
import unittest
import json
from arena.board import Board, BLACK, WHITE, EMPTY, RED, YELLOW
from arena.board_view import to_svg
from arena.record import Result, calculate_elo_ratings


class TestOthelloBoard(unittest.TestCase):
    def test_initial_board(self):
        board = Board()
        self.assertEqual(len(board.cells), 8)
        for row in board.cells:
            self.assertEqual(len(row), 8)

        # 4 center pieces
        # D4 is (3, 3) = White, E4 is (4, 3) = Black
        # D5 is (3, 4) = Black, E5 is (4, 4) = White
        self.assertEqual(board.cells[3][3], WHITE)
        self.assertEqual(board.cells[3][4], BLACK)
        self.assertEqual(board.cells[4][3], BLACK)
        self.assertEqual(board.cells[4][4], WHITE)

        self.assertEqual(board.player, BLACK)
        self.assertEqual(board.score(), (2, 2))
        self.assertTrue(board.is_active())

    def test_initial_legal_moves(self):
        board = Board()
        moves = sorted(board.legal_moves())
        expected = sorted(["C4", "D3", "E6", "F5"])
        self.assertEqual(moves, expected)

    def test_making_move_and_flipping(self):
        board = Board()
        # Black plays C4
        board.move("C4")

        # C4 is (2, 3), D4 is (3, 3), E4 is (4, 3)
        # D4 was White, should now be flipped to Black
        self.assertEqual(board.cells[3][2], BLACK)  # C4
        self.assertEqual(board.cells[3][3], BLACK)  # D4 flipped!
        self.assertEqual(board.cells[3][4], BLACK)  # E4

        # Score after C4: Black has 4, White has 1
        self.assertEqual(board.score(), (4, 1))

        # Next player is White
        self.assertEqual(board.player, WHITE)

        # White's legal moves after C4
        white_moves = sorted(board.legal_moves())
        self.assertIn("C3", white_moves)
        self.assertIn("C5", white_moves)
        self.assertIn("E3", white_moves)

    def test_multi_directional_flip(self):
        """
        Set up a custom board position to test multi-directional simultaneous flips:
        Horizontal, vertical, and diagonal flips all from a single placed disc!
        """
        board = Board()
        # Clear board
        board.cells = [[EMPTY for _ in range(8)] for _ in range(8)]

        # Place center disc for Black move at D4 (3, 3)
        # 1. Horizontal: Black at B4 (1, 3), White at C4 (2, 3)
        board.cells[3][1] = BLACK
        board.cells[3][2] = WHITE

        # 2. Vertical: Black at D2 (3, 1), White at D3 (3, 2)
        board.cells[1][3] = BLACK
        board.cells[2][3] = WHITE

        # 3. Diagonal: Black at B2 (1, 1), White at C3 (2, 2)
        board.cells[1][1] = BLACK
        board.cells[2][2] = WHITE

        # Verify D4 is legal for Black and flips all 3 directions
        flips = set(board.get_flips(3, 3, BLACK))
        expected_flips = {(2, 3), (3, 2), (2, 2)}
        self.assertEqual(flips, expected_flips)

        # Execute move at D4
        board.player = BLACK
        board.move("D4")

        # All three white discs should be flipped to Black
        self.assertEqual(board.cells[3][2], BLACK)
        self.assertEqual(board.cells[2][3], BLACK)
        self.assertEqual(board.cells[2][2], BLACK)
        self.assertEqual(board.cells[3][3], BLACK)

    def test_pass_handling(self):
        """
        Test pass condition when current player has no legal moves
        """
        board = Board()
        board.cells = [[EMPTY for _ in range(8)] for _ in range(8)]

        # Set board where Black has NO legal moves, but White does
        # White at A1, White at B1, Black at C1
        board.cells[0][0] = WHITE
        board.cells[0][1] = WHITE
        board.cells[0][2] = BLACK

        # Black is player, but has no moves
        board.player = BLACK
        self.assertEqual(len(board.legal_moves(BLACK)), 0)

        # Calling pass_turn() transfers turn to White
        board.pass_turn()
        self.assertEqual(board.player, WHITE)
        self.assertTrue(board.is_active())

    def test_game_over_and_winner(self):
        """
        Test game over when neither player can move
        """
        board = Board()
        board.cells = [[EMPTY for _ in range(8)] for _ in range(8)]

        # Board with only 2 Black discs and 1 White disc, completely disconnected
        board.cells[0][0] = BLACK
        board.cells[0][1] = BLACK
        board.cells[7][7] = WHITE

        board.player = BLACK
        self.assertEqual(len(board.legal_moves(BLACK)), 0)
        self.assertEqual(len(board.legal_moves(WHITE)), 0)

        # Passing when neither has moves terminates the game
        board.pass_turn()
        self.assertFalse(board.is_active())
        self.assertEqual(board.winner, BLACK)  # 2 Black vs 1 White
        self.assertFalse(board.draw)

    def test_draw_condition(self):
        board = Board()
        board.cells = [[EMPTY for _ in range(8)] for _ in range(8)]

        board.cells[0][0] = BLACK
        board.cells[7][7] = WHITE

        board.player = BLACK
        board.pass_turn()
        self.assertFalse(board.is_active())
        self.assertEqual(board.winner, EMPTY)
        self.assertTrue(board.draw)

    def test_illegal_moves(self):
        board = Board()
        # Occupied square
        with self.assertRaises(ValueError):
            board.move("D4")

        # Empty square that does not outflank
        with self.assertRaises(ValueError):
            board.move("A1")

        # Invalid format
        with self.assertRaises(ValueError):
            board.move("Z99")

        # Cannot pass when legal moves exist
        with self.assertRaises(ValueError):
            board.move("PASS")

    def test_coordinate_parsing(self):
        self.assertEqual(Board.coord_to_str(0, 0), "A1")
        self.assertEqual(Board.coord_to_str(7, 7), "H8")
        self.assertEqual(Board.coord_to_str(2, 3), "C4")

        self.assertEqual(Board.str_to_coord("a1"), (0, 0))
        self.assertEqual(Board.str_to_coord("H8"), (7, 7))
        self.assertEqual(Board.str_to_coord("C4"), (2, 3))
        self.assertIsNone(Board.str_to_coord("I9"))
        self.assertIsNone(Board.str_to_coord(""))

    def test_board_string_representations(self):
        board = Board()
        # JSON
        board_json = board.json()
        parsed = json.loads(board_json)
        self.assertIn("Column names", parsed)
        self.assertEqual(len(parsed["Column names"]), 8)
        self.assertIn("Row 1", parsed)
        self.assertIn("Row 8", parsed)

        # Alternative ASCII
        alt = board.alternative()
        self.assertIn("A B C D E F G H", alt)
        self.assertIn("4", alt)

        # SVG
        svg_content = board.svg()
        self.assertIn("<svg", svg_content)
        self.assertIn("blackDisc", svg_content)
        self.assertIn("whiteDisc", svg_content)

    def test_backward_compatibility(self):
        self.assertEqual(RED, BLACK)
        self.assertEqual(YELLOW, WHITE)

        res = Result(
            black_player="gpt-4o",
            white_player="claude-3-5-sonnet",
            black_won=True,
            white_won=False,
            black_score=40,
            white_score=24,
        )
        self.assertEqual(res.red_player, "gpt-4o")
        self.assertEqual(res.yellow_player, "claude-3-5-sonnet")
        self.assertTrue(res.red_won)
        self.assertFalse(res.yellow_won)

        ratings = calculate_elo_ratings([res])
        self.assertGreater(ratings["gpt-4o"], ratings["claude-3-5-sonnet"])


class TestPlayerProcessMove(unittest.TestCase):
    def setUp(self):
        from arena.player import Player
        # Create Player object without calling external APIs
        self.player = Player.__new__(Player)
        self.player.color = BLACK
        self.player.model = "test-model"
        self.player.evaluation = ""
        self.player.threats = ""
        self.player.opportunities = ""
        self.player.strategy = ""

    def test_process_valid_json_move(self):
        board = Board()
        reply = json.dumps({
            "evaluation": "Balanced start",
            "threats": "None yet",
            "opportunities": "Control center",
            "strategy": "Opening book C4",
            "move": "C4"
        })
        self.player.process_move(reply, board)
        self.assertFalse(board.forfeit)
        self.assertEqual(board.cells[3][2], BLACK)
        self.assertEqual(self.player.strategy, "Opening book C4")

    def test_process_markdown_wrapped_json(self):
        board = Board()
        reply = """Here is my move:
```json
{
    "evaluation": "Good",
    "threats": "None",
    "opportunities": "Center",
    "strategy": "Play D3",
    "move": "D3"
}
```
Thanks!"""
        self.player.process_move(reply, board)
        self.assertFalse(board.forfeit)
        self.assertEqual(board.cells[2][3], BLACK)

    def test_process_illegal_move_causes_forfeit(self):
        board = Board()
        reply = json.dumps({
            "evaluation": "Illegal attempt",
            "threats": "None",
            "opportunities": "None",
            "strategy": "Trying corner early",
            "move": "A1"
        })
        self.player.process_move(reply, board)
        self.assertTrue(board.forfeit)
        self.assertEqual(board.winner, WHITE)  # Opponent awarded win on forfeit


class TestOthelloGame(unittest.TestCase):
    def test_game_initialization_and_board_flow(self):
        from arena.game import Game
        game = Game.__new__(Game)
        game.board = Board()
        from arena.player import Player
        p1 = Player.__new__(Player)
        p1.color = BLACK
        p1.model = "model_b"
        p1.evaluation, p1.threats, p1.opportunities, p1.strategy = "eval_b", "", "", ""

        p2 = Player.__new__(Player)
        p2.color = WHITE
        p2.model = "model_w"
        p2.evaluation, p2.threats, p2.opportunities, p2.strategy = "eval_w", "", "", ""

        game.players = {BLACK: p1, WHITE: p2, RED: p1, YELLOW: p2}

        self.assertTrue(game.is_active())
        self.assertIn("eval_b", game.thoughts(BLACK))
        self.assertIn("eval_w", game.thoughts(WHITE))

        # Test board move flow through game
        game.board.move("C4")
        self.assertEqual(game.board.player, WHITE)
        self.assertEqual(game.board.score(), (4, 1))

        # Reset
        game.reset()
        self.assertEqual(game.board.player, BLACK)
        self.assertEqual(game.board.score(), (2, 2))


if __name__ == "__main__":
    unittest.main()

