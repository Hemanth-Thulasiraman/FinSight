import os
from openai import OpenAI
from dotenv import load_dotenv
from db.database import get_connection, release_connection

load_dotenv()

openai_client = OpenAI()

def get_embedding(text: str) -> list:
    """Convert text to a vector embedding."""
    response = openai_client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding

def retrieve_prior_research(ticker: str, query: str) -> dict:
    """
    Check if prior research exists for this ticker.
    Returns relevant sections from past briefs.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
 
        # TODO 1: check if any brief exists for this ticker
        cursor.execute("SELECT COUNT(*) FROM research_briefs WHERE ticker_name = %s", (ticker,))
        count = cursor.fetchone()[0]
        if count == 0:
            return {"has_prior_research": False, "ticker": ticker, "sections": []}

        embedding = get_embedding(query)
        
        cursor.execute("SELECT section_name, section_text FROM brief_sections JOIN research_briefs ON brief_sections.brief_id = research_briefs.brief_id WHERE research_briefs.ticker_name = %s ORDER BY embedding <=> %s::vector LIMIT 5", (ticker, str(embedding)))
      
        return {
            "has_prior_research": True,
            "ticker": ticker,
            "sections": [
                {"section_name": row[0], "section_text": row[1]}
                for row in cursor.fetchall()
            ]
        }
    

    except Exception as e:
        return {"error": True, "message": f"Memory retrieval failed: {str(e)}"}
    finally:
        release_connection(conn)