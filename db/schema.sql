-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table 1: run_log
CREATE TABLE IF NOT EXISTS run_log (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL,    
    number_of_tool_calls INT,
    time_elapsed FLOAT ,
    cost FLOAT ,
    error_message VARCHAR ,
    brief_s3_path VARCHAR ,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Table 2: news_articles
CREATE TABLE IF NOT EXISTS news_articles (
    article_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES run_log(run_id) ON DELETE RESTRICT NOT NULL,
    headline VARCHAR,
    source VARCHAR,
    url VARCHAR,
    published_date TIMESTAMP,
    body_summary TEXT,
    s3_path VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
-- Table 3: research_briefs
CREATE TABLE IF NOT EXISTS research_briefs (
    brief_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES run_log(run_id) ON DELETE RESTRICT NOT NULL,
    ticker_name VARCHAR,
    s3_path VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Table 4: brief_sections
CREATE TABLE IF NOT EXISTS brief_sections (
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID REFERENCES research_briefs(brief_id) ON DELETE RESTRICT NOT NULL,
    section_name VARCHAR NOT NULL,
    section_text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);