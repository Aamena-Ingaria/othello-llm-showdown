"""
The main entry-point for the Othello (Reversi) LLM Showdown
Create the Gradio app and launch it
"""


from arena.othello import make_display
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv(override=True)
    app = make_display()
    app.launch()
