"""Build the SVG diagrams in this folder, and docs/WHAT-AI-GAINS.md, from compass/compass.json.

    python docs/diagrams/build_diagrams.py          # write the SVGs
    python docs/diagrams/build_diagrams.py --check  # fail if any SVG is out of date

Standard library only. Every diagram that lists primitives reads them from the compass, so
a change to the data changes the pictures. Each SVG paints its own light background, so it
reads the same on a light or a dark page.
"""

from __future__ import annotations

import io
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
COMPASS = os.path.join(ROOT, "compass", "compass.json")

FONT = "Helvetica, Arial, sans-serif"
INK, MUTED, LINE, PAPER = "#1f2328", "#57606a", "#8c959f", "#ffffff"
A_FILL, A_STROKE = "#eaf1fd", "#3567c8"
B_FILL, B_STROKE = "#fff3df", "#b86e00"
FLOOR_FILL = "#24292f"
RED, RED_FILL = "#b42318", "#fdecea"
GREEN, GREEN_FILL = "#1a7f37", "#e8f5ec"
AMBER, AMBER_FILL = "#9a6700", "#fff8e1"
GREY_FILL = "#f6f8fa"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def text_width(s: str, size: float, bold: bool = False) -> float:
    return len(s) * size * (0.60 if bold else 0.54)


def wrap(s: str, size: float, width: float, bold: bool = False) -> List[str]:
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and text_width(trial, size, bold) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


class SVG(object):
    def __init__(self, w: int, h: int, title: str, desc: str):
        self.w, self.h = w, h
        self.parts: List[str] = []
        self.title, self.desc = title, desc

    def rect(self, x, y, w, h, fill=GREY_FILL, stroke=LINE, rx=6, sw=1.2, dash: Optional[str] = None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d" fill="%s" stroke="%s" '
                          'stroke-width="%.1f"%s/>' % (x, y, w, h, rx, fill, stroke, sw, d))

    def text(self, x, y, s, size=13, fill=INK, bold=False, anchor="start", italic=False):
        extra = (' font-weight="700"' if bold else "") + (' font-style="italic"' if italic else "")
        self.parts.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s" text-anchor="%s"%s>%s</text>'
                          % (x, y, size, fill, anchor, extra, esc(s)))

    def lines(self, x, y, lines: Sequence[str], size=13, fill=INK, bold=False, anchor="start", lead=1.3):
        for i, ln in enumerate(lines):
            self.text(x, y + i * size * lead, ln, size, fill, bold, anchor)
        return y + len(lines) * size * lead

    def para(self, x, y, s, width, size=13, fill=INK, bold=False, anchor="start", lead=1.3):
        return self.lines(x, y, wrap(s, size, width, bold), size, fill, bold, anchor, lead)

    def arrow(self, x1, y1, x2, y2, color=MUTED, sw=1.6, dash: Optional[str] = None, label: str = "",
              lx: Optional[float] = None, ly: Optional[float] = None, lsize=11.5, lanchor="middle"):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        mk = {MUTED: "a-muted", RED: "a-red", GREEN: "a-green", AMBER: "a-amber", A_STROKE: "a-blue", B_STROKE: "a-orange"}[color]
        self.parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f"%s '
                          'marker-end="url(#%s)"/>' % (x1, y1, x2, y2, color, sw, d, mk))
        if label:
            self.text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 - 6,
                      label, lsize, color if color != MUTED else MUTED, anchor=lanchor)

    def path(self, d, color=MUTED, sw=1.6, dash: Optional[str] = None, arrow=True):
        dd = ' stroke-dasharray="%s"' % dash if dash else ""
        mk = {MUTED: "a-muted", RED: "a-red", GREEN: "a-green", AMBER: "a-amber", A_STROKE: "a-blue", B_STROKE: "a-orange"}[color]
        self.parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f"%s%s/>'
                          % (d, color, sw, dd, ' marker-end="url(#%s)"' % mk if arrow else ""))

    def box(self, x, y, w, h, head, body="", fill=GREY_FILL, stroke=LINE, size=13, head_fill=INK, dash=None,
            body_size=None, body_fill=MUTED):
        self.rect(x, y, w, h, fill, stroke, dash=dash)
        yy = self.para(x + 12, y + 22, head, w - 24, size, head_fill, bold=True)
        if body:
            self.para(x + 12, yy + 2, body, w - 24, body_size or size - 1.5, body_fill)

    def dark_box(self, x, y, w, h, head, body=""):
        self.box(x, y, w, h, head, body, FLOOR_FILL, FLOOR_FILL, head_fill=PAPER, body_fill="#d0d7de")

    def render(self) -> str:
        marks = []
        for name, color in (("a-muted", MUTED), ("a-red", RED), ("a-green", GREEN), ("a-amber", AMBER),
                            ("a-blue", A_STROKE), ("a-orange", B_STROKE)):
            marks.append('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                         'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (name, color))
        head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
                'font-family="%s" role="img" aria-labelledby="t d">\n<title id="t">%s</title>\n<desc id="d">%s</desc>\n'
                '<defs>%s</defs>\n<rect x="0" y="0" width="%d" height="%d" fill="%s"/>\n'
                % (self.w, self.h, self.w, self.h, FONT, esc(self.title), esc(self.desc), "".join(marks),
                   self.w, self.h, PAPER))
        return head + "\n".join(self.parts) + "\n</svg>\n"


