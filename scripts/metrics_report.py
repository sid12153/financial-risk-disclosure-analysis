from __future__ import annotations

import csv
from pathlib import Path
from statistics import median

LOG_PATH = Path("C:/Users/Siddharth/Desktop/Portfolio_Projects/Finance-AI-RAG/monitoring/query_log.csv")

def pct(values, p):
    if not values:
        return None
    xs = sorted(values)
    k = (len(xs) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)

def bucket_top_score(s):
    if s < 0.40: return "0.00-0.39"
    if s < 0.50: return "0.40-0.49"
    if s < 0.60: return "0.50-0.59"
    if s < 0.70: return "0.60-0.69"
    if s < 0.80: return "0.70-0.79"
    if s < 0.90: return "0.80-0.89"
    return "0.90-1.00"

def fnum(row, key):
    v = (row.get(key) or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except Exception:
        return None

def main():
    if not LOG_PATH.exists():
        print(f"Missing {LOG_PATH}")
        return

    rows = []
    with LOG_PATH.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)

    if not rows:
        print("No rows in log.")
        return

    # Overall buckets
    refused_flags = []
    top_scores = []
    total_ms = []
    planner_ms = []
    retrieval_ms = []
    verifier_ms = []
    summary_ms = []

    answered_total = []
    refused_total = []

    by_doc = {}
    hist = {}

    for row in rows:
        doc = (row.get("doc_id") or "").strip()
        refused = (row.get("refused") or "").strip().upper() == "TRUE"
        refused_flags.append(refused)

        t_total = fnum(row, "total_ms")
        t_plan = fnum(row, "planner_ms")
        t_ret = fnum(row, "retrieval_ms")
        t_ver = fnum(row, "verifier_ms")
        t_sum = fnum(row, "summary_ms")

        if t_total is not None:
            total_ms.append(t_total)
            if refused:
                refused_total.append(t_total)
            else:
                answered_total.append(t_total)

        if t_plan is not None: planner_ms.append(t_plan)
        if t_ret is not None: retrieval_ms.append(t_ret)
        if t_ver is not None: verifier_ms.append(t_ver)
        if t_sum is not None: summary_ms.append(t_sum)

        ts = fnum(row, "top_score")
        if ts is not None:
            top_scores.append(ts)
            hist[bucket_top_score(ts)] = hist.get(bucket_top_score(ts), 0) + 1

        if doc:
            if doc not in by_doc:
                by_doc[doc] = {"n": 0, "refused": 0, "top_scores": [], "total_ms": []}
            by_doc[doc]["n"] += 1
            by_doc[doc]["refused"] += (1 if refused else 0)
            if ts is not None:
                by_doc[doc]["top_scores"].append(ts)
            if t_total is not None:
                by_doc[doc]["total_ms"].append(t_total)

    refusal_rate = sum(1 for x in refused_flags if x) / len(refused_flags) * 100.0

    print("\n=== Overall ===")
    print(f"Requests: {len(rows)}")
    print(f"Refusal rate: {refusal_rate:.1f}%")

    if total_ms:
        print(f"Latency (E2E) ms: P50={pct(total_ms,50):.0f}  P95={pct(total_ms,95):.0f}  P99={pct(total_ms,99):.0f}")
    if answered_total:
        print(f"Answered latency ms: P50={pct(answered_total,50):.0f}  P95={pct(answered_total,95):.0f}")
    if refused_total:
        print(f"Refused latency  ms: P50={pct(refused_total,50):.0f}  P95={pct(refused_total,95):.0f}")

    print("\n=== Step latency ms ===")
    if planner_ms:
        print(f"Planner:   P50={pct(planner_ms,50):.0f}  P95={pct(planner_ms,95):.0f}  P99={pct(planner_ms,99):.0f}")
    if retrieval_ms:
        print(f"Retrieval: P50={pct(retrieval_ms,50):.0f}  P95={pct(retrieval_ms,95):.0f}  P99={pct(retrieval_ms,99):.0f}")
    if verifier_ms:
        print(f"Verifier:  P50={pct(verifier_ms,50):.0f}  P95={pct(verifier_ms,95):.0f}  P99={pct(verifier_ms,99):.0f}")
    if summary_ms:
        print(f"Summary:   P50={pct(summary_ms,50):.0f}  P95={pct(summary_ms,95):.0f}  P99={pct(summary_ms,99):.0f}")

    if top_scores:
        print("\n=== Top score ===")
        print(f"Mean={sum(top_scores)/len(top_scores):.3f}  Median={median(top_scores):.3f}")

    print("\n=== Top-score histogram ===")
    for k in ["0.00-0.39","0.40-0.49","0.50-0.59","0.60-0.69","0.70-0.79","0.80-0.89","0.90-1.00"]:
        print(f"{k}: {hist.get(k,0)}")

    print("\n=== By document ===")
    for doc, d in sorted(by_doc.items(), key=lambda x: x[0]):
        n = d["n"]
        rr = (d["refused"] / n) * 100.0 if n else 0.0
        avg_ts = sum(d["top_scores"]) / len(d["top_scores"]) if d["top_scores"] else 0.0
        doc_p50 = pct(d["total_ms"], 50) if d["total_ms"] else None
        p50_str = f"{doc_p50:.0f}" if doc_p50 is not None else "-"
        print(f"{doc}: n={n} refusal={rr:.1f}% avg_top_score={avg_ts:.3f} latency_p50_ms={p50_str}")

if __name__ == "__main__":
    main()
