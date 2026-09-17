from arena.game import Game
from arena.board import BLACK, WHITE
from arena.llm import LLM
import gradio as gr
import pandas as pd


css = """
.dataframe-fix .table-wrap {
    min-height: 800px;
    max-height: 800px;
}
footer { display: none !important; }
"""

js = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

ALL_MODEL_NAMES = LLM.all_model_names()


def message_html(game) -> str:
    """
    Return the message for the top of the UI
    """
    return f'<div style="text-align: center; font-size: 20px; font-weight: 600; padding: 6px; letter-spacing: 0.3px;">{game.board.message()}</div>'


def format_records_for_table(games):
    """
    Turn the results objects into a pandas DataFrame for the Gradio Dataframe
    """
    df = pd.DataFrame(
        [
            [
                game.when,
                getattr(game, "black_player", getattr(game, "red_player", "")),
                getattr(game, "white_player", getattr(game, "yellow_player", "")),
                "Black" if getattr(game, "black_won", getattr(game, "red_won", False)) else "White" if getattr(game, "white_won", getattr(game, "yellow_won", False)) else "Draw",
                f"{getattr(game, 'black_score', '-')}:{getattr(game, 'white_score', '-')}",
            ]
            for game in reversed(games)
        ],
        columns=["When", "Black Player", "White Player", "Winner", "Score"],
    )

    if not df.empty and "When" in df.columns:
        df["When"] = pd.to_datetime(df["When"]).dt.floor("s")

    return df


def format_ratings_for_table(ratings):
    """
    Turn the ratings into a List of Lists for the Gradio Dataframe
    """
    items = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    return [[item[0], int(round(item[1]))] for item in items]


def load_callback(black_llm, white_llm):
    """
    Callback called when the game is started. Create a new Game object for the state.
    """
    game = Game(black_llm, white_llm)
    enabled = gr.Button(interactive=True)
    message = message_html(game)
    return (
        game,
        game.board.svg(),
        message,
        "",
        "",
        enabled,
        enabled,
        enabled,
    )


def leaderboard_callback(game):
    """
    Callback called when the user switches to the Leaderboard tab. Load in the results.
    """
    records_df = format_records_for_table(Game.get_games())
    ratings_df = format_ratings_for_table(Game.get_ratings())
    return records_df, ratings_df


def move_callback(game):
    """
    Callback called when the user clicks to do a single move.
    """
    game.move()
    message = message_html(game)
    if_active = gr.Button(interactive=game.board.is_active())
    return (
        game,
        game.board.svg(),
        message,
        game.thoughts(BLACK),
        game.thoughts(WHITE),
        if_active,
        if_active,
    )


def run_callback(game):
    """
    Callback called when the user runs an entire game. Reset the board, run the game, store results.
    Yield interim results so the UI updates.
    """
    enabled = gr.Button(interactive=True)
    disabled = gr.Button(interactive=False)
    game.reset()
    message = message_html(game)
    yield (
        game,
        game.board.svg(),
        message,
        game.thoughts(BLACK),
        game.thoughts(WHITE),
        disabled,
        disabled,
        disabled,
    )
    while game.board.is_active():
        game.move()
        message = message_html(game)
        yield (
            game,
            game.board.svg(),
            message,
            game.thoughts(BLACK),
            game.thoughts(WHITE),
            disabled,
            disabled,
            disabled,
        )
    game.record()
    yield (
        game,
        game.board.svg(),
        message,
        game.thoughts(BLACK),
        game.thoughts(WHITE),
        disabled,
        disabled,
        enabled,
    )


def model_callback(player_color, game, new_model_name):
    """
    Callback when the user changes the model
    """
    player = game.players[player_color]
    player.switch_model(new_model_name)
    return game


def black_model_callback(game, new_model_name):
    """
    Callback when Black model is changed
    """
    return model_callback(BLACK, game, new_model_name)


def white_model_callback(game, new_model_name):
    """
    Callback when White model is changed
    """
    return model_callback(WHITE, game, new_model_name)


def player_section(name, color_symbol, default):
    """
    Create the left and right sections of the UI
    """
    with gr.Row():
        gr.HTML(f'<div style="text-align: center; font-size: 19px; font-weight: bold; padding: 4px;">{color_symbol} {name} Player</div>')
    with gr.Row():
        dropdown = gr.Dropdown(ALL_MODEL_NAMES, value=default, label=f"{name} LLM", interactive=True)
    with gr.Row():
        gr.HTML('<div style="text-align: center; font-size: 16px; font-weight: 600; color: #94a3b8; margin-top: 8px;">Inner thoughts</div>')
    with gr.Row():
        thoughts = gr.HTML(label="Thoughts")
    return thoughts, dropdown


