-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the table for Lead Intelligence
CREATE TABLE IF NOT EXISTS lead_intelligence_logs (
    id SERIAL PRIMARY KEY,
    lead_id BIGINT NOT NULL,
    interaction_id VARCHAR(100),
    content_type VARCHAR(50),             -- 'transcript', 'summary', 'audit'
    text_content TEXT NOT NULL,
    model_version VARCHAR(50),
    embedding VECTOR(768),                -- Dimension for Gemini text-embedding-004
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for lead lookup
CREATE INDEX IF NOT EXISTS idx_lead_intel_lead_id ON lead_intelligence_logs(lead_id);

-- Vector index for RAG search
CREATE INDEX IF NOT EXISTS idx_lead_intel_vector ON lead_intelligence_logs 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
