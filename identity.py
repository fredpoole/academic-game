"""Identity options and the documented biases they bring.

Effects model how the *system* responds to a professor, not differences in
ability. Each rule's direction comes from the cited research; the exact sizes
are the game's own rough estimates, chosen to be modest. Individually small,
they compound over a career. Real experiences vary widely, and evidence on
some groups is thin, so those groups get fewer, smaller effects.
"""

GENDERS = ["Man", "Woman", "Non-binary"]
RACES = ["White", "Black", "Brown", "Asian"]
ORIENTATIONS = ["Straight", "Gay or lesbian", "Bisexual", "Queer"]

DEFAULT_IDENTITY = dict(gender="Man", race="White", orientation="Straight", out=True)

# Neutral effects: no penalty.
BASE = dict(eval=0.0, service_tax=0.0, grant_mult=1.0, cite_mult=1.0,
            raise_mult=1.0, energy_drain=0.0, rep_mult=1.0)

# Each rule: (applies?, effects, what the research found, sources)
RULES = [
    (lambda i: i["gender"] == "Woman",
     dict(eval=-0.10, service_tax=0.6, cite_mult=0.90, grant_mult=0.93, raise_mult=0.92),
     "Women get lower teaching evaluations for comparable teaching, do more internal service, are cited "
     "less, are funded less when reviewers judge the person rather than the science, and earn about 82% "
     "of men's salaries (a raw gap that also reflects rank and field).",
     "Mengel, Sauermann & Zölitz 2019; Chávez & Mitchell 2020; Guarino & Borden 2017; "
     "Larivière et al. 2013; Dion, Sumner & Mitchell 2018; Witteman et al. 2019; AAUP 2022"),
    (lambda i: i["gender"] == "Non-binary",
     dict(energy_drain=3.0, rep_mult=0.92),
     "LGBTQ+ STEM professionals report more harassment and professional devaluation; trans and "
     "non-binary respondents also report more health strain. Evidence on evaluations, citations, and "
     "grants is lacking, so the game applies none.",
     "Cech & Waidzunas 2021"),
    (lambda i: i["race"] == "Black",
     dict(eval=-0.15, service_tax=1.5, grant_mult=0.60, cite_mult=0.90),
     "Instructors of color get lower evaluations; faculty of color carry a 'cultural taxation' of "
     "mentoring and diversity service; Black NIH applicants were funded about 10 points less often after "
     "controls (topic choice explains about a fifth of the gap); minoritized scholars are cited less.",
     "Chávez & Mitchell 2020; Padilla 1994; Ginther et al. 2011; Hoppe et al. 2019; Kozlowski et al. 2022"),
    (lambda i: i["race"] == "Brown",
     dict(eval=-0.10, service_tax=1.0, cite_mult=0.95),
     "Instructors of color get lower evaluations; faculty of color carry a 'cultural taxation' of "
     "mentoring and diversity service; minoritized scholars are cited less.",
     "Chávez & Mitchell 2020; Padilla 1994; Kozlowski et al. 2022"),
    (lambda i: i["race"] == "Asian",
     dict(eval=-0.05, grant_mult=0.95),
     "Math instructors with Chinese or Korean surnames were rated lower for clarity on RateMyProfessors, "
     "often with comments about accent; Asian NIH applicants had a 4-point raw funding gap.",
     "Subtirelu 2015; Ginther et al. 2011"),
    (lambda i: i["orientation"] != "Straight" and i["out"],
     dict(energy_drain=3.0, rep_mult=0.90),
     "LGBTQ+ STEM professionals report fewer career opportunities, more harassment, and more "
     "professional devaluation, not explained by differences in training or work effort.",
     "Cech & Waidzunas 2021"),
    (lambda i: i["orientation"] != "Straight" and not i["out"],
     dict(energy_drain=2.5),
     "Concealing a stigmatized identity avoids some bias but carries its own stress and psychological "
     "costs. (The game's out/not-out split is a modeling choice.)",
     "Pachankis 2007"),
]


def effects_for(identity):
    """Combine every rule that applies. Penalties stack, so intersecting
    identities (e.g., Black women) face compounding effects."""
    fx = dict(BASE)
    applied = []
    for test, rule, label, source in RULES:
        if not test(identity):
            continue
        for k, v in rule.items():
            if k.endswith("mult"):
                fx[k] *= v
            else:
                fx[k] += v
        applied.append((label, source))
    return fx, applied


def describe(identity):
    noun = {"Man": "man", "Woman": "woman", "Non-binary": "non-binary person"}[identity["gender"]]
    text = f"{identity['race']} {noun}"
    if identity["orientation"] == "Straight":
        return text + ", straight"
    out = "out at work" if identity["out"] else "not out at work"
    return f"{text}, {identity['orientation'].lower()} ({out})"
