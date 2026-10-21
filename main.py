"""Winning the Academic Game - a pygame game about how academia got gamified.

Run:  python main.py
"""

import asyncio
import math
import re
import sys
import webbrowser
from urllib.parse import quote

import pygame

from events import EVENTS
from model import (ACTIVITIES, ACT_KEYS, BASE_HOURS, CATEGORIES, MAX_HOURS,
                   MAX_PER_ACTIVITY, MIN_CLASS_HOURS, RUBRICS, SCORE_CHASING, STAR_LABELS,
                   STEP, YEARS, Career)

W, H = 1280, 800
GAME_URL = "https://fredpoole.github.io/academic-game/"
WEB = sys.platform == "emscripten"
FPS = 60

BG = (246, 242, 233)
PANEL = (255, 253, 248)
INK = (38, 38, 46)
MUTED = (115, 112, 120)
LINE = (220, 212, 198)
GOLD = (214, 164, 38)
RED = (196, 66, 60)
GREEN = (58, 146, 84)
DARK = (34, 36, 48)
CAT_COLORS = {
    "Research": (64, 104, 180),
    "Teaching": (214, 118, 50),
    "Service": (78, 148, 92),
    "Visibility": (148, 88, 170),
    "Admin": (120, 120, 128),
}
HIDDEN_COLORS = {
    "knowledge": (64, 104, 180),
    "learning": (214, 118, 50),
    "real_service": (78, 148, 92),
    "wellbeing": (196, 86, 120),
}

_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("helveticaneue,helvetica,arial", size, bold=bold)
    return _fonts[key]


def text(surf, s, pos, size=18, color=INK, bold=False, anchor="topleft"):
    img = font(size, bold).render(str(s), True, color)
    r = img.get_rect(**{anchor: pos})
    surf.blit(img, r)
    return r


def wrap(s, size, width, bold=False):
    f = font(size, bold)
    lines = []
    for para in s.split("\n"):
        line = ""
        for word in para.split(" "):
            trial = f"{line} {word}".strip()
            if f.size(trial)[0] <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def text_block(surf, s, pos, width, size=18, color=INK, bold=False, spacing=1.3):
    x, y = pos
    for line in wrap(s, size, width, bold):
        text(surf, line, (x, y), size, color, bold)
        y += int(size * spacing)
    return y


def panel(surf, rect, color=PANEL, radius=14, border=LINE):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border, rect, 1, border_radius=radius)


def bar(surf, rect, frac, color, bg=(232, 226, 214), radius=6):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, bg, rect, border_radius=radius)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        fill = rect.copy()
        fill.width = max(radius * 2, int(rect.width * frac))
        pygame.draw.rect(surf, color, fill, border_radius=radius)


def star(surf, center, r, color, filled=True):
    cx, cy = center
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    pygame.draw.polygon(surf, color if filled else (225, 218, 205), pts)


def check(surf, center, ok, size=10):
    cx, cy = center
    if ok:
        pygame.draw.circle(surf, GREEN, center, size)
        pygame.draw.lines(surf, (255, 255, 255), False,
                          [(cx - size * 0.45, cy), (cx - size * 0.1, cy + size * 0.4),
                           (cx + size * 0.5, cy - size * 0.4)], 3)
    else:
        pygame.draw.circle(surf, RED, center, size)
        d = size * 0.4
        pygame.draw.line(surf, (255, 255, 255), (cx - d, cy - d), (cx + d, cy + d), 3)
        pygame.draw.line(surf, (255, 255, 255), (cx - d, cy + d), (cx + d, cy - d), 3)


def medal(surf, center, name, small=False):
    cx, cy = center
    r = 13 if small else 18
    pygame.draw.polygon(surf, (190, 70, 70), [(cx - r * 0.6, cy - r * 1.6), (cx - r * 0.1, cy - r * 1.6),
                                              (cx + r * 0.25, cy - r * 0.5), (cx - r * 0.3, cy - r * 0.5)])
    pygame.draw.polygon(surf, (60, 90, 170), [(cx + r * 0.6, cy - r * 1.6), (cx + r * 0.1, cy - r * 1.6),
                                              (cx - r * 0.25, cy - r * 0.5), (cx + r * 0.3, cy - r * 0.5)])
    pygame.draw.circle(surf, GOLD, center, r)
    pygame.draw.circle(surf, (245, 205, 90), center, int(r * 0.7))
    star(surf, center, r * 0.5, GOLD)


def fmt_money(v):
    if v >= 1_000_000:
        return f"${v / 1_000_000:.2f}M"
    if v >= 1000:
        return f"${v / 1000:.0f}K"
    return f"${v:,.0f}"


def fmt_stat(key, v):
    if key == "eval_avg":
        return f"{v:.2f}"
    if key == "grant_dollars":
        return fmt_money(v)
    if key in ("service", "reputation"):
        return f"{int(v)}"
    return f"{v}"


# ---------------------------------------------------------------------------
# The professor
# ---------------------------------------------------------------------------

