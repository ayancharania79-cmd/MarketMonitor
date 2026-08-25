#!/usr/bin/env python3
"""Flag suspicious swings in a freshly-fetched data/quotes.json before it's built/published.

Compares the working-tree quotes.json against the version at git HEAD (the last
committed, already-vetted snapshot) and prints any ticker whose price moved by
more than THRESHOLD without a plausible same-day explanation. A big move isn't
necessarily wrong (real gaps happen, M&A, etc.) — but it's exactly the kind of
thing a bad WebSearch-sourced number looks like (see: TTE briefly reported as
$89.35 instead of ~$61 because a fetch pass grabbed the wrong listing). Run
this after refreshing quotes.json and before tools/build.py; anything it flags
is worth one quick verification search before publishing.
"""
import json, subprocess, sys, pathlib

THRESHOLD = 0.20  # 20% move triggers a flag

BASE = pathlib.Path(__file__).parent.parent

def load_head_quotes():
    try:
        raw = subprocess.run(
            ["git", "show", "HEAD:data/quotes.json"],
            cwd=BASE, capture_output=True, text=True, check=True,
        ).stdout
        return {(q["exchange"], q["ticker"]): q for q in json.loads(raw)}
    except Exception as e:
        print(f"(no previous committed quotes.json to compare against: {e})")
        return {}

def main():
    new = json.load(open(BASE / "data" / "quotes.json"))
    old = load_head_quotes()
    flagged = []
    for q in new:
        key = (q["exchange"], q["ticker"])
        prev = old.get(key)
        if not prev or prev.get("price") is None or q.get("price") is None:
            continue
        if prev.get("currency") != q.get("currency"):
            flagged.append((q["ticker"], prev["price"], q["price"], "currency changed: "
                             f"{prev.get('currency')} -> {q.get('currency')}"))
            continue
        delta = abs(q["price"] - prev["price"]) / prev["price"]
        if delta > THRESHOLD:
            flagged.append((q["ticker"], prev["price"], q["price"], f"{delta*100:.0f}% move"))
    if flagged:
        print(f"⚠ {len(flagged)} ticker(s) moved >{THRESHOLD*100:.0f}% since the last committed snapshot — verify before publishing:")
        for ticker, old_p, new_p, why in flagged:
            print(f"  {ticker}: {old_p} -> {new_p}  ({why})")
        sys.exit(1)
    else:
        print("No suspicious swings vs. the last committed snapshot.")

if __name__ == "__main__":
    main()
