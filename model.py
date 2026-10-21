"""Game logic for Winning the Academic Game (no pygame here).

The professor's career runs for YEARS years. Each year the player splits a
work week across activities, answers a couple of events, and then gets an
annual review that only counts what is easy to count. A second set of hidden
scores tracks what the job is actually for: knowledge, student learning,
real service, and the professor's own wellbeing.
"""

import random
from collections import defaultdict

YEARS = 10
BASE_HOURS = 40
MAX_HOURS = 60
MAX_PER_ACTIVITY = 20
STEP = 1
MIN_CLASS_HOURS = 6  # rigorous + crowd-pleasing teaching: the classes must be taught

CATEGORIES = ["Research", "Teaching", "Service", "Visibility", "Admin"]

ACTIVITIES = [
    dict(key="deep", cat="Research", name="Deep, slow research",
         pitch="One big question. Few papers, slowly."),
    dict(key="salami", cat="Research", name="Salami-slice papers",
         pitch="Split studies into many papers. +Pubs fast!"),
    dict(key="trendy", cat="Research", name="Chase hot topics",
         pitch="Write on what's trending. +Citations!"),
    dict(key="grants", cat="Research", name="Write grant proposals",
         pitch="Roll for loot. Grants boost all research."),
    dict(key="rigor", cat="Teaching", name="Rigorous teaching",
         pitch="Demanding work, real feedback. Evals may dip."),
    dict(key="pleaser", cat="Teaching", name="Crowd-pleasing teaching",
         pitch="Easy A's, fun lectures. +Evals, +Enrollment!"),
    dict(key="mentor", cat="Teaching", name="Deep mentoring",
         pitch="Long office hours, real advising. Hard to count."),
    dict(key="vis_service", cat="Service", name="Visible committee service",
         pitch="Chair task forces. Great CV lines!"),
    dict(key="review", cat="Service", name="Peer review & editing",
         pitch="Review manuscripts, edit journals. A little credit."),
    dict(key="invis_service", cat="Service", name="Invisible service",
         pitch="Fix broken things, mentor colleagues. No credit."),
    dict(key="social", cat="Visibility", name="Social media self-promo",
         pitch="Threads, videos, hot takes. +Reputation fast!"),
    dict(key="conference", cat="Visibility", name="Conferences & field-building",
         pitch="Present, organize panels, meet students. Slow burn."),
    dict(key="forms", cat="Admin", name="Forms & meetings",
         pitch="Assessment reports, compliance, meetings. Required."),
    dict(key="email", cat="Admin", name="Inbox zero",
         pitch="Clear the daily quests. Deans love it."),
]
ACT_KEYS = [a["key"] for a in ACTIVITIES]
# Activities built mainly to score points on the annual review.
SCORE_CHASING = ("salami", "trendy", "grants", "pleaser", "vis_service", "social", "forms", "email")

DEFAULT_ALLOC = dict(deep=6, salami=3, trendy=2, grants=4, rigor=6, pleaser=4,
                     mentor=2, vis_service=2, review=2, invis_service=1, social=2,
                     conference=2, forms=2, email=2)

# How each kind of paper gets cited over time: deep work starts slow and
# keeps growing; quick work spikes and fades.
PAPER_KINDS = {
    "deep":     dict(rate=4.0, grow=1.5, cap=18.0),
    "salami":   dict(rate=2.0, mult=0.80),
    "trendy":   dict(rate=12.0, mult=0.80),
    "prestige": dict(rate=8.0, mult=0.88),
    "guild":    dict(rate=5.0, mult=0.85),
}

TITLES = ["Assistant Professor", "Associate Professor", "Full Professor"]

RUBRICS = {
    3: dict(name="Third-Year Reappointment", need=2, hard=False, criteria=[
        ("Publications", "pubs", 5),
        ("Average teaching evaluation", "eval_avg", 3.6),
        ("Service lines on CV", "service", 2),
    ]),
    6: dict(name="Tenure Review", need=4, hard=True, criteria=[
        ("Publications", "pubs", 10),
        ("h-index", "h", 4),
        ("Average teaching evaluation", "eval_avg", 3.8),
        ("External grants won", "grants_won", 1),
        ("Service lines on CV", "service", 5),
    ]),
    10: dict(name="Promotion to Full Professor", need=5, hard=False, criteria=[
        ("Publications", "pubs", 22),
        ("h-index", "h", 9),
        ("Grant dollars", "grant_dollars", 750_000),
        ("Reputation", "reputation", 45),
        ("Service lines on CV", "service", 10),
        ("Average teaching evaluation", "eval_avg", 3.8),
    ]),
}

