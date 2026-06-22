"""End-to-end ranking pipeline.

Steps:
  1. Load candidates.
  2. Extract structured evidence per candidate.
  3. Build a lexical-semantic similarity to the JD (offline TF-IDF cosine).
  4. Score = weighted fit -> negative penalties -> behavioural modifier -> honeypot gate.
  5. Sort, take top-N, normalise scores, attach grounded reasoning, write CSV.

Pure CPU, no network, comfortably inside the 5-minute / 16 GB budget.
"""

import csv
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .features import extract_features
from .job_profile import build_job_profile
from .loader import iter_candidates
from .reasoning import build_reasoning
from .scoring import score_candidate


def _semantic_similarities(texts, jd_query):
    """Offline TF-IDF cosine between each candidate text and the JD query.

    Catches the 'plain-language Tier-5' who describes building a recommender
    without ever using the buzzwords, while staying fully offline and fast.
    """
    vec = TfidfVectorizer(
        sublinear_tf=True,
        max_features=60000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
    )
    matrix = vec.fit_transform(texts)
    jd_vec = vec.transform([jd_query])
    sims = linear_kernel(jd_vec, matrix).ravel()  # tf-idf is L2-normalised
    hi = float(sims.max()) or 1.0
    lo = float(sims.min())
    span = (hi - lo) or 1.0
    return [(s - lo) / span for s in sims]


def run(candidates_path: str, out_path: str, top_n: int = 100, verbose: bool = True):
    t0 = time.time()
    jd = build_job_profile()

    feats, texts = [], []
    for cand in iter_candidates(candidates_path):
        f = extract_features(cand)
        feats.append(f)
        texts.append(f["semantic_text"])
    if verbose:
        print(f"[1/4] loaded + featurised {len(feats):,} candidates "
              f"({time.time() - t0:.1f}s)")

    sims = _semantic_similarities(texts, jd.semantic_query)
    if verbose:
        print(f"[2/4] semantic similarity computed ({time.time() - t0:.1f}s)")

    scored = []
    for f, sim in zip(feats, sims):
        final, breakdown = score_candidate(f, sim, jd.component_weights)
        scored.append((final, f, breakdown))
    if verbose:
        print(f"[3/4] scored all candidates ({time.time() - t0:.1f}s)")

    # rank: score desc, tie-break candidate_id ascending (matches validator)
    scored.sort(key=lambda x: (-x[0], x[1]["candidate_id"]))
    top = scored[:top_n]

    # normalise the top-N finals into a clean, non-increasing 4-decimal column
    raw = [s for s, _, _ in top]
    hi, lo = max(raw), min(raw)
    span = (hi - lo) or 1.0
    scored_top = []
    for final, f, breakdown in top:
        score = round(0.20 + 0.79 * (final - lo) / span, 4)
        scored_top.append((score, f, breakdown))

    # The validator's tie rule applies to the *output* score: when two rounded
    # scores collide, candidate_id must be ascending. Re-sort on the rounded
    # value so rounding never breaks the tie ordering.
    scored_top.sort(key=lambda x: (-x[0], x[1]["candidate_id"]))

    rows, prev = [], 1.01
    for rank, (score, f, breakdown) in enumerate(scored_top, start=1):
        if score > prev:           # belt-and-braces monotonicity guard
            score = prev
        prev = score
        reasoning = build_reasoning(f, breakdown, rank)
        rows.append([f["candidate_id"], rank, f"{score:.4f}", reasoning])

    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        w.writerows(rows)

    if verbose:
        n_hp = sum(1 for s, _, _ in scored if s == -1.0)
        print(f"[4/4] wrote {out_path} — top {top_n} of {len(scored):,} "
              f"({n_hp} honeypots gated out) in {time.time() - t0:.1f}s total")
    return rows
