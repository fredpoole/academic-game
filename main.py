"""Winning the Academic Game - a pygame game about how academia got gamified.

Run:  python main.py              (set ACADEMIC_PHONE=1 to try the phone layout)
"""

import asyncio
import os

import pygame

import screens
import ui
from events import EVENTS
from identity import DEFAULT_IDENTITY
from model import Career
from phone import PHONE_SCREENS
from ui import DARK, FPS, GOLD, WEB, text

DESKTOP_SCREENS = dict(Title=screens.TitleScreen, Identity=screens.IdentityScreen,
                       Allocate=screens.AllocateScreen, Event=screens.EventScreen,
                       Review=screens.ReviewScreen, Milestone=screens.MilestoneScreen,
                       Final=screens.FinalScreen)


def detect_phone():
    """Phones get the tall layout; computers and tablets get the wide one."""
    if WEB:
        import platform
        platform.window.eval(ui.POINTER_JS)  # also records whether this is a phone
        return bool(platform.window.agPhone)
    return os.environ.get("ACADEMIC_PHONE") == "1"


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class App:
    def __init__(self, phone=None):
        pygame.init()
        pygame.display.set_caption("Winning the Academic Game")
        self.phone = detect_phone() if phone is None else phone
        self.size = (ui.PW, ui.PH) if self.phone else (ui.W, ui.H)
        self.S = PHONE_SCREENS if self.phone else DESKTOP_SCREENS
        self.surf = pygame.display.set_mode(self.size)
        self.clock = pygame.time.Clock()
        self.identity = dict(DEFAULT_IDENTITY)
        self.preview = Career()
        self.career = self.preview
        self.screen = self.S["Title"](self)
        self.events = []
        self.event_i = 0
        self.pending_milestone = None

    def new_game(self):
        self.screen = self.S["Identity"](self)

    def begin_career(self, identity):
        self.identity = dict(identity)
        self.career = Career(identity=identity)
        self.screen = self.S["Allocate"](self)

    def start_year(self):
        self.events = self.career.draw_events(EVENTS, n=2)
        self.event_i = 0
        self.show_event()

    def show_event(self):
        if self.event_i < len(self.events):
            self.screen = self.S["Event"](self, self.events[self.event_i], self.event_i, len(self.events))
        else:
            report = self.career.run_year()
            self.screen = self.S["Review"](self, report)

    def next_event(self):
        self.event_i += 1
        self.show_event()

    def after_review(self):
        result = self.career.finish_year()
        if result:
            self.screen = self.S["Milestone"](self, result)
        else:
            self.after_milestone()

    def after_milestone(self):
        if self.career.game_over:
            self.screen = self.S["Final"](self)
        else:
            self.screen = self.S["Allocate"](self)

    def fix_pointer(self, e):
        """Replace a web mouse event's position with where the pointer really is."""
        import platform
        px, py = platform.window.agPX, platform.window.agPY
        if px is None or px < 0:
            return e
        pos = (int(px * self.size[0]), int(py * self.size[1]))
        ui.set_pointer(pos)
        if e.type == pygame.MOUSEMOTION:
            return pygame.event.Event(e.type, pos=pos, rel=e.rel, buttons=e.buttons)
        return pygame.event.Event(e.type, pos=pos, button=e.button)

    def wrong_orientation(self):
        """Phones should be held upright, tablets sideways. Mice and trackpads don't care."""
        import platform
        w = platform.window
        landscape = w.innerWidth > w.innerHeight
        if self.phone:
            return landscape
        return bool(w.agTouch) and not landscape

    def take_swipe(self):
        """Pass finger swipes (tracked by the page script) to screens that scroll."""
        import platform
        frac = platform.window.agScroll
        if frac:
            platform.window.agScroll = 0
            if hasattr(self.screen, "scroll_by"):
                self.screen.scroll_by(frac * self.size[1])

    def draw_rotate(self, surf):
        w, h = self.size
        surf.fill(DARK)
        k = w / 1280 * (2.2 if self.phone else 1)  # the phone canvas is shown small when sideways
        cx, cy = w // 2, int(h * 0.36)
        tall = pygame.Rect(0, 0, 120 * k, 210 * k)
        wide = pygame.Rect(0, 0, 210 * k, 120 * k)
        (wide if self.phone else tall).center = (cx - 120 * k, cy)
        (tall if self.phone else wide).center = (cx + 120 * k, cy)
        pygame.draw.rect(surf, (255, 255, 255), wide if self.phone else tall, max(2, int(6 * k)),
                         border_radius=int(18 * k))
        pygame.draw.rect(surf, GOLD, tall if self.phone else wide, max(2, int(6 * k)), border_radius=int(18 * k))
        msg = "Turn your phone upright" if self.phone else "Turn your phone sideways"
        sub = "The game is laid out for a tall screen." if self.phone else "The game is built for a wide screen."
        big, small = (52, 30) if self.phone else (90, 56)
        y = int(h * 0.58)
        for line, size, col in ([(ln, big, (255, 255, 255)) for ln in ui.wrap(msg, big, w - 60, bold=True)]
                                + [(ln, small, (190, 192, 210)) for ln in ui.wrap(sub, small, w - 60)]):
            text(surf, line, (w // 2, y), size, col, bold=size == big, anchor="midtop")
            y += int(size * 1.3)

    async def run(self):
        # async so the same loop runs on the desktop and in the browser (pygbag)
        rotate, check_at = False, 0.0
        while True:
            dt = self.clock.tick(FPS) / 1000
            if WEB:
                check_at -= dt
                if check_at <= 0:
                    rotate, check_at = self.wrong_orientation(), 0.5
                self.take_swipe()
            for e in pygame.event.get():
                quit_key = e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not WEB
                if e.type == pygame.QUIT or quit_key:
                    pygame.quit()
                    return
                if WEB and e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    e = self.fix_pointer(e)
                if not rotate:
                    self.screen.handle(e)
            if rotate:
                self.draw_rotate(self.surf)
            else:
                self.screen.update(dt)
                self.screen.draw(self.surf)
            pygame.display.flip()
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(App().run())
