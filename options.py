# =========================
# ====== CONFIG TOP =======
# =========================

# --- Folders ---
MAPS_DIR = "maps"
ATTACKS_DIR = "attacks"
HIGH_SCORE_FILE = "high_scores.csv"

# --- Default dimensions (fallback; maps are 10x10) ---
GRID_W, GRID_H = 10, 10

# --- ANSI Colors ---
COLOR_RESET        = "\x1b[0m"
COLOR_PLAYER       = "\x1b[38;5;21m"    # royal blue
COLOR_COIN         = "\x1b[38;5;226m"   # gold
COLOR_WARNING      = "\x1b[38;5;208m"   # orange
COLOR_DAMAGE       = "\x1b[38;5;196m"   # red
COLOR_WALL         = "\x1b[38;5;245m"   # gray
COLOR_HUD_LABEL    = "\x1b[38;5;45m"    # cyan
COLOR_HUD_VALUE    = "\x1b[38;5;220m"   # yellow
COLOR_TITLE        = "\x1b[38;5;51m"    # light blue
COLOR_TITLE_ACCENT = "\x1b[38;5;199m"   # accent
COLOR_MULTI_BANNER = "\x1b[38;5;201m"   # magenta

# --- ASCII Characters ---
PLAYER_CHAR         = "@"
COIN_CHAR           = "o"
WALL_CHAR           = "H"   # internal walls
BORDER_CHAR         = "H"   # inner border
ATTACK_WARNING_CHAR = "!"
ATTACK_DAMAGE_CHAR  = "X"

# --- Inner border around the map ---
BORDER_ENABLED = True

# --- HUD / UI ---
TITLE_TEXT        = "MINI-ADVENTURE - MadeByQwerty"
CONTROL_HINT      = "Arrows/WASD: move, Q: quit"
SPEED_LABEL       = "Speed"
MULTI_LABEL       = "Multi%"
SCORE_LABEL       = "Score"
TIME_LABEL        = "Time"
MULTI_BANNER_TEXT = "▶ Multi-attacks!"

# HUD side layout (relative to inner rows 0..9)
SIDE_GAP_SPACES      = 4
SIDE_ROW_SCORE_INDEX = 4   # 5th row (index 0)
SIDE_ROW_TIME_INDEX  = 5   # 6th row (index 0)

# --- Timings & acceleration ---
TICK           = 0.05
BASE_IDLE      = 1.5
BASE_WARNING   = 1.0
DAMAGE_DUR     = 0.5

ATTACKS_PER_STEP = 3     # acceleration every X attacks
STEP_DELTA       = 0.1   # -0.1s on idle & warning per step
MIN_IDLE         = 0.0
MIN_WARNING      = 0.5

# --- Multi-attack probability ---
EXTRA_ATTACK_STEP   = 5     # steps: 0..4 -> 0%, 5..9 -> 10%, etc.
EXTRA_ATTACK_GROWTH = 0.10  # +10% per step
EXTRA_ATTACK_MAX    = 1.0   # capped at 100%

# --- Wave staggering (vagues 1..9) ---
# Chaque cellule d'un pattern peut être marquée 1..9 pour indiquer
# son ordre d'apparition/disparition. Le délai entre niveaux de vague
# est défini ici (en secondes).
WAVE_STAGGER = 0.1
