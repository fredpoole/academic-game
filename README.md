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
5. **The reveal.** Game score compared with knowledge created, student learning, real service, and wellbeing. Then a "behind the scenes" page showing what each choice really did, a short explainer on Goodhart's Law (Strathern 1997) and value capture (Nguyen 2024) with links to both, and a share page (results on top, reality below) with buttons for X, Bluesky, Facebook, LinkedIn, or saving the results card as a PNG image to attach to a post.

## Identity effects and sources

Identity effects model bias in the system, not differences in ability. The direction of each effect comes from the cited research. The sizes are the game's own modest estimates, not figures taken from the studies. Individually small, they compound over a career. They're defined in `identity.py`.

- **Women:** lower evaluations for comparable teaching (Mengel, Sauermann & Zölitz 2019, *JEEA*: students randomly assigned, no difference in learning; Chávez & Mitchell 2020, *PS*: identical online courses). More internal service (Guarino & Borden 2017, *Research in Higher Education*). Fewer citations (Larivière et al. 2013, *Nature*; Dion, Sumner & Mitchell 2018, *Political Analysis*). A funding gap when reviewers judge the applicant rather than the science (Witteman et al. 2019, *The Lancet*). Women's full-time faculty salaries average about 82% of men's, a raw gap that also reflects rank and field (AAUP 2021–22).
- **Black faculty:** lower evaluations for instructors of color (Chávez & Mitchell 2020). "Cultural taxation" of mentoring and diversity service, a concept, not a measured number of hours (Padilla 1994, *Educational Researcher*). Black NIH applicants were about 10 points less likely to be funded after controls, 2000–2006 data (Ginther et al. 2011, *Science*). Topic choice explains about a fifth of that gap (Hoppe et al. 2019, *Science Advances*). Minoritized scholars face citation disadvantages (Kozlowski et al. 2022, *PNAS*).
- **Brown (Latinx, South Asian, Middle Eastern) faculty:** lower evaluations for instructors of color, cultural taxation, citation disadvantages. Same sources, minus the NIH findings. No grant effect is applied.
- **Asian faculty:** math instructors with Chinese or Korean surnames were rated lower for clarity on RateMyProfessors, often with comments about accent (Subtirelu 2015, *Language in Society*). Asian NIH applicants had a 4-point raw funding gap (Ginther et al. 2011). I couldn't confirm it persists after controls, so the game applies only a small effect.
- **LGBTQ+ faculty:** fewer career opportunities, more harassment and professional devaluation, not explained by training or work effort (Cech & Waidzunas 2021, *Science Advances*). The study measured LGBTQ identity, not whether people were out. The game's out/not-out split is a modeling choice.
- **Non-binary faculty:** more harassment and devaluation, plus more health strain (Cech & Waidzunas 2021). There's no evidence on evaluations, citations, or grants, so none are applied.
- **Not out at work:** concealing a stigmatized identity carries stress and psychological costs (Pachankis 2007, *Psychological Bulletin*).

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
