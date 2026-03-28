FinSight — Project Retrospective
What I built

I built FinSight, an AI-powered financial research agent that generates structured, cited company briefs by combining news, market data, memory retrieval, and brief generation into one workflow. Instead of forcing analysts to manually gather information across fragmented sources, FinSight reduces research time from hours to minutes while preserving an audit trail of the sources used.

What worked well

The problem framing was strong because I focused on a real analyst workflow bottleneck and designed the project around saving time while improving consistency.
The tool registry was clear and practical, with each tool having a defined purpose, output format, and fallback behavior when something failed.
The human-in-the-loop checkpoints made the system more credible by adding safeguards for ticker ambiguity and numerical accuracy before delivery.

What I would do differently

I would make the agent loop more dynamic from the start, because right now the design still leans somewhat structured rather than fully agentic in how it decides next actions.
I would build stronger failure handling earlier, especially around rate limits, stale sources, and partial API failures, since those are major risks in any real production workflow.
I would also prioritize source validation and factual verification more aggressively, because financial research is only useful if the user can trust every number and claim in the final brief.

What I learned

I learned why an agent is different from a fixed pipeline, especially when the workflow needs to adapt based on what it discovers mid-run.
I learned how important fallback logic and explicit failure flags are when tools return weak, empty, or unreliable data.
I learned that human review is not just a safety feature but a core design choice when building systems that generate high-stakes financial content.

Version 2 improvement list
True ReAct loop — LLM decides tool order dynamically
Retry logic with exponential backoff on API failures
Source freshness scoring — flag briefs with stale sources
Streaming API responses — stream brief generation token by token
Full S3 integration for production brief storage
Rate limit handling for NewsAPI and yfinance
Multi-company comparison briefs
Slack/email notification when brief is ready
PostgreSQL checkpointer — replace MemorySaver with persistent state so HITL pauses survive server restarts
Evaluation against agent output vs baseline — automated comparison of brief quality between pipeline and agent runs