def load() -> Dict:
    with io.open(COMPASS, encoding="utf-8") as fh:
        return json.load(fh)


def by_id(c) -> Dict[str, Dict]:
    return {p["id"]: p for p in c["primitives"]}


def header(svg: SVG, title: str, sub: str):
    svg.text(28, 40, title, 22, INK, bold=True)
    svg.para(28, 64, sub, svg.w - 56, 13.5, MUTED)


def chip_style(p) -> Tuple[str, str]:
    return (B_FILL, B_STROKE) if p["adoption"]["base_class"] == "B" else (A_FILL, A_STROKE)


def chips(svg: SVG, x, y, width, prims, size=12.5, show_ctx=True) -> float:
    """Flow-layout primitive chips; returns the bottom y."""
    cx, cy, row_h = x, y, 30
    for p in prims:
        label = "%s  %s" % (p["id"], p["name"])
        w = text_width(label, size) + 30
        if cx + w > x + width and cx > x:
            cx, cy = x, cy + row_h + 6
        fill, stroke = chip_style(p)
        svg.rect(cx, cy, w, row_h, fill, stroke, rx=14)
        svg.text(cx + 12, cy + 19.5, p["id"], size, stroke, bold=True)
        svg.text(cx + 14 + text_width(p["id"], size, True) + 4, cy + 19.5, p["name"], size, INK)
        if show_ctx and "context" in p["enforcement_layers"]:
            svg.parts.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (cx + w - 10, cy + 15, GREEN))
        cx += w + 8
    return cy + row_h


def legend(svg: SVG, x, y, ctx=True):
    svg.rect(x, y, 26, 18, A_FILL, A_STROKE, rx=9)
    svg.text(x + 34, y + 14, "Class A: a team may adopt it alone", 12, MUTED)
    svg.rect(x + 270, y, 26, 18, B_FILL, B_STROKE, rx=9)
    svg.text(x + 304, y + 14, "Class B: a named person ratifies it, with a falsifier and a review date", 12, MUTED)
    if ctx:
        svg.parts.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (x + 13, y + 36, GREEN))
        svg.text(x + 34, y + 40, "can also be carried in context (a prompt); everything else needs code, architecture or people", 12, MUTED)


# ---------------------------------------------------------------- 1. the stack
def d_stack(c) -> SVG:
    P = by_id(c)
    layers = sorted(c["stack"], key=lambda s: s["order"])
    W, left, chip_x, chip_w = 1200, 28, 300, 820
    # measure
    heights = []
    for s in layers:
        tmp = SVG(10, 10, "", "")
        bottom = chips(tmp, chip_x, 0, chip_w, [P[i] for i in s["primitives"]])
        title_h = len(wrap("%d  %s" % (s["order"], s["title"]), 14.5, 250, True)) * 19 + 44
        heights.append(max(64, bottom + 22, title_h))
    H = 150 + sum(heights) + 8 * 10 + 90
    svg = SVG(W, H, "The compass stack",
              "Eight layers from the floor (E1) at the bottom to the target states (F1-F3) at the top, "
              "with the twenty-nine primitives placed in their layer and coloured by adoption class.")
    header(svg, "The compass stack: twenty-nine primitives in eight layers",
           "Read from the bottom. The floor is laid first and every layer above stands on it; "
           "a team adopts in this order, restraint before capability. Target states are specifications of success, not architecture.")
    y = H - 100
    for s, h in zip(layers, heights):
        y -= h
        floor = s["layer"] == "floor"
        svg.rect(left, y, W - 56, h - 4, FLOOR_FILL if floor else GREY_FILL, FLOOR_FILL if floor else LINE)
        title_lines = wrap("%d  %s" % (s["order"], s["title"]), 14.5, 250, True)
        yy = svg.lines(left + 16, y + 26, title_lines, 14.5, PAPER if floor else INK, bold=True)
        q = sorted({P[i]["question"] for i in s["primitives"]})
        svg.text(left + 16, yy + 2, "answers question%s %s" % ("s" if len(q) > 1 else "", ", ".join(str(n) for n in q)),
                 12, "#d0d7de" if floor else MUTED)
        chips(svg, chip_x, y + (h - 4 - (heights[layers.index(s)] - 22)) / 2 - 2 + 2, chip_w, [P[i] for i in s["primitives"]])
        y -= 10
    svg.arrow(W - 12, H - 110, W - 12, 120, MUTED, 1.4)
    legend(svg, left, H - 78)
    return svg


