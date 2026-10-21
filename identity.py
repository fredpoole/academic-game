"""Identity options and the documented biases they bring.

Effects model how the *system* responds to a professor, not differences in
ability: the same teaching gets lower evaluations, the same papers get fewer
citations, the same proposals get funded less often, and some faculty are
asked to do more unpaid service and mentoring. Sizes are rough, research-
calibrated approximations: individually small, they compound over a career.
Real experiences vary widely, and evidence on some groups is thin.
"""

GENDERS = ["Man", "Woman", "Non-binary"]
RACES = ["White", "Black", "Brown", "Asian"]
RACE_NOTES = {"Brown": "Latinx, South Asian, or Middle Eastern"}
ORIENTATIONS = ["Straight", "Gay or lesbian", "Bisexual", "Queer"]

DEFAULT_IDENTITY = dict(gender="Man", race="White", orientation="Straight", out=True)

# Neutral effects: no penalty.
BASE = dict(eval=0.0, service_tax=0.0, grant_mult=1.0, cite_mult=1.0,
            raise_mult=1.0, energy_drain=0.0, rep_mult=1.0)

# Each rule: (applies?, effects, short label, source)
RULES = [
    (lambda i: i["gender"] == "Woman",
     dict(eval=-0.10, service_tax=0.6, cite_mult=0.90, grant_mult=0.93, raise_mult=0.92),
     "Women receive lower teaching evaluations for identical teaching, do more internal service, "
     "are cited less, and earn less.",
     "Mengel, Sauermann & Zölitz 2019; Guarino & Borden 2017; Larivière et al. 2013; "
     "Dion, Sumner & Mitchell 2018; Witteman et al. 2019; AAUP salary surveys"),
    (lambda i: i["gender"] == "Non-binary",
     dict(eval=-0.10, service_tax=0.5, cite_mult=0.95, energy_drain=3.0, rep_mult=0.92),
     "Trans and non-binary scholars report more devaluation, harassment, and work stress. "
     "Direct evidence on evaluations is limited, so effects here are cautious estimates.",
     "Cech & Waidzunas 2021"),
    (lambda i: i["race"] == "Black",
     dict(eval=-0.15, service_tax=1.5, grant_mult=0.60, cite_mult=0.90),
     "Black faculty receive lower evaluations, carry a heavy 'cultural taxation' of mentoring and "
     "diversity service, and were funded at NIH about 10 points less often than comparable white applicants.",
     "Chávez & Mitchell 2020; Padilla 1994; Ginther et al. 2011; Hoppe et al. 2019; Kozlowski et al. 2022"),
    (lambda i: i["race"] == "Brown",
     dict(eval=-0.10, service_tax=1.0, grant_mult=0.95, cite_mult=0.95),
     "Latinx and other faculty of color receive lower evaluations and are asked to mentor and serve "
     "far more often than white colleagues.",
     "Chávez & Mitchell 2020; Padilla 1994; Kozlowski et al. 2022"),
    (lambda i: i["race"] == "Asian",
     dict(eval=-0.05, grant_mult=0.90, rep_mult=0.92),
     "Asian faculty face perceived-foreignness bias in evaluations, a smaller NIH funding gap, and "
     "are underrepresented in academic leadership.",
     "Subtirelu 2015; Ginther et al. 2011"),
    (lambda i: i["orientation"] != "Straight" and i["out"],
     dict(energy_drain=3.0, rep_mult=0.90, cite_mult=0.97),
     "Out LGBTQ+ scholars report fewer career opportunities, more harassment, and professional "
     "devaluation, even after accounting for training and effort.",
     "Cech & Waidzunas 2021"),
    (lambda i: i["orientation"] != "Straight" and not i["out"],
     dict(energy_drain=2.5),
     "Staying closeted avoids some bias but carries its own cost: the constant work of concealing "
     "part of yourself drains energy.",
     "Pachankis 2007; Cech & Waidzunas 2021"),
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
