# Neural Dive 🎮

**A cyberpunk terminal roguelike where you learn computer science by battling AI entities.**

```
╔═══════════════════════════════════════════════════════════════╗
║                        NEURAL DIVE                            ║
║        Descend through neural layers. Answer questions.       ║
║             Defeat AI bosses. Master computer science.        ║
╚═══════════════════════════════════════════════════════════════╝
```

## Features

- 🎓 **122 unique CS questions** across algorithms, systems, web, ML, and more
- 🎮 **Roguelike gameplay** with wandering NPCs and procedural maps
- 🎨 **Cyberpunk theme** with Unicode graphics (light/dark mode support)
- 🏆 **Boss battles** to win, score tracking, and unique question sets per NPC
- ⚙️ **Highly configurable** themes, difficulty, and content

---

## Quick Start

```bash
# Install
pip install -e .

# Play
./ndive

# Or with options
./ndive --help
./ndive --light      # Light terminal
./ndive --classic    # ASCII graphics
```

**Controls:** Arrow keys to move • Space/Enter to interact • >/< for stairs • Q to quit

---

## Gameplay

**Objective:** Descend through 3 neural layers, answer CS questions, defeat AI bosses.

**Layers:**
- **Layer 1**: Algorithms & Data Structures (complete ALGO_SPIRIT, HEAP_MASTER, PATTERN_ARCHITECT)
- **Layer 2**: Systems & Web (complete WEB_ARCHITECT, CRYPTO_GUARDIAN, SYSTEM_CORE, SCALE_MASTER)
- **Layer 3**: Deep Core - defeat VIRUS_HUNTER, THEORY_ORACLE, or AI_CONSCIOUSNESS to win!

**Mechanics:**
- **Coherence** = health (80/100 start, +8 correct, -30 wrong, -45 from enemies)
- **Knowledge Modules** = rewards from correct answers
- **Score** = correct answers + NPCs defeated + knowledge + remaining coherence

Required NPCs glow brighter than optional ones.

---

## Configuration

```bash
# Command line
./ndive --theme cyberpunk --background dark
./ndive -t classic -b light
./ndive --width 60 --height 30 --seed 42

# Environment variables
export NEURAL_DIVE_THEME=cyberpunk      # or 'classic'
export NEURAL_DIVE_BACKGROUND=dark      # or 'light'
```

Edit `neural_dive/config.py` for game parameters (NPC speed, rewards, map size, etc).

---

## Adding Content

### Add Questions

1. Edit `neural_dive/data/questions.json` following [QUESTION_GUIDE.md](QUESTION_GUIDE.md):
   ```json
   "my_question": {
     "question_text": "What is...?",
     "topic": "algorithms",
     "answers": [...]
   }
   ```

2. Run redistribution to assign to NPCs:
   ```bash
   python3 scripts/redistribute_questions.py
   ```
   This ensures each NPC gets unique questions (no duplicates).

3. Test: `./ndive --fixed --seed 42`

### Add NPCs

Edit `neural_dive/data/npcs.json`, then run `redistribute_questions.py`.

---

## Development

```bash
# Setup
pip install -e ".[dev]"
pre-commit install

# Common tasks
make run           # Play game
make lint          # Check code quality
make format        # Auto-format
make test          # Run tests
make clean         # Remove artifacts
```

**Project Structure:**
```
neural_dive/
├── data/          # questions.json, npcs.json, terminals.json
├── game.py        # Core game logic
├── rendering.py   # Terminal UI
├── themes.py      # Visual themes
└── ...
scripts/
└── redistribute_questions.py  # Assign questions to NPCs uniquely
ndive              # Launcher
```

---

## Documentation

- [Question Guide](QUESTION_GUIDE.md) - How to write good questions
- [Scripts README](scripts/README.md) - Helper utilities

---

## Topics Covered

122 questions across: Algorithms • Data Structures • Systems • Networking • Databases • Security • Web Dev • Distributed Systems • Machine Learning • Design Patterns • Testing • DevOps • Programming Fundamentals • Software Engineering • Theory • Architecture • Compilers • Version Control • AI/ML

---

## License

MIT License - Free to use, modify, and distribute. See [LICENSE](LICENSE).

---

## Contributing

Contributions welcome! Add questions, fix bugs, improve docs. See [QUESTION_GUIDE.md](QUESTION_GUIDE.md) for question guidelines.

**Made with ❤️ for CS learners everywhere**
