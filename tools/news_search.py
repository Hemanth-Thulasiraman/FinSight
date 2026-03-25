import os
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MIN_ARTICLE_THRESHOLD = 3

def search_news(ticker: str, company_name: str) -> dict:
    """
    Search recent news articles for a company.
    Returns articles with coverage assessment.
    """
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY environment variable not set")

    client = NewsApiClient(api_key=NEWS_API_KEY)

    # Search window: last 30 days
    to_date = datetime.today().strftime("%Y-%m-%d")
    from_date = (datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")

    try:
        response = client.get_everything(q=company_name, from_param=from_date, to=to_date, language="en", sort_by="relevancy")

        articles = response.get("articles", [])


        if len(articles) < MIN_ARTICLE_THRESHOLD:
            coverage_flag = "LOW_COVERAGE"
        else:
            coverage_flag = "OK"

        relevant_articles = [
            a for a in articles
            if company_name.lower() in (a.get("title") or "").lower()
            or company_name.lower() in (a.get("description") or "").lower()
        ]
        if not relevant_articles:
            coverage_flag = "LOW_COVERAGE"

        return {
            "ticker": ticker,
            "company_name": company_name,
            "coverage_flag": coverage_flag,
            "article_count": len(relevant_articles),
            "articles": [
                {
                    "headline": a["title"],
                    "source": a["source"]["name"],    
                    "url": a["url"],
                    "published_date": a["publishedAt"],
                    "description": a["description"]
                }
                for a in relevant_articles[:10]  # max 10 articles
            ],
            "error": False
        }

    except Exception as e:
        return {"error": True, "message": f"News search failed: {str(e)}"}
