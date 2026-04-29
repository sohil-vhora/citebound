"""
Run all eval test cases against Citebound and produce a results CSV + summary.

Usage: python evals/run_evals.py
"""

import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Allow importing from scripts/
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from answer import answer_question  # noqa: E402
from test_cases import TEST_CASES  # noqa: E402


# ─────────────────────────────────────────────────────────────
# Scoring rules
# ─────────────────────────────────────────────────────────────
REFUSAL_PHRASES = {
    "refuse_personal": [
        "can't tell you",
        "cannot tell you",
        "RCIC",
        "rcic",
        "consult an authorized representative",
        "consult a regulated",
    ],
    "refuse_scope": [
        "I can only answer questions about",
        "outside",
        "isn't the right tool",
        "not the right tool",
        "I'm focused on",
    ],
    "refuse_no_source": [
        "don't have a source",
        "don't have a current source",
        "I understood your follow-up as",
    ],
}


def score_case(case: dict, result: dict) -> dict:
    """
    Score a single test case. Returns dict with pass/fail and reason.
    """
    answer = result["answer"].lower()
    refused = result["refused"]
    expected = case["expected_behavior"]

    score = {
        "case_id": case["id"],
        "category": case["category"],
        "expected_behavior": expected,
        "actually_refused": refused,
        "best_distance": result["best_distance"],
        "search_query_used": result.get("search_query_used", case["question"]),
        "passed": False,
        "fail_reason": "",
        "answer_excerpt": result["answer"][:300].replace("\n", " "),
    }

    # Check forbidden patterns first — these are auto-fails
    for forbidden in case.get("forbidden_patterns", []):
        if forbidden.lower() in answer:
            score["fail_reason"] = f"forbidden phrase present: '{forbidden}'"
            return score

    # Now check expected behavior
    if expected == "answer":
        if refused:
            score["fail_reason"] = "refused when answer was expected"
            return score
        # Check that all expected facts appear
        missing = [f for f in case["expected_facts"] if f.lower() not in answer]
        if missing:
            score["fail_reason"] = f"missing expected facts: {missing}"
            return score
        score["passed"] = True
        return score

    if expected in ("refuse_personal", "refuse_scope", "refuse_no_source"):
        # For personal refusals: model can refuse via the system prompt without
        # the distance-threshold trigger. So `refused=False` is acceptable as
        # long as the answer text contains refusal phrases.
        phrases = REFUSAL_PHRASES.get(expected, [])
        any_phrase = any(p.lower() in answer for p in phrases)
        if not any_phrase:
            score["fail_reason"] = (
                f"expected {expected} but no refusal phrase found in answer"
            )
            return score
        # Also check expected facts (e.g., RCIC mention)
        missing = [f for f in case["expected_facts"] if f.lower() not in answer]
        if missing:
            score["fail_reason"] = f"missing expected refusal facts: {missing}"
            return score
        score["passed"] = True
        return score

    score["fail_reason"] = f"unknown expected_behavior: {expected}"
    return score


# ─────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────
def main():
    print(f"Running {len(TEST_CASES)} eval cases...\n")
    results = []
    start = time.time()

    for i, case in enumerate(TEST_CASES, start=1):
        print(f"[{i:2d}/{len(TEST_CASES)}] {case['id']}... ", end="", flush=True)
        try:
            result = answer_question(case["question"])
            score = score_case(case, result)
            status = "PASS" if score["passed"] else "FAIL"
            print(f"{status}", end="")
            if not score["passed"]:
                print(f" — {score['fail_reason']}")
            else:
                print()
            results.append(score)
        except Exception as e:
            print(f"ERROR — {e}")
            results.append({
                "case_id": case["id"],
                "category": case["category"],
                "expected_behavior": case["expected_behavior"],
                "actually_refused": None,
                "best_distance": None,
                "search_query_used": None,
                "passed": False,
                "fail_reason": f"exception: {e}",
                "answer_excerpt": "",
            })

    elapsed = time.time() - start

    # ─────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n{'=' * 60}")
    print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
    print(f"Pass rate: {100 * passed / total:.1f}%")
    print(f"Elapsed: {elapsed:.1f}s")

    # Per-category breakdown
    print("\nBy category:")
    cats = {}
    for r in results:
        cats.setdefault(r["category"], {"passed": 0, "total": 0})
        cats[r["category"]]["total"] += 1
        if r["passed"]:
            cats[r["category"]]["passed"] += 1
    for cat, counts in cats.items():
        print(f"  {cat}: {counts['passed']}/{counts['total']}")

    # ─────────────────────────────────────────────────────────────
    # Persist results to CSV (for reading) and JSON (for diffing across runs)
    # ─────────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)

    csv_path = out_dir / f"results_{timestamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    json_path = out_dir / f"results_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "total": total,
            "passed": passed,
            "pass_rate": passed / total,
            "elapsed_seconds": elapsed,
            "by_category": cats,
            "cases": results,
        }, f, indent=2)

    print(f"\nResults saved to:")
    print(f"  {csv_path}")
    print(f"  {json_path}")


if __name__ == "__main__":
    main()