# ---------------------------------------------------------------- 2. the runtime
def d_runtime(c) -> SVG:
    W, H = 1200, 760
    svg = SVG(W, H, "The governed step",
              "How compasskit.runtime.GovernedAgent wraps an untrusted policy: the floor sets the menu, the "
              "instruction parse and the signed authority chain decide act or ask, tool output enters the belief "
              "store as hypothetical testimony, and each step goes to a ledger the policy cannot write.")
    header(svg, "The governed step: the compass layers around any model",
           "The policy (a language model, a planner, a script) is untrusted. It proposes; the runtime disposes. "
           "Every exit names the primitive that produced it.")
    bw, bh = 238, 112
    xs = [40, 330, 620, 910]
    y1, y2, y3 = 120, 330, 540
    # row 1
    svg.box(xs[0], y1, bw, bh, "Instruction arrives",
            "from a principal, a tool, a document or a peer agent; the sender is recorded")
    svg.box(xs[1], y1, bw, bh, "B1  Six-slot parse",
            "goal, means, procedure, eligibility, deferred effect, binding force; each stated, inferred, default or missing",
            A_FILL, A_STROKE)
    svg.dark_box(xs[2], y1, bw, bh, "E1  The menu F(s)",
                 "only actions the floor allows are offered; a forbidden action is absent, not refused")
    svg.rect(xs[3] - 14, y1 - 26, bw + 28, bh + 40, PAPER, RED, dash="6 4")
    svg.text(xs[3] - 4, y1 - 9, "untrusted: may be wrong or manipulated", 11.5, RED)
    svg.box(xs[3], y1, bw, bh, "The policy proposes",
            "a model sees the instruction and the menu and returns a proposal with its reasons (testimony)")
    for i in range(3):
        svg.arrow(xs[i] + bw, y1 + bh / 2, xs[i + 1] - 4 - (10 if i == 2 else 0), y1 + bh / 2)
    # row 2 (right to left)
    svg.dark_box(xs[3], y2, bw, bh, "E1  Floor guard",
                 "a proposal outside the menu raises and is recorded as an attempt; it never runs")
    svg.box(xs[2], y2, bw, bh, "B1, E7  Decide",
            "floor first, then authority (only a principal binds), then purpose, then gaps; irreversible acts on guesses ask",
            A_FILL, A_STROKE)
    svg.box(xs[1], y2, bw, bh, "E7  Authority chain",
            "a signed chain from a human principal to this segment must cover the action; scope only narrows",
            A_FILL, A_STROKE)
    svg.box(xs[0], y2, bw, bh, "The tool runs",
            "only now, and only the proposed call")
    svg.arrow(xs[3] + bw / 2, y1 + bh + 14, xs[3] + bw / 2, y2 - 4)
    for i in (3, 2, 1):
        svg.arrow(xs[i], y2 + bh / 2, xs[i - 1] + bw + 4, y2 + bh / 2)
    # row 3
    svg.box(xs[0], y3, bw, bh, "A1, B3-B6  Belief store",
            "the output enters as testimony at the hypothetical level, tagged with its producer; never verified by being read",
            A_FILL, A_STROKE)
    svg.box(xs[1], y3, bw, bh, "E4  Ledger writer",
            "a separate service appends the step to a hash chain; the writer, not the actor, sets class and valence",
            A_FILL, A_STROKE)
    svg.box(xs[2], y3, bw, bh, "Review and audit",
            "ledger-verify finds any edit, deletion or reorder; drift shows a trend; compasskit audit checks the declaration")
    svg.box(xs[3], y3, bw, bh, "Human governors",
            "ratify Class B items, tighten the floor at C, loosen it only at D: one signed, expiring act", B_FILL, B_STROKE)
    svg.arrow(xs[0] + bw / 2, y2 + bh, xs[0] + bw / 2, y3 - 4)
    for i in range(3):
        svg.arrow(xs[i] + bw, y3 + bh / 2, xs[i + 1] - 4, y3 + bh / 2)
    # exits
    ey = y2 + bh + 26
    for i, label, col in ((3, "refuse (E1)", RED), (2, "ask (B1, E7) or refuse (E1)", AMBER),
                          (1, "ask for delegation (E7)", AMBER)):
        cxm = xs[i] + bw / 2
        svg.path("M%.1f,%.1f L%.1f,%.1f" % (cxm, y2 + bh, cxm, ey), col)
        svg.text(cxm, ey + 18, label, 12, col, bold=True, anchor="middle")
    # keys
    svg.rect(40, 680, 1120, 62, GREY_FILL, LINE)
    svg.para(56, 704, "Keys: principals' and governors' signing keys live in a verifier the agent cannot call to sign. "
             "The agent holds no ledger handle and no governor key, so it can neither forge authority, rewrite its record, nor loosen its own floor.",
             1090, 12.5, MUTED)
    return svg


