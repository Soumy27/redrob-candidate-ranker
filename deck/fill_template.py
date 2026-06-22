#!/usr/bin/env python3
"""Fill the official Redrob / H2S "Idea Submission Template" with our content.

We stamp answer text directly onto the provided template PDF (keeping its exact
cover, branding bars and section headings), replacing the prompt-questions on
each content slide with our own answers. Output: ../Redrob_Idea_Submission_Agilus.pdf
"""

import io
import os

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, "..", "..", "Idea Submission Template _ Redrob - Google Slides.pdf")
OUT = os.path.join(HERE, "..", "Redrob_Idea_Submission_Agilus.pdf")

W, H = 720.0, 405.0          # template page size (points)
PX = 0.72                    # image-pixel -> point scale (720/1000)

pdfmetrics.registerFont(TTFont("Body", "/System/Library/Fonts/Supplemental/Arial.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))

INK = HexColor("#33333B")
PURPLE = HexColor("#7A5CFF")
WHITE = HexColor("#FFFFFF")
BOXBG = HexColor("#F4F2FF")
BOXLINE = HexColor("#D9D2FF")


def yc(py):                  # image-y (px, top origin) -> point-y
    return H - py * PX


def xc(px):
    return px * PX


# --------------------------------------------------------------------------- #
def wrap_runs(c, runs, x, y, width, size=11.5, leading=16.5):
    """Lay out (text, bold) runs with word wrap. Returns the y after the block."""
    space = c.stringWidth(" ", "Body", size)
    cx, cy = x, y
    for text, bold in runs:
        font = "Body-Bold" if bold else "Body"
        for word in text.split():
            ww = c.stringWidth(word, font, size)
            if cx + ww > x + width and cx > x:
                cx = x
                cy -= leading
            c.setFont(font, size)
            c.setFillColor(INK)
            c.drawString(cx, cy, word)
            cx += ww + space
    return cy - leading


def bullets(c, items, start_y=300, x_dot=50, x_text=66, width=596,
            size=11.5, leading=16.5, gap=9):
    """Draw purple-dot bullets; each item is a list of (text, bold) runs."""
    y = start_y
    for runs in items:
        c.setFillColor(PURPLE)
        c.circle(x_dot, y + 3.5, 2.6, fill=1, stroke=0)
        y = wrap_runs(c, runs, x_text, y, width, size, leading) - gap
    return y


def cover_body(c, top_px=132, bot_px=545):
    """White-out the prompt region (content slides are white) below the heading."""
    c.setFillColor(WHITE)
    y_top, y_bot = yc(top_px), yc(bot_px)
    c.rect(0, y_bot, W, y_top - y_bot, fill=1, stroke=0)


def box(c, x, y, w, h, text, size=8.6):
    c.setFillColor(BOXBG)
    c.setStrokeColor(BOXLINE)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 5, fill=1, stroke=1)
    c.setFont("Body-Bold", size)
    c.setFillColor(INK)
    # centre, allow up to two lines
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if c.stringWidth(t, "Body-Bold", size) <= w - 10:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    ty = y + h / 2 + (len(lines) - 1) * (size + 1) / 2 - size / 2 + 1
    for ln in lines:
        c.drawCentredString(x + w / 2, ty, ln)
        ty -= size + 1


def arrow(c, x1, y, x2):
    c.setStrokeColor(PURPLE)
    c.setFillColor(PURPLE)
    c.setLineWidth(1.3)
    c.line(x1, y, x2 - 4, y)
    c.line(x2 - 4, y, x2 - 8, y + 3)
    c.line(x2 - 4, y, x2 - 8, y - 3)


# --------------------------------------------------------------------------- #
def page_cover(c):
    """Slide 1 — fill Team Name / Leader / Problem Statement (no white-out)."""
    c.setFont("Body", 13)
    c.setFillColor(INK)
    c.drawString(xc(168), yc(358), "Agilus")
    c.drawString(xc(258), yc(404), "Soumy Dhiran")
    runs = [("Build an AI system that ranks candidates for a role the way a great recruiter "
             "would — by understanding the job and the whole candidate profile, not by "
             "matching keywords.", False)]
    wrap_runs(c, runs, xc(238), yc(450), 430, size=12, leading=16)


def page_solution(c):
    cover_body(c)
    bullets(c, [
        [("Proposed solution.  ", True),
         ("A hybrid candidate-ranking engine that fuses three signals — an offline "
          "semantic match between the JD and each candidate's real text, a structured "
          "evidence-weighted fit score, and a behavioural-availability modifier — and "
          "forces impossible / honeypot profiles to the bottom.", False)],
        [("What makes it different.  ", True),
         ("It ranks evidence, not keywords. A skill counts only when it appears in real "
          "career history, not in a self-listed tag — so keyword-stuffers (a "
          "“Marketing Manager” listing every AI skill) are filtered out, while genuine "
          "engineers who never used the buzzwords still surface.", False)],
    ])


def page_jd(c):
    cover_body(c)
    bullets(c, [
        [("Key requirements from the JD.  ", True),
         ("Production embeddings & retrieval, vector / hybrid search, ranking evaluation "
          "(NDCG / MRR / MAP), strong Python; ~6–8 yrs at product (not services) "
          "companies; Pune / Noida or willing to relocate; and explicit negatives — "
          "consulting-only careers, CV / speech without NLP, research-only, title-chasers.", False)],
        [("Signals that matter most.  ", True),
         ("Real career-history evidence and job title are decisive, then production / "
          "shipping language, the experience band, and availability (recruiter response "
          "rate and recency).", False)],
        [("Fit beyond keywords.  ", True),
         ("Concept evidence is weighted by where it appears — career descriptions count "
          "far more than bare skill tags — and the JD's stated negatives apply penalties.", False)],
    ])


def page_method(c):
    cover_body(c)
    bullets(c, [
        [("Retrieve.  ", True),
         ("All candidates and a plain-language JD query are vectorised with TF-IDF "
          "(1–2 grams); cosine similarity is the semantic signal — fully offline.", False)],
        [("Score.  ", True),
         ("A weighted sum of semantic similarity, core-concept evidence, title / role, "
          "production signal, experience band, location and nice-to-haves.", False)],
        [("Combine.  ", True),
         ("The fit score is multiplied by stated-negative penalties, then by a behavioural "
          "modifier (≈0.45–1.12); honeypots are forced to the bottom. Final sort is "
          "score-descending, ties broken by candidate_id.", False)],
    ])


def page_explain(c):
    cover_body(c)
    bullets(c, [
        [("How decisions are explained.  ", True),
         ("Every candidate gets a 1–2 sentence reason built only from its own record — "
          "title, years, a named in-profile skill, response rate, location — plus honest "
          "concerns drawn from the penalties that fired.", False)],
        [("Preventing hallucination.  ", True),
         ("Reasoning is assembled from verified fields only; all 100 rows were checked "
          "programmatically — every title, years, skill, response rate and location "
          "matches the source data.", False)],
        [("Suspicious profiles.  ", True),
         ("A detector flags arithmetic-impossible records (a single role longer than the "
          "whole career, ≥4 ‘expert’ skills with 0 months used) and sinks them; "
          "inactive / low-quality profiles are down-weighted by the behavioural modifier.", False)],
    ])


def page_workflow(c):
    cover_body(c)
    bullets(c, [
        [("End-to-end pipeline.  ", True),
         ("candidates.jsonl  →  load & extract evidence  →  TF-IDF semantic match to the "
          "JD  →  weighted fit score  →  negative penalties  →  behavioural modifier  "
          "→  honeypot gate  →  sort  →  top-100 with reasoning  →  submission.csv.", False)],
        [("Validation.  ", True),
         ("The output passes the official validate_submission.py (100 rows, unique ranks, "
          "non-increasing scores) and reproduces identically on every run.", False)],
    ])


def page_arch(c):
    cover_body(c, top_px=132, bot_px=545)
    # left-to-right pipeline, two rows
    y1 = yc(250)
    boxes1 = [
        (xc(60), "100K candidates  (JSONL)"),
        (xc(232), "Evidence extraction  (titles, history, signals)"),
        (xc(456), "Semantic match  (TF-IDF → JD)"),
    ]
    bw, bh = xc(150), 56
    xs = [xc(60), xc(258), xc(486)]
    labels1 = ["100K candidates (JSONL)", "Evidence extraction (titles, history, signals)",
               "Semantic match (TF-IDF vs JD)"]
    for x, lab in zip(xs, labels1):
        box(c, x, y1, bw, bh, lab)
    arrow(c, xs[0] + bw, y1 + bh / 2, xs[1])
    arrow(c, xs[1] + bw, y1 + bh / 2, xs[2])

    y2 = yc(360)
    labels2 = ["Weighted fit score", "Penalties × behavioural × honeypot gate",
               "Top-100 ranking + reasoning (CSV)"]
    for x, lab in zip(xs, labels2):
        box(c, x, y2, bw, bh, lab)
    arrow(c, xs[0] + bw, y2 + bh / 2, xs[1])
    arrow(c, xs[1] + bw, y2 + bh / 2, xs[2])
    # down arrow connecting row 1 -> row 2
    c.setStrokeColor(PURPLE)
    c.setLineWidth(1.3)
    c.line(xs[2] + bw / 2, y1, xs[2] + bw / 2, y1 - 8)
    c.line(xs[2] + bw / 2, y1 - 8, xs[0] + bw / 2, y1 - 8)
    c.line(xs[0] + bw / 2, y1 - 8, xs[0] + bw / 2, y2 + bh)
    c.setFillColor(PURPLE)
    c.line(xs[0] + bw / 2, y2 + bh, xs[0] + bw / 2 - 3, y2 + bh + 4)
    c.line(xs[0] + bw / 2, y2 + bh, xs[0] + bw / 2 + 3, y2 + bh + 4)

    c.setFont("Body", 9.5)
    c.setFillColor(INK)
    c.drawString(xc(60), yc(420),
                 "CPU-only · no network / LLM calls · ~60s for 100K candidates · deterministic output")


def page_results(c):
    cover_body(c)
    bullets(c, [
        [("Ranking quality.  ", True),
         ("The top 100 are 100% AI / ML / NLP / Search / Recommendation engineers with "
          "real retrieval and ranking experience — zero non-technical keyword-stuffers, "
          "and 34 impossible honeypot profiles gated out of the pool.", False)],
        [("Meets the constraints.  ", True),
         ("CPU-only, no network or LLM calls, under 4 GB RAM, and ~60 seconds for all "
          "100,000 candidates (limits are 5 minutes / 16 GB). Fully deterministic — "
          "re-running produces a byte-identical CSV (verified by checksum).", False)],
    ])


def page_tech(c):
    cover_body(c)
    bullets(c, [
        [("Stack.  ", True),
         ("Python 3 with scikit-learn (TF-IDF + cosine), NumPy and SciPy.", False)],
        [("Why these.  ", True),
         ("They are fully offline, CPU-friendly and fast at 100K scale — we deliberately "
          "avoid per-candidate neural inference so the system meets real production latency "
          "limits, the exact tradeoff the JD asks about.", False)],
        [("Scope.  ", True),
         ("pandas / openpyxl are used only for an optional spreadsheet export. No external "
          "or hosted-LLM APIs are used anywhere in the ranking.", False)],
    ])


def page_assets(c):
    cover_body(c)
    bullets(c, [
        [("GitHub repository.  ", True),
         ("github.com/Soumy27/redrob-candidate-ranker", False)],
        [("Ranked output.  ", True),
         ("Top-100 candidates as a validated CSV (Agilus.csv).", False)],
        [("Runnable sandbox.  ", True),
         ("Google Colab notebook that ranks a 100-candidate sample end-to-end.", False)],
        [("Demo video.  ", True),
         ("<add link>", False)],
    ])


PAGES = {
    0: page_cover, 1: page_solution, 2: page_jd, 3: page_method, 4: page_explain,
    5: page_workflow, 6: page_arch, 7: page_results, 8: page_tech, 9: page_assets,
    # page 10 (index 10) = Thank You -> leave untouched
}


def main():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    n = len(PdfReader(TEMPLATE).pages)
    for i in range(n):
        if i in PAGES:
            PAGES[i](c)
        c.showPage()
    c.save()
    buf.seek(0)

    overlay = PdfReader(buf)
    base = PdfReader(TEMPLATE)
    writer = PdfWriter()
    for i, page in enumerate(base.pages):
        page.merge_page(overlay.pages[i])
        writer.add_page(page)
    with open(OUT, "wb") as f:
        writer.write(f)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
