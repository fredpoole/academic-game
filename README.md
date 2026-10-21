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

0. **Choose your professor.** Pick gender, race/ethnicity, and sexual orientation (and whether you're out at work), or randomize. Identity doesn't change what you can do, but it changes how the system responds, based on published research. The effects stay hidden until the end.
1. **Plan the year.** Split your weekly hours, one hour at a time, across 14 activities: deep research, salami-slicing, chasing hot topics, grant writing, rigorous or crowd-pleasing teaching, mentoring, committee service, peer review and editing, invisible service, social media self-promotion, conferences and field-building, forms and meetings, and inbox zero. Going over 40 hours drains energy, and low energy reduces output.
2. **Events.** Two scenarios each year, drawn from a pool of about 50 (so each playthrough differs), such as salami-slicing a dataset, reviewer #2, an editorship offer, the assessment report, AI-drafted papers, donuts on evaluation day, or capping a class for the rankings. You only see the "game" effects of each choice.
3. **Annual review.** Points, stars, a merit raise, and badges.
4. **Milestones.** Reappointment (Year 3), tenure (Year 6, fail it and the game ends), and Full Professor (Year 10). The rubric is always visible, so players learn to work backward from it.
5. **The reveal.** Game score compared with knowledge created, student learning, real service, and wellbeing. Then a "behind the scenes" page showing what each choice really did, a short explainer on Goodhart's Law (Strathern 1997) and value capture (Nguyen 2024) with links to both, and a share page (results on top, reality below) with buttons for X, Bluesky, Facebook, LinkedIn, or copying the text.

## Identity effects and sources

Identity effects model bias in the system, not differences in ability. Sizes are rough, research-calibrated approximations: individually small, they compound over a career. They're defined in `identity.py`.

- **Women:** lower teaching evaluations, more internal service, fewer citations, a grant gap, smaller raises. Mengel, Sauermann & Zölitz (2019), *JEEA*; Guarino & Borden (2017), *Research in Higher Education*; Larivière et al. (2013), *Nature*; Dion, Sumner & Mitchell (2018), *Political Analysis*; Witteman et al. (2019), *The Lancet*; AAUP Faculty Compensation Survey.
- **Black faculty:** lower evaluations, "cultural taxation" of mentoring and service, a roughly 10-point NIH funding gap, fewer citations. Chávez & Mitchell (2020), *PS: Political Science & Politics*; Padilla (1994), *Educational Researcher*; Ginther et al. (2011), *Science*; Hoppe et al. (2019), *Science Advances*; Kozlowski et al. (2022), *PNAS*.
- **Latinx / South Asian / Middle Eastern ("Brown") faculty:** lower evaluations and heavier service and mentoring demands. Chávez & Mitchell (2020); Padilla (1994); Kozlowski et al. (2022).
- **Asian faculty:** perceived-foreignness bias in evaluations and a smaller NIH funding gap. Subtirelu (2015), *Language in Society*; Ginther et al. (2011).
- **LGBTQ+ faculty (out):** fewer career opportunities, more harassment and devaluation. Cech & Waidzunas (2021), *Science Advances*.
- **Non-binary faculty:** more devaluation, harassment, and stress. Cech & Waidzunas (2021). Direct evidence on evaluations is limited, so these effects are cautious estimates.
- **Not out at work:** concealment drains energy. Pachankis (2007), *Psychological Bulletin*.

Effects stack, so intersecting identities face compounding costs. In simulation, with identical strategies and choices, a balanced career reaches tenure about 23% of the time as a white man and about 14% as a Black woman.

## Files

- `model.py`: career rules, scoring, rubrics, hidden scores. All balance numbers live here.
- `identity.py`: identity options, bias effects, and research sources.
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
