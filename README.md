# 🧭 MINI-ADVENTURE — by MadeByQwerty

**Mini-Adventure** is a fast ASCII arcade-survivor that runs entirely in your terminal.  
Dodge attack patterns, grab coins, and survive as long as you can!

---

## ▶️ How to Play

**Controls**
| Action | Key |
|:-------|:----|
| Move | Arrow keys or **WASD** |
| Quit | **Q** |
| Confirm / Select | **Enter** |

**Goal**  
Collect **coins (`o`)** to increase your score and avoid **warnings (`!`)** and **damage cells (`X`)**.  
Each wave introduces one or more attack patterns.

### Game phases
1. **Idle** – calm before the storm.  
2. **Warning** – patterns appear as `!` (orange).  
3. **Damage** – they turn to `X` (red).  

Survive as long as possible. Each new wave gets a little faster, and the chances of getting two at once increase!

---

## 💻 Installation & Run

**Requirements**
- Python **3.8+**
- Windows terminal (uses `msvcrt` for keyboard input)

**How to launch**
```bash
python mini_adventure.py
```

That’s it! No dependencies, no install — just pure Python and ASCII art.

---

## 🗺️ Maps

All maps are stored in the `maps/` folder.  
Each map is a **10×10 grid** made of ASCII characters.

| Symbol | Meaning |
|:--------|:---------|
| `#` | Wall (blocks movement and coins) |
| `P` | Player spawn (optional, at most 1) |
| `.` or space | Empty floor |

If no `P` is found, the game picks the first free cell automatically.

### Example (`Ruins.map`)
```
.##.....#.
.....#....
#..#####..
...#......
.....P.#..
...#...#..
...#..##..
.........#
.##.....#.
.....#....
```

### Rules
- Exactly **10 lines**, each with **10 characters**
- Only one `P` (or none)
- Use only `#`, `P`, `.`, or spaces
- Files must be placed in `maps/` and end with `.map` or `.txt`

When you select a map in the main menu, a preview is shown next to its Top 10 high scores.

---

## 💥 Attack Patterns

Attack patterns define the shapes that appear during the warning and damage phases.  
They are stored in the `attacks/` folder and can have **any shape up to 10×10**.

**Every non-space character activates a cell.**  
**Digits `1`–`9` define the wave delay** inside the same attack:
- `1` = appears immediately  
- `9` = appears last (after 8× `WAVE_STAGGER` delay, default 0.1 s)

All other non-space characters are treated as wave 1.

### Example (`circle.txt`)
```
  434
 43234
 32123
 43234
  434
```

This creates a multi-wave ring: inner cells appear first, outer ones later.

You can freely draw your own `.txt` files — any non-space characters are valid.

---

## 🏆 High Scores

Scores are automatically saved in `high_scores.csv` with:
| Field | Description |
|:-------|:-------------|
| map | Map name |
| score | Number of coins collected |
| time_sec | Survival time |
| datetime | Date of the run |

The menu shows the **Top 10 per map**.

---

## ⚙️ Game Settings (in `options.py`)

All parameters can be tuned easily:

| Category | Variable | Description |
|:-----------|:-----------|:-------------|
| Timing | `BASE_IDLE`, `BASE_WARNING`, `DAMAGE_DUR` | Base durations per phase |
| Difficulty curve | `ATTACKS_PER_STEP`, `STEP_DELTA` | Acceleration every few waves |
| Multi-attack chance | `EXTRA_ATTACK_STEP`, `EXTRA_ATTACK_GROWTH`, `EXTRA_ATTACK_MAX` | Probability growth for multiple simultaneous attacks |
| Wave staggering | `WAVE_STAGGER` | Delay (seconds) between internal sub-waves (1–9) |
| HUD | `TITLE_TEXT`, `CONTROL_HINT`, etc. | Text and colors used in the interface |

You can fully customize visuals, speed, and behavior.

---

## 🧠 Author

**MadeByQwerty** — solo indie developer.  

Find more projects on [itch.io](https://madebyqwerty.itch.io)

---

## 🪄 License

Released under the **MIT License**.  
Please credit **MadeByQwerty** if you use or modify the project.
