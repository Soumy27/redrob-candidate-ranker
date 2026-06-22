#!/usr/bin/env python3
"""Convenience: produce an XLSX copy of the ranked submission.

The official submission format is CSV (see submission_spec). This script just
mirrors submission.csv into submission.xlsx for easier human inspection.

    python make_xlsx.py --csv ./submission.csv --out ./submission.xlsx
"""

import argparse

import pandas as pd


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="submission.csv")
    p.add_argument("--out", default="submission.xlsx")
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    with pd.ExcelWriter(args.out, engine="openpyxl") as xl:
        df.to_excel(xl, index=False, sheet_name="ranking")
        ws = xl.sheets["ranking"]
        ws.column_dimensions["A"].width = 16
        ws.column_dimensions["B"].width = 6
        ws.column_dimensions["C"].width = 9
        ws.column_dimensions["D"].width = 120
    print(f"wrote {args.out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
