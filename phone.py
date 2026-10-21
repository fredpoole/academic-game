"""Phone (portrait) screens for Winning the Academic Game.

Same game, same rules, laid out tall and narrow with bigger text and finger-
sized buttons. Each screen reuses the logic of its desktop counterpart in
screens.py and only changes where things are drawn.
"""

from urllib.parse import quote

import pygame

from identity import GENDERS, ORIENTATIONS, RACES, RULES, describe
from model import (ACTIVITIES, BASE_HOURS, MAX_HOURS, MAX_PER_ACTIVITY, MIN_CLASS_HOURS, RUBRICS,
                   SCORE_CHASING, STAR_LABELS, STEP, Career)
from screens import EventScreen, FinalScreen, IdentityScreen, Screen, identity_tiles
from ui import *  # noqa: F401,F403  (shared toolkit: colors, text helpers, widgets)

M = 16  # side margin
CW = PW - 2 * M  # content width
NAV_Y = PH - 62  # bottom button row

TABS = [("Research", ["Research"]), ("Teaching", ["Teaching"]), ("Service", ["Service"]),
        ("Other", ["Visibility", "Admin"])]

SHORT_LABELS = {"Publications": "Papers", "Average teaching evaluation": "Avg eval",
                "Service lines on CV": "Service", "External grants won": "Grants",
                "Grant dollars": "Grant $", "h-index": "h-index", "Reputation": "Reputation"}


def phone_header(screen, surf):
    """Dark top bar: year and title, key stats, salary and energy, Restart."""
    g = screen.g
    pygame.draw.rect(surf, DARK, (0, 0, PW, 112))
    r = text(surf, f"Year {g.year} of 10", (M, 12), 26, (255, 255, 255), bold=True)
    text(surf, g.title, (r.right + 10, 19), 17, (180, 182, 200))
    stats = (f"{g.pubs} papers  ·  {g.citations:,} cites  ·  h {g.h}  ·  {fmt_money(g.grant_dollars)}"
             + (f"  ·  eval {g.eval_avg:.2f}" if g.evals else ""))
    text(surf, stats, (M, 50), 16, (200, 202, 216))
    text(surf, f"${g.salary:,.0f}", (M, 80), 18, (255, 255, 255), bold=True)
    ecol = GREEN if g.energy >= 60 else GOLD if g.energy >= 30 else RED
    text(surf, "Energy", (150, 82), 15, (180, 182, 200))
    bar(surf, (210, 86, 230, 12), g.energy / 100, ecol, bg=(70, 72, 90))
    text(surf, f"{int(g.energy)}", (448, 80), 16, (255, 255, 255))
    if screen.restart_armed > 0:
        pygame.draw.rect(surf, RED, screen.restart.rect, border_radius=8)
        text(surf, "Confirm?", screen.restart.rect.center, 16, (255, 255, 255), bold=True, anchor="center")
    else:
        screen.restart.draw(surf)


def place_restart(screen):
    screen.restart.rect = pygame.Rect(PW - M - 98, 10, 98, 34)
    screen.restart.size = 16


# ---------------------------------------------------------------------------
# Title and character selection
# ---------------------------------------------------------------------------