def make_display():
    """
    The Gradio UI to show the Othello Game, with event handlers
    """
    with gr.Blocks(
        title="Othello Battle",
        css=css,
        js=js,
        theme=gr.themes.Default(primary_hue="emerald"),
    ) as blocks:
        game = gr.State()

        with gr.Tabs():
            with gr.TabItem("Game"):
                with gr.Row():
                    gr.HTML(
                        '<div style="text-align: center; font-size: 26px; font-weight: 800; padding: 10px; letter-spacing: 0.5px;">⚔️ Othello (Reversi) LLM Showdown</div>'
                    )
                with gr.Row():
                    with gr.Column(scale=1):
                        black_thoughts, black_dropdown = player_section("Black", "⚫", ALL_MODEL_NAMES[0])
                    with gr.Column(scale=2):
                        with gr.Row():
                            message = gr.HTML(
                                '<div style="text-align: center; font-size: 18px">The Board</div>'
                            )
                        with gr.Row():
                            board_display = gr.HTML()
                        with gr.Row():
                            with gr.Column(scale=1):
                                move_button = gr.Button("Next move", variant="secondary")
                            with gr.Column(scale=1):
                                run_button = gr.Button("Run game", variant="primary")
                            with gr.Column(scale=1):
                                reset_button = gr.Button("Start Over", variant="stop")
                        with gr.Row():
                            gr.HTML(
                                '<div style="text-align: center; font-size: 15px; color: #10b981; font-weight: 500; margin-top: 10px;">🦙 Powered by Local Ollama Models · 100% Free, Private &amp; Offline</div>'
                            )

                    with gr.Column(scale=1):
                        default_white = ALL_MODEL_NAMES[1] if len(ALL_MODEL_NAMES) > 1 else ALL_MODEL_NAMES[0]
                        white_thoughts, white_dropdown = player_section(
                            "White", "⚪", default_white
                        )
            with gr.TabItem("Leaderboard") as leaderboard_tab:
                with gr.Row():
                    with gr.Column(scale=1):
                        ratings_df = gr.Dataframe(
                            headers=["Player", "ELO"],
                            label="Ratings",
                            column_widths=[2, 1],
                            wrap=True,
                            column_count=2,
                            row_count=10,
                            max_height=800,
                            elem_classes=["dataframe-fix"],
                        )
                    with gr.Column(scale=2):
                        results_df = gr.Dataframe(
                            headers=["When", "Black Player", "White Player", "Winner", "Score"],
                            label="Game History",
                            column_widths=[2, 2, 2, 1, 1],
                            wrap=True,
                            column_count=5,
                            row_count=10,
                            max_height=800,
                            elem_classes=["dataframe-fix"],
                        )
                with gr.Row():
                    gr.HTML(
                        '<div style="text-align: center; font-size: 15px; color: #64748b; margin-top: 10px;">Classic 8x8 Othello (Reversi) Arena Leaderboard</div>'
                    )

        blocks.load(
            load_callback,
            inputs=[black_dropdown, white_dropdown],
            outputs=[
                game,
                board_display,
                message,
                black_thoughts,
                white_thoughts,
                move_button,
                run_button,
                reset_button,
            ],
        )
        move_button.click(
            move_callback,
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                black_thoughts,
                white_thoughts,
                move_button,
                run_button,
            ],
        )
        black_dropdown.change(black_model_callback, inputs=[game, black_dropdown], outputs=[game])
        white_dropdown.change(
            white_model_callback, inputs=[game, white_dropdown], outputs=[game]
        )
        run_button.click(
            run_callback,
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                black_thoughts,
                white_thoughts,
                move_button,
                run_button,
                reset_button,
            ],
        )
        reset_button.click(
            load_callback,
            inputs=[black_dropdown, white_dropdown],
            outputs=[
                game,
                board_display,
                message,
                black_thoughts,
                white_thoughts,
                move_button,
                run_button,
                reset_button,
            ],
        )

        leaderboard_tab.select(
            leaderboard_callback, inputs=[game], outputs=[results_df, ratings_df]
        )

    return blocks