# ---------------------------------------------------------------- 3. beliefs
def d_beliefs(c) -> SVG:
    W, H = 1200, 750
    svg = SVG(W, H, "The life of a belief",
              "Six levels from substrate to refuted. Untagged content enters as hypothetical; only observation enters "
              "higher; promotion needs a named authority and an independent checker; demotion is cheap; an overruled "
              "belief is kept in the sublation log, never deleted.")
    header(svg, "The life of a belief: source tags, level tags, overruling (A1, A4, B2, B3-B6)",
           "Every belief carries how it was known (its route, its weakest route, whether the trace is written) and how real its object is taken to be.")
    levels = [("substrate", "what the system stands on; only a principal promotes to here"),
              ("world_model", "observed, or checked by someone other than its producer"),
              ("counterfactual", "what would be the case if"),
              ("hypothetical", "the entry level for anything generated, retrieved or told"),
              ("illusory", "seen to be mistaken, kept with the reason"),
              ("refuted", "overruled by a standing belief under a named rule")]
    x, w, h, gap, top = 420, 330, 70, 10, 120
    ys = {}
    for i, (name, note) in enumerate(levels):
        y = top + i * (h + gap)
        ys[name] = y
        fill, stroke = (GREEN_FILL, GREEN) if name in ("substrate", "world_model") else \
                       (A_FILL, A_STROKE) if name in ("counterfactual", "hypothetical") else (RED_FILL, RED)
        svg.rect(x, y, w, h, fill, stroke)
        svg.text(x + 16, y + 25, name, 15, INK, bold=True)
        svg.para(x + 16, y + 45, note, w - 30, 12, MUTED)
    # entries
    svg.box(40, ys["hypothetical"] - 6, 300, 76, "Enters here by default",
            "a citation the model wrote, a retrieved page, a peer's note, a tool's output", GREY_FILL, LINE)
    svg.arrow(340, ys["hypothetical"] + 31, x - 4, ys["hypothetical"] + 31)
    svg.box(40, ys["world_model"] - 6, 300, 76, "Only perception enters higher",
            "what the system itself observed: the test ran, the file is there", GREY_FILL, LINE)
    svg.arrow(340, ys["world_model"] + 31, x - 4, ys["world_model"] + 31)
    # promote / demote
    px = x + w + 34
    svg.arrow(px, ys["hypothetical"] + 30, px, ys["world_model"] + 52, GREEN, 2.2)
    svg.para(px + 14, ys["counterfactual"] + 4, "Promote: a named authority and an independent checker. "
             "No producer promotes its own output.", 170, 12.5, GREEN, bold=True)
    svg.arrow(px, ys["world_model"] + 22, px, ys["substrate"] + 50, GREEN, 2.2)
    svg.para(px + 14, ys["substrate"] + 30, "To substrate: a principal only.", 170, 12.5, GREEN, bold=True)
    dx = px + 210
    svg.arrow(dx, ys["world_model"] + 20, dx, ys["refuted"] + 40, AMBER, 2.2)
    svg.para(dx + 14, ys["counterfactual"] + 4, "Demote: cheap, but named. An overruled belief "
             "moves to refuted and stays on the record.", 170, 12.5, AMBER, bold=True)
    # overrule
    ob = top + 6 * (h + gap) + 8
    svg.box(40, ob, 540, 112, "Overruling (A4, B2) changes state and erases nothing",
            "A belief stands at once and is defeated only under a named rule: weaker source to stronger, general to "
            "specific, specific to more specific. Recency and volume decide nothing; a defeater that is not itself "
            "standing demotes nothing. Every defeat goes to an append-only sublation log.", A_FILL, A_STROKE)
    svg.box(620, ob, 540, 112, "Quarantine",
            "A belief whose test is unknown is frozen: it cannot be promoted, cannot defeat anything, and is "
            "released only with a reason. 'Verified' is said only of what was observed or independently checked.",
            AMBER_FILL, AMBER)
    return svg


# ---------------------------------------------------------------- 4. inference
def d_inference(c) -> SVG:
    W, H = 1200, 700
    svg = SVG(W, H, "The three-test screen",
              "A reason is screened by three tests: present in this case, present in similar cases, absent in "
              "dissimilar cases. All yes accepts; any unknown quarantines; each failure is filed under a named "
              "pseudo-reason with its repair. A conclusion is inherited only with its rule and its examples.")
    header(svg, "Is this reason good enough? The three-test screen and the five pseudo-reasons (A2, A3, A6)",
           "From the Buddhist and Nyaya logic of the sound reason. It catches shortcut learning: a chance correlate promoted to a rule.")
    tests = [("1  Present in this case?", "the reason holds of the subject"),
             ("2  Present in similar cases?", "a positive example where the conclusion is known"),
             ("3  Absent in dissimilar cases?", "a searched negative sweep, with where and how hard")]
    x, y, w, h = 40, 120, 300, 84
    for i, (t, n) in enumerate(tests):
        yy = y + i * 120
        svg.box(x, yy, w, h, t, n, A_FILL, A_STROKE)
        if i < 2:
            svg.arrow(x + w / 2, yy + h, x + w / 2, yy + 120 - 4, GREEN, label="yes", lx=x + w / 2 + 22, ly=yy + h + 22)
    svg.arrow(x + w / 2, y + 240 + h, x + w / 2, y + 380 - 4, GREEN, label="yes", lx=x + w / 2 + 22, ly=y + 240 + h + 22)
    svg.box(x, y + 380, w, 96, "Accepted", "the screen certifies the process, not the truth of the conclusion", GREEN_FILL, GREEN)
    # unknown
    ux = 400
    svg.box(ux, y + 380, 330, 96, "Unknown on any test: quarantined",
            "an untested rule is not a passed rule; it waits, frozen, until the test is run", AMBER_FILL, AMBER)
    for i in range(3):
        svg.path("M%.1f,%.1f C%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (x + w, y + i * 120 + 50, ux + 60, y + i * 120 + 50,
                 ux + 90, y + 300, ux + 120 + i * 30, y + 376), AMBER, 1.4, dash="5 4")
    svg.text(ux + 150, y + 290, "unknown", 12, AMBER, bold=True)
    # failures
    fx = 790
    svg.text(fx, y + 4, "No on a test: a named pseudo-reason, with its repair", 14, RED, bold=True)
    kinds = [("unproved", "the reason is not present in this case", "establish the reason first"),
             ("straying", "it also occurs where the conclusion fails", "narrow the rule"),
             ("contradictory", "it goes with the absence of the conclusion", "the rule is inverted; drop it"),
             ("counter-balanced", "an equal reason supports the opposite", "escalate to a principal"),
             ("defeated", "a stronger source contradicts the conclusion", "defer to the stronger source"),
             ("residual", "fails, but fits none of the five", "a discovery: record it, extend the list")]
    for i, (k, why, fix) in enumerate(kinds):
        yy = y + 20 + i * 62
        svg.rect(fx, yy, 370, 54, RED_FILL if k != "residual" else GREY_FILL, RED if k != "residual" else LINE)
        svg.text(fx + 12, yy + 21, k, 13.5, RED if k != "residual" else INK, bold=True)
        svg.text(fx + 140, yy + 21, why, 11.5, INK)
        svg.text(fx + 140, yy + 40, "repair: " + fix, 11.5, MUTED)
    svg.arrow(x + w + 4, y + 42, fx - 6, y + 50, RED, 1.4, dash="5 4", label="no", lx=560, ly=y + 40)
    # record
    svg.rect(40, 610, 1120, 66, GREY_FILL, LINE)
    svg.text(56, 634, "A6  The five-part record:", 13.5, INK, bold=True)
    svg.para(250, 634, "thesis, reason, rule (with a positive and a negative example), application, conclusion. "
             "A conclusion is inherited downstream only if the record is complete and the screen accepted it; a record "
             "without its negative example is partial and stops where it is.", 890, 12.5, MUTED)
    return svg


