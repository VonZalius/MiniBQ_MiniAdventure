import os
import time
import random
import msvcrt
import sys
import ctypes
import csv
from datetime import datetime
from shutil import get_terminal_size

import options as cfg

# (These two variables are modular: fallback from options, then fixed by the map)
GRID_W, GRID_H = cfg.GRID_W, cfg.GRID_H

# =========================
# ===== BOILERPLATE  ======
# =========================
def enable_vt_mode():
    if os.name == 'nt':
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)

ESC = "\x1b"

def enter_alt_screen():
    # alternate screen + hide cursor + home + clear once
    sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[H\x1b[2J")
    sys.stdout.flush()

def exit_alt_screen():
    # show cursor + back to primary screen
    sys.stdout.write("\x1b[?25h\x1b[?1049l")
    sys.stdout.flush()


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def header_line(left, right=""):
    try:
        cols = get_terminal_size().columns
    except Exception:
        cols = 80
    space = max(1, cols - len(left) - len(right))
    return left + (" " * space) + right

# ======================
#     HIGH SCORES
# ======================
import re
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def visible_len(s: str) -> int:
    return len(strip_ansi(s))

def load_high_scores(path):
    rows = []
    if not os.path.exists(path):
        return rows
    try:
        import csv
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    rows.append({
                        "map": r.get("map", "Empty map"),
                        "score": int(r["score"]),
                        "time_sec": float(r["time_sec"]),
                        "datetime": r["datetime"],
                    })
                except Exception:
                    continue
    except Exception:
        return []
    rows.sort(key=lambda r: (-r["score"], r["time_sec"]))  # global sort
    return rows

def save_high_score(path, map_label, score, time_sec):
    rows = load_high_scores(path)
    rows.append({
        "map": map_label,
        "score": int(score),
        "time_sec": float(time_sec),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    rows.sort(key=lambda r: (-r["score"], r["time_sec"]))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["map", "score", "time_sec", "datetime"])
        writer.writeheader()
        writer.writerows(rows)

def build_scoreboard_lines(rows, current_map, limit=10):
    lines = []
    display_name = current_map[:-4] if isinstance(current_map, str) and current_map.lower().endswith(".map") else current_map
    header = f"{cfg.COLOR_HUD_LABEL}Top {limit} — {display_name}{cfg.COLOR_RESET}"
    lines.append(header)
    filtered = [r for r in rows if r.get("map", "Empty map") == current_map]
    if not filtered:
        lines.append("(no scores yet)")
        return lines
    filtered.sort(key=lambda r: (-r["score"], r["time_sec"]))
    for i, r in enumerate(filtered[:limit], start=1):
        score = r["score"]
        t = int(round(r["time_sec"]))
        dt = r["datetime"]
        lines.append(f"{i:>2}) {score:>4} pts — {t:>3}s — {dt}")
    return lines

def pad_visible(s: str, width: int) -> str:
    add = max(0, width - visible_len(s))
    return s + (" " * add)

def side_by_side(left_lines, right_lines, gap=4):
    n = max(len(left_lines), len(right_lines))
    left_lines = left_lines + [""] * (n - len(left_lines))
    right_lines = right_lines + [""] * (n - len(right_lines))
    left_width = max((visible_len(s) for s in left_lines), default=0)
    spacer = " " * gap
    out = []
    for L, R in zip(left_lines, right_lines):
        out.append(pad_visible(L, left_width) + spacer + R)
    return out

# ======================
#        MAP MENU
# ======================
def list_maps(folder):
    try:
        return sorted([
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f)) and (f.lower().endswith(".map") or f.lower().endswith(".txt"))
        ])
    except FileNotFoundError:
        return []

def draw_menu(options, idx, preview_grid=None):
    clear()
    title_bar = f"{cfg.COLOR_TITLE}{cfg.TITLE_TEXT}{cfg.COLOR_RESET}"
    underline = f"{cfg.COLOR_TITLE_ACCENT}{'═'*len(cfg.TITLE_TEXT)}{cfg.COLOR_RESET}"
    print(title_bar)
    print(underline)
    hint  = f"{cfg.COLOR_HUD_LABEL}↑/↓ or W/S: select  |  Enter: confirm  |  Q: quit{cfg.COLOR_RESET}"
    print(hint)
    print()
    for i, name in enumerate(options):
        cursor = f"{cfg.COLOR_TITLE_ACCENT}>{cfg.COLOR_RESET}" if i == idx else " "
        display = name[:-4] if name.lower().endswith(".map") else name
        print(f"{cursor} {display}")

    print()

    # Right column: Top 10 highscores (per current map)
    current_map = "Empty map" if idx == 0 else options[idx]
    highs = load_high_scores(cfg.HIGH_SCORE_FILE)
    right_col = build_scoreboard_lines(highs, current_map, limit=10)

    if preview_grid:
        # Render preview + scoreboard side by side
        combined = side_by_side([f"{cfg.COLOR_HUD_LABEL}Preview:{cfg.COLOR_RESET}"] + preview_grid, right_col, gap=6)
        for line in combined:
            print(line)
    else:
        # Fallback: just print the scoreboard
        for line in right_col:
            print(line)

def read_map_file(path):
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = [line.rstrip("\n") for line in f.readlines()]
    lines = [ln for ln in raw_lines if ln != ""]
    if len(lines) != 10 or any(len(ln) != 10 for ln in lines):
        raise ValueError("The map must have 10 lines of 10 characters.")
    walls = set()
    start = None
    for y, row in enumerate(lines):
        for x, ch in enumerate(row):
            if ch == '#':
                walls.add((x, y))
            elif ch == 'P':
                start = (x, y)
    return walls, start, 10, 10

def build_preview_from_map(walls, start, w, h):
    grid = []
    for y in range(h):
        row = []
        for x in range(w):
            if start == (x, y):
                row.append(f"{cfg.COLOR_PLAYER}{cfg.PLAYER_CHAR}{cfg.COLOR_RESET}")
            elif (x, y) in walls:
                row.append(f"{cfg.COLOR_WALL}{cfg.WALL_CHAR}{cfg.COLOR_RESET}")
            else:
                row.append(".")
        grid.append(" ".join(row))
    return grid

def select_map():
    maps = list_maps(cfg.MAPS_DIR)
    options = ["(Empty default map)"] + maps
    idx = 0

    def preview(i):
        if i == 0:
            return [" ".join("." for _ in range(10)) for _ in range(10)]
        else:
            fname = maps[i - 1]
            try:
                walls, start, w, h = read_map_file(os.path.join(cfg.MAPS_DIR, fname))
                return build_preview_from_map(walls, start, w, h)
            except Exception as e:
                return [f"Read error: {e}"]

    prev = preview(idx)

    while True:
        draw_menu(options, idx, prev)
        key = msvcrt.getch()
        if key in (b'\x00', b'\xe0'):
            k = msvcrt.getch()
            if k == b'H':
                idx = (idx - 1) % len(options); prev = preview(idx)
            elif k == b'P':
                idx = (idx + 1) % len(options); prev = preview(idx)
        else:
            ch = key.lower()
            if ch == b'q':
                clear(); print("Goodbye!"); sys.exit(0)
            elif ch == b'w':
                idx = (idx - 1) % len(options); prev = preview(idx)
            elif ch == b's':
                idx = (idx + 1) % len(options); prev = preview(idx)
            elif ch in (b'\r', b'\n'):
                if idx == 0:
                    return set(), None, 10, 10, "Empty map"
                fname = maps[idx - 1]
                walls, start, w, h = read_map_file(os.path.join(cfg.MAPS_DIR, fname))
                return walls, start, w, h, fname

# ======================
#     PATTERNS (attacks/)
# ======================
def list_attack_files(folder):
    try:
        return sorted([
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith((".txt", ".pat"))
        ])
    except FileNotFoundError:
        return []

def load_free_shape(path):
    """
    Lit un pattern ASCII libre. Tout caractère non-espace active une cellule.
    Les chiffres '1'..'9' indiquent la vague (1 = immédiat, 9 = +8*WAVE_STAGGER).
    Tout autre caractère => vague 1.
    Retourne: {"cells": [(x,y,wave), ...], "w": w, "h": h}
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = [ln.rstrip("\n") for ln in f.readlines()]
    # trim empty lines top/bottom
    while raw and raw[0].strip() == "":
        raw.pop(0)
    while raw and raw[-1].strip() == "":
        raw.pop()
    if not raw:
        return None

    # crop horizontal bounds
    min_c = None; max_c = None
    for ln in raw:
        if ln.strip() == "":
            continue
        for i, ch in enumerate(ln):
            if ch != " ":
                min_c = i if min_c is None else min(min_c, i)
                max_c = i if max_c is None else max(max_c, i)
    if min_c is None:
        return None

    cropped = [ln[min_c:max_c+1] for ln in raw]
    h = len(cropped)
    w = max(len(ln) for ln in cropped) if h > 0 else 0
    cropped = [ln.ljust(w, " ") for ln in cropped]

    cells = []
    for y, ln in enumerate(cropped):
        for x, ch in enumerate(ln):
            if ch == " ":
                continue
            if ch in "123456789":
                wave = int(ch)
            else:
                wave = 1
            cells.append((x, y, wave))
    return {"cells": cells, "w": w, "h": h}

def load_attack_patterns(folder):
    patterns = []
    for fname in list_attack_files(folder):
        path = os.path.join(folder, fname)
        try:
            shp = load_free_shape(path)
            if shp and shp["cells"]:
                patterns.append(shp)
        except Exception:
            pass
    return patterns

def rotate_cells(cells, w, h, k):
    """
    Rotation 0/90/180/270° des cellules (x,y,wave).
    Retourne (new_cells, new_w, new_h)
    """
    k = k % 4
    if k == 0:
        return list(cells), w, h
    out = []
    if k == 1:
        for (x, y, wave) in cells:
            out.append((h - 1 - y, x, wave))
        return out, h, w
    if k == 2:
        for (x, y, wave) in cells:
            out.append((w - 1 - x, h - 1 - y, wave))
        return out, w, h
    # k == 3
    for (x, y, wave) in cells:
        out.append((y, w - 1 - x, wave))
    return out, h, w

def mirror_cells(cells, w, h, mirror_h=False, mirror_v=False):
    """
    Retourne la forme horizontalement et/ou verticalement.
    cells: [(x, y, wave)]
    Retourne (new_cells, w, h)
    """
    if not mirror_h and not mirror_v:
        return list(cells), w, h

    out = []
    for (x, y, wave) in cells:
        nx = (w - 1 - x) if mirror_h else x
        ny = (h - 1 - y) if mirror_v else y
        out.append((nx, ny, wave))
    return out, w, h


def place_shape_in_grid(cells, w, h):
    """
    Place aléatoirement la forme dans la grille.
    Retourne: dict[(gx,gy)] = wave
    """
    if w > GRID_W or h > GRID_H:
        return None
    ox = random.randint(0, GRID_W - w)
    oy = random.randint(0, GRID_H - h)
    placed = {}
    for (x, y, wave) in cells:
        placed[(ox + x, oy + y)] = wave
    return placed

def choose_attack(patterns):
    """Choisit un pattern, applique une rotation et un miroir aléatoires, puis le place dans la grille."""
    if not patterns:
        return {}
    for _ in range(40):
        shp = random.choice(patterns)

        # Rotation aléatoire (0, 90, 180, 270°)
        k = random.randint(0, 3)
        rot_cells, rw, rh = rotate_cells(shp["cells"], shp["w"], shp["h"], k)

        # Miroir aléatoire
        mirror_h = random.choice([False, True])
        mirror_v = random.choice([False, True])
        mirrored_cells, mw, mh = mirror_cells(rot_cells, rw, rh, mirror_h, mirror_v)

        # Placement aléatoire
        placed = place_shape_in_grid(mirrored_cells, mw, mh)
        if placed is not None:
            return placed  # dict[(x,y)] = wave
    return {}


def merged_cells(attacks):
    """
    attacks: list[dict[(x,y)->'!' or 'X']]
    Fusionne en donnant la priorité au 'X'.
    """
    merged = {}
    for atk in attacks:
        for pos, ch in atk.items():
            if ch == cfg.ATTACK_DAMAGE_CHAR:
                merged[pos] = cfg.ATTACK_DAMAGE_CHAR
            else:
                if pos not in merged:
                    merged[pos] = cfg.ATTACK_WARNING_CHAR
    return merged

# ======================
#      WAVE RENDERING
# ======================
def attacks_wave_render(current_attacks, phase, phase_elapsed,
                        fade_attacks=None, fade_elapsed=0.0):
    """
    Convertit des attaques stockées comme dict pos->wave (1..9)
    en couches dict pos->'!'/'X' selon la phase, avec un délai
    de cfg.WAVE_STAGGER entre vagues successives.

    current_attacks: list[dict[(x,y)->wave]]
    fade_attacks:    list[dict[(x,y)->wave]] (résidus à faire disparaître pendant idle)
    Retourne list[dict[(x,y)->'!'/'X']]
    """
    to_draw = []

    def draw_warning(atk):
        d = {}
        for pos, wave in atk.items():
            if phase_elapsed >= (wave - 1) * cfg.WAVE_STAGGER:
                d[pos] = cfg.ATTACK_WARNING_CHAR
        return d

    def draw_damage(atk):
        d = {}
        for pos, wave in atk.items():
            if phase_elapsed >= (wave - 1) * cfg.WAVE_STAGGER:
                d[pos] = cfg.ATTACK_DAMAGE_CHAR
            else:
                d[pos] = cfg.ATTACK_WARNING_CHAR
        return d

    def draw_fade(atk):
        # Pendant l'idle, on efface progressivement: la cellule reste affichée
        # tant que fade_elapsed < (wave-1)*stagger. Au-delà, elle disparaît.
        d = {}
        for pos, wave in atk.items():
            if fade_elapsed < (wave - 1) * cfg.WAVE_STAGGER:
                d[pos] = cfg.ATTACK_DAMAGE_CHAR
        return d

    if phase == 'warning':
        for atk in current_attacks:
            to_draw.append(draw_warning(atk))
    elif phase == 'damage':
        for atk in current_attacks:
            to_draw.append(draw_damage(atk))
    elif phase == 'idle' and fade_attacks:
        for atk in fade_attacks:
            to_draw.append(draw_fade(atk))

    return to_draw

# ======================
#           GAME
# ======================
def fmt_sec(s): return f"{s:.1f}s"

def draw_game(px, py, attacks, score, elapsed, coin_pos, walls,
              idle_dur, warning_dur, damage_dur, multi_prob, multi_active):
    # clear()  # ENLEVER ceci

    lines = []

    title_bar = f"{cfg.COLOR_TITLE}{cfg.TITLE_TEXT}{cfg.COLOR_RESET}"
    underline = f"{cfg.COLOR_TITLE_ACCENT}{'═'*len(cfg.TITLE_TEXT)}{cfg.COLOR_RESET}"
    hint = f"{cfg.COLOR_HUD_LABEL}{cfg.CONTROL_HINT}{cfg.COLOR_RESET}"

    # On remplit la liste 'lines' au lieu de print()
    lines.append(title_bar)
    lines.append(underline)
    lines.append(hint)

    speed = (f"{cfg.COLOR_HUD_LABEL}{cfg.SPEED_LABEL}:{cfg.COLOR_RESET} "
             f"idle {cfg.COLOR_HUD_VALUE}{fmt_sec(idle_dur)}{cfg.COLOR_RESET} • "
             f"warning {cfg.COLOR_HUD_VALUE}{fmt_sec(warning_dur)}{cfg.COLOR_RESET} • "
             f"damage {cfg.COLOR_HUD_VALUE}{fmt_sec(damage_dur)}{cfg.COLOR_RESET}")
    prob  = f"{cfg.COLOR_HUD_LABEL}{cfg.MULTI_LABEL}:{cfg.COLOR_RESET} {cfg.COLOR_HUD_VALUE}{int(multi_prob*100)}%{cfg.COLOR_RESET}"
    lines.append(header_line(speed, prob))

    # ===== Bandeau d’état de l’attaque =====
    # Calcule sur la frame courante : nb d'attaques non vides dans `attacks`
    non_empty = sum(1 for a in attacks if a)
    if non_empty > 1:
        # Multi-attaque : bandeau coloré d’origine
        banner = f"{cfg.COLOR_MULTI_BANNER}{cfg.MULTI_BANNER_TEXT}{cfg.COLOR_RESET}"
    else:
        # Attaque simple : bandeau gris "Normal attack"
        dim = "\x1b[90m"  # gris (ANSI)
        normal_text = getattr(cfg, "NORMAL_BANNER_TEXT", "----------")
        banner = f"{dim}{normal_text}{cfg.COLOR_RESET}"
    lines.append(banner)
    # =======================================

    view_w = GRID_W + (2 if cfg.BORDER_ENABLED else 0)
    view_h = GRID_H + (2 if cfg.BORDER_ENABLED else 0)
    layer = merged_cells(attacks)

    side_gap = cfg.SIDE_GAP_SPACES
    side_row_score = (1 if cfg.BORDER_ENABLED else 0) + cfg.SIDE_ROW_SCORE_INDEX
    side_row_time  = (1 if cfg.BORDER_ENABLED else 0) + cfg.SIDE_ROW_TIME_INDEX

    for ry in range(view_h):
        row_cells = []

        if cfg.BORDER_ENABLED and (ry == 0 or ry == view_h - 1):
            row_cells = [f"{cfg.COLOR_WALL}{cfg.BORDER_CHAR}{cfg.COLOR_RESET}"] * view_w
            row_text = " ".join(row_cells)
        else:
            y = ry - (1 if cfg.BORDER_ENABLED else 0)
            for rx in range(view_w):
                if cfg.BORDER_ENABLED and (rx == 0 or rx == view_h - 1):
                    row_cells.append(f"{cfg.COLOR_WALL}{cfg.BORDER_CHAR}{cfg.COLOR_RESET}")
                else:
                    x = rx - (1 if cfg.BORDER_ENABLED else 0)
                    here = (x, y)

                    if here in walls:
                        row_cells.append(f"{cfg.COLOR_WALL}{cfg.WALL_CHAR}{cfg.COLOR_RESET}")
                        continue

                    in_attack = here in layer
                    if in_attack:
                        ch = layer[here]
                        if here == (px, py):
                            row_cells.append(f"{cfg.COLOR_PLAYER}{ch}{cfg.COLOR_RESET}")
                        elif here == coin_pos:
                            row_cells.append(f"{cfg.COLOR_COIN}{ch}{cfg.COLOR_RESET}")
                        else:
                            row_cells.append(
                                f"{cfg.COLOR_WARNING}{cfg.ATTACK_WARNING_CHAR}{cfg.COLOR_RESET}"
                                if ch == cfg.ATTACK_WARNING_CHAR else
                                f"{cfg.COLOR_DAMAGE}{cfg.ATTACK_DAMAGE_CHAR}{cfg.COLOR_RESET}"
                            )
                    else:
                        if here == (px, py):
                            row_cells.append(f"{cfg.COLOR_PLAYER}{cfg.PLAYER_CHAR}{cfg.COLOR_RESET}")
                        elif here == coin_pos:
                            row_cells.append(f"{cfg.COLOR_COIN}{cfg.COIN_CHAR}{cfg.COLOR_RESET}")
                        else:
                            row_cells.append(".")

            row_text = " ".join(row_cells)

        if ry == side_row_score:
            row_text += " " * side_gap + f"{cfg.COLOR_HUD_VALUE}{cfg.SCORE_LABEL}:{cfg.COLOR_RESET} {cfg.COLOR_COIN}{score}{cfg.COLOR_RESET}"
        elif ry == side_row_time:
            row_text += " " * side_gap + f"{cfg.COLOR_HUD_VALUE}{cfg.TIME_LABEL}:{cfg.COLOR_RESET} {int(elapsed)}s"

        lines.append(row_text)

    lines.append("")  # print() final blank line

    # ==== ÉCRITURE ATOMIQUE DE LA FRAME ====
    frame = "\n".join(lines)

    # Curseur en haut puis écrire la frame, puis nettoyer le reste de l'écran
    sys.stdout.write("\x1b[H")
    sys.stdout.write(frame)
    sys.stdout.write("\x1b[J")
    sys.stdout.flush()


def handle_input(px, py, walls):
    if msvcrt.kbhit():
        key = msvcrt.getch()
        nx, ny = px, py
        if key in (b'\x00', b'\xe0'):
            k = msvcrt.getch()
            if   k == b'H': ny = max(0, py - 1)
            elif k == b'P': ny = min(GRID_H - 1, py + 1)
            elif k == b'K': nx = max(0, px - 1)
            elif k == b'M': nx = min(GRID_W - 1, px + 1)
        else:
            ch = key.lower()
            if ch == b'q':
                clear(); print("Goodbye!"); sys.exit(0)
            elif ch == b'w': ny = max(0, py - 1)
            elif ch == b's': ny = min(GRID_H - 1, py + 1)
            elif ch == b'a': nx = max(0, px - 1)
            elif ch == b'd': nx = min(GRID_W - 1, px + 1)
        if (nx, ny) not in walls:
            px, py = nx, ny
    return px, py

def random_free_cell(exclude, walls):
    while True:
        pos = (random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1))
        if pos not in exclude and pos not in walls:
            return pos

def timings_for_attack_count(attack_count):
    steps = attack_count // cfg.ATTACKS_PER_STEP
    idle = max(cfg.MIN_IDLE, cfg.BASE_IDLE - cfg.STEP_DELTA * steps)
    warning = max(cfg.MIN_WARNING, cfg.BASE_WARNING - cfg.STEP_DELTA * steps)
    return idle, warning, cfg.DAMAGE_DUR

def extra_attack_probability(attack_count):
    steps = attack_count // cfg.EXTRA_ATTACK_STEP
    return min(cfg.EXTRA_ATTACK_MAX, steps * cfg.EXTRA_ATTACK_GROWTH)

# ======================
#         RUN
# ======================
def run_game(walls, start, attack_patterns, map_label):
    # initial position
    if start and start not in walls:
        px, py = start
    else:
        px, py = (0, 0)
        if (px, py) in walls:
            for yy in range(GRID_H):
                for xx in range(GRID_W):
                    if (xx, yy) not in walls:
                        px, py = xx, yy
                        break
                else:
                    continue
                break

    score = 0
    coin_pos = random_free_cell({(px, py)}, walls)

    wave_count = 0
    idle_dur, warning_dur, damage_dur = timings_for_attack_count(wave_count)

    phase = 'idle'
    phase_start = time.time()
    current_attacks = []      # list of dict[(x,y)->wave]
    fade_attacks = None       # attaques à faire disparaître en idle
    fade_start = 0.0

    multi_active = False
    game_start = phase_start

    try:
        while True:
            now = time.time()
            elapsed = now - game_start
            phase_elapsed = now - phase_start
            changed_phase = False  # NEW : pour éviter le flash au switch

            # =======================
            #       PHASE IDLE
            # =======================
            if phase == 'idle':
                # Nettoyage du fade terminé
                if fade_attacks and (now - fade_start) >= (8 * cfg.WAVE_STAGGER + 1e-6):
                    fade_attacks = None

                # Passage en phase warning
                if phase_elapsed >= idle_dur:
                    phase = 'warning'
                    phase_start = now
                    changed_phase = True

                    atk1 = choose_attack(attack_patterns)
                    current_attacks = [atk1] if atk1 else []
                    prob = extra_attack_probability(wave_count)
                    multi_active = False
                    if random.random() < prob:
                        atk2 = choose_attack(attack_patterns)
                        if atk2:
                            current_attacks.append(atk2)
                            multi_active = True

            # =======================
            #      PHASE WARNING
            # =======================
            elif phase == 'warning':
                if phase_elapsed >= warning_dur:
                    phase = 'damage'
                    phase_start = now
                    changed_phase = True
                    # On garde current_attacks (rendu géré par attacks_wave_render)

            # =======================
            #       PHASE DAMAGE
            # =======================
            elif phase == 'damage':
                if phase_elapsed >= damage_dur:
                    # Passage en idle avec fade
                    fade_attacks = current_attacks
                    fade_start = now

                    wave_count += 1
                    idle_dur, warning_dur, damage_dur = timings_for_attack_count(wave_count)
                    phase = 'idle'
                    phase_start = now
                    changed_phase = True
                    current_attacks = []
                    multi_active = False

            # Si on vient de changer de phase, reset phase_elapsed
            if changed_phase:
                phase_elapsed = 0.0

            # =======================
            #        INPUT
            # =======================
            px, py = handle_input(px, py, walls)

            # =======================
            #        COINS
            # =======================
            if (px, py) == coin_pos:
                score += 1
                coin_pos = random_free_cell({(px, py)}, walls)

            # =======================
            #        HUD DATA
            # =======================
            multi_prob = extra_attack_probability(wave_count)

            # =======================
            #        RENDU
            # =======================
            if phase == 'idle' and fade_attacks:
                to_draw = attacks_wave_render(current_attacks, phase, phase_elapsed,
                                              fade_attacks=fade_attacks,
                                              fade_elapsed=(now - fade_start))
            else:
                to_draw = attacks_wave_render(current_attacks, phase, phase_elapsed)

            # (On peut laisser multi_active tel quel; l'affichage est basé sur `attacks` dans draw_game)
            draw_game(px, py, to_draw, score, elapsed, coin_pos, walls,
                      idle_dur, warning_dur, damage_dur, multi_prob, multi_active)

            # =======================
            #       COLLISIONS
            # =======================
            if phase == 'damage':
                merged = merged_cells(to_draw)
                if (px, py) in merged and merged[(px, py)] == cfg.ATTACK_DAMAGE_CHAR:
                    try:
                        save_high_score(cfg.HIGH_SCORE_FILE, map_label, score, elapsed)
                    except Exception:
                        pass
                    print(f"{cfg.COLOR_DAMAGE}You were hit! GAME OVER.{cfg.COLOR_RESET}")
                    print(f"Final score: {score} | Time: {int(elapsed)}s")
                    print("Press any key to quit...")
                    msvcrt.getch()
                    return

            time.sleep(cfg.TICK)

    except KeyboardInterrupt:
        clear()
        print("Interrupted. Goodbye!")


# ======================
#         MAIN
# ======================
def main():
    global GRID_W, GRID_H

    if os.name == "nt":
        enable_vt_mode()

    walls, start, w, h, label = select_map()
    GRID_W, GRID_H = w, h

    attack_patterns = load_attack_patterns(cfg.ATTACKS_DIR)
    if not attack_patterns:
        clear()
        print(f"{cfg.COLOR_ERROR}Aucune attaque trouvée dans '{cfg.ATTACKS_DIR}'.{cfg.COLOR_RESET}")
        print(f"{cfg.COLOR_HINT}Ajoute au moins un fichier .txt avec une forme d'attaque.{cfg.COLOR_RESET}")
        input(f"\n{cfg.COLOR_HINT}Appuie sur Entrée pour quitter...{cfg.COLOR_RESET}")
        return

    try:
        enter_alt_screen()
        run_game(walls, start, attack_patterns, label)
    finally:
        exit_alt_screen()

if __name__ == "__main__":
    main()