def draw_professor(surf, cx, base_y, s, g, t=0.0):
    """A simple stick-figure professor. Ages, tires, and piles up papers."""
    energy = g.energy
    years = (g.year - 1) / (YEARS - 1)
    overtime = g.total_hours() > BASE_HOURS

    # Stack of papers next to the professor, one sheet per publication.
    n = min(g.pubs, 45)
    for i in range(n):
        y = base_y - (i + 1) * 3 * s
        r = pygame.Rect(cx - 95 * s, y, 42 * s, 3 * s)
        pygame.draw.rect(surf, (255, 255, 255) if i % 2 else (236, 232, 222), r)
        pygame.draw.rect(surf, (180, 172, 160), r, 1)
    if g.pubs > 45:
        text(surf, f"x{g.pubs}", (cx - 74 * s, base_y - 140 * s), int(13 * s), MUTED, anchor="midbottom")

    # Grant money bag
    if g.grants_won:
        bag = (int(cx + 80 * s), int(base_y - 16 * s))
        pygame.draw.circle(surf, (150, 120, 60), bag, int(16 * s))
        pygame.draw.rect(surf, (150, 120, 60), (bag[0] - 6 * s, bag[1] - 24 * s, 12 * s, 10 * s))
        text(surf, "$", bag, int(18 * s), (255, 236, 160), bold=True, anchor="center")

    slump = (1 - energy / 100) * 10 * s
    hip = (cx, base_y - 62 * s)
    neck = (cx + slump * 0.4, base_y - 122 * s + slump)
    head = (int(neck[0] + slump * 0.5), int(neck[1] - 26 * s))

    # Legs
    pygame.draw.line(surf, INK, hip, (cx - 16 * s, base_y), max(2, int(4 * s)))
    pygame.draw.line(surf, INK, hip, (cx + 16 * s, base_y), max(2, int(4 * s)))
    # Tweed jacket
    jacket = (132, 96, 70) if g.title_level < 2 else (70, 62, 90)
    pygame.draw.polygon(surf, jacket, [(neck[0] - 20 * s, neck[1] + 4 * s), (neck[0] + 20 * s, neck[1] + 4 * s),
                                       (hip[0] + 18 * s, hip[1] + 6 * s), (hip[0] - 18 * s, hip[1] + 6 * s)])
    pygame.draw.polygon(surf, (250, 250, 250), [(neck[0] - 6 * s, neck[1] + 4 * s), (neck[0] + 6 * s, neck[1] + 4 * s),
                                                (neck[0], neck[1] + 22 * s)])
    tie = [(150, 40, 40), (40, 70, 150), (180, 140, 30)][g.title_level]
    pygame.draw.polygon(surf, tie, [(neck[0] - 3 * s, neck[1] + 5 * s), (neck[0] + 3 * s, neck[1] + 5 * s),
                                    (neck[0] + 4 * s, neck[1] + 26 * s), (neck[0], neck[1] + 31 * s),
                                    (neck[0] - 4 * s, neck[1] + 26 * s)])
    # Arms: up when energized, drooping when exhausted
    lift = (energy - 50) / 50 * 20 * s
    for side in (-1, 1):
        sh = (neck[0] + side * 18 * s, neck[1] + 8 * s)
        elbow = (sh[0] + side * 14 * s, sh[1] + 26 * s - lift * 0.5)
        hand = (elbow[0] + side * 6 * s, elbow[1] + 24 * s - lift * 1.6)
        pygame.draw.line(surf, jacket, sh, elbow, max(3, int(7 * s)))
        pygame.draw.line(surf, jacket, elbow, hand, max(3, int(7 * s)))
        pygame.draw.circle(surf, (240, 208, 176), hand, int(5 * s))
    # Head
    pygame.draw.circle(surf, (240, 208, 176), head, int(24 * s))
    # Hair goes grey as the career goes on
    brown, grey = (95, 66, 44), (200, 200, 205)
    hair = tuple(int(b + (gr - b) * years) for b, gr in zip(brown, grey))
    hair_rect = pygame.Rect(head[0] - 25 * s, head[1] - 27 * s, 50 * s, 30 * s)
    pygame.draw.arc(surf, hair, hair_rect, math.radians(10 + years * 50), math.radians(170 - years * 50),
                    max(3, int(9 * s)))
    pygame.draw.circle(surf, hair, (head[0] - 23 * s, head[1] - 2 * s), int(6 * s))
    pygame.draw.circle(surf, hair, (head[0] + 23 * s, head[1] - 2 * s), int(6 * s))
    # Glasses
    for side in (-1, 1):
        pygame.draw.circle(surf, INK, (head[0] + side * 9 * s, head[1] - 2 * s), int(7 * s), max(1, int(2 * s)))
        pygame.draw.circle(surf, INK, (head[0] + side * 9 * s, head[1] - 2 * s), max(1, int(2 * s)))
    pygame.draw.line(surf, INK, (head[0] - 2 * s, head[1] - 3 * s), (head[0] + 2 * s, head[1] - 3 * s), 2)
    # Tired eye bags
    if energy < 45:
        for side in (-1, 1):
            pygame.draw.arc(surf, (150, 120, 140),
                            (head[0] + side * 9 * s - 6 * s, head[1] + 2 * s, 12 * s, 7 * s),
                            math.pi, 2 * math.pi, max(1, int(2 * s)))
    # Mouth
    mouth = pygame.Rect(head[0] - 9 * s, head[1] + 6 * s, 18 * s, 10 * s)
    if energy >= 60:
        pygame.draw.arc(surf, INK, mouth, math.pi, 2 * math.pi, max(1, int(2 * s)))
    elif energy >= 35:
        pygame.draw.line(surf, INK, (mouth.left, mouth.centery + 2 * s), (mouth.right, mouth.centery + 2 * s),
                         max(1, int(2 * s)))
    else:
        mouth.y += 6 * s
        pygame.draw.arc(surf, INK, mouth, 0, math.pi, max(1, int(2 * s)))
    # Sweat when working overtime
    if overtime:
        for i in range(2):
            phase = (t * 1.2 + i * 0.5) % 1.0
            sx = head[0] + (28 + i * 6) * s
            sy = head[1] - 14 * s + phase * 34 * s
            pygame.draw.circle(surf, (110, 170, 230), (int(sx), int(sy)), int(4 * s))
    # Mortarboard for full professors
    if g.title_level == 2:
        top = head[1] - 24 * s
        pygame.draw.polygon(surf, DARK, [(head[0] - 30 * s, top), (head[0], top - 10 * s),
                                         (head[0] + 30 * s, top), (head[0], top + 10 * s)])
        pygame.draw.line(surf, GOLD, (head[0], top), (head[0] + 24 * s, top + 16 * s), 2)


# ---------------------------------------------------------------------------
# UI widgets
# ---------------------------------------------------------------------------

class Button:
    def __init__(self, rect, label, on_click, kind="primary", size=20, enabled=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.kind = kind
        self.size = size
        self.enabled = enabled or (lambda: True)

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            if self.enabled():
                self.on_click()
            return True
        return False

    def draw(self, surf):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        on = self.enabled()
        if self.kind == "primary":
            col = (DARK if not hover else (60, 64, 86)) if on else (190, 186, 180)
            pygame.draw.rect(surf, col, self.rect, border_radius=10)
            fg = (255, 255, 255)
        elif self.kind == "choice":
            col = (255, 255, 255) if not hover else (246, 240, 226)
            pygame.draw.rect(surf, col, self.rect, border_radius=10)
            pygame.draw.rect(surf, DARK if hover else LINE, self.rect, 2, border_radius=10)
            fg = INK
        else:  # small +/- buttons
            col = ((236, 230, 218) if not hover else (222, 214, 198)) if on else (244, 241, 235)
            pygame.draw.rect(surf, col, self.rect, border_radius=8)
            fg = INK if on else (190, 186, 180)
        if self.kind == "choice":
            lines = wrap(self.label, self.size, self.rect.width - 40)
            y = self.rect.centery - len(lines) * self.size * 0.65
            for ln in lines:
                text(surf, ln, (self.rect.x + 20, y), self.size, fg)
                y += self.size * 1.3
        else:
            text(surf, self.label, self.rect.center, self.size, fg, bold=True, anchor="center")


class Screen:
    has_header = False

    def __init__(self, app):
        self.app = app
        self.buttons = []
        self.t = 0.0
        # Restart needs two clicks: the first arms it, the second restarts.
        self.restart_armed = 0.0
        self.restart = Button((560, 16, 130, 34), "Restart", self.click_restart, kind="small", size=16)

    @property
    def g(self):
        return self.app.career

    def click_restart(self):
        if self.restart_armed > 0:
            self.app.new_game()
        else:
            self.restart_armed = 3.0

    def handle(self, e):
        if self.has_header and self.restart.handle(e):
            return
        for b in list(self.buttons):
            if b.handle(e):
                return

    def update(self, dt):
        self.t += dt
        self.restart_armed = max(0.0, self.restart_armed - dt)

    def draw(self, surf):
        for b in self.buttons:
            b.draw(surf)

    def header(self, surf):
        g = self.g
        pygame.draw.rect(surf, DARK, (0, 0, W, 64))
        text(surf, "WINNING THE ACADEMIC GAME", (24, 12), 13, (180, 182, 200), bold=True)
        text(surf, f"Year {g.year} of {YEARS}  ·  {g.title}", (24, 30), 22, (255, 255, 255), bold=True)
        text(surf, "Salary", (720, 14), 13, (180, 182, 200))
        text(surf, f"${g.salary:,.0f}", (720, 30), 20, (255, 255, 255), bold=True)
        text(surf, "Badges", (860, 14), 13, (180, 182, 200))
        text(surf, f"{len(g.badges)}", (860, 30), 20, (255, 255, 255), bold=True)
        text(surf, "Energy", (960, 14), 13, (180, 182, 200))
        ecol = GREEN if g.energy >= 60 else GOLD if g.energy >= 30 else RED
        bar(surf, (960, 36, 280, 14), g.energy / 100, ecol, bg=(70, 72, 90))
        text(surf, f"{int(g.energy)}", (1246, 43), 14, (255, 255, 255), anchor="midleft")
        if self.restart_armed > 0:
            pygame.draw.rect(surf, RED, self.restart.rect, border_radius=8)
            text(surf, "Click to confirm", self.restart.rect.center, 14, (255, 255, 255), bold=True, anchor="center")
        else:
            self.restart.draw(surf)


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

class TitleScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [Button((W // 2 - 140, 650, 280, 58), "Begin your career", self.start, size=22)]

    def start(self):
        self.app.new_game()

    def draw(self, surf):
        surf.fill(BG)
        text(surf, "WINNING THE", (W // 2, 70), 30, MUTED, bold=True, anchor="midtop")
        text(surf, "Academic Game", (W // 2, 108), 72, INK, bold=True, anchor="midtop")
        intro = ("You are a newly hired Assistant Professor. Your job is to create knowledge, educate students, "
                 "and serve your university and community.\n\n"
                 "But nobody can measure those things directly. So your university counts what it can: "
                 "publications, citations, grant dollars, teaching evaluations, enrollment, and lines on your CV. "
                 "Every year you get scored. Score high enough and you level up: tenure in Year 6, "
                 "Full Professor in Year 10.\n\n"
                 "Each year, split your work week across activities and make choices as events come up. "
                 "Can you win the game?")
        text_block(surf, intro, (W // 2 - 330, 220), 660, 20, INK)
        draw_professor(surf, 190, 560, 1.4, self.app.preview, self.t)
        tips = ["Hours over 40 drain energy.", "Low energy = less output.", "Watch the next review rubric."]
        for i, tip in enumerate(tips):
            text(surf, "•  " + tip, (W - 330, 470 + i * 30), 17, MUTED)
        super().draw(surf)


class AllocateScreen(Screen):
    has_header = True
    ROW_H = 40
    LEFT_X = 28

    def __init__(self, app):
        super().__init__(app)
        self.rows = []
        y = 96
        last_cat = None
        for act in ACTIVITIES:
            if act["cat"] != last_cat:
                last_cat = act["cat"]
                self.rows.append(("cat", act["cat"], y))
                y += 21
            self.rows.append(("act", act, y))
            k = act["key"]
            self.buttons.append(Button((470, y + 5, 34, 28), "-", lambda k=k: self.adjust(k, -STEP),
                                       kind="small", enabled=lambda k=k: self.g.alloc[k] > 0))
            self.buttons.append(Button((560, y + 5, 34, 28), "+", lambda k=k: self.adjust(k, STEP),
                                       kind="small",
                                       enabled=lambda k=k: self.g.alloc[k] < MAX_PER_ACTIVITY
                                       and self.g.total_hours() + STEP <= MAX_HOURS))
            y += self.ROW_H
        self.buttons.append(Button((990, 726, 262, 54), "Start the year  >", self.go,
                                   enabled=lambda: self.g.alloc_valid()))

    def adjust(self, key, d):
        self.g.alloc[key] = max(0, min(MAX_PER_ACTIVITY, self.g.alloc[key] + d))

    def go(self):
        self.app.start_year()

    def draw(self, surf):
        g = self.g
        surf.fill(BG)
        self.header(surf)
        panel(surf, (14, 74, 750, 716))
        text(surf, "Your work week", (self.LEFT_X, 82), 13, MUTED, bold=True)
        text(surf, "hours / week", (577, 82), 13, MUTED, bold=True, anchor="midtop")
        for kind, item, y in self.rows:
            if kind == "cat":
                col = CAT_COLORS[item]
                text(surf, item.upper(), (self.LEFT_X, y + 5), 12, col, bold=True)
                continue
            act = item
            col = CAT_COLORS[act["cat"]]
            pygame.draw.rect(surf, col, (self.LEFT_X - 8, y + 5, 4, 30), border_radius=2)
            text(surf, act["name"], (self.LEFT_X + 4, y + 3), 17, INK, bold=True)
            text(surf, act["pitch"], (self.LEFT_X + 4, y + 23), 13, MUTED)
            text(surf, f"{g.alloc[act['key']]}", (532, y + 19), 20, INK, bold=True, anchor="center")
            bar(surf, (610, y + 17, 140, 12), g.alloc[act["key"]] / MAX_PER_ACTIVITY, col)

        # Right side: professor, stats, rubric
        panel(surf, (778, 74, 488, 236))
        draw_professor(surf, 900, 292, 0.95, g, self.t)
        x = 1010
        text(surf, "THIS YEAR'S PLAN", (x, 92), 12, MUTED, bold=True)
        total = g.total_hours()
        tcol = INK if total <= BASE_HOURS else RED
        text(surf, f"{total}", (x, 110), 46, tcol, bold=True)
        text(surf, f"/ {BASE_HOURS} hrs", (x + font(46, True).size(str(total))[0] + 8, 132), 18, MUTED)
        msg_y = 168
        drop = round((total - BASE_HOURS) * 2.2 - 5)
        if total > BASE_HOURS and drop > 0:
            msg_y = text_block(surf, f"Overtime! Energy will drop ~{drop} this year.", (x, msg_y), 240, 15, RED)
        elif total > BASE_HOURS:
            msg_y = text_block(surf, "Overtime: you'll barely recover energy.", (x, msg_y), 240, 15, GOLD)
        elif total < BASE_HOURS:
            msg_y = text_block(surf, "Under 40 hours: you'll recover energy.", (x, msg_y), 240, 15, GREEN)
        if g.class_hours() < MIN_CLASS_HOURS:
            text_block(surf, f"Your classes need at least {MIN_CLASS_HOURS} hrs of rigorous or crowd-pleasing teaching.",
                       (x, msg_y + 4), 240, 15, RED)
        elif g.energy < 40:
            text_block(surf, f"Exhausted: output at {int(g.efficiency() * 100)}%.", (x, msg_y + 4), 240, 15, RED)

        panel(surf, (778, 320, 488, 168))
        text(surf, "YOUR STATS", (796, 332), 12, MUTED, bold=True)
        stats = [
            ("Publications", f"{g.pubs}"), ("Citations", f"{g.citations}"),
            ("h-index", f"{g.h}"), ("Grant $", fmt_money(g.grant_dollars)),
            ("Avg eval", f"{g.eval_avg:.2f}" if g.evals else "-"), ("Enrollment", f"{g.enrollment}"),
            ("Service lines", f"{int(g.service)}"), ("Reputation", f"{int(g.reputation)}"),
        ]
        for i, (label, val) in enumerate(stats):
            cx = 796 + (i % 4) * 118
            cy = 356 + (i // 4) * 64
            text(surf, val, (cx, cy), 26, INK, bold=True)
            text(surf, label, (cx, cy + 32), 13, MUTED)

        ry = g.next_review_year()
        panel(surf, (778, 498, 488, 218))
        if ry:
            r = RUBRICS[ry]
            yrs = ry - g.year
            when = "at the end of this year" if yrs == 0 else f"at the end of Year {ry}"
            text(surf, f"NEXT: {r['name'].upper()}", (796, 510), 12, MUTED, bold=True)
            text(surf, f"{when}  ·  meet {r['need']} of {len(r['criteria'])}", (796, 528), 15, INK)
            for i, (label, key, val, req, ok) in enumerate(g.rubric_status(ry)):
                yy = 556 + i * 25
                check(surf, (808, yy + 9), ok, 8)
                text(surf, label, (824, yy), 15, INK)
                text(surf, f"{fmt_stat(key, val)} / {fmt_stat(key, req)}", (1250, yy), 15,
                     GREEN if ok else MUTED, bold=True, anchor="topright")
        super().draw(surf)


class EventScreen(Screen):
    has_header = True

    def __init__(self, app, event, index, count):
        super().__init__(app)
        self.event = event
        self.index = index
        self.count = count
        self.result = None
        self.choice = None
        n = len(event["options"])
        bh = 78
        top = 800 - 70 - n * (bh + 14)
        for i, opt in enumerate(event["options"]):
            self.buttons.append(Button((420, top + i * (bh + 14), 760, bh), opt["label"],
                                       lambda o=opt: self.pick(o), kind="choice", size=20))

    def pick(self, opt):
        self.choice = opt
        self.result = self.g.apply_choice(self.event, opt)
        self.buttons = [Button((930, 680, 250, 54), "Continue  >", self.app.next_event)]

    def draw(self, surf):
        surf.fill(BG)
        self.header(surf)
        panel(surf, (60, 100, 1160, 660))
        draw_professor(surf, 220, 600, 1.25, self.g, self.t)
        text(surf, f"EVENT {self.index + 1} OF {self.count}  ·  YEAR {self.g.year}", (420, 130), 13, MUTED, bold=True)
        text(surf, self.event["title"], (420, 152), 38, INK, bold=True)
        if self.result is None:
            text_block(surf, self.event["text"], (420, 214), 780, 21, INK)
        else:
            text(surf, "You chose:", (420, 220), 15, MUTED, bold=True)
            yy = text_block(surf, self.choice["label"], (420, 242), 780, 22, INK, bold=True)
            yy = text_block(surf, self.choice["outcome"], (420, yy + 14), 780, 21, INK)
            x, yy = 420, yy + 20
            for chip in self.result:
                w = font(16, True).size(chip)[0] + 24
                if x + w > 1200:
                    x, yy = 420, yy + 42
                good = not (re.search(r"-\$?\d", chip)
                            or any(t in chip for t in ("down", "Not funded", "someone else", "delayed")))
                col = (226, 240, 228) if good else (248, 226, 222)
                pygame.draw.rect(surf, col, (x, yy, w, 34), border_radius=17)
                text(surf, chip, (x + 12, yy + 8), 16, GREEN if good else RED, bold=True)
                x += w + 10
        super().draw(surf)


class ReviewScreen(Screen):
    has_header = True

    def __init__(self, app, report):
        super().__init__(app)
        self.r = report
        self.buttons = [Button((970, 714, 250, 54), "Continue  >", self.app.after_review)]

    def draw(self, surf):
        g, r = self.g, self.r
        surf.fill(BG)
        self.header(surf)
        panel(surf, (60, 90, 700, 690))
        text(surf, "ANNUAL PERFORMANCE REVIEW", (90, 112), 13, MUTED, bold=True)
        text(surf, f"Year {r['year']}", (90, 132), 36, INK, bold=True)
        y = 182
        text(surf, "Item", (90, y), 13, MUTED, bold=True)
        text(surf, "This year", (480, y), 13, MUTED, bold=True, anchor="topright")
        text(surf, "Points", (720, y), 13, MUTED, bold=True, anchor="topright")
        y += 24
        for label, val, pts in r["items"]:
            pygame.draw.line(surf, LINE, (90, y - 5), (720, y - 5))
            text(surf, label, (90, y), 16, INK)
            text(surf, val, (480, y), 16, MUTED, anchor="topright")
            text(surf, f"{pts:+.0f}", (720, y), 16, GREEN if pts > 0 else RED if pts < 0 else MUTED,
                 bold=True, anchor="topright")
            y += 27
        pygame.draw.line(surf, INK, (90, y - 4), (720, y - 4), 2)
        text(surf, "Total score", (90, y + 4), 22, INK, bold=True)
        text(surf, f"{r['score']:.0f}", (720, y + 2), 26, INK, bold=True, anchor="topright")
        y += 46
        for i in range(5):
            star(surf, (104 + i * 36, y + 16), 15, GOLD, filled=i < r["stars"])
        text(surf, STAR_LABELS[r["stars"]], (290, y + 4), 22, INK, bold=True)
        text(surf, f"Merit raise: {r['raise_pct']:.1f}%   (new salary ${g.salary:,.0f})", (90, y + 46), 17, MUTED)
        y += 78
        text(surf, "Comment from the Dean:", (90, y), 14, MUTED, bold=True)
        text_block(surf, f"“{r['comment']}”", (90, y + 20), 640, 18, INK)

        panel(surf, (780, 90, 440, 600))
        draw_professor(surf, 1000, 340, 1.1, g, self.t)
        yy = 370
        for note in r["notes"]:
            yy = text_block(surf, "•  " + note, (800, yy), 400, 16, INK) + 6
        if r["new_badges"]:
            text(surf, "ACHIEVEMENTS UNLOCKED", (800, yy + 8), 12, GOLD, bold=True)
            yy += 32
            for b in r["new_badges"][:5]:
                medal(surf, (818, yy + 18), b, small=True)
                text(surf, b, (842, yy + 8), 17, INK, bold=True)
                yy += 40
        super().draw(surf)


class MilestoneScreen(Screen):
    has_header = True

    def __init__(self, app, result):
        super().__init__(app)
        self.r = result
        label = "See your results  >" if self.g.game_over else "Continue  >"
        self.buttons = [Button((940, 700, 280, 56), label, self.app.after_milestone)]

    def draw(self, surf):
        r, g = self.r, self.g
        surf.fill(BG)
        self.header(surf)
        panel(surf, (60, 90, 1160, 690))
        text(surf, "MILESTONE REVIEW", (100, 116), 13, MUTED, bold=True)
        text(surf, r["name"], (100, 136), 40, INK, bold=True)
        text(surf, f"The committee checks your record against the rubric. You need {r['need']} of "
                   f"{len(r['rows'])} criteria.", (100, 194), 18, MUTED)
        y = 240
        for label, key, val, req, ok in r["rows"]:
            check(surf, (116, y + 14), ok, 12)
            text(surf, label, (142, y + 2), 22, INK)
            text(surf, f"{fmt_stat(key, val)}", (620, y + 2), 22, GREEN if ok else RED, bold=True, anchor="topright")
            text(surf, f"needed {fmt_stat(key, req)}", (640, y + 6), 17, MUTED)
            y += 46
        y += 20
        if r["passed"]:
            outcome = {3: "REAPPOINTED", 6: "TENURE GRANTED", 10: "PROMOTED TO FULL PROFESSOR"}[r["year"]]
            col = GREEN
            sub = {3: "Keep it up. Tenure review is in Year 6.",
                   6: "Level up! You are now an Associate Professor, with job security for life.",
                   10: "Maximum level reached. You have won the Academic Game."}[r["year"]]
        else:
            outcome = {3: "CONDITIONAL REAPPOINTMENT", 6: "TENURE DENIED", 10: "PROMOTION DENIED"}[r["year"]]
            col = RED
            sub = {3: "The committee is concerned. Improve your numbers before the tenure review.",
                   6: "Game over. You have one year to find a new job.",
                   10: "You remain an Associate Professor."}[r["year"]]
        pygame.draw.rect(surf, col, (100, y, 1080, 90), border_radius=12)
        text(surf, outcome, (130, y + 14), 34, (255, 255, 255), bold=True)
        text(surf, sub, (130, y + 56), 18, (255, 255, 255))
        if r["passed"] and r["year"] == 10:
            draw_professor(surf, 1080, 330, 0.9, g, self.t)
        super().draw(surf)


def open_url(url):
    if WEB:
        import platform  # pygbag's platform module exposes the browser window
        platform.window.open(url, "_blank")
    else:
        webbrowser.open(url)


def copy_text(s):
    try:
        if WEB:
            import platform
            platform.window.navigator.clipboard.writeText(s)
        else:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put_text(s)
        return True
    except Exception:
        return False


class FinalScreen(Screen):
    PAGES = 5

    def __init__(self, app):
        super().__init__(app)
        self.page = 0
        self.scroll = 0
        self.anim = 0.0
        self.share_msg = ""
        self.set_buttons()

    def set_buttons(self):
        self.buttons = []
        if self.page > 0:
            self.buttons.append(Button((60, 726, 180, 52), "<  Back", lambda: self.turn(-1), kind="small", size=18))
        if self.page < self.PAGES - 1:
            labels = ["What really happened  >", "Behind the scenes  >", "Discuss  >", "Share results  >"]
            self.buttons.append(Button((940, 726, 280, 52), labels[self.page], lambda: self.turn(1)))
        else:
            self.buttons.append(Button((940, 726, 280, 52), "Play again", self.app.new_game))
            text_q, url_q = quote(self.share_text()), quote(GAME_URL)
            links = [
                ("Share on X", f"https://twitter.com/intent/tweet?text={text_q}&url={url_q}"),
                ("Bluesky", f"https://bsky.app/intent/compose?text={quote(self.share_text() + ' ' + GAME_URL)}"),
                ("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={url_q}"),
                ("LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={url_q}"),
            ]
            for i, (label, url) in enumerate(links):
                self.buttons.append(Button((160 + i * 196, 620, 180, 46), label,
                                           lambda u=url: self.share(u), size=17))
            self.buttons.append(Button((160 + 4 * 196, 620, 176, 46), "Copy text", self.copy, kind="small", size=17))

    def share_text(self):
        g = self.g
        if g.denied:
            outcome = "was denied tenure"
        else:
            outcome = f"finished as {g.title}"
        return (f"I played Winning the Academic Game and {outcome} with a {int(g.game_pct() * 100)}% game score, "
                f"but only {int(g.real_impact() * 100)}% real impact. I'm \"{g.archetype()[0]}.\" "
                f"Can you beat the system?")

    def share(self, url):
        open_url(url)
        self.share_msg = "Opened in a new tab. If nothing appeared, allow pop-ups or use Copy text."

    def copy(self):
        ok = copy_text(self.share_text() + " " + GAME_URL)
        self.share_msg = "Copied! Paste it anywhere." if ok else "Couldn't copy here. Select the text above instead."

    def turn(self, d):
        self.page += d
        self.scroll = 0
        self.anim = 0.0
        self.set_buttons()

    def handle(self, e):
        if e.type == pygame.MOUSEWHEEL and self.page == 2:
            self.scroll = max(0, self.scroll - e.y * 30)
        super().handle(e)

    def update(self, dt):
        super().update(dt)
        self.anim = min(1.0, self.anim + dt * 0.7)

    def draw(self, surf):
        surf.fill(BG)
        pages = [self.page_scoreboard, self.page_reveal, self.page_behind, self.page_discuss, self.page_share]
        pages[self.page](surf)
        for i in range(self.PAGES):
            pygame.draw.circle(surf, INK if i == self.page else LINE,
                               (W // 2 - (self.PAGES - 1) * 10 + i * 20, 752), 5)
        super().draw(surf)

    def page_scoreboard(self, surf):
        g = self.g
        text(surf, "FINAL SCOREBOARD", (W // 2, 40), 14, MUTED, bold=True, anchor="midtop")
        title = "Career over: tenure denied" if g.denied else f"Career complete: {g.title}"
        text(surf, title, (W // 2, 62), 40, INK, bold=True, anchor="midtop")
        panel(surf, (60, 130, 1160, 580))
        draw_professor(surf, 230, 560, 1.4, g, self.t)
        stats = [
            ("Publications", f"{g.pubs}"), ("Citations", f"{g.citations:,}"), ("h-index", f"{g.h}"),
            ("Grant dollars", fmt_money(g.grant_dollars)), ("Avg teaching eval", f"{g.eval_avg:.2f}"),
            ("Final salary", f"${g.salary:,.0f}"), ("Service lines", f"{int(g.service)}"),
            ("Reputation", f"{int(g.reputation)}"), ("Badges earned", f"{len(g.badges)}"),
        ]
        for i, (label, val) in enumerate(stats):
            x = 440 + (i % 3) * 250
            y = 170 + (i // 3) * 96
            text(surf, val, (x, y), 40, INK, bold=True)
            text(surf, label, (x, y + 48), 16, MUTED)
        y = 470
        text(surf, "TOTAL GAME SCORE", (440, y), 13, MUTED, bold=True)
        text(surf, f"{g.game_score():,.0f} points", (440, y + 18), 34, INK, bold=True)
        bar(surf, (440, y + 66, 700, 22), g.game_pct() * self.anim, DARK)
        text(surf, f"{int(g.game_pct() * 100)}% of an outstanding record", (440, y + 96), 16, MUTED)
        x = 440
        for b in g.badges[:12]:
            medal(surf, (x + 14, 678), b, small=True)
            x += 40
        text(surf, "By every number your university tracks, this is how you did.",
             (W // 2, 140), 16, MUTED, anchor="midtop")

    def page_reveal(self, surf):
        g = self.g
        name, line = g.archetype()
        text(surf, "BUT WAS THAT THE JOB?", (W // 2, 40), 14, MUTED, bold=True, anchor="midtop")
        text(surf, name, (W // 2, 62), 44, INK, bold=True, anchor="midtop")
        text(surf, line, (W // 2, 118), 20, MUTED, anchor="midtop")

        panel(surf, (60, 160, 560, 550))
        text(surf, "WHAT THE GAME MEASURED", (90, 184), 13, MUTED, bold=True)
        text(surf, "Your game score", (90, 214), 22, INK, bold=True)
        bar(surf, (90, 252, 500, 36), g.game_pct() * self.anim, DARK)
        text(surf, f"{int(g.game_pct() * 100)}%", (590, 296), 26, INK, bold=True, anchor="topright")
        text_block(surf, "Publications, citations, grants, evaluations, enrollment, CV lines, responsiveness. "
                         "Counted every year, used for raises, tenure, and promotion.", (90, 340), 500, 17, MUTED)
        avg = g.average_alloc()
        counted = sum(avg[k] for k in SCORE_CHASING)
        total = sum(avg.values()) or 1
        text_block(surf, f"On average, {counted:.0f} of your {total:.0f} weekly hours went to activities "
                         f"built to score points.", (90, 440), 500, 20, INK, bold=True)

        panel(surf, (640, 160, 580, 550))
        text(surf, "WHAT THE JOB WAS FOR (HIDDEN UNTIL NOW)", (670, 184), 13, MUTED, bold=True)
        hp = g.hidden_pcts()
        rows = [
            ("knowledge", "Meaningful knowledge created", self.knowledge_note(hp["knowledge"])),
            ("learning", "What students actually learned", self.learning_note(hp["learning"])),
            ("real_service", "Real service to people", self.service_note(hp["real_service"])),
            ("wellbeing", "Your own wellbeing", self.wellbeing_note(hp["wellbeing"])),
        ]
        y = 214
        for key, label, note in rows:
            text(surf, label, (670, y), 20, INK, bold=True)
            text(surf, f"{int(hp[key] * 100)}%", (1190, y), 20, HIDDEN_COLORS[key], bold=True, anchor="topright")
            bar(surf, (670, y + 30, 520, 18), hp[key] * self.anim, HIDDEN_COLORS[key])
            text(surf, note, (670, y + 56), 15, MUTED)
            y += 118

    @staticmethod
    def knowledge_note(p):
        return ("Work people will still be building on in 20 years." if p > 0.7 else
                "Some lasting ideas, many forgettable papers." if p > 0.35 else
                "Lots of papers. Very few new ideas.")

    @staticmethod
    def learning_note(p):
        return ("Your students left able to do hard things." if p > 0.7 else
                "Students learned some things, and liked you." if p > 0.35 else
                "Students loved the class. They don't remember it.")

    @staticmethod
    def service_note(p):
        return ("You fixed real problems that nobody gave you credit for." if p > 0.6 else
                "Some real help, some committee theater." if p > 0.3 else
                "Impressive titles. Few people were actually helped.")

    @staticmethod
    def wellbeing_note(p):
        return ("You had a life outside work." if p > 0.7 else
                "Tired, but holding on." if p > 0.4 else
                "Burned out. The game took everything.")

    def page_behind(self, surf):
        g = self.g
        text(surf, "BEHIND THE SCENES", (W // 2, 40), 14, MUTED, bold=True, anchor="midtop")
        text(surf, "What your choices really did", (W // 2, 62), 40, INK, bold=True, anchor="midtop")
        clip = pygame.Rect(60, 130, 1160, 580)
        panel(surf, clip)

        # Your build: average weekly hours per activity
        avg = g.average_alloc()
        text(surf, "YOUR BUILD (AVG HRS/WEEK)", (90, 150), 13, MUTED, bold=True)
        y = 176
        for act in ACTIVITIES:
            v = avg[act["key"]]
            text(surf, act["name"], (90, y), 15, INK)
            bar(surf, (300, y + 3, 160, 12), v / MAX_PER_ACTIVITY, CAT_COLORS[act["cat"]])
            text(surf, f"{v:.0f}", (470, y), 15, MUTED)
            y += 46

        # Event reveals, scrollable
        surf.set_clip(pygame.Rect(520, 140, 690, 560))
        y = 150 - self.scroll
        if not g.reveals:
            text(surf, "No events recorded.", (540, y), 18, MUTED)
        for year, title, label, reveal in g.reveals:
            text(surf, f"YEAR {year}  ·  {title.upper()}", (540, y), 12, MUTED, bold=True)
            y = text_block(surf, f"You chose: {label}", (540, y + 18), 650, 16, INK, bold=True)
            y = text_block(surf, reveal, (540, y + 2), 650, 16, (70, 70, 84)) + 16
        content_h = y + self.scroll - 150
        self.scroll = min(self.scroll, max(0, content_h - 540))
        surf.set_clip(None)
        if content_h > 560:
            text(surf, "scroll for more", (1200, 690), 13, MUTED, anchor="bottomright")

    def page_discuss(self, surf):
        text(surf, "FOR DISCUSSION", (W // 2, 40), 14, MUTED, bold=True, anchor="midtop")
        text(surf, "Goodhart's Law", (W // 2, 62), 44, INK, bold=True, anchor="midtop")
        text(surf, "“When a measure becomes a target, it ceases to be a good measure.”",
             (W // 2, 124), 22, MUTED, anchor="midtop")
        panel(surf, (110, 180, 1060, 520))
        qs = [
            "Which choices felt obviously right in the moment? Which looked different after the reveal?",
            "Every metric in this game measures something real. Where exactly did each one stop "
            "matching the thing it was supposed to measure?",
            "Who designed the scoring rules, and what were they trying to learn about professors?",
            "Replay twice: once to max out promotion and salary, once to max out learning and knowledge. "
            "Compare the two builds. How much do they overlap?",
            "Where else are you playing a metric: GPA, test scores, social media, résumé lines?",
            "If you could change one scoring rule so the winning strategy is also the good strategy, what would it be?",
        ]
        y = 210
        for i, q in enumerate(qs, 1):
            pygame.draw.circle(surf, DARK, (156, y + 14), 16)
            text(surf, str(i), (156, y + 14), 17, (255, 255, 255), bold=True, anchor="center")
            y = text_block(surf, q, (190, y + 2), 940, 19, INK) + 22


    def page_share(self, surf):
        g = self.g
        text(surf, "SHARE", (W // 2, 30), 14, MUTED, bold=True, anchor="midtop")
        text(surf, "Your results vs. reality", (W // 2, 50), 40, INK, bold=True, anchor="midtop")
        card = pygame.Rect(160, 110, 960, 490)
        panel(surf, card)

        # Top: what the game saw
        text(surf, "THE GAME", (190, 130), 13, MUTED, bold=True)
        title = "Tenure denied" if g.denied else g.title
        text(surf, title, (190, 150), 30, INK, bold=True)
        stats = [(f"{g.pubs}", "papers"), (f"{g.h}", "h-index"), (fmt_money(g.grant_dollars), "grants"),
                 (f"{g.eval_avg:.2f}", "avg eval"), (f"${g.salary / 1000:.0f}K", "salary"),
                 (f"{len(g.badges)}", "badges")]
        for i, (val, label) in enumerate(stats):
            x = 190 + i * 150
            text(surf, val, (x, 196), 28, INK, bold=True)
            text(surf, label, (x, 230), 14, MUTED)
        text(surf, "Game score", (190, 266), 16, INK, bold=True)
        bar(surf, (330, 268, 680, 18), g.game_pct() * self.anim, DARK)
        text(surf, f"{int(g.game_pct() * 100)}%", (1090, 264), 20, INK, bold=True, anchor="topright")

        pygame.draw.line(surf, LINE, (190, 312), (1090, 312), 2)

        # Bottom: what actually happened
        name, line = g.archetype()
        text(surf, "REALITY", (190, 330), 13, MUTED, bold=True)
        text(surf, name, (190, 350), 30, INK, bold=True)
        text(surf, line, (190, 390), 16, MUTED)
        hp = g.hidden_pcts()
        rows = [("knowledge", "Knowledge created"), ("learning", "Student learning"),
                ("real_service", "Real service"), ("wellbeing", "Wellbeing")]
        for i, (key, label) in enumerate(rows):
            x = 190 + (i % 2) * 460
            y = 428 + (i // 2) * 52
            text(surf, label, (x, y), 15, INK, bold=True)
            text(surf, f"{int(hp[key] * 100)}%", (x + 420, y), 15, HIDDEN_COLORS[key], bold=True, anchor="topright")
            bar(surf, (x, y + 22, 420, 14), hp[key] * self.anim, HIDDEN_COLORS[key])
        text(surf, f"Real impact: {int(g.real_impact() * 100)}%", (190, 540), 22, INK, bold=True)
        text(surf, GAME_URL, (1090, 548), 14, MUTED, anchor="topright")

        if self.share_msg:
            text(surf, self.share_msg, (W // 2, 680), 15, MUTED, anchor="midtop")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Winning the Academic Game")
        self.surf = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.preview = Career()
        self.career = self.preview
        self.screen = TitleScreen(self)
        self.events = []
        self.event_i = 0
        self.pending_milestone = None

    def new_game(self):
        self.career = Career()
        self.screen = AllocateScreen(self)

    def start_year(self):
        self.events = self.career.draw_events(EVENTS, n=2)
        self.event_i = 0
        self.show_event()

    def show_event(self):
        if self.event_i < len(self.events):
            self.screen = EventScreen(self, self.events[self.event_i], self.event_i, len(self.events))
        else:
            report = self.career.run_year()
            self.screen = ReviewScreen(self, report)

    def next_event(self):
        self.event_i += 1
        self.show_event()

    def after_review(self):
        result = self.career.finish_year()
        if result:
            self.screen = MilestoneScreen(self, result)
        else:
            self.after_milestone()

    def after_milestone(self):
        if self.career.game_over:
            self.screen = FinalScreen(self)
        else:
            self.screen = AllocateScreen(self)

    async def run(self):
        # async so the same loop runs on the desktop and in the browser (pygbag)
        web = sys.platform == "emscripten"
        while True:
            dt = self.clock.tick(FPS) / 1000
            for e in pygame.event.get():
                quit_key = e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not web
                if e.type == pygame.QUIT or quit_key:
                    pygame.quit()
                    return
                self.screen.handle(e)
            self.screen.update(dt)
            self.screen.draw(self.surf)
            pygame.display.flip()
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(App().run())
