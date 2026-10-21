"""Desktop (wide-screen) screens for Winning the Academic Game."""

import random
from urllib.parse import quote

import pygame

from identity import GENDERS, ORIENTATIONS, RACES, RULES, describe
from model import (ACTIVITIES, BASE_HOURS, MAX_HOURS, MAX_PER_ACTIVITY, MIN_CLASS_HOURS, RUBRICS,
                   SCORE_CHASING, STAR_LABELS, STEP, YEARS, Career)
from ui import *  # noqa: F401,F403  (shared toolkit: colors, text helpers, widgets)

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


class IdentityScreen(Screen):
    X = 300
    ROWS = [("gender", "Gender", GENDERS, 140), ("race", "Race / ethnicity", RACES, 240),
            ("orientation", "Sexual orientation", ORIENTATIONS, 360), ("out", "Out at work?", [True, False], 460)]

    def __init__(self, app):
        super().__init__(app)
        self.sel = dict(app.identity)
        self.preview = Career(identity=self.sel)
        for key, _, options, y in self.ROWS:
            for i, opt in enumerate(options):
                label = ("Yes" if opt else "No") if key == "out" else opt
                enabled = (lambda: self.sel["orientation"] != "Straight") if key == "out" else None
                self.buttons.append(Toggle((self.X + i * 160, y, 150, 50), label,
                                           lambda k=key, o=opt: self.pick(k, o),
                                           lambda k=key, o=opt: self.sel[k] == o, enabled=enabled))
        self.buttons.append(Button((self.X, 690, 200, 56), "Randomize", self.randomize, kind="small", size=19))
        self.buttons.append(Button((960, 690, 280, 56), "Start your career  >",
                                   lambda: self.app.begin_career(self.sel)))

    def pick(self, key, value):
        self.sel[key] = value
        self.preview = Career(identity=self.sel)

    def randomize(self):
        self.sel = dict(gender=random.choice(GENDERS), race=random.choice(RACES),
                        orientation=random.choice(ORIENTATIONS), out=random.random() < 0.6)
        self.preview = Career(identity=self.sel)

    def draw(self, surf):
        surf.fill(BG)
        text(surf, "STEP 1", (60, 40), 14, MUTED, bold=True)
        text(surf, "Choose your professor", (60, 60), 40, INK, bold=True)
        for key, label, _, y in self.ROWS:
            off = key == "out" and self.sel["orientation"] == "Straight"
            text(surf, label, (60, y + 14), 19, MUTED if off else INK, bold=True)
        panel(surf, (980, 120, 260, 360))
        draw_professor(surf, 1120, 420, 1.15, self.preview, self.t)
        text_block(surf, describe(self.sel), (996, 436), 230, 14, MUTED)
        note = ("Your identity doesn't change what you are able to do. It may change how the system responds "
                "to what you do: evaluations, citations, grants, service requests, and more. Effects follow patterns "
                "documented in published research and are revealed, with sources, at the end of the game.")
        panel(surf, (60, 540, 1180, 120))
        text_block(surf, note, (84, 560), 1130, 18, INK)
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
            draw_chips(surf, self.result, 420, yy + 20, 1200)
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


def identity_tiles(g):
    """What identity bias cost this career, as (big number, label, detail) tiles."""
    c = g.costs
    years = max(1, len(g.history))
    grant_cut = 1 - g.idfx["grant_mult"]
    tiles = [
        (c["eval"] > 0, f"-{c['eval'] / years:.2f}", "on every teaching evaluation",
         f"{c['eval'] * 25:.0f} annual review points lost"),
        (c["service_hours"] > 0, f"{c['service_hours']:,.0f} hrs", "of extra mentoring and service",
         "expected of you, barely credited"),
        (c["cites"] >= 1, f"{c['cites']:,.0f}", "citations you didn't receive", "for the same papers"),
        (grant_cut > 0 and c["grant_odds"] > 0, f"{grant_cut * 100:.0f}% lower", "grant odds on every application",
         f"about {c['grant_odds']:.1f} grants you'd otherwise have won"),
        (g.fair_salary - g.salary >= 1, f"${g.fair_salary - g.salary:,.0f}", "less salary",
         "in raises over your career"),
        (c["energy"] > 0, f"-{c['energy']:.0f}", "energy", "lost to devaluation, harassment, or concealment"),
    ]
    return [tl[1:] for tl in tiles if tl[0]]


