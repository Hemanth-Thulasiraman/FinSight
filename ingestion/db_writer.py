#db writer file
from db.database import get_connection, release_connection
from ingestion.models import RunLog, NewsArticle, ResearchBrief, BriefSection

def insert_run_log(run_log: RunLog) -> None:
    """Insert a RunLog record into the run_log table."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO run_log (ticker_name, status, number_of_tool_calls, time_elapsed, cost, error_message, brief_s3_path) VALUES (%s, %s, %s, %s, %s, %s, %s)", (run_log.ticker_name, run_log.status, run_log.number_of_tool_calls, run_log.time_elapsed, run_log.cost, run_log.error_message, run_log.brief_s3_path))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        release_connection(conn)

def insert_news_article(article: NewsArticle) -> None:
    """Insert a NewsArticle record into the news_articles table."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO news_articles (run_id, headline, source, url, published_date, body_summary, s3_path) VALUES (%s, %s, %s, %s, %s, %s, %s)", (article.run_id, article.headline, article.source, article.url, article.published_date, article.body_summary, article.s3_path))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        release_connection(conn)

def insert_research_brief(brief: ResearchBrief) -> None:
    """Insert a ResearchBrief record into the research_briefs table."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO research_briefs (run_id, ticker_name, s3_path) VALUES (%s, %s, %s)", (brief.run_id, brief.ticker_name, brief.s3_path))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        release_connection(conn)

def insert_brief_section(section: BriefSection) -> None:
    """Insert a BriefSection record into the brief_sections table."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO brief_sections (brief_id, section_name, section_text, embedding) VALUES (%s, %s, %s, %s)", (section.brief_id, section.section_name, section.section_text, str(section.embedding)))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        release_connection(conn)
