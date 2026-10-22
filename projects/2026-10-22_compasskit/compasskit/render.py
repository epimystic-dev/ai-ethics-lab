"""Render the compass as a human-readable Markdown catalogue (docs/PRIMITIVES.md).

The catalogue in docs/ is generated from compass.json by this module, and a test fails if
the two drift apart, so the human-readable and machine-readable forms cannot disagree.
"""

from __future__ import annotations

from typing import List

from .spec import Compass

_LAYER_WORDS = {
    "context": "context (the model can apply it in its own output)",
    "middleware": "middleware (code around the model)",
    "architecture": "architecture (what actions exist at all)",
    "governance": "governance (named people and records)",
}


def _cls(p) -> str:
    a = p["adoption"]
    s = "Class " + a["base_class"]
    if a["conditional"]:
        s += "; " + "; ".join("%s: Class %s" % (c["part"], c["class"]) for c in a["conditional"])
    return s


def catalogue(c: Compass) -> str:
    d = c.data
    L: List[str] = []
    L.append("# The compass primitives")
    L.append("")
    L.append("*Generated from `compass/compass.json` (version %s) by `python -m compasskit catalogue`. "
             "Do not edit by hand.*" % d["version"])
    L.append("")
    L.append(d["description"])
    L.append("")
    L.append("## How to read this")
    L.append("")
    for line in d["how_to_read"]:
        L.append("- " + line)
    L.append("")
    L.append("## Adoption classes")
    L.append("")
    L.append("| Class | Who decides |")
    L.append("|---|---|")
    for k in ("A", "B", "C", "D"):
        L.append("| %s | %s |" % (k, d["adoption_classes"][k]))
    L.append("")
    L.append(d["adoption_classes"]["note"])
    L.append("")
    L.append("## The floor beneath everything")
    L.append("")
    L.append(d["floor"]["description"])
    L.append("")
    L.append("| Thesis | In practice |")
    L.append("|---|---|")
    for t in d["floor"]["theses"]:
        L.append("| %s %s | %s |" % (t["id"], t["name"], t["in_practice"]))
    L.append("")
    for i, r in enumerate(d["floor"]["sub_rules"], 1):
        L.append("%d. %s" % (i, r))
    L.append("")
    L.append(d["floor"]["note"])
    L.append("")
    L.append("## Nine questions")
    L.append("")
    L.append("| # | Question | The answer in one line | Primitives |")
    L.append("|---|---|---|---|")
    for q in d["questions"]:
        L.append("| %d | %s | %s | %s |" % (q["id"], q["question"], q["answer"], ", ".join(q["primitives"])))
    L.append("")
    L.append("## The stack, floor first")
    L.append("")
    for s in sorted(d["stack"], key=lambda x: x["order"]):
        L.append("%d. **%s**: %s" % (s["order"] + 1, s["title"], ", ".join(s["primitives"])))
    L.append("")
    for key in "ABCDEFG":
        series = d["series"][key]
        L.append("## Series %s: %s" % (key, series["title"]))
        L.append("")
        L.append(series["scope"])
        L.append("")
        for p in c.select(series=key):
            L.append("### %s %s" % (p["id"], p["name"]))
            L.append("")
            L.append("**In one sentence.** " + p["summary"])
            L.append("")
            L.append("**For example.** " + p["example"])
            L.append("")
            L.append("**Statement.** " + p["statement"])
            L.append("")
            L.append("**Warrant.** " + p["warrant"])
            L.append("")
            L.append("**Failure mode addressed.** " + p["failure_mode"])
            L.append("")
            L.append("**Sketch.** " + p["sketch"])
            L.append("")
            L.append("**Class.** " + p["adoption"]["class_reason"])
            L.append("")
            L.append("**Falsifier.** " + p["falsifier"])
            L.append("")
            facts = ["answers question %d" % p["question"], _cls(p),
                     "enforced at: " + "; ".join(_LAYER_WORDS[x] for x in p["enforcement_layers"])]
            if p.get("data_contract"):
                facts.append("data contract: `compass/%s`" % p["data_contract"])
            if p.get("reference_implementation"):
                facts.append("reference implementation: `%s`" % p["reference_implementation"])
            if p.get("book_chapters"):
                facts.append("book chapters: " + ", ".join(str(n) for n in p["book_chapters"]))
            L.append("*" + " | ".join(facts) + "*")
            L.append("")
    L.append("## Limits")
    L.append("")
    for line in d["limits"]:
        L.append("- " + line)
    L.append("")
    L.append("---")
    L.append("")
    L.append("Adapted from Appendix B of *%s* (%s), CC-BY-4.0. See `NOTICE.md` for the attribution and "
             "the list of changes." % (d["source"]["work"], d["source"]["edition"]))
    L.append("")
    return "\n".join(L)
