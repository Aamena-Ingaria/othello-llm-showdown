# ⚔️ Othello (Reversi) LLM Arena

### A battleground for pitting Large Language Models against each other in classic 8x8 Othello (Reversi)

![Othello](othello.png)

An interactive battle arena where AI models compete in the strategic board game **Othello (Reversi)**. Watch local LLMs analyze positions, calculate outflanks, avoid tactical traps, and explain their inner thoughts in real-time.

---

## ✨ Features

- **Classic 8x8 Othello Engine**: Full implementation of standard Reversi rules, disc outflanking and flipping in all 8 directions, pass turns, and disc count scoring.
- **Rich SVG Board**: Dark green felt surface, coordinate markers (`A`–`H`, `1`–`8`), 3D radial-gradient Black & White discs, and golden pulse indicator for the latest move.
- **LLM Inner Thoughts**: Inspect each model's live reasoning:
  - **Evaluation**: Positional assessment and mobility control
  - **Threats**: Opponent corners and dangerous flanks
  - **Opportunities**: Strategic squares and stable discs
  - **Strategy**: Tactical calculation and planned path
- **100% Free, Private & Offline**: Powered by local models running via [Ollama](https://ollama.com). No paid API keys or external calls needed.
- **ELO Ratings & History**: Built-in leaderboard tracking game outcomes and dynamic ELO ratings.
- **Managed with `uv`**: Fast, modern virtual environment and dependency management.

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (recommended for package management)
- **[Ollama](https://ollama.com)** (for running local models)

### 2. Pull the Models

Ensure Ollama is running, then pull the supported models:

```bash
ollama pull llama3.2:3b
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:7b
```

### 3. Installation & Setup with `uv`

Initialize the environment and install dependencies:

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
```

### 4. Launch the Game

Start the Gradio interface:

```bash
uv run app.py
```

*(Alternatively, in Git Bash run `./run.sh`, or on Windows Command Prompt run `run.bat`)*

Then open **`http://127.0.0.1:7860`** in your browser!

---

## 🎮 How It Works

1. **Select Players**: Choose the LLM model for the **Black Player** (moves first) and the **White Player**.
2. **Next Move**: Advance the game turn-by-turn to inspect what each model is thinking.
3. **Run Game**: Automatically play through the full match until game over.
4. **Leaderboard**: Switch to the **Leaderboard** tab to view match history and updated ELO rankings.

---

## 📁 Project Structure

```
├── arena/
│   ├── board.py           # 8x8 Othello engine, flip logic & game state
│   ├── board_view.py      # Interactive SVG renderer with 3D disc styling
│   ├── game.py            # Game runner and player controller
│   ├── llm.py             # Ollama local model interface (OpenAI compatible)
│   ├── othello.py         # Gradio arena UI & event handlers
│   ├── player.py          # Prompt engineering & structured JSON parser
│   └── record.py          # Results logging & ELO calculation
├── app.py                 # Application entry point
├── pyproject.toml         # uv project configuration
├── requirements.txt       # Dependencies
├── run.sh                 # Git Bash launcher
├── run.bat                # Windows batch launcher
└── test_othello.py        # Automated test suite (15 tests)
```

---

## 🧪 Testing

Run the automated test suite to verify board mechanics, flips, and move parsing:

```bash
uv run python test_othello.py
```

---

## 🙏 Acknowledgments

Built on top of the Connect 4 LLM Arena created by [Ed Donner](https://github.com/ed-donner) as part of his LLM Engineering course. This project extends the original arena to support full Othello (Reversi) rules and gameplay.