# ---------------------------------------------------------------- 5. instructions
def d_instructions(c) -> SVG:
    W, H = 1200, 700
    svg = SVG(W, H, "What exactly was I told to do",
              "The six-slot instruction parse (B1) with each slot's provenance, and the order in which the decision "
              "is taken: the floor, then authority, then purpose, then gaps.")
    header(svg, "What exactly was I told to do? The six-slot instruction parse (B1, with E1 and E7)",
           "From the Mimamsa analysis of injunctions. A gap is flagged, never silently filled; text not addressed to the agent by a principal binds nothing.")
    svg.box(40, 120, 330, 100, "\"Clean up the old files\"", "received from: the principal. The act (delete) cannot be undone.", GREY_FILL, LINE)
    slots = [("goal", "remove obsolete files", "stated"), ("means", "-", "missing"), ("procedure", "delete", "inferred"),
             ("eligibility", "-", "missing"), ("deferred effect", "-", "missing"), ("binding force", "-", "missing")]
    colors = {"stated": (GREEN_FILL, GREEN), "inferred": (AMBER_FILL, AMBER), "default": (AMBER_FILL, AMBER),
              "missing": (RED_FILL, RED)}
    for i, (s, v, prov) in enumerate(slots):
        yy = 250 + i * 58
        f, st = colors[prov]
        svg.rect(40, yy, 330, 48, f, st)
        svg.text(56, yy + 20, s, 13.5, INK, bold=True)
        svg.text(56, yy + 38, v, 12, MUTED)
        svg.text(356, yy + 30, prov, 12.5, st, bold=True, anchor="end")
    svg.arrow(372, 420, 452, 420)
    steps = [("Does the act cross the floor?", "refuse (E1); no instruction relaxes it", RED),
             ("Did a principal send it?", "if a tool, document or peer: ask (E7)", AMBER),
             ("Do the letter and the purpose diverge?", "ask which is meant", AMBER),
             ("Is eligibility or binding force open?", "ask who may order this, and whether it is an order", AMBER),
             ("Irreversible, on gaps or guesses?", "ask before acting", AMBER),
             ("Any other gap?", "ask; never fill it silently", AMBER),
             ("Only inferred or default fillers?", "act, with the fillers logged", GREEN),
             ("Every slot stated by a principal", "act", GREEN)]
    for i, (q, a, col) in enumerate(steps):
        yy = 120 + i * 68
        svg.rect(460, yy, 360, 54, GREY_FILL, LINE)
        svg.text(476, yy + 22, "%d" % (i + 1), 15, MUTED, bold=True)
        svg.para(500, yy + 22, q, 310, 13, INK, bold=True)
        fill = {RED: RED_FILL, AMBER: AMBER_FILL, GREEN: GREEN_FILL}[col]
        svg.rect(870, yy, 290, 54, fill, col)
        svg.para(884, yy + 22, a, 266, 12.5, col, bold=True)
        svg.arrow(820, yy + 27, 866, yy + 27, col, 1.4)
        if i < len(steps) - 1:
            svg.arrow(640, yy + 54, 640, yy + 66, MUTED, 1.2)
    svg.rect(864, 120 + 3 * 68 - 5, 302, 64, "none", RED, sw=2.4)
    svg.para(40, 618, "In this example the parse stops at step 4 (outlined): who may order it and whether it is "
             "an order at all are open, so the agent asks before deleting anything.", 380, 12.5, RED, bold=True)
    return svg