class FinalScreen(Screen):
    PAGES = 6

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
        if self.page == 4:
            for i, (label, url) in enumerate(READINGS):
                self.buttons.append(Button((90 + i * 590, 636, 220, 44), label,
                                           lambda u=url: self.read(u), kind="small", size=16))
        if self.page < self.PAGES - 1:
            labels = ["What really happened  >", "Who you were  >", "Behind the scenes  >", "Why this happens  >",
                      "Share results  >"]
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
            self.buttons.append(Button((160 + 4 * 196, 620, 176, 46), "Save image", self.save, kind="small", size=17))

    def share_text(self):
        g = self.g
        if g.denied:
            outcome = "was denied tenure"
        else:
            outcome = f"finished as {g.title}"
        return (f"I played Winning the Academic Game and {outcome} with a {int(g.game_pct() * 100)}% game score, "
                f"but only {int(g.real_impact() * 100)}% real impact. I'm \"{g.archetype()[0]}.\" "
                f"Can you beat the system?")

    def read(self, url):
        open_url(url)
        self.share_msg = "Opened in a new tab. If nothing appeared, allow pop-ups."

    def share(self, url):
        open_url(url)
        self.share_msg = "Opened in a new tab. Save the image to attach it. If nothing appeared, allow pop-ups."

    def save(self):
        # The title and results card, without the buttons
        shot = self.app.surf.subsurface(pygame.Rect(140, 20, 1000, 600)).copy()
        try:
            self.share_msg = save_image(shot, "academic-game-results.png")
        except Exception:
            self.share_msg = "Couldn't save the image here. Try a screenshot instead."

    def turn(self, d):
        self.page += d
        self.scroll = 0
        self.anim = 0.0
        self.share_msg = ""
        self.set_buttons()

    def handle(self, e):
        if e.type == pygame.MOUSEWHEEL and self.page == 3:
            self.scroll = max(0, self.scroll - e.y * 30)
        super().handle(e)

    def update(self, dt):
        super().update(dt)
        self.anim = min(1.0, self.anim + dt * 0.7)

    def draw(self, surf):
        surf.fill(BG)
        pages = [self.page_scoreboard, self.page_reveal, self.page_identity, self.page_behind, self.page_discuss,
                 self.page_share]
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
        text(surf, "WHY THIS HAPPENS", (W // 2, 30), 14, MUTED, bold=True, anchor="midtop")
        text(surf, "Goodhart's Law and value capture", (W // 2, 50), 40, INK, bold=True, anchor="midtop")
        sections = [
            (60, "Goodhart's Law",
             "\u201cWhen a measure becomes a target, it ceases to be a good measure.\u201d",
             "Economist Charles Goodhart noticed in 1975 that statistics used to steer monetary policy stopped "
             "behaving once policy started targeting them. Anthropologist Marilyn Strathern gave the idea its "
             "familiar wording in 1997, writing about audits of British universities, the very system this game "
             "models. Every number you chased began as a reasonable signal of good work. Once careers depended on "
             "it, the rational move was to produce the signal instead of the work.",
             "Goodhart, C. (1975). Problems of monetary management: The U.K. experience. "
             "Strathern, M. (1997). \u2018Improving ratings\u2019: Audit in the British university system. "
             "European Review, 5(3), 305\u2013321."),
            (650, "Value capture",
             "When a simple score quietly replaces what you actually cared about.",
             "Philosopher C. Thi Nguyen calls it value capture: our rich, subtle values meet simplified, "
             "quantified versions of them, like citation counts, GPAs, rankings, or step counts, and the simple "
             "version takes over our reasoning. Goodhart's Law is about what happens to the measure. Value capture "
             "is about what happens to us. Your professor probably started out wanting to understand things and "
             "help students. By the end, which did they want: that, or the points?",
             "Nguyen, C. T. (2024). Value capture. Journal of Ethics and Social Philosophy, 27(3). "
             "See also Nguyen, The Score (2026)."),
        ]
        for x, title, tagline, body, cite in sections:
            panel(surf, (x, 110, 570, 590))
            text(surf, title, (x + 30, 132), 28, INK, bold=True)
            y = text_block(surf, tagline, (x + 30, 176), 510, 18, MUTED, bold=True)
            y = text_block(surf, body, (x + 30, y + 14), 510, 17, INK, spacing=1.4)
            text_block(surf, cite, (x + 30, y + 18), 510, 13, MUTED)
        if self.share_msg:
            text(surf, self.share_msg, (W // 2, 708), 14, MUTED, anchor="midtop")


    def page_identity(self, surf):
        g = self.g
        text(surf, "WHO YOU WERE", (W // 2, 30), 14, MUTED, bold=True, anchor="midtop")
        text(surf, "The same work, scored differently", (W // 2, 50), 40, INK, bold=True, anchor="midtop")
        text(surf, f"You played as: {describe(g.identity)}", (W // 2, 102), 18, MUTED, anchor="midtop")
        panel(surf, (60, 136, 1160, 570))
        tiles = identity_tiles(g)
        if not tiles:
            text(surf, "The system gave you the benefit of the doubt.", (100, 166), 28, INK, bold=True)
            text_block(surf, "Nothing about your identity cost you points. Players who chose other identities and "
                             "made exactly your choices faced documented biases like these:",
                       (100, 210), 1080, 18, MUTED)
            y = 262
            for _, _, label, source in RULES:
                y = text_block(surf, "•  " + label, (100, y), 1080, 14, INK, spacing=1.25)
                y = text_block(surf, source, (122, y), 1060, 12, MUTED, spacing=1.2) + 5
            return
        for i, (big, label, sub) in enumerate(tiles):
            x = 100 + (i % 3) * 370
            y = 166 + (i // 3) * 112
            text(surf, big, (x, y), 34, RED, bold=True)
            text(surf, label, (x, y + 44), 16, INK, bold=True)
            text(surf, sub, (x, y + 66), 14, MUTED)
        y = 166 + ((len(tiles) + 2) // 3) * 112 + 6
        pygame.draw.line(surf, LINE, (100, y - 10), (1180, y - 10), 2)
        text(surf, "WHAT THE RESEARCH SAYS", (100, y), 12, MUTED, bold=True)
        y += 22
        for label, source in g.id_applied:
            y = text_block(surf, "•  " + label, (100, y), 1080, 15, INK)
            y = text_block(surf, source, (122, y), 1060, 13, MUTED) + 6
        text_block(surf, "The direction of each effect comes from the research above; the sizes are the game's own "
                         "modest estimates. Real experiences vary widely, and evidence on some groups is limited.",
                   (100, 664), 1080, 13, MUTED)

    def page_share(self, surf):
        g = self.g
        text(surf, "WINNING THE ACADEMIC GAME", (W // 2, 30), 14, MUTED, bold=True, anchor="midtop")
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
