**FinSight \- Problem Framing Document** 

**Problem Statement**   
A financial research analyst begins their day by gathering news articles and stock market data across multiple fragmented sources. Researching a single company takes a whole day and still produces incomplete coverage. The process is manual, meaning two analysts researching the same company on the same day may check different sources and reach different conclusions with no audit trail to explain why. At scale, a team of 5 analysts can cover at most 5 companies per day \- creating a bottleneck that forces teams to prioritize only their highest-conviction positions and ignore everything else. FinSight changes this by compressing research time from hours to minutes and producing a structured, cited brief with a full audit trail of every source the agent consulted.

**Why an Agent \- Not a Pipeline** 

1. When the agent discovers Elon Musk sold his Tesla shares , it must decide to pull Elon Musk recent public statements and SEC Form 4 fillings . A pipeline cannot do this because its execution steps are hardcoded at write time \- it will finish its fixed sequence regardless of what it finds mid-run. In financial research this matters because a $3.5B insider sale is a significant signal \- an analyst who doesn't investigate further may miss a major red flag and produce a brief that presents an incomplete or misleading picture to the investor.  
2. When the news search tool returns zero results for a small-cap company, the agent broaden the query to company name, retry with CEO name, then logs a LOW\_COVERAGE flag if still empty. A pipeline cannot do this because it has no mechanism to inspect its own outputs \- it passes an empty result downstream silently without raising an error. In financial research this matters because the LLM receiving empty context will hallucinate news that never happened, and the user has no way of knowing the brief is fabricated.  
3. Different companies require fundamentally different amounts of research effort. Researching Apple requires few tool calls because there are many news articles from many years. Researching a small-cap biotech may require 10+ tool calls because agent must try multiple sources, retry with different queries, and may still conclude coverage is insufficient. A pipeline cannot handle this because it runs a fixed number of steps regardless of input \- it either over-researches simple companies wasting cost, or under-researches complex ones producing incomplete briefs. In financial research this matters because following a uniform depth approach on variable complexity inputs leads to incorrect results.

**Tool Registry** 

1. **Tool name:** Company profile   
   **What it does:** It gets company information using the name    
   **API/service used:** FMP API   
   **Output format:** JSON   
   **What the agent does with the output:** The agent uses this information to gather news articles in the next step like articles based on company name, sector, exchange and so on   
   **What happens if it fails or returns garbage:** retry once, check the ticker name else ask the user to verify ticker  
     
2. **Tool name:** Recent news  
   **What it does:** Gets latest news articles   
   **API/service used:** NewsAPI  
   **Output format:** JSON  
   **What the agent does with the output:** The agents processes the news articles and gathers information about the company and stores it in the database  
   **What happens if it fails or returns garbage:** It needs to check two things: is the result count above a minimum threshold (say 3 articles), and does the content actually mention the company? If either check fails, it logs LOW\_COVERAGE and continues with reduced confidence.  
     
3. **Tool name:** Financial Data  
   **What it does:** Gets the financial data alone for that company  
   **API/service used:** FMP API or yfinance  
   **Output format:** JSON for FMP and yfinance gives data frame  
   **What the agent does with the output:** The agent extracts the financial data and stores it in the database.  
   **What happens if it fails or returns garbage:** logs an INSUFFICIENT_FINANCIAL_DATA flag, proceeds with available data, and notes the gap explicitly in the brief.  
     
4. **Tool name:** Memory retrieval  
   **What it does:** Helps agents check for past research about a company  
   **API/service used:** Pgvector \+postgreSQL   
   **Output format:** String  
   **What the agent does with the output:** It checks if a brief exists for this ticker, pulls the last run date, and uses the prior findings to avoid redundant tool calls and add a "changes since last research" section to the new brief.  
   **What happens if it fails or returns garbage:** The agent won't have past research data and will have to find if there's any new data available.  
     
5. **Tool name:** Save Final Brief  
   **What it does:** Writes the completed research brief as a markdown file to local disk during development and to an S3 bucket in production  
   **API/service used:** Python file I/O (dev), boto3 S3 (production)  
   **Output format:** Markdown file named brief\_{ticker}\_{timestamp}.md  
   **What the agent does with the output:** This is the terminal tool \- saving the brief is the final step. The agent notifies the user of the file path and logs the completed run.  
   **What happens if it fails:** Retry once. If retry fails, print the brief to console as fallback and log a SAVE\_FAILURE event in the run trace.

**Human-in-the-Loop Checkpoints**   
Two specific checkpoints — disambiguation before run start, final review before delivery — with state persistence, approval flows, and rejection handling.

1. **Checkpoint name:** Ambiguity check    
   **When it occurs:** It occurs before the agents starts its research.    
   **What the human reviews:** The human reviews if the ticker is correct.    
   **Why the agent can't handle this alone:** A single company name can map to multiple entities  the agent can make a best-guess match but cannot confirm user intent without asking. Intent disambiguation requires the human who made the request.  
   **what the agent does while waiting:** Saves current state to PostgreSQL and pauses execution. Resumes when human submits approval or rejection via the API.   
   **What happens if human approves:** Then the agent starts the research    
   **What happens if human rejects:** Agent should list the possible matching tickers and ask the user to select the correct one. then proceed with he confirmed entity.  
     
2. **Checkpoint name:** Final Brief Review  
   **When it occurs:** After the brief is fully drafted, before it is saved and delivered  
   **What the human reviews:** Factual accuracy of all numerical claims \- revenue figures, earnings numbers, market cap, any percentage changes  
   **Why the agent can't handle this alone:** The LLM cannot self-verify whether a number it generated matches the source data \- it can hallucinate figures that look plausible but are fabricated  
   **What the agent does while waiting:** Saves current state to PostgreSQL and pauses execution. Resumes when human submits approval or rejection via the API.  
   **What happens if human approves:** Brief is saved to S3 and delivered to user  
   **What happens if human rejects:** Agent logs the rejection reason, re-runs only the tools relevant to the flagged section, regenerates that section, and returns for re-review.

**Success Metrics**   
Eight metrics, all measurable, with thresholds and justifications.

**5\. Success Metrics**

| Metric | Target | Why it matters |
| ----- | ----- | ----- |
| **Task completion rate** | **\>90% of runs produce a valid brief** | **Measures reliability** |
| **Brief quality score** | **\>4/5 on human eval rubric** | **Measures usefulness** |
| **Hallucination rate** | **\<5% of factual claims unverified** | **Measures trustworthiness** |
| **Latency per run** | **\<90 seconds** | **Measures usability** |
| **Cost per run** | **\<$0.50** | **Measures viability** |
| **Tool call accuracy** | **\>85% correct tool \+ correct params** | **Measures agent reasoning** |
| **Tool call efficiency ratio** | **Flag any run exceeding 12 calls (2x baseline of 6\)** | **Excessive tool calls increase cost and latency with no quality improvement** |
| **Source Freshness Score** | **Flag any brief where avg source age exceeds 30 days** | **Outdated data leads investors to make decisions based on an outdated company picture** |

