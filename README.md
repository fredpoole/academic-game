# Winning the Academic Game

A short Pygame game, about 20–30 minutes, about Goodhart's Law in academia. You play a professor over a 10-year career. Each year you split a work week across activities and make choices as events come up. The university scores you only on what it can count. A hidden second scorecard tracks what the job is actually for, and it is revealed at the end.

## Play online

https://fredpoole.github.io/academic-game/ (it takes about 15 seconds to load; click the page if it waits). Every push to `main` rebuilds and redeploys the site automatically.

## Run locally

```bash
pip install pygame
python main.py
```

Press Esc to quit.

## How it plays

1. **Plan the year.** Split your weekly hours across 11 activities (deep research, salami-slicing, chasing hot topics, grant writing, rigorous or crowd-pleasing teaching, mentoring, visible or invisible service, networking, inbox zero). Going over 40 hours drains energy, and low energy reduces output.
2. **Events.** Two scenarios each year, such as salami-slicing a dataset, reviewer #2, the viral thread, donuts on evaluation day, or capping a class for the rankings. You only see the "game" effects of each choice.
3. **Annual review.** Points, stars, a merit raise, and badges.
4. **Milestones.** Reappointment (Year 3), tenure (Year 6, fail it and the game ends), and Full Professor (Year 10). The rubric is always visible, so players learn to work backward from it.
5. **The reveal.** Game score compared with knowledge created, student learning, real service, and wellbeing. Then a "behind the scenes" page showing what each choice really did, and discussion questions.

## Files

- `model.py`: career rules, scoring, rubrics, hidden scores. All balance numbers live here.
- `events.py`: event scenarios. Add your own by copying an entry. Effects named `knowledge`, `learning`, and `real_service` stay hidden until the end.
- `main.py`: Pygame screens and drawing.

## Balance (from simulating 300 careers per strategy)

| Strategy | Tenure | Full Prof | Hidden impact |
|---|---|---|---|
| Pure metric-gaming | ~100% | ~90–99% | ~5–25% |
| Balanced, plays along with events | ~66% | ~20% | ~35–45% |
| Balanced, honest choices | ~1% | 0% | ~60–80% |
| Idealist | 0% | 0% | ~90%+ |

To make the game more or less forgiving, adjust `RUBRICS` in `model.py`.
