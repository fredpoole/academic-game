# Winning the Academic Game

A short Pygame game, about 20–30 minutes, about Goodhart's Law in academia. You play a professor over a 10-year career. Each year you split a work week across activities and make choices as events come up. The university scores you only on what it can count. A hidden second scorecard tracks what the job is actually for, and it is revealed at the end.

## Play online

https://fredpoole.github.io/academic-game/ (it takes about 15 seconds to load). Every push to `main` rebuilds and redeploys the site automatically.

## Run locally

```bash
pip install pygame
python main.py
```

Press Esc to quit.

## How it plays

1. **Plan the year.** Split your weekly hours, one hour at a time, across 14 activities: deep research, salami-slicing, chasing hot topics, grant writing, rigorous or crowd-pleasing teaching, mentoring, committee service, peer review and editing, invisible service, social media self-promotion, conferences and field-building, forms and meetings, and inbox zero. Going over 40 hours drains energy, and low energy reduces output.
2. **Events.** Two scenarios each year, drawn from a pool of about 50 (so each playthrough differs), such as salami-slicing a dataset, reviewer #2, an editorship offer, the assessment report, AI-drafted papers, donuts on evaluation day, or capping a class for the rankings. You only see the "game" effects of each choice.
3. **Annual review.** Points, stars, a merit raise, and badges.
4. **Milestones.** Reappointment (Year 3), tenure (Year 6, fail it and the game ends), and Full Professor (Year 10). The rubric is always visible, so players learn to work backward from it.
5. **The reveal.** Game score compared with knowledge created, student learning, real service, and wellbeing. Then a "behind the scenes" page showing what each choice really did, discussion questions, and a share page (results on top, reality below) with buttons for X, Bluesky, Facebook, LinkedIn, or copying the text.

## Files

- `model.py`: career rules, scoring, rubrics, hidden scores. All balance numbers live here.
- `events.py`: event scenarios. Add your own by copying an entry. Effects named `knowledge`, `learning`, and `real_service` stay hidden until the end.
- `main.py`: Pygame screens and drawing.

## Balance (from simulating 300 careers per strategy)

| Strategy | Tenure | Full Prof | Hidden impact |
|---|---|---|---|
| Pure metric-gaming | ~100% | ~90–100% | ~5–30% |
| Balanced, plays along with events | ~50% | ~10% | ~35–45% |
| Balanced, mixed choices | ~25% | ~1% | ~45–60% |
| Idealist | 0% | 0% | ~70–95% |

To make the game more or less forgiving, adjust `RUBRICS` in `model.py`.