class PhoneTitle(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [Button((M, NAV_Y, CW, 54), "Begin your career", self.app.new_game, size=22)]

    def draw(self, surf):
        surf.fill(BG)
        text(surf, "WINNING THE", (PW // 2, 36), 22, MUTED, bold=True, anchor="midtop")
        text(surf, "Academic Game", (PW // 2, 66), 50, INK, bold=True, anchor="midtop")
        draw_professor(surf, PW // 2 + 30, 330, 1.05, self.app.preview, self.t)
        intro = ("You are a newly hired Assistant Professor. Your job is to create knowledge, educate students, "
                 "and serve your university and community.\n\n"
                 "Nobody can measure those things directly, so your university counts what it can: papers, "
                 "citations, grants, teaching evaluations, enrollment, and lines on your CV. Score high enough "
                 "and you level up: tenure in Year 6, Full Professor in Year 10.\n\n"
                 "Each year, split your work week and make choices as events come up. Can you win the game?")
        text_block(surf, intro, (M + 8, 356), CW - 16, 20, INK, spacing=1.32)
        super().draw(surf)


class PhoneIdentity(IdentityScreen):
    ROWS = [("gender", "Gender", 300), ("race", "Race / ethnicity", 396),
            ("orientation", "Sexual orientation", 492), ("out", "Out at work?", 648)]

    def __init__(self, app):
        Screen.__init__(self, app)
        self.sel = dict(app.identity)
        self.preview = Career(identity=self.sel)
        options = {"gender": GENDERS, "race": RACES, "orientation": ORIENTATIONS, "out": [True, False]}
        for key, _, y in self.ROWS:
            opts = options[key]
            cols = 3 if key == "gender" else 4 if key == "race" else 2
            w = (CW - (cols - 1) * 8) // cols
            for i, opt in enumerate(opts):
                label = ("Yes" if opt else "No") if key == "out" else opt
                enabled = (lambda: self.sel["orientation"] != "Straight") if key == "out" else None
                x = M + (i % cols) * (w + 8)
                yy = y + 30 + (i // cols) * 60
                self.buttons.append(Toggle((x, yy, w, 52), label, lambda k=key, o=opt: self.pick(k, o),
                                           lambda k=key, o=opt: self.sel[k] == o, size=19, enabled=enabled))
        self.buttons.append(Button((M, NAV_Y, 150, 54), "Randomize", self.randomize, kind="small", size=19))
        self.buttons.append(Button((M + 162, NAV_Y, CW - 162, 54), "Start your career  >",
                                   lambda: self.app.begin_career(self.sel), size=21))

    def draw(self, surf):
        surf.fill(BG)
        text(surf, "STEP 1", (M, 20), 15, MUTED, bold=True)
        text(surf, "Choose your professor", (M, 40), 32, INK, bold=True)
        panel(surf, (M, 88, CW, 196))
        draw_professor(surf, 120, 270, 0.88, self.preview, self.t)
        text_block(surf, describe(self.sel), (230, 120), CW - 230, 20, INK, bold=True)
        text_block(surf, "Your identity changes how the system responds to your work, not what you can do. "
                         "Effects follow published research and are revealed at the end.",
                   (230, 186), CW - 230, 14, MUTED)
        for key, label, y in self.ROWS:
            off = key == "out" and self.sel["orientation"] == "Straight"
            text(surf, label, (M, y), 19, MUTED if off else INK, bold=True)
        Screen.draw(self, surf)


# ---------------------------------------------------------------------------
# Planning the year
# ---------------------------------------------------------------------------

class PhoneAllocate(Screen):
    has_header = True
    ROW_Y = 300
    ROW_H = 90

    def __init__(self, app):
        super().__init__(app)
        place_restart(self)
        self.tab = 0
        self.tab_buttons = []
        tw = (CW - 3 * 6) // 4
        for i, (name, _) in enumerate(TABS):
            b = Toggle((M + i * (tw + 6), 244, tw, 48), name, lambda i=i: self.set_tab(i),
                       lambda i=i: self.tab == i, size=17)
            self.tab_buttons.append(b)
        self.start = Button((M, NAV_Y, CW, 54), "Start the year  >", self.app.start_year,
                            enabled=lambda: self.g.alloc_valid(), size=22)
        self.set_tab(0)

    def acts(self):
        return [a for a in ACTIVITIES if a["cat"] in TABS[self.tab][1]]

    def set_tab(self, i):
        self.tab = i
        self.buttons = list(self.tab_buttons) + [self.start]
        for r, act in enumerate(self.acts()):
            y = self.ROW_Y + r * self.ROW_H
            k = act["key"]
            self.buttons.append(Button((PW - M - 52 - 62 - 52, y + 18, 52, 52), "-",
                                       lambda k=k: self.adjust(k, -STEP), kind="small", size=26,
                                       enabled=lambda k=k: self.g.alloc[k] > 0))
            self.buttons.append(Button((PW - M - 52, y + 18, 52, 52), "+", lambda k=k: self.adjust(k, STEP),
                                       kind="small", size=26,
                                       enabled=lambda k=k: self.g.alloc[k] < MAX_PER_ACTIVITY
                                       and self.g.total_hours() + STEP <= MAX_HOURS))

    def adjust(self, key, d):
        self.g.alloc[key] = max(0, min(MAX_PER_ACTIVITY, self.g.alloc[key] + d))

    def draw(self, surf):
        g = self.g
        surf.fill(BG)
        phone_header(self, surf)

        # This year's plan
        panel(surf, (M, 120, CW, 116))
        draw_professor(surf, 70, 226, 0.5, g, self.t)
        text(surf, "THIS YEAR'S PLAN", (150, 130), 14, MUTED, bold=True)
        total = g.total_hours()
        r = text(surf, f"{total}", (150, 146), 40, INK if total <= BASE_HOURS else RED, bold=True)
        text(surf, f"/ {BASE_HOURS} hrs", (r.right + 8, 166), 18, MUTED)
        drop = round((total - BASE_HOURS) * 2.2 - 5)
        if g.class_hours() < MIN_CLASS_HOURS:
            msg, col = f"Classes need {MIN_CLASS_HOURS}+ hrs of rigorous or crowd-pleasing teaching.", RED
        elif total > BASE_HOURS and drop > 0:
            msg, col = f"Overtime! Energy will drop ~{drop}.", RED
        elif total > BASE_HOURS:
            msg, col = "Overtime: you'll barely recover energy.", GOLD
        elif total < BASE_HOURS:
            msg, col = "Under 40 hours: you'll recover energy.", GREEN
        elif g.energy < 40:
            msg, col = f"Exhausted: output at {int(g.efficiency() * 100)}%.", RED
        else:
            msg, col = "Split your 40 hours across the tabs below.", MUTED
        text_block(surf, msg, (150, 196), CW - 140, 15, col, spacing=1.2)

        # Tabs show how many hours each one holds
        for b, (name, cats) in zip(self.tab_buttons, TABS):
            hrs = sum(g.alloc[a["key"]] for a in ACTIVITIES if a["cat"] in cats)
            b.label = f"{name} {hrs}"

        for r, act in enumerate(self.acts()):
            y = self.ROW_Y + r * self.ROW_H
            col = CAT_COLORS[act["cat"]]
            pygame.draw.rect(surf, PANEL, (M, y, CW, self.ROW_H - 8), border_radius=12)
            pygame.draw.rect(surf, col, (M, y, 6, self.ROW_H - 8), border_radius=3)
            name_w = PW - M - 52 - 62 - 52 - (M + 18) - 8
            yy = text_block(surf, act["name"], (M + 18, y + 8), name_w, 20, INK, bold=True, spacing=1.15)
            text_block(surf, act["pitch"], (M + 18, yy + 2), name_w, 14, MUTED, spacing=1.2)
            text(surf, f"{g.alloc[act['key']]}", (PW - M - 52 - 31, y + 44), 28, INK, bold=True, anchor="center")

        # Next review
        ry = g.next_review_year()
        panel(surf, (M, 672, CW, 146))
        if ry:
            rb = RUBRICS[ry]
            when = "this year" if ry == g.year else f"Year {ry}"
            text(surf, f"NEXT: {rb['name'].upper()} ({when}) · NEED {rb['need']} OF {len(rb['criteria'])}",
                 (M + 14, 682), 13, MUTED, bold=True)
            for i, (label, key, val, req, ok) in enumerate(g.rubric_status(ry)):
                x = M + 14 + (i % 2) * (CW // 2)
                y = 708 + (i // 2) * 34
                check(surf, (x + 10, y + 11), ok, 10)
                text(surf, SHORT_LABELS.get(label, label), (x + 26, y), 18, INK)
                text(surf, f"{fmt_stat(key, val)}/{fmt_stat(key, req)}", (x + CW // 2 - 28, y), 18,
                     GREEN if ok else MUTED, bold=True, anchor="topright")
        super().draw(surf)


# ---------------------------------------------------------------------------
# Events, reviews, milestones
# ---------------------------------------------------------------------------

class PhoneEvent(EventScreen):
    has_header = True

    def __init__(self, app, event, index, count):
        Screen.__init__(self, app)
        place_restart(self)
        self.event = event
        self.index = index
        self.count = count
        self.result = None
        self.choice = None
        heights = [max(64, len(wrap(o["label"], 20, CW - 64)) * 27 + 30) for o in event["options"]]
        y = NAV_Y + 54 - sum(heights) - 10 * (len(heights) - 1)
        for opt, h in zip(event["options"], heights):
            self.buttons.append(Button((M + 8, y, CW - 16, h), opt["label"], lambda o=opt: self.pick(o),
                                       kind="choice", size=20))
            y += h + 10

    def pick(self, opt):
        self.choice = opt
        self.result = self.g.apply_choice(self.event, opt)
        self.buttons = [Button((M, NAV_Y, CW, 54), "Continue  >", self.app.next_event, size=22)]

    def draw(self, surf):
        surf.fill(BG)
        phone_header(self, surf)
        x, w = M + 12, CW - 24
        text(surf, f"EVENT {self.index + 1} OF {self.count}  ·  YEAR {self.g.year}", (x, 132), 14, MUTED, bold=True)
        y = text_block(surf, self.event["title"], (x, 154), w, 30, INK, bold=True, spacing=1.15)
        if self.result is None:
            text_block(surf, self.event["text"], (x, y + 12), w, 21, INK, spacing=1.35)
        else:
            text(surf, "You chose:", (x, y + 16), 15, MUTED, bold=True)
            y = text_block(surf, self.choice["label"], (x, y + 38), w, 21, INK, bold=True)
            y = text_block(surf, self.choice["outcome"], (x, y + 12), w, 21, INK, spacing=1.35)
            y = draw_chips(surf, self.result, x, y + 18, PW - M, size=17)
            draw_professor(surf, PW // 2, min(NAV_Y - 20, y + 210), 0.9, self.g, self.t)
        Screen.draw(self, surf)


class PhoneReview(Screen):
    has_header = True

    def __init__(self, app, report):
        super().__init__(app)
        place_restart(self)
        self.r = report
        self.buttons = [Button((M, NAV_Y, CW, 54), "Continue  >", self.app.after_review, size=22)]

    def draw(self, surf):
        g, r = self.g, self.r
        surf.fill(BG)
        phone_header(self, surf)
        x, right = M + 8, PW - M - 8
        text(surf, f"ANNUAL REVIEW  ·  YEAR {r['year']}", (x, 126), 15, MUTED, bold=True)
        y = 154
        for label, val, pts in r["items"]:
            text(surf, label, (x, y), 18, INK)
            text(surf, val, (right - 64, y), 17, MUTED, anchor="topright")
            text(surf, f"{pts:+.0f}", (right, y), 18, GREEN if pts > 0 else RED if pts < 0 else MUTED,
                 bold=True, anchor="topright")
            y += 29
        pygame.draw.line(surf, INK, (x, y + 2), (right, y + 2), 2)
        text(surf, "Total score", (x, y + 10), 22, INK, bold=True)
        text(surf, f"{r['score']:.0f}", (right, y + 8), 26, INK, bold=True, anchor="topright")
        y += 50
        for i in range(5):
            star(surf, (x + 14 + i * 32, y + 14), 13, GOLD, filled=i < r["stars"])
        text(surf, STAR_LABELS[r["stars"]], (x + 172, y + 2), 20, INK, bold=True)
        text(surf, f"Merit raise {r['raise_pct']:.1f}%  ·  salary ${g.salary:,.0f}", (x, y + 36), 16, MUTED)
        y = text_block(surf, f"Dean: “{r['comment']}”", (x, y + 64), right - x, 17, INK, spacing=1.3)
        for note in r["notes"][:3]:
            y = text_block(surf, "•  " + note, (x, y + 6), right - x, 16, MUTED, spacing=1.25)
        for b in r["new_badges"][:3]:
            if y + 40 > NAV_Y - 4:
                break
            medal(surf, (x + 13, y + 26), b, small=True)
            text(surf, b, (x + 36, y + 16), 17, INK, bold=True)
            y += 34
        super().draw(surf)


class PhoneMilestone(Screen):
    has_header = True

    def __init__(self, app, result):
        super().__init__(app)
        place_restart(self)
        self.r = result
        label = "See your results  >" if self.g.game_over else "Continue  >"
        self.buttons = [Button((M, NAV_Y, CW, 54), label, self.app.after_milestone, size=22)]

    def draw(self, surf):
        r = self.r
        surf.fill(BG)
        phone_header(self, surf)
        x, right = M + 8, PW - M - 8
        text(surf, "MILESTONE REVIEW", (x, 128), 15, MUTED, bold=True)
        y = text_block(surf, r["name"], (x, 150), right - x, 32, INK, bold=True, spacing=1.15)
        y = text_block(surf, f"The committee checks your record against the rubric. You need {r['need']} of "
                             f"{len(r['rows'])}.", (x, y + 8), right - x, 18, MUTED)
        y += 14
        for label, key, val, req, ok in r["rows"]:
            check(surf, (x + 12, y + 14), ok, 12)
            text(surf, SHORT_LABELS.get(label, label), (x + 34, y + 2), 21, INK)
            text(surf, f"{fmt_stat(key, val)}", (right - 112, y + 2), 21, GREEN if ok else RED, bold=True,
                 anchor="topright")
            text(surf, f"need {fmt_stat(key, req)}", (right, y + 6), 15, MUTED, anchor="topright")
            y += 44
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
        lines = wrap(outcome, 28, CW - 40, bold=True) + [""] + wrap(sub, 18, CW - 40)
        box_h = 36 + len(lines) * 30
        pygame.draw.rect(surf, col, (M, y + 12, CW, box_h), border_radius=12)
        yy = text_block(surf, outcome, (M + 20, y + 28), CW - 40, 28, (255, 255, 255), bold=True, spacing=1.15)
        text_block(surf, sub, (M + 20, yy + 8), CW - 40, 18, (255, 255, 255))
        super().draw(surf)


# ---------------------------------------------------------------------------
# The ending
# ---------------------------------------------------------------------------

class PhoneFinal(FinalScreen):
    SCROLL_PAGES = (2, 3, 4)  # identity, behind the scenes, Goodhart
    SCROLL_TOP = 0

    def __init__(self, app):
        self.content_h = 0
        super().__init__(app)

    def set_buttons(self):
        self.buttons = []
        if self.page > 0:
            self.buttons.append(Button((M, NAV_Y, 120, 54), "<  Back", lambda: self.turn(-1), kind="small", size=19))
        nx = M + (132 if self.page > 0 else 0)
        if self.page < self.PAGES - 1:
            labels = ["What really happened  >", "Who you were  >", "Behind the scenes  >",
                      "Why this happens  >", "Share results  >"]
            self.buttons.append(Button((nx, NAV_Y, PW - M - nx, 54), labels[self.page], lambda: self.turn(1),
                                       size=20))
        else:
            self.buttons.append(Button((nx, NAV_Y, PW - M - nx, 54), "Play again", self.app.new_game, size=20))
            text_q, url_q = quote(self.share_text()), quote(GAME_URL)
            links = [
                ("Share on X", f"https://twitter.com/intent/tweet?text={text_q}&url={url_q}"),
                ("Bluesky", f"https://bsky.app/intent/compose?text={quote(self.share_text() + ' ' + GAME_URL)}"),
                ("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={url_q}"),
                ("LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={url_q}"),
            ]
            bw = (CW - 8) // 2
            self.buttons.append(Button((M, 682, CW, 50), "Save image to share", self.save, size=20))
            for i, (label, url) in enumerate(links):
                self.buttons.append(Button((M + (i % 2) * (bw + 8), 740 + (i // 2) * 44, bw, 38), label,
                                           lambda u=url: self.share(u), kind="small", size=17))
        if self.page == 4:
            bw = (CW - 8) // 2
            for i, (label, url) in enumerate(READINGS):
                self.buttons.append(Button((M + i * (bw + 8), NAV_Y - 52, bw, 44), label,
                                           lambda u=url: self.read(u), kind="small", size=16))

    def scroll_by(self, dy):
        if self.page in self.SCROLL_PAGES:
            self.scroll = max(0, min(self.scroll + dy, self.max_scroll()))

    def max_scroll(self):
        return max(0, self.content_h - (self.view_bottom() - self.SCROLL_TOP))

    def view_bottom(self):
        return NAV_Y - (62 if self.page == 4 else 12)

    def handle(self, e):
        if e.type == pygame.MOUSEWHEEL:
            self.scroll_by(-e.y * 40)
        elif e.type == pygame.MOUSEMOTION and e.buttons and e.buttons[0] and not WEB:
            self.scroll_by(-e.rel[1])
        Screen.handle(self, e)

    def save(self):
        shot = self.app.surf.subsurface(pygame.Rect(M, 12, CW, 660)).copy()
        try:
            self.share_msg = save_image(shot, "academic-game-results.png")
        except Exception:
            self.share_msg = "Couldn't save the image here. Try a screenshot instead."

    def draw(self, surf):
        surf.fill(BG)
        pages = [self.page_scoreboard, self.page_reveal, self.page_identity, self.page_behind,
                 self.page_discuss, self.page_share]
        if self.page in self.SCROLL_PAGES:
            view = pygame.Rect(0, self.SCROLL_TOP, PW, self.view_bottom() - self.SCROLL_TOP)
            surf.set_clip(view)
            bottom = pages[self.page](surf, self.SCROLL_TOP + 16 - self.scroll)
            surf.set_clip(None)
            self.content_h = bottom + self.scroll - self.SCROLL_TOP + 16
            self.scroll = min(self.scroll, self.max_scroll())
            if self.max_scroll() > 0 and self.scroll < self.max_scroll() - 4:
                band = pygame.Rect(0, view.bottom - 30, PW, 30)
                surf.fill(BG, band)
                pygame.draw.line(surf, LINE, band.topleft, band.topright)
                text(surf, "swipe up for more", (PW // 2, band.y + 7), 14, MUTED, bold=True, anchor="midtop")
        else:
            pages[self.page](surf)
        Screen.draw(self, surf)

    def page_title(self, surf, kicker, title, y=16):
        text(surf, kicker, (PW // 2, y), 14, MUTED, bold=True, anchor="midtop")
        lines = wrap(title, 28, CW, bold=True)
        for i, ln in enumerate(lines):
            text(surf, ln, (PW // 2, y + 20 + i * 33), 28, INK, bold=True, anchor="midtop")
        return y + 20 + len(lines) * 33

    def page_scoreboard(self, surf):
        g = self.g
        title = "Tenure denied" if g.denied else f"Career complete: {g.title}"
        y = self.page_title(surf, "FINAL SCOREBOARD", title)
        draw_professor(surf, PW // 2 + 40, y + 200, 0.95, g, self.t)
        stats = [
            ("Papers", f"{g.pubs}"), ("Citations", f"{g.citations:,}"), ("h-index", f"{g.h}"),
            ("Grants", fmt_money(g.grant_dollars)), ("Avg eval", f"{g.eval_avg:.2f}"),
            ("Salary", f"${g.salary / 1000:.0f}K"), ("Service", f"{int(g.service)}"),
            ("Reputation", f"{int(g.reputation)}"), ("Badges", f"{len(g.badges)}"),
        ]
        top = y + 222
        for i, (label, val) in enumerate(stats):
            x = M + 8 + (i % 3) * (CW // 3)
            yy = top + (i // 3) * 74
            text(surf, val, (x, yy), 30, INK, bold=True)
            text(surf, label, (x, yy + 38), 15, MUTED)
        y = top + 3 * 74 + 6
        text(surf, "TOTAL GAME SCORE", (M + 8, y), 13, MUTED, bold=True)
        text(surf, f"{g.game_score():,.0f} points", (M + 8, y + 18), 26, INK, bold=True)
        bar(surf, (M + 8, y + 56, CW - 16, 20), g.game_pct() * self.anim, DARK)
        text(surf, f"{int(g.game_pct() * 100)}% of an outstanding record", (M + 8, y + 84), 16, MUTED)

    def page_reveal(self, surf):
        g = self.g
        name, line = g.archetype()
        y = self.page_title(surf, "BUT WAS THAT THE JOB?", name)
        y = text_block(surf, line, (M + 8, y + 4), CW - 16, 18, MUTED) + 10
        panel(surf, (M, y, CW, 140))
        text(surf, "WHAT THE GAME MEASURED", (M + 16, y + 12), 13, MUTED, bold=True)
        text(surf, "Your game score", (M + 16, y + 34), 20, INK, bold=True)
        text(surf, f"{int(g.game_pct() * 100)}%", (PW - M - 16, y + 32), 22, INK, bold=True, anchor="topright")
        bar(surf, (M + 16, y + 66, CW - 32, 22), g.game_pct() * self.anim, DARK)
        avg = g.average_alloc()
        counted = sum(avg[k] for k in SCORE_CHASING)
        text_block(surf, f"{counted:.0f} of your {sum(avg.values()):.0f} weekly hours went to point-scoring activities.",
                   (M + 16, y + 98), CW - 32, 15, MUTED)
        y += 152
        hp = g.hidden_pcts()
        rows = [
            ("knowledge", "Meaningful knowledge created", self.knowledge_note(hp["knowledge"])),
            ("learning", "What students actually learned", self.learning_note(hp["learning"])),
            ("real_service", "Real service to people", self.service_note(hp["real_service"])),
            ("wellbeing", "Your own wellbeing", self.wellbeing_note(hp["wellbeing"])),
        ]
        panel(surf, (M, y, CW, NAV_Y - 12 - y))
        text(surf, "WHAT THE JOB WAS FOR (HIDDEN UNTIL NOW)", (M + 16, y + 12), 13, MUTED, bold=True)
        y += 36
        for key, label, note in rows:
            text(surf, label, (M + 16, y), 18, INK, bold=True)
            text(surf, f"{int(hp[key] * 100)}%", (PW - M - 16, y), 18, HIDDEN_COLORS[key], bold=True,
                 anchor="topright")
            bar(surf, (M + 16, y + 26, CW - 32, 14), hp[key] * self.anim, HIDDEN_COLORS[key])
            text(surf, note, (M + 16, y + 46), 14, MUTED)
            y += 76

    def page_identity(self, surf, y):
        g = self.g
        y = self.page_title(surf, "WHO YOU WERE", "The same work, scored differently", y)
        y = text_block(surf, f"You played as: {describe(g.identity)}", (M + 8, y + 4), CW - 16, 17, MUTED) + 12
        tiles = identity_tiles(g)
        if not tiles:
            y = text_block(surf, "The system gave you the benefit of the doubt.", (M + 8, y), CW - 16, 24, INK,
                           bold=True)
            y = text_block(surf, "Nothing about your identity cost you points. Players who chose other identities "
                                 "and made your exact choices faced documented biases like these:",
                           (M + 8, y + 8), CW - 16, 17, MUTED) + 10
            for _, _, label, source in RULES:
                y = text_block(surf, "•  " + label, (M + 8, y), CW - 16, 16, INK, spacing=1.3)
                y = text_block(surf, source, (M + 24, y + 2), CW - 32, 13, MUTED) + 12
            return y
        for row in range(0, len(tiles), 2):
            bottom = y
            for i, (big, label, sub) in enumerate(tiles[row:row + 2]):
                x = M + 8 + i * (CW // 2)
                text(surf, big, (x, y), 28, RED, bold=True)
                yy = text_block(surf, label, (x, y + 36), CW // 2 - 16, 15, INK, bold=True, spacing=1.2)
                bottom = max(bottom, text_block(surf, sub, (x, yy + 2), CW // 2 - 16, 13, MUTED, spacing=1.2))
            y = bottom + 18
        pygame.draw.line(surf, LINE, (M + 8, y), (PW - M - 8, y), 2)
        text(surf, "WHAT THE RESEARCH SAYS", (M + 8, y + 12), 13, MUTED, bold=True)
        y += 36
        for label, source in g.id_applied:
            y = text_block(surf, "•  " + label, (M + 8, y), CW - 16, 16, INK, spacing=1.3)
            y = text_block(surf, source, (M + 24, y + 2), CW - 32, 13, MUTED) + 12
        y = text_block(surf, "The direction of each effect comes from the research above; the sizes are the game's "
                             "own modest estimates. Real experiences vary widely, and evidence on some groups is "
                             "limited.", (M + 8, y + 4), CW - 16, 13, MUTED)
        return y

    def page_behind(self, surf, y):
        g = self.g
        y = self.page_title(surf, "BEHIND THE SCENES", "What your choices really did", y) + 10
        text(surf, "YOUR BUILD (AVG HRS/WEEK)", (M + 8, y), 13, MUTED, bold=True)
        y += 24
        avg = g.average_alloc()
        for act in ACTIVITIES:
            v = avg[act["key"]]
            text(surf, act["name"], (M + 8, y), 15, INK)
            bar(surf, (300, y + 4, 140, 11), v / MAX_PER_ACTIVITY, CAT_COLORS[act["cat"]])
            text(surf, f"{v:.0f}", (PW - M - 8, y), 15, MUTED, anchor="topright")
            y += 26
        y += 14
        text(surf, "WHAT EACH CHOICE REALLY DID", (M + 8, y), 13, MUTED, bold=True)
        y += 24
        if not g.reveals:
            y = text_block(surf, "No events recorded.", (M + 8, y), CW - 16, 17, MUTED)
        for year, title, label, reveal in g.reveals:
            text(surf, f"YEAR {year}  ·  {title.upper()}", (M + 8, y), 12, MUTED, bold=True)
            y = text_block(surf, f"You chose: {label}", (M + 8, y + 18), CW - 16, 17, INK, bold=True)
            y = text_block(surf, reveal, (M + 8, y + 2), CW - 16, 17, (70, 70, 84), spacing=1.3) + 16
        return y

    def page_discuss(self, surf, y):
        y = self.page_title(surf, "WHY THIS HAPPENS", "Goodhart's Law and value capture", y) + 20
        sections = [
            ("Goodhart's Law",
             "“When a measure becomes a target, it ceases to be a good measure.”",
             "Economist Charles Goodhart noticed in 1975 that statistics used to steer monetary policy stopped "
             "behaving once policy started targeting them. Anthropologist Marilyn Strathern gave the idea its "
             "familiar wording in 1997, writing about audits of British universities, the very system this game "
             "models. Every number you chased began as a reasonable signal of good work. Once careers depended on "
             "it, the rational move was to produce the signal instead of the work.",
             "Goodhart, C. (1975). Problems of monetary management: The U.K. experience. Strathern, M. (1997). "
             "‘Improving ratings’: Audit in the British university system. European Review, 5(3), "
             "305–321."),
            ("Value capture",
             "When a simple score quietly replaces what you actually cared about.",
             "Philosopher C. Thi Nguyen calls it value capture: our rich, subtle values meet simplified, "
             "quantified versions of them, like citation counts, GPAs, rankings, or step counts, and the simple "
             "version takes over our reasoning. Goodhart's Law is about what happens to the measure. Value capture "
             "is about what happens to us. Your professor probably started out wanting to understand things and "
             "help students. By the end, which did they want: that, or the points?",
             "Nguyen, C. T. (2024). Value capture. Journal of Ethics and Social Philosophy, 27(3). "
             "See also Nguyen, The Score (2026)."),
        ]
        for title, tagline, body, cite in sections:
            text(surf, title, (M + 8, y), 24, INK, bold=True)
            y = text_block(surf, tagline, (M + 8, y + 34), CW - 16, 17, MUTED, bold=True)
            y = text_block(surf, body, (M + 8, y + 10), CW - 16, 18, INK, spacing=1.4)
            y = text_block(surf, cite, (M + 8, y + 10), CW - 16, 13, MUTED) + 26
        if self.share_msg:
            y = text_block(surf, self.share_msg, (M + 8, y), CW - 16, 14, MUTED)
        return y

    def page_share(self, surf):
        g = self.g
        card = pygame.Rect(M, 12, CW, 660)
        panel(surf, card)
        x, w = M + 18, CW - 36
        text(surf, "WINNING THE ACADEMIC GAME", (PW // 2, 28), 13, MUTED, bold=True, anchor="midtop")
        text(surf, "Your results vs. reality", (PW // 2, 48), 26, INK, bold=True, anchor="midtop")
        text(surf, "THE GAME", (x, 96), 13, MUTED, bold=True)
        text(surf, "Tenure denied" if g.denied else g.title, (x, 114), 24, INK, bold=True)
        stats = [(f"{g.pubs}", "papers"), (f"{g.h}", "h-index"), (fmt_money(g.grant_dollars), "grants"),
                 (f"{g.eval_avg:.2f}", "avg eval"), (f"${g.salary / 1000:.0f}K", "salary"),
                 (f"{len(g.badges)}", "badges")]
        for i, (val, label) in enumerate(stats):
            sx = x + (i % 3) * (w // 3)
            sy = 152 + (i // 3) * 58
            text(surf, val, (sx, sy), 24, INK, bold=True)
            text(surf, label, (sx, sy + 30), 13, MUTED)
        text(surf, "Game score", (x, 274), 16, INK, bold=True)
        text(surf, f"{int(g.game_pct() * 100)}%", (x + w, 272), 18, INK, bold=True, anchor="topright")
        bar(surf, (x, 298, w, 14), g.game_pct() * self.anim, DARK)
        pygame.draw.line(surf, LINE, (x, 328), (x + w, 328), 2)
        name, line = g.archetype()
        text(surf, "REALITY", (x, 340), 13, MUTED, bold=True)
        y = text_block(surf, name, (x, 358), w, 24, INK, bold=True, spacing=1.15)
        y = text_block(surf, line, (x, y + 2), w, 15, MUTED) + 8
        hp = g.hidden_pcts()
        for key, label in [("knowledge", "Knowledge created"), ("learning", "Student learning"),
                           ("real_service", "Real service"), ("wellbeing", "Wellbeing")]:
            text(surf, label, (x, y), 15, INK, bold=True)
            text(surf, f"{int(hp[key] * 100)}%", (x + w, y), 15, HIDDEN_COLORS[key], bold=True, anchor="topright")
            bar(surf, (x, y + 22, w, 12), hp[key] * self.anim, HIDDEN_COLORS[key])
            y += 44
        text(surf, f"Real impact: {int(g.real_impact() * 100)}%", (x, y + 4), 22, INK, bold=True)
        text(surf, GAME_URL, (x, y + 38), 13, MUTED)
        if self.share_msg:
            text_block(surf, self.share_msg, (x, 646), w, 13, GREEN)


PHONE_SCREENS = dict(Title=PhoneTitle, Identity=PhoneIdentity, Allocate=PhoneAllocate, Event=PhoneEvent,
                     Review=PhoneReview, Milestone=PhoneMilestone, Final=PhoneFinal)
