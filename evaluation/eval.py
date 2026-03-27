import time
import json
from datetime import datetime

TEST_TICKERS = ["AAPL", "NVDA", "TSLA", "MSFT"]

def evaluate_brief_quality(brief_content: str) -> dict:
    """
    Score a brief on 5 dimensions.
    Returns scores and a total out of 5.
    """
    scores = {}

    # Check 1: Has all 5 required sections
    required_sections = [
        "Company Overview",
        "Recent News",
        "Financial Analysis",
        "Risk Flags",
        "Summary"
    ]
    sections_found = sum(
        1 for s in required_sections
        if s.lower() in brief_content.lower()
    )
    scores["has_all_sections"] = sections_found / len(required_sections)

    # Check 2: Contains financial figures
    import re
    has_numbers = len(re.findall(r'\$[\d,.]+|\d+\.?\d*%', brief_content)) > 3
    scores["has_financial_figures"] = 1.0 if has_numbers else 0.0

    # Check 3: Contains risk flags
    has_risks = "risk" in brief_content.lower()
    scores["has_risk_flags"] = 1.0 if has_risks else 0.0

    # Check 4: Has recommendation
    has_recommendation = "recommend" in brief_content.lower()
    scores["has_recommendation"] = 1.0 if has_recommendation else 0.0

    # Check 5: Reasonable length (>500 words)
    word_count = len(brief_content.split())
    scores["adequate_length"] = 1.0 if word_count > 500 else word_count / 500

    total = sum(scores.values()) / len(scores)
    return {"scores": scores, "total": round(total, 2), "word_count": word_count}

def run_evaluation():
    """
    Run agent on test tickers and record metrics.
    Non-interactive version for automated evaluation.
    """
    from tools.company_profile import get_company_profile
    from tools.news_search import search_news
    from tools.financial_data import get_financial_data
    from baseline.pipeline import run_baseline

    results = []

    for ticker in TEST_TICKERS:
        print(f"\nEvaluating {ticker}...")
        start_time = time.time()

        try:
            brief = run_baseline(ticker)
            elapsed = time.time() - start_time
            quality = evaluate_brief_quality(brief)

            result = {
                "ticker": ticker,
                "status": "COMPLETED",
                "latency_seconds": round(elapsed, 2),
                "quality_score": quality["total"],
                "word_count": quality["word_count"],
                "section_scores": quality["scores"],
                "timestamp": datetime.now().isoformat()
            }
            print(f"  ✅ {ticker}: quality={quality['total']}, latency={elapsed:.1f}s")

        except Exception as e:
            elapsed = time.time() - start_time
            result = {
                "ticker": ticker,
                "status": "FAILED",
                "error": str(e),
                "latency_seconds": round(elapsed, 2),
                "timestamp": datetime.now().isoformat()
            }
            print(f"  ❌ {ticker}: FAILED — {str(e)}")

        results.append(result)

    # Summary
    completed = [r for r in results if r["status"] == "COMPLETED"]
    completion_rate = len(completed) / len(results)
    avg_quality = sum(r["quality_score"] for r in completed) / len(completed) if completed else 0
    avg_latency = sum(r["latency_seconds"] for r in results) / len(results)

    summary = {
        "run_date": datetime.now().isoformat(),
        "total_tickers": len(TEST_TICKERS),
        "completion_rate": round(completion_rate, 2),
        "avg_quality_score": round(avg_quality, 2),
        "avg_latency_seconds": round(avg_latency, 2),
        "results": results
    }

    # Save report
    with open("evaluation/eval_report.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Evaluation Complete")
    print(f"Completion rate: {completion_rate:.0%}")
    print(f"Avg quality score: {avg_quality:.2f}/1.0")
    print(f"Avg latency: {avg_latency:.1f}s")
    print(f"Report saved to evaluation/eval_report.json")

    return summary

if __name__ == "__main__":
    run_evaluation()