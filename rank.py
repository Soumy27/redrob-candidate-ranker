#!/usr/bin/env python3
"""Produce the top-100 candidate ranking CSV for the Redrob Senior AI Engineer JD.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runs on CPU only, makes no network calls, and finishes well inside the
5-minute / 16 GB budget on the full 100K-candidate pool.
"""

import argparse

from candidate_ranker.pipeline import run


def main():
    p = argparse.ArgumentParser(description="Redrob candidate ranker")
    p.add_argument("--candidates", required=True,
                   help="Path to candidates.jsonl or candidates.jsonl.gz")
    p.add_argument("--out", default="submission.csv",
                   help="Output CSV path (default: submission.csv)")
    p.add_argument("--top", type=int, default=100, help="How many to rank")
    p.add_argument("--quiet", action="store_true", help="Suppress progress logs")
    args = p.parse_args()

    run(args.candidates, args.out, top_n=args.top, verbose=not args.quiet)


if __name__ == "__main__":
    main()
