"""Shared drawing toolkit for Winning the Academic Game: colors, text, widgets,
the professor figure, and browser helpers. Used by both the desktop and the
phone layouts.
"""

import base64
import math
import os
import re
import sys
import webbrowser

import pygame

from model import BASE_HOURS, YEARS

W, H = 1280, 800  # desktop (wide) layout
PW, PH = 500, 890  # phone (portrait) layout
GAME_URL = "https://fredpoole.github.io/academic-game/"
READINGS = [
    ("Read Strathern (1997)", "https://www.cambridge.org/core/journals/european-review/article/"
                              "improving-ratings-audit-in-the-british-university-system/FC2EE640C0C44E3DB87C29FB666E9AAB"),
    ("Read Nguyen (2024)", "https://jesp.org/paper/36346f73-90e0-81ae-bf22-ebd3754e0a2f"),
]
WEB = sys.platform == "emscripten"

# On phones, the browser sends taps to the game without moving the "mouse"
# first, so every tap arrives at the position of the first one. This script
# records where each pointer or finger actually lands (as a fraction of the
# canvas) so the game can use the real position, and adds up vertical finger
# swipes so long pages can scroll. It also decides whether this is a phone,
# and on a touch device goes fullscreen on the first tap, where allowed.
POINTER_JS = """(() => {
  if (window.agHooked) return;
  window.agHooked = true;
  window.agPX = -1; window.agPY = -1; window.agScroll = 0;
  const q = new URLSearchParams(location.search);
  window.agTouch = navigator.maxTouchPoints > 0 || 'ontouchstart' in window
    || window.matchMedia('(pointer: coarse)').matches;
  // A screen under 600px on its short side is a phone, whatever it reports about touch.
  window.agPhone = q.has('phone') || (!q.has('desktop') && Math.min(screen.width, screen.height) < 600);
  document.body.style.background = '#f6f2e9';
  let lastY = null;
  const canvasRect = () => { const c = document.getElementById('canvas'); return c && c.getBoundingClientRect(); };
  const rec = (x, y) => {
    const r = canvasRect();
    if (!r) return;
    window.agPX = (x - r.left) / r.width;
    window.agPY = (y - r.top) / r.height;
  };
  window.addEventListener('pointerdown', e => rec(e.clientX, e.clientY), true);
  window.addEventListener('pointermove', e => rec(e.clientX, e.clientY), true);
  window.addEventListener('touchstart', e => {
    const t = e.touches[0];
    if (t) { rec(t.clientX, t.clientY); lastY = t.clientY; }
  }, true);
  window.addEventListener('touchmove', e => {
    const t = e.touches[0], r = canvasRect();
    if (t && r && lastY !== null) { window.agScroll += (lastY - t.clientY) / r.height; lastY = t.clientY; }
  }, true);
  window.addEventListener('touchend', () => { lastY = null; }, true);
  if (window.agTouch) {
    window.addEventListener('touchend', () => {
      const d = document.documentElement;
      if (d.requestFullscreen && !document.fullscreenElement) d.requestFullscreen().catch(() => {});
    }, {once: true, capture: true});
  }
})()"""

_pointer = None  # last real pointer position on the web, in game coordinates


def set_pointer(pos):
    global _pointer
    _pointer = pos


def mouse_pos():
    return _pointer or pygame.mouse.get_pos()
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

SKIN = {"White": (240, 208, 176), "Black": (122, 82, 56), "Brown": (192, 138, 98), "Asian": (234, 198, 160)}
HAIR = {"White": (95, 66, 44), "Black": (34, 28, 26), "Brown": (44, 32, 28), "Asian": (26, 22, 24)}
PRIDE = [(228, 3, 3), (255, 140, 0), (255, 237, 0), (0, 128, 38), (36, 64, 142), (115, 41, 130)]


def draw_professor(surf, cx, base_y, s, g, t=0.0):
    """A simple stick-figure professor. Ages, tires, and piles up papers."""
    ident = g.identity
    skin = SKIN[ident["race"]]
    gender = ident["gender"]
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
    accent = [(150, 40, 40), (40, 70, 150), (180, 140, 30)][g.title_level]
    if gender == "Man":
        pygame.draw.polygon(surf, accent, [(neck[0] - 3 * s, neck[1] + 5 * s), (neck[0] + 3 * s, neck[1] + 5 * s),
                                           (neck[0] + 4 * s, neck[1] + 26 * s), (neck[0], neck[1] + 31 * s),
                                           (neck[0] - 4 * s, neck[1] + 26 * s)])
    elif gender == "Woman":
        pygame.draw.polygon(surf, accent, [(neck[0] - 6 * s, neck[1] + 4 * s), (neck[0] + 6 * s, neck[1] + 4 * s),
                                           (neck[0], neck[1] + 20 * s)])
        pygame.draw.circle(surf, GOLD, (int(neck[0]), int(neck[1] + 14 * s)), max(2, int(3 * s)))
    else:
        bow = (neck[0], neck[1] + 7 * s)
        pygame.draw.polygon(surf, accent, [(bow[0], bow[1]), (bow[0] - 8 * s, bow[1] - 5 * s), (bow[0] - 8 * s, bow[1] + 5 * s)])
        pygame.draw.polygon(surf, accent, [(bow[0], bow[1]), (bow[0] + 8 * s, bow[1] - 5 * s), (bow[0] + 8 * s, bow[1] + 5 * s)])
    if ident["orientation"] != "Straight" and ident["out"]:
        pin = (int(neck[0] - 12 * s), int(neck[1] + 16 * s))
        for i, col in enumerate(PRIDE):
            pygame.draw.rect(surf, col, (pin[0] - 4 * s, pin[1] - 5 * s + i * 1.7 * s, 8 * s, 1.8 * s))
    # Arms: up when energized, drooping when exhausted
    lift = (energy - 50) / 50 * 20 * s
    for side in (-1, 1):
        sh = (neck[0] + side * 18 * s, neck[1] + 8 * s)
        elbow = (sh[0] + side * 14 * s, sh[1] + 26 * s - lift * 0.5)
        hand = (elbow[0] + side * 6 * s, elbow[1] + 24 * s - lift * 1.6)
        pygame.draw.line(surf, jacket, sh, elbow, max(3, int(7 * s)))
        pygame.draw.line(surf, jacket, elbow, hand, max(3, int(7 * s)))
        pygame.draw.circle(surf, skin, hand, int(5 * s))
    # Hair goes grey as the career goes on
    base, grey = HAIR[ident["race"]], (200, 200, 205)
    hair = tuple(int(b + (gr - b) * years) for b, gr in zip(base, grey))
    # Longer styles are drawn behind the head
    if gender == "Woman" and ident["race"] == "Black":
        pygame.draw.circle(surf, hair, (head[0], head[1] - 6 * s), int(34 * s))
    elif gender == "Woman":
        pygame.draw.ellipse(surf, hair, (head[0] - 30 * s, head[1] - 30 * s, 60 * s, 78 * s))
    elif gender == "Non-binary":
        pygame.draw.ellipse(surf, hair, (head[0] - 29 * s, head[1] - 30 * s, 58 * s, 54 * s))
    # Head
    pygame.draw.circle(surf, skin, head, int(24 * s))
    if gender == "Man":
        hair_rect = pygame.Rect(head[0] - 25 * s, head[1] - 27 * s, 50 * s, 30 * s)
        pygame.draw.arc(surf, hair, hair_rect, math.radians(10 + years * 50), math.radians(170 - years * 50),
                        max(3, int(9 * s)))
        pygame.draw.circle(surf, hair, (head[0] - 23 * s, head[1] - 2 * s), int(6 * s))
        pygame.draw.circle(surf, hair, (head[0] + 23 * s, head[1] - 2 * s), int(6 * s))
    elif not (gender == "Woman" and ident["race"] == "Black"):
        # Fringe across the top of the head
        pygame.draw.arc(surf, hair, (head[0] - 25 * s, head[1] - 27 * s, 50 * s, 34 * s),
                        math.radians(15), math.radians(165), max(3, int(10 * s)))
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
        # Small buttons get a slightly larger invisible tap area for fingers
        hit = self.rect.inflate(16, 10) if self.kind == "small" else self.rect
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and hit.collidepoint(e.pos):
            if self.enabled():
                self.on_click()
            return True
        return False

    def draw(self, surf):
        hover = self.rect.collidepoint(mouse_pos())
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


class Toggle(Button):
    """A button that shows whether its option is selected."""

    def __init__(self, rect, label, on_click, selected, size=17, enabled=None):
        super().__init__(rect, label, on_click, kind="small", size=size, enabled=enabled)
        self.selected = selected

    def draw(self, surf):
        on = self.enabled()
        hover = self.rect.collidepoint(mouse_pos())
        if not on:
            pygame.draw.rect(surf, (244, 241, 235), self.rect, border_radius=10)
            text(surf, self.label, self.rect.center, self.size, (195, 190, 182), anchor="center")
        elif self.selected():
            pygame.draw.rect(surf, DARK, self.rect, border_radius=10)
            text(surf, self.label, self.rect.center, self.size, (255, 255, 255), bold=True, anchor="center")
        else:
            pygame.draw.rect(surf, (255, 255, 255) if not hover else (246, 240, 226), self.rect, border_radius=10)
            pygame.draw.rect(surf, DARK if hover else LINE, self.rect, 2, border_radius=10)
            text(surf, self.label, self.rect.center, self.size, INK, anchor="center")


def open_url(url):
    if WEB:
        import platform  # pygbag's platform module exposes the browser window
        platform.window.open(url, "_blank")
    else:
        webbrowser.open(url)


def save_image(surface, filename):
    """Save a surface as a PNG: a browser download on the web, ~/Downloads on desktop.
    Returns a message for the player."""
    if WEB:
        import platform
        tmp = "/tmp/" + filename
        pygame.image.save(surface, tmp)
        with open(tmp, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        platform.window.eval(
            "(()=>{const a=document.createElement('a');"
            f"a.href='data:image/png;base64,{data}';a.download='{filename}';"
            "document.body.appendChild(a);a.click();a.remove();})()")
        return "Image downloaded. Attach it to your post!"
    folder = os.path.expanduser("~/Downloads")
    path = os.path.join(folder if os.path.isdir(folder) else ".", filename)
    pygame.image.save(surface, path)
    return f"Image saved to {path}"


def chip_is_good(chip):
    return not (re.search(r"-\$?\d", chip)
                or any(t in chip for t in ("down", "Not funded", "someone else", "delayed")))


def draw_chips(surf, chips, x0, y, max_x, size=16):
    """Green/red pills listing what a choice changed. Returns the bottom y."""
    h, gap = round(size * 2.1), round(size * 0.6)
    x = x0
    for chip in chips:
        w = font(size, True).size(chip)[0] + int(size * 1.5)
        if x + w > max_x:
            x, y = x0, y + h + gap - 2
        good = chip_is_good(chip)
        pygame.draw.rect(surf, (226, 240, 228) if good else (248, 226, 222), (x, y, w, h), border_radius=h // 2)
        text(surf, chip, (x + int(size * 0.75), y + (h - font(size, True).get_height()) // 2 + 1), size,
             GREEN if good else RED, bold=True)
        x += w + gap
    return y + h
