# Baseline Evaluation — AAPL Run

## What works
- All 5 tools connected and returning real data
- GPT-4o produces readable, structured brief
- News citations present for news section

## Weaknesses identified
1. Financial figures have no source citations —
   hallucination risk with no audit trail
2. Brief has no timestamp — undated research
   is dangerous in finance
3. LOW_COVERAGE flag is ignored — pipeline
   passes thin context to LLM which may hallucinate
4. No reflection step — pipeline never asks
   "is this brief good enough?"
5. Static depth — Apple and a small biotech
   get identical treatment

## Baseline metrics (manual estimate)
- Task completion rate: 100% (1/1 runs)
- Brief quality score: 3/5 (readable but unverified)
- Hallucination risk: HIGH (no source citations on numbers)
- Latency: ~15 seconds
- Cost per run: ~$0.03