# Points per unit in the annual review. Only countable things appear here.
REVIEW_WEIGHTS = dict(pub=8, cite=0.1, grant=20, eval=25, enroll=0.3,
                      service=6, responsive=8, review=1, talk=3, compliance=10)

STAR_LABELS = ["", "Unsatisfactory", "Needs Improvement", "Meets Expectations",
               "Exceeds Expectations", "Outstanding"]
RAISES = [0, 0.0, 0.5, 1.5, 2.5, 4.0]  # percent merit raise by stars

# Reference values for showing hidden scores as a percentage: roughly what a
# dedicated, sustainable career could achieve in each area.
HIDDEN_SCALE = dict(knowledge=220, learning=260, real_service=110)

BADGES = [
    ("First Publication", lambda g: g.pubs >= 1),
    ("Prolific: 10 Papers", lambda g: g.pubs >= 10),
    ("Paper Mill: 25 Papers", lambda g: g.pubs >= 25),
    ("100 Citations", lambda g: g.citations >= 100),
    ("500 Citations", lambda g: g.citations >= 500),
    ("h-index 5", lambda g: g.h >= 5),
    ("h-index 10", lambda g: g.h >= 10),
    ("Grant Getter", lambda g: g.grants_won >= 1),
    ("Million-Dollar Scholar", lambda g: g.grant_dollars >= 1_000_000),
    ("Fan Favorite: Evals 4.5+", lambda g: g.evals and g.evals[-1] >= 4.5),
    ("Packed House: 80+ Students", lambda g: g.enrollment >= 80),
    ("Committee Regular", lambda g: g.service >= 6),
    ("Influencer", lambda g: g.reputation >= 50),
    ("Reviewer of the Year: 40 Reviews", lambda g: g.reviews_done >= 40),
    ("Conference Circuit: 10 Talks", lambda g: g.talks >= 10),
    ("Iron Professor: 56-hr Weeks", lambda g: g.total_hours() >= 56),
]


class Paper:
    __slots__ = ("kind", "rate", "cites", "year")

    def __init__(self, kind, year):
        self.kind = kind
        self.rate = PAPER_KINDS[kind]["rate"]
        self.cites = 0.0
        self.year = year

    def age(self):
        spec = PAPER_KINDS[self.kind]
        if "grow" in spec:
            self.rate = min(spec["cap"], self.rate + spec["grow"])
        else:
            self.rate *= spec["mult"]


class Career:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.year = 1
        self.energy = 75.0
        self.salary = 85_000.0
        self.alloc = dict(DEFAULT_ALLOC)

        self.papers = []
        self.frac = defaultdict(float)
        self.deep_progress = 0.0
        self.grants_won = 0
        self.grant_dollars = 0
        self.grant_active = 0
        self.evals = []
        self.enrollment = 40
        self.service = 0.0
        self.reputation = 10.0
        self.reviews_done = 0
        self.talks = 0
        self.editor = False
        self.guild = False
        self.badges = []
        self.title_level = 0
        self.game_over = False
        self.denied = False

        # Hidden: what the job is actually for.
        self.knowledge = 0.0
        self.learning = 0.0
        self.real_service = 0.0
        self.wellbeing = []

        self.mods = defaultdict(float)  # this year's event modifiers
        self.history = []  # per year: allocation, review score, stars
        self.reveals = []  # (year, event title, choice label, reveal text)
        self.used_events = set()

    # ---- derived stats -------------------------------------------------
    @property
    def pubs(self):
        return len(self.papers)

    @property
    def citations(self):
        return int(sum(p.cites for p in self.papers))

    @property
    def h(self):
        cites = sorted((int(p.cites) for p in self.papers), reverse=True)
        h = 0
        for i, c in enumerate(cites, 1):
            if c >= i:
                h = i
        return h

    @property
    def eval_avg(self):
        return sum(self.evals) / len(self.evals) if self.evals else 0.0

    @property
    def title(self):
        return TITLES[self.title_level]

    def stat(self, key):
        return getattr(self, key)

    def total_hours(self):
        return sum(self.alloc.values())

    def class_hours(self):
        return self.alloc["rigor"] + self.alloc["pleaser"]

    def alloc_valid(self):
        return self.class_hours() >= MIN_CLASS_HOURS and self.total_hours() <= MAX_HOURS

    def efficiency(self):
        return 0.55 + 0.45 * self.energy / 100

    def next_review_year(self):
        for y in sorted(RUBRICS):
            if y >= self.year:
                return y
        return None

    def rubric_status(self, year):
        r = RUBRICS[year]
        rows = []
        for label, key, req in r["criteria"]:
            val = self.stat(key)
            rows.append((label, key, val, req, val >= req))
        return rows

    # ---- papers ----------------------------------------------------------
    def add_papers(self, kind, n):
        for _ in range(int(n)):
            self.papers.append(Paper(kind, self.year))

    def add_cites(self, n):
        if not self.papers:
            self.add_papers("salami", 1)
        recent = self.papers[-3:]
        for p in recent:
            p.cites += n / len(recent)

    def roll_grant(self, chance, big=False):
        if self.rng.random() < chance:
            amount = (self.rng.uniform(600, 1200) if big else
                      self.rng.uniform(180, 420) + self.reputation * 3)
            amount = int(round(amount)) * 1000
            self.grants_won += 1
            self.grant_dollars += amount
            self.grant_active = max(self.grant_active, 3)
            return amount
        return 0

    # ---- events ----------------------------------------------------------
    def eligible_events(self, events):
        out = []
        for ev in events:
            if ev["id"] in self.used_events:
                continue
            lo, hi = ev.get("years", (1, YEARS))
            if not lo <= self.year <= hi:
                continue
            cond = ev.get("when")
            if cond and not cond(self):
                continue
            out.append(ev)
        return out

    def draw_events(self, events, n=2):
        pool = self.eligible_events(events)
        urgent = [e for e in pool if e.get("urgent")]
        normal = [e for e in pool if not e.get("urgent")]
        self.rng.shuffle(normal)
        picked = (urgent + normal)[:n]
        for e in picked:
            self.used_events.add(e["id"])
        return picked

    def apply_choice(self, event, option):
        """Apply an event option. Returns list of visible change strings."""
        fx = option.get("fx", {})
        shown = []
        for kind, label in (("salami", "publication"), ("trendy", "publication"),
                            ("prestige", "top-tier publication"),
                            ("deep_paper", "major publication")):
            n = fx.get(kind, 0)
            if n:
                self.add_papers("deep" if kind == "deep_paper" else kind, n)
                shown.append(f"+{n} {label}{'s' if n > 1 else ''}")
        if fx.get("guild"):
            self.guild = True
            shown.append("Joined a co-authorship network")
        if fx.get("editor"):
            self.editor = True
            shown.append("Now a journal editor")
        if fx.get("talks"):
            self.talks += fx["talks"]
            shown.append(f"+{fx['talks']} presentation{'s' if fx['talks'] > 1 else ''}")
        if fx.get("reviews"):
            self.reviews_done += fx["reviews"]
            shown.append(f"+{fx['reviews']} manuscript review{'s' if fx['reviews'] > 1 else ''}")
        if fx.get("cites"):
            self.add_cites(fx["cites"])
            shown.append(f"+{fx['cites']} citations")
        if fx.get("frac_salami"):
            self.frac["salami"] += fx["frac_salami"]
            shown.append("Paper delayed to next year")
        if fx.get("deep_progress"):
            v = fx["deep_progress"]
            self.deep_progress = max(0.0, self.deep_progress + v)
            shown.append(f"Major project {'+' if v > 0 else ''}{v}%")
        if fx.get("reputation"):
            v = fx["reputation"]
            self.reputation = max(0.0, min(100.0, self.reputation + v))
            shown.append(f"Reputation {'+' if v > 0 else ''}{v}")
        if fx.get("service"):
            self.service += fx["service"]
            shown.append(f"+{fx['service']:g} service line{'s' if fx['service'] > 1 else ''}")
        if fx.get("energy"):
            v = fx["energy"]
            self.energy = max(0.0, min(100.0, self.energy + v))
            shown.append(f"Energy {'+' if v > 0 else ''}{v}")
        if fx.get("salary"):
            v = fx["salary"]
            self.salary += v
            shown.append(f"Salary {'+' if v > 0 else '-'}${abs(v):,}")
        if fx.get("eval"):
            v = fx["eval"]
            self.mods["eval"] += v
            shown.append(f"Evals this year {'+' if v > 0 else ''}{v:.2f}")
        if fx.get("enrollment"):
            v = fx["enrollment"]
            self.mods["enrollment"] += v
            shown.append(f"Enrollment {'+' if v > 0 else ''}{v}")
        if fx.get("grant_bonus"):
            self.mods["grant_bonus"] += fx["grant_bonus"]
            shown.append(f"Grant odds +{int(fx['grant_bonus'] * 100)}% this year")
        if fx.get("responsiveness"):
            v = fx["responsiveness"]
            self.mods["responsiveness"] += v
            shown.append(f"Responsiveness {'up' if v > 0 else 'down'}")
        if fx.get("compliance"):
            v = fx["compliance"]
            self.mods["compliance"] += v
            shown.append(f"Compliance {'up' if v > 0 else 'down'}")
        if fx.get("review"):
            v = fx["review"]
            self.mods["review"] += v
            shown.append(f"Annual review {'+' if v > 0 else ''}{v} pts")
        if fx.get("grant_roll"):
            amount = self.roll_grant(fx["grant_roll"], big=True)
            shown.append(f"FUNDED! +${amount:,}" if amount else
                         "Not funded. 'Very good, not discussed.'")
        if fx.get("award_roll"):
            if self.rng.random() < fx["award_roll"]:
                self.award(fx.get("badge", "Award"))
                self.mods["review"] += 10
                shown.append(f"You won: {fx.get('badge')}! +10 review pts")
            else:
                shown.append("Award went to someone else.")
        elif fx.get("badge"):
            if self.award(fx["badge"]):
                shown.append(f"Badge: {fx['badge']}")

        self.knowledge += fx.get("knowledge", 0)
        self.learning += fx.get("learning", 0)
        self.real_service += fx.get("real_service", 0)

        if option.get("reveal"):
            self.reveals.append((self.year, event["title"], option["label"], option["reveal"]))
        return shown

    def award(self, name):
        if name in self.badges:
            return False
        self.badges.append(name)
        return True

    # ---- the year --------------------------------------------------------
    def run_year(self):
        a = self.alloc
        m = self.mods
        eff = self.efficiency()
        boost = 1.3 if self.grant_active > 0 else 1.0
        start_pubs, start_cites, start_service = self.pubs, self.citations, int(self.service)
        notes = []

        # Research
        self.deep_progress += a["deep"] * 3.2 * eff * boost
        self.knowledge += a["deep"] * 0.9 * eff
        while self.deep_progress >= 100:
            self.deep_progress -= 100
            self.add_papers("deep", 1)
            self.knowledge += 20
            notes.append("Your big project was finally published!")

        self.frac["salami"] += a["salami"] * 0.17 * eff * boost
        self.knowledge += a["salami"] * 0.1 * eff
        self.frac["trendy"] += a["trendy"] * 0.10 * eff * boost
        self.knowledge += a["trendy"] * 0.3 * eff
        self.reputation += a["trendy"] * 0.25
        for kind in ("salami", "trendy"):
            while self.frac[kind] >= 1:
                self.frac[kind] -= 1
                self.add_papers(kind, 1)
        if self.guild:
            n = 1 + (self.rng.random() < 0.5)
            self.add_papers("guild", n)
            self.knowledge += 0.5 * n
            notes.append(f"Your network added you to {n} more paper{'s' if n > 1 else ''}.")

        grant_won = 0
        if a["grants"] > 0 or m["grant_bonus"] > 0:
            chance = a["grants"] * 0.035 * eff * (1 + self.reputation / 100 + 0.3 * self.grants_won)
            chance = min(0.8, chance + m["grant_bonus"])
            grant_won = self.roll_grant(chance)
            if grant_won:
                notes.append(f"Grant funded: ${grant_won:,}! Research output +30% for 3 years.")
            elif a["grants"] > 0:
                notes.append(f"Grant rejected ({int(chance * 100)}% odds). Revise and resubmit?")

        # Teaching
        ev = 3.5 + a["pleaser"] * 0.085 - a["rigor"] * 0.03 + a["mentor"] * 0.01
        ev += m["eval"] + self.rng.gauss(0, 0.08)
        ev = max(1.0, min(5.0, ev))
        self.evals.append(round(ev, 2))
        self.learning += (a["rigor"] * 1.3 + a["mentor"] * 1.5 + a["pleaser"] * 0.25) * eff
        self.enrollment = int(max(8, 40 + a["pleaser"] * 5 - a["rigor"] * 1.2
                                  + self.reputation * 0.1 + m["enrollment"]))

        # Service, visibility, admin
        new_reviews = int(round(a["review"] * 1.5 * eff))
        self.reviews_done += new_reviews
        self.service += a["vis_service"] * 0.35 + a["review"] * 0.12 + a["invis_service"] * 0.04
        self.reputation += a["vis_service"] * 0.15 + a["review"] * 0.2
        self.real_service += (a["vis_service"] * 0.25 + a["review"] * 0.8 + a["invis_service"] * 1.1
                              + a["forms"] * 0.05 + a["email"] * 0.1) * eff
        self.knowledge += a["review"] * 0.15 * eff
        if self.editor:
            self.service += 1
            self.reputation += 2
            self.real_service += 4
            self.energy -= 3
            notes.append("Editing the journal took its usual toll on your weekends.")

        # Social media: fast reputation and a citation bump, nothing else.
        self.reputation += a["social"] * 1.0 * eff
        if a["social"] and self.papers:
            self.add_cites(a["social"] * 0.8)
        # Conferences: slower reputation, but they actually feed the field.
        self.frac["talks"] += a["conference"] * 0.35 * eff
        new_talks = int(self.frac["talks"])
        self.frac["talks"] -= new_talks
        self.talks += new_talks
        self.reputation += a["conference"] * 0.5 * eff
        self.knowledge += a["conference"] * 0.25 * eff
        self.real_service += a["conference"] * 0.35 * eff

        responsive = max(0.0, min(1.0, a["email"] / 5 + m["responsiveness"]))
        compliance = max(0.0, min(1.0, a["forms"] / 3 + m["compliance"]))
        self.reputation = max(0.0, min(100.0, self.reputation * 0.93))

        # Citations accumulate; reputation makes people notice your work.
        for p in self.papers:
            p.cites += p.rate * (1 + self.reputation / 80)
            p.age()

        # Energy: overtime drains it, a normal week slowly restores it.
        total = self.total_hours()
        self.energy = max(0.0, min(100.0, self.energy + 5 - max(0, total - BASE_HOURS) * 2.2
                                         + max(0, BASE_HOURS - total) * 1.0))
        self.wellbeing.append(self.energy)
        if self.grant_active > 0 and not grant_won:
            self.grant_active -= 1

        # Annual review: only the countable things.
        W = REVIEW_WEIGHTS
        new_pubs = self.pubs - start_pubs
        new_cites = self.citations - start_cites
        new_service = int(self.service) - start_service
        items = [
            ("New publications", f"{new_pubs}", new_pubs * W["pub"]),
            ("New citations", f"{new_cites}", new_cites * W["cite"]),
            ("Grant funded", "Yes" if grant_won else "No", W["grant"] if grant_won else 0),
            ("Teaching evaluation", f"{ev:.2f} / 5", (ev - 3.0) * W["eval"]),
            ("Enrollment", f"{self.enrollment} students", max(0, self.enrollment - 40) * W["enroll"]),
            ("New service lines", f"{new_service}", new_service * W["service"]),
            ("Manuscripts reviewed", f"{new_reviews}", new_reviews * W["review"]),
            ("Conference presentations", f"{new_talks}", new_talks * W["talk"]),
            ("Reports filed & meetings", f"{int(compliance * 100)}%", compliance * W["compliance"]),
            ("Email responsiveness", f"{int(responsive * 100)}%", responsive * W["responsive"]),
        ]
        if m["review"]:
            items.append(("Other items on your report", "", m["review"]))
        score = sum(p for _, _, p in items)
        stars = 5 if score >= 85 else 4 if score >= 60 else 3 if score >= 40 else 2 if score >= 20 else 1
        raise_pct = RAISES[stars]
        self.salary *= 1 + raise_pct / 100

        before = set(self.badges)
        for name, test in BADGES:
            if test(self):
                self.award(name)
        new_badges = [b for b in self.badges if b not in before]

        report = dict(year=self.year, items=items, score=score, stars=stars,
                      raise_pct=raise_pct, notes=notes, new_badges=new_badges,
                      comment=self.dean_comment(items, stars, ev))
        self.history.append(dict(year=self.year, alloc=dict(a), score=score, stars=stars,
                                 energy=self.energy))
        self.mods = defaultdict(float)
        return report

    def dean_comment(self, items, stars, ev):
        pts = {label: p for label, _, p in items}
        if stars >= 5:
            return "Outstanding productivity. You are a model for the department."
        if self.energy < 25:
            return "Strong numbers, though you look tired. Keep it up!"
        if pts["New publications"] < 8:
            return "The committee would like to see more publications next year."
        if pts["Reports filed & meetings"] < 5:
            return "Your assessment report is overdue, and you have missed several faculty meetings."
        if ev < 3.6:
            return "Your evaluation scores are below the college average. Consider ways to boost them."
        if pts["Grant funded"] == 0 and self.year >= 3:
            return "External funding is a strategic priority. Have you applied for grants?"
        if pts["New service lines"] == 0:
            return "We'd like to see you take a more visible service role."
        return "Solid year. Keep building your record."

    def finish_year(self):
        """Run a milestone review if one is due, then advance. Returns review dict or None."""
        result = None
        if self.year in RUBRICS:
            r = RUBRICS[self.year]
            rows = self.rubric_status(self.year)
            met = sum(1 for row in rows if row[4])
            passed = met >= r["need"]
            result = dict(year=self.year, name=r["name"], rows=rows, met=met,
                          need=r["need"], passed=passed, hard=r["hard"])
            if self.year == 6:
                if passed:
                    self.title_level = 1
                else:
                    self.denied = True
                    self.game_over = True
            elif self.year == 10 and passed:
                self.title_level = 2
        if self.year >= YEARS:
            self.game_over = True
        if not self.game_over:
            self.year += 1
        return result

    # ---- endgame ---------------------------------------------------------
    def game_score(self):
        return sum(h["score"] for h in self.history)

    def hidden_pcts(self):
        out = {k: max(0.0, min(1.0, getattr(self, k) / scale * YEARS / max(1, len(self.history))))
               for k, scale in HIDDEN_SCALE.items()}
        out["wellbeing"] = (sum(self.wellbeing) / len(self.wellbeing) / 100) if self.wellbeing else 0.8
        return out

    def real_impact(self):
        hp = self.hidden_pcts()
        return (hp["knowledge"] + hp["learning"] + hp["real_service"]) / 3

    def game_pct(self):
        # 90 review points a year is an outstanding record.
        years = max(1, len(self.history))
        return max(0.0, min(1.0, self.game_score() / (90 * years)))

    def average_alloc(self):
        if not self.history:
            return dict(self.alloc)
        n = len(self.history)
        return {k: sum(h["alloc"][k] for h in self.history) / n for k in ACT_KEYS}

    def archetype(self):
        g = self.game_pct()
        hp = self.hidden_pcts()
        real = (hp["knowledge"] + hp["learning"] + hp["real_service"]) / 3
        if self.denied and g >= 0.5:
            return ("The Near Miss", "You played the game hard and still lost. The rubric always wins.")
        if g >= 0.65 and real >= 0.6:
            if hp["wellbeing"] < 0.4:
                return ("The Burned-Out Overachiever",
                        "You won the game and did real work, and it cost you your health.")
            return ("The Rare Unicorn",
                    "You found the narrow overlap where the metrics and the mission agree.")
        if g >= 0.65:
            return ("The Metric Maximizer", "You won the game. But the game wasn't the job.")
        if real >= 0.5:
            return ("The Quiet Scholar", "You did the job. The game barely noticed.")
        if real >= 0.3 or g >= 0.4:
            return ("The Pragmatist", "You played some of the game and did some of the job.")
        return ("The Lost Player", "Neither the game nor the job got much out of this career.")
