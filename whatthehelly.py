"""
Factorise!  -  a drag-and-drop algebra game.

    python factor_game.py

Needs factor_logic.py next to it. sympy is optional but recommended:
    pip install sympy
Without it the game still runs, but only accepts the one expected arrangement.
"""

import random
import time
import tkinter as tk
import sympy as sp

import logic

# ---------------------------------------------------------------- appearance
W, H = 980, 620
TILE_W, TILE_H = 56, 56
GAP = 8
SLOT_Y = 245                 # y of the slot row
TRAY_Y = 355                 # y of the first tray row
TRAY_PER_ROW = 10
SNAP_RADIUS = 46

BG      = "#f4f1ea"
SLOT_BG = "#e2ddd2"
SLOT_OK = "#cdebd8"
TILE_BG = "#3d5a80"          # decoys look identical - that is the point
TILE_FG = "#ffffff"
INK     = "#22303c"
MUTED   = "#8a8378"
GOOD    = "#2a9d5c"
BAD     = "#c1443a"

DISTRACTOR_COUNT = {1: 2, 2: 2, 3: 3}


class FactorGame:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
        self.canvas.pack()

        self.level = tk.IntVar(value=1)
        self._build_controls(root)

        self.streak = 0
        self.best_streak = 0
        self.solved_count = 0
        self.best_time = None
        self.tag_counter = 0
        self.drag = {"tile": None, "x": 0, "y": 0}

        self.new_round()
        self.tick()

    def _build_controls(self, root):
        bar = tk.Frame(root, bg=BG)
        bar.pack(fill="x", pady=(0, 12))

        tk.Button(bar, text="Check", width=9, command=self.check).pack(side="left", padx=(16, 6))
        tk.Button(bar, text="Reset", width=9, command=self.reset_tiles).pack(side="left", padx=6)
        tk.Button(bar, text="New problem", width=12, command=self.new_round).pack(side="left", padx=6)

        tk.Label(bar, text="   difficulty:", bg=BG, fg=MUTED).pack(side="left")
        for value, label in [(1, "1"), (2, "2"), (3, "3"), (0, "mixed")]:
            tk.Radiobutton(bar, text=label, variable=self.level, value=value, bg=BG,
                           command=self.new_round).pack(side="left")

        root.bind("<Return>", lambda e: self.check())
        root.bind("<space>", lambda e: self.new_round())

    # ------------------------------------------------------------ one round
    def new_round(self):
        self.canvas.delete("all")
        self.problem = logic.make_problem(self.level.get())
        self.answer = self.problem.answer
        self.solved = False
        self.started = time.time()
        self.tiles = []

        self.canvas.create_text(W // 2, 100, text=self.problem.display,
                                font=("Georgia", 42), fill=INK)
        self.canvas.create_text(W // 2, 155,
                                text="drag the tiles to factorise  \u00b7  "
                                     "not every tile is needed",
                                font=("Helvetica", 13), fill=MUTED)
        self.hud = self.canvas.create_text(24, 26, anchor="w", font=("Helvetica", 12), fill=MUTED)
        self.clock = self.canvas.create_text(W - 24, 26, anchor="e",
                                             font=("Helvetica", 12), fill=MUTED)
        self.feedback = self.canvas.create_text(W // 2, 545, text="",
                                                font=("Helvetica", 15, "bold"))

        # --- slots: exactly as many as the expected answer needs
        n = len(self.answer)
        left = W // 2 - (n * (TILE_W + GAP) - GAP) // 2
        self.slots = []
        for i in range(n):
            cx = left + i * (TILE_W + GAP) + TILE_W // 2
            rect = self.canvas.create_rectangle(
                cx - TILE_W // 2, SLOT_Y - TILE_H // 2,
                cx + TILE_W // 2, SLOT_Y + TILE_H // 2,
                fill=SLOT_BG, outline="#c9c2b4", dash=(4, 3))
            self.slots.append({"cx": cx, "cy": SLOT_Y, "tile": None, "rect": rect})

        # --- tray: the answer's tiles plus a few decoys, shuffled together
        decoys = logic.distractors(self.problem, DISTRACTOR_COUNT[self.problem.level])
        texts = list(self.answer) + decoys
        random.shuffle(texts)

        for i, text in enumerate(texts):
            row, col = divmod(i, TRAY_PER_ROW)
            in_row = min(len(texts) - row * TRAY_PER_ROW, TRAY_PER_ROW)
            row_left = W // 2 - (in_row * (TILE_W + GAP) - GAP) // 2
            cx = row_left + col * (TILE_W + GAP) + TILE_W // 2
            cy = TRAY_Y + row * (TILE_H + 14)
            self.tiles.append(self.make_tile(text, cx, cy))

        self.update_hud()

    def make_tile(self, text, cx, cy):
        self.tag_counter += 1
        tag = f"tile{self.tag_counter}"
        self.canvas.create_rectangle(cx - TILE_W // 2, cy - TILE_H // 2,
                                     cx + TILE_W // 2, cy + TILE_H // 2,
                                     fill=TILE_BG, outline="", tags=tag)
        self.canvas.create_text(cx, cy, text=text, font=("Georgia", 24),
                                fill=TILE_FG, tags=tag)

        tile = {"tag": tag, "text": text, "home": (cx, cy), "slot": None}
        self.canvas.tag_bind(tag, "<Button-1>", lambda e, t=tile: self.press(e, t))
        self.canvas.tag_bind(tag, "<B1-Motion>", self.motion)
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.release)
        return tile

    # -------------------------------------------------------- drag and drop
    def press(self, event, tile):
        if self.solved:
            return
        self.drag = {"tile": tile, "x": event.x, "y": event.y}
        self.canvas.tag_raise(tile["tag"])
        if tile["slot"] is not None:                # lifted back out of a slot
            self.free_slot(tile["slot"])
            tile["slot"] = None

    def motion(self, event):
        tile = self.drag["tile"]
        if tile is None:
            return
        self.canvas.move(tile["tag"], event.x - self.drag["x"], event.y - self.drag["y"])
        self.drag["x"], self.drag["y"] = event.x, event.y

    def release(self, event):
        tile = self.drag["tile"]
        if tile is None:
            return
        self.drag["tile"] = None

        cx, cy = self.centre(tile)
        target, best = None, SNAP_RADIUS
        for i, slot in enumerate(self.slots):
            d = ((slot["cx"] - cx) ** 2 + (slot["cy"] - cy) ** 2) ** 0.5
            if d < best:
                target, best = i, d

        if target is None:                          # dropped nowhere useful
            self.move_to(tile, *tile["home"])
            return

        occupant = self.slots[target]["tile"]
        if occupant is not None:                    # bump whoever was there
            occupant["slot"] = None
            self.move_to(occupant, *occupant["home"])

        self.slots[target]["tile"] = tile
        tile["slot"] = target
        self.canvas.itemconfig(self.slots[target]["rect"], fill=SLOT_OK)
        self.move_to(tile, self.slots[target]["cx"], self.slots[target]["cy"])

    def free_slot(self, i):
        self.slots[i]["tile"] = None
        self.canvas.itemconfig(self.slots[i]["rect"], fill=SLOT_BG)

    def centre(self, tile):
        x1, y1, x2, y2 = self.canvas.bbox(tile["tag"])
        return (x1 + x2) / 2, (y1 + y2) / 2

    def move_to(self, tile, x, y):
        cx, cy = self.centre(tile)
        self.canvas.move(tile["tag"], x - cx, y - cy)

    # -------------------------------------------------------- clock and HUD
    def tick(self):
        if not self.solved:
            self.canvas.itemconfig(self.clock, text=f"{time.time() - self.started:5.1f} s")
        self.root.after(200, self.tick)

    def update_hud(self):
        best = f"    best streak {self.best_streak}" if self.best_streak else ""
        pb = f"    best time {self.best_time:.1f} s" if self.best_time else ""
        self.canvas.itemconfig(
            self.hud,
            text=f"level {self.problem.level}: {logic.LEVEL_NAMES[self.problem.level]}"
                 f"    solved {self.solved_count}    streak {self.streak}{best}{pb}")

    # ---------------------------------------------------------- the verdict
    def reset_tiles(self):
        if self.solved:
            return
        for tile in self.tiles:
            tile["slot"] = None
            self.move_to(tile, *tile["home"])
        for i in range(len(self.slots)):
            self.free_slot(i)
        self.say("", MUTED)

    def check(self):
        if self.solved:
            return
        if any(slot["tile"] is None for slot in self.slots):
            self.say("Some slots are still empty.", BAD)
            return

        tokens = [slot["tile"]["text"] for slot in self.slots]
        correct, message = logic.judge(self.problem, tokens)

        if correct:
            elapsed = time.time() - self.started
            self.solved = True
            self.solved_count += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            if self.best_time is None or elapsed < self.best_time:
                self.best_time = elapsed
            self.say(f"{message}    {elapsed:.1f} s    streak {self.streak}"
                     "        (press space for the next one)", GOOD)
        else:
            self.streak = 0
            self.say(message, BAD)
        self.update_hud()

    def say(self, text, colour):
        self.canvas.itemconfig(self.feedback, text=text, fill=colour)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Factorise!")
    root.configure(bg=BG)
    root.resizable(False, False)
    FactorGame(root)
    root.mainloop()