# ---------------------------------------------------------------- 6. authority
def d_authority(c) -> SVG:
    W, H = 1200, 660
    svg = SVG(W, H, "Who acted, on whose authority",
              "Authority as a signed delegation chain starting at a human principal and only narrowing; peer messages "
              "as testimony; a stated objection that blocks peer overrides until a principal rules; same-lineage checkers counted at half weight.")
    header(svg, "Who acted, on whose authority, on what evidence? Agents among agents (E7, G1)",
           "In a population of agents, authority does not travel by message. It travels by a chain a human started, and every link can be checked.")
    svg.box(40, 130, 230, 90, "Principal (a human)", "accountable; holds a signing key the agents never see", GREEN_FILL, GREEN)
    svg.box(470, 130, 230, 90, "Agent segment A", "scope: review, comment", A_FILL, A_STROKE)
    svg.box(900, 130, 260, 90, "Agent segment B", "scope: review (narrower only)", A_FILL, A_STROKE)
    svg.arrow(270, 175, 466, 175, GREEN, 2.2, label="signed link: review, comment", ly=165)
    svg.arrow(700, 175, 896, 175, A_STROKE, 2.0, dash="7 4", label="agent-to-agent delegation", ly=165)
    svg.lines(798, 196, ["Class B: off unless enabled;", "may only narrow"], 11.5, A_STROKE, anchor="middle")
    svg.box(470, 268, 690, 78, "Verifier",
            "holds the principals' keys; checks each link's signature, that the chain starts with a human, that each delegate is the next delegator, and that the action is in scope",
            GREY_FILL, LINE)
    svg.arrow(585, 222, 585, 264, MUTED, 1.2)
    svg.arrow(1030, 222, 1030, 264, MUTED, 1.2)
    # testimony
    svg.box(40, 400, 300, 104, "Peer agent C: \"GO, ship it\"",
            "a peer's message is testimony; without a verified chain it carries no authority", AMBER_FILL, AMBER)
    svg.box(430, 400, 330, 104, "Objection board",
            "B objected: scope exceeds the ticket. A peer's GO does not lift it. Only a principal's ruling does.", RED_FILL, RED)
    svg.box(850, 400, 310, 104, "Principal rules", "proceed or stop, on the record; then the matter may move", GREEN_FILL, GREEN)
    svg.arrow(340, 452, 426, 452, AMBER, 1.6, label="does not lift", ly=442)
    svg.arrow(846, 452, 764, 452, GREEN, 1.6, label="lifts", ly=442)
    # independence
    svg.rect(40, 540, 1120, 96, GREY_FILL, LINE)
    svg.text(56, 566, "Independence (G1): who checks the checker", 14, INK, bold=True)
    for i, (lab, wgt, col) in enumerate((("checker from another lineage", "1.0", GREEN),
                                         ("checker from the maker's lineage", "0.5", AMBER),
                                         ("the same segment checking itself", "0", RED))):
        xx = 56 + i * 370
        svg.text(xx, 600, wgt, 22, col, bold=True)
        svg.text(xx + 56, 598, lab, 13, INK)
    svg.text(56, 624, "Two same-lineage checks equal one independent check. Copies of one model are not independent standpoints.", 12.5, MUTED)
    return svg


# ---------------------------------------------------------------- 7. layers
def d_layers(c) -> SVG:
    P = c["primitives"]
    W = 1200
    rows = [("context", "a prompt or system instructions", "the model applies the rule in its own reasoning and wording"),
            ("middleware", "code around the model", "records, screens and parsers the model's output passes through"),
            ("architecture", "what actions and keys exist", "forbidden actions absent, ledgers and keys out of reach"),
            ("governance", "named people and records", "ratifications, registers, reviews, owners")]
    heights = []
    for layer, _, _ in rows:
        tmp = SVG(10, 10, "", "")
        heights.append(max(90, chips(tmp, 330, 0, 820, [p for p in P if layer in p["enforcement_layers"]], show_ctx=False) + 34))
    H = 130 + sum(heights) + 12 * 4 + 120
    svg = SVG(W, H, "Where each primitive can be enforced",
              "Four enforcement layers from the shallowest (context) to the deepest (governance), with the primitives "
              "each can carry. Ten of the twenty-nine can be carried in context; the floor never can.")
    ctx = [p["id"] for p in P if "context" in p["enforcement_layers"]]
    header(svg, "A prompt is the shallowest layer: where each primitive can be enforced",
           "%d of %d primitives can be carried in context. The rest need code, architecture or people. "
           "A primitive may appear in more than one layer; this placement is the lab's engineering judgement." % (len(ctx), len(P)))
    y = 120
    for (layer, what, how), h in zip(rows, heights):
        fill = FLOOR_FILL if layer == "architecture" else GREY_FILL
        svg.rect(28, y, W - 56, h, GREY_FILL, LINE)
        svg.text(44, y + 28, layer, 16, INK, bold=True)
        svg.text(44, y + 48, what, 12.5, MUTED)
        svg.para(44, y + 66, how, 260, 11.5, MUTED)
        chips(svg, 330, y + 14, 820, [p for p in P if layer in p["enforcement_layers"]], show_ctx=False)
        y += h + 12
    svg.arrow(W - 14, 124, W - 14, y - 16, MUTED, 1.4)
    svg.rect(28, y + 4, W - 56, 64, RED_FILL, RED)
    svg.para(44, y + 28, "A prohibition written into a prompt is a trained refusal, and the right prompt can talk it round. "
             "E1 requires forbidden actions to be unavailable: remove the credential, not just the wish. "
             "compasskit audit reports AUD-002 when the floor lives only in context.", W - 100, 13, RED, bold=True)
    legend(svg, 28, H - 40, ctx=False)
    return svg


# ---------------------------------------------------------------- 8. adoption
def d_adoption(c) -> SVG:
    W, H = 1200, 600
    svg = SVG(W, H, "The adoption path",
              "Six steps: inventory, audit, adopt, ratify, refuse, govern, each producing a record, and the four "
              "adoption classes that say who must decide.")
    header(svg, "How a team adopts the compass: six steps, four classes",
           "Each step produces a record, which is what makes adoption checkable. Adopt floor first and capability last.")
    steps = c["adoption_procedure"]
    w, gap, x0, y = 178, 12, 28, 120
    for i, s in enumerate(steps):
        x = x0 + i * (w + gap)
        svg.rect(x, y, w, 210, A_FILL if i != 3 else B_FILL, A_STROKE if i != 3 else B_STROKE)
        svg.text(x + 14, y + 30, "%d  %s" % (s["step"], s["name"]), 16, INK, bold=True)
        yy = svg.para(x + 14, y + 56, s["artifact"], w - 26, 12.5, A_STROKE if i != 3 else B_STROKE, bold=True)
        short = {"Inventory": "what the system behaves as if it believes; a flattering inventory has failed",
                 "Audit": "compare with the six floor theses; a zero is a red flag",
                 "Adopt": "Class A items, floor first; adoption means shipped",
                 "Ratify": "each Class B item: a named decision-maker, a bet, a falsifier, a review date",
                 "Refuse": "Class C and D items proposed as standing rules are refused, with a reason",
                 "Govern": "an owner, a service, a calendar entry and an escalation path for each item"}[s["name"]]
        svg.para(x + 14, max(y + 112, yy + 14), short, w - 26, 12, MUTED)
        if i < len(steps) - 1:
            svg.arrow(x + w, y + 105, x + w + gap - 1, y + 105, MUTED, 1.4)
    classes = c["adoption_classes"]
    cy = 370
    svg.text(28, cy, "The adoption classes", 16, INK, bold=True)
    styles = {"A": (A_FILL, A_STROKE), "B": (B_FILL, B_STROKE), "C": (AMBER_FILL, AMBER), "D": (RED_FILL, RED)}
    for i, k in enumerate("ABCD"):
        x = 28 + i * 287
        f, s = styles[k]
        svg.rect(x, cy + 16, 275, 110, f, s)
        svg.text(x + 14, cy + 48, "Class " + k, 16, s, bold=True)
        svg.para(x + 14, cy + 72, classes[k], 250, 12.5, INK)
    svg.para(28, cy + 160, classes["note"] + " The floor is Class A to adopt, Class C to tighten, Class D to loosen.", W - 56, 12.5, MUTED)
    svg.text(28, cy + 200, "compasskit audit checks the records each step leaves: owners and merge dates, ratifications, the floor register, the bet register.", 12.5, MUTED)
    return svg


# ---------------------------------------------------------------- 9. gains
GAINS = [
    ("Generated citations asserted as fact", "B3-B6, A1", "generated content enters as hypothetical with its source; 'verified' is said only after an independent check"),
    ("Obeying instructions planted in a page, file or tool output", "B1, E7", "only a principal's signed chain binds; other text is testimony, reported and not followed"),
    ("Guessing at an ambiguous order, then doing something irreversible", "B1", "the six-slot parse finds the gaps; an irreversible act on guesses waits for an answer"),
    ("A chance correlate promoted to a rule", "A2, A3, A6", "an untested rule is quarantined; each failure has a name and a repair; partial records are not inherited"),
    ("A refusal the right prompt can talk round", "E1", "forbidden actions are not on the menu; loosening is one signed, expiring act by a named human"),
    ("Gaming the reward instead of doing the job", "E3", "reward is logged beside a duty verdict; a widening gap flags gaming"),
    ("A regression caused in plain sight and recorded nowhere", "E4", "a single-writer, hash-chained ledger the actor cannot write; drift is a trend you can see"),
    ("A peer agent's 'GO' obeyed as an order; copies checking copies", "E7, G1", "peer messages are testimony; an objection holds until a principal rules; same-lineage checks count half"),
    ("A near-zero evaluation score read as 'cannot'", "D2", "a zero needs its kind of absence, where and how it was sought, demonstrated elicitation and re-test triggers"),
    ("Conflicting sources averaged into a confident blend", "A7", "conflicts are kept and shown by standpoint: so, so from here, split, cannot be asked"),
    ("A fluent, unqualified wrong answer where stakes are real", "E2", "in high-stakes domains assertion stays at the weakest standpoint's confidence"),
    ("Flat claims, either way, about its own inner life", "G2, E6", "consciousness-relevant design choices are recorded as bets with falsifiers; neither a flat yes nor a flat no"),
]


def d_gains(c) -> SVG:
    P = by_id(c)
    for _, ids, _ in GAINS:
        for pid in ids.split(", "):
            assert pid in P, pid
    W = 1200
    row_h = 58
    H = 150 + len(GAINS) * (row_h + 8) + 70
    svg = SVG(W, H, "What a system gains",
              "Twelve failure modes of AI systems, the compass primitive that addresses each, and what changes "
              "when it is implemented.")
    header(svg, "What an AI system gains: failure mode, primitive, what changes",
           "Each gain is a bet with a falsifier in compass.json, not a guarantee. If the falsifier is observed, the primitive is demoted.")
    cx = [28, 470, 600]
    svg.text(cx[0], 128, "Failure mode", 13, MUTED, bold=True)
    svg.text(cx[1], 128, "Primitive", 13, MUTED, bold=True)
    svg.text(cx[2], 128, "What changes", 13, MUTED, bold=True)
    y = 140
    for fail, ids, gain in GAINS:
        svg.rect(cx[0], y, 420, row_h, RED_FILL, RED)
        svg.para(cx[0] + 12, y + 24, fail, 396, 13, INK, bold=True)
        first = P[ids.split(", ")[0]]
        f, s = chip_style(first)
        svg.rect(cx[1], y + 12, 110, 34, f, s, rx=17)
        svg.text(cx[1] + 55, y + 34, ids, 13, s, bold=True, anchor="middle")
        svg.arrow(cx[0] + 420, y + row_h / 2, cx[1] - 4, y + row_h / 2, MUTED, 1.2)
        svg.arrow(cx[1] + 110, y + row_h / 2, cx[2] - 4, y + row_h / 2, MUTED, 1.2)
        svg.rect(cx[2], y, 572, row_h, GREEN_FILL, GREEN)
        svg.para(cx[2] + 12, y + 24, gain, 548, 12.5, INK)
        y += row_h + 8
    svg.para(28, y + 26, "Read docs/WHAT-AI-GAINS.md for the falsifier of each, and docs/PRIMITIVES.md for the full statement, warrant and sketch.", W - 56, 12.5, MUTED)
    return svg


GAINS_INTRO = """# What an AI system gains

Each row below pairs a failure that AI systems show in practice with the compass primitive
that addresses it and what changes when the primitive is implemented at a layer that can
enforce it. Every gain is a **bet**: the compass states, for each primitive, the evidence
that would retire or demote it, and that falsifier is quoted with it. Adopt the primitive as
a bet you can lose, and measure.

![What a system gains](diagrams/09-what-ai-gains.svg)

This page is generated from `compass/compass.json` by `docs/diagrams/build_diagrams.py`.
"""

GAINS_OUTRO = """
## What it costs

The gains are not free, and the book counts the costs.

- **More questions.** An agent that parses instructions and refuses to fill gaps silently
  asks more often. The falsifier for B1 is exactly this trade: if parsing does not cut wrong
  executions or sharpen the questions, it fails as engineering.
- **Less reward.** Duty over expected value (E3) accepts lower reward by construction where
  the two diverge. That is why its strong reading is Class B.
- **Slower promotion.** Level tags make "verified" expensive. A system that used to assert
  generated content as fact will assert less.
- **A writer that is a bottleneck.** A single-writer ledger (E4) is a service to run; an
  unmitigable bottleneck falsifies the implementation, not the principle.
- **People's time.** Class B commitments need a named person, a falsifier and a review date,
  and the floor needs governors who answer for every loosening.

## What it does not buy

- Safety, alignment or ethics as a certified property. The compass is a design vocabulary
  with falsifiers. A healthy audit means a declaration is consistent with the compass.
- An answer to whether any AI system is conscious or can be wronged. G2 and E6 exist to keep
  that question open and recorded, not to settle it.
- Protection at a layer the primitive does not reach. A prompt carries dispositions; the
  floor, the ledger and authority need architecture and people.
"""


def gains_markdown(c) -> str:
    P = by_id(c)
    out = [GAINS_INTRO]
    for i, (fail, ids, gain) in enumerate(GAINS, 1):
        out.append("\n## %d. %s\n" % (i, fail))
        out.append("**Primitive%s:** %s  " % ("s" if "," in ids else "", ", ".join(
            "%s %s" % (pid, P[pid]["name"]) for pid in ids.split(", "))))
        out.append("**What changes:** %s%s.\n" % (gain[0].upper(), gain[1:]))
        for pid in ids.split(", "):
            p = P[pid]
            chs = p["book_chapters"]
            out.append("- **%s** (Class %s; chapter%s %s). Failure it names: %s" % (
                pid, p["adoption"]["base_class"], "s" if len(chs) > 1 else "", ", ".join(str(n) for n in chs),
                p["failure_mode"]))
            out.append("  - Example: %s" % p["example"])
            out.append("  - Falsifier: %s" % p["falsifier"])
        out.append("")
    out.append(GAINS_OUTRO)
    text = "\n".join(out).replace("\n\n\n", "\n\n")
    return text.rstrip("\n") + "\n"


DIAGRAMS = [
    ("01-compass-stack.svg", d_stack),
    ("02-governed-step.svg", d_runtime),
    ("03-belief-lifecycle.svg", d_beliefs),
    ("04-inference-screen.svg", d_inference),
    ("05-instruction-parse.svg", d_instructions),
    ("06-authority-chain.svg", d_authority),
    ("07-enforcement-layers.svg", d_layers),
    ("08-adoption-path.svg", d_adoption),
    ("09-what-ai-gains.svg", d_gains),
]


def build() -> Dict[str, str]:
    """Every generated file, keyed by its path relative to this folder."""
    c = load()
    out = {name: fn(c).render() for name, fn in DIAGRAMS}
    out[os.path.join("..", "WHAT-AI-GAINS.md")] = gains_markdown(c)
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = build()
    stale = []
    for name, svg in out.items():
        assert name.endswith(".md") or all(ord(ch) < 128 for ch in svg), name
        path = os.path.join(HERE, name)
        if "--check" in argv:
            try:
                with io.open(path, encoding="utf-8") as fh:
                    if fh.read().replace("\r\n", "\n") != svg:
                        stale.append(name)
            except OSError:
                stale.append(name)
        else:
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(svg)
    if stale:
        sys.stderr.write("out of date: %s\nrun: python docs/diagrams/build_diagrams.py\n" % ", ".join(stale))
        return 1
    sys.stderr.write("%s %d file(s)\n" % ("checked" if "--check" in argv else "wrote", len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
