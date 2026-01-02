-- Create marketing_form_submissions table
-- Run this in your Supabase SQL Editor AFTER creating the users table

CREATE TABLE IF NOT EXISTS marketing_form_submissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    form_data JSONB NOT NULL,
    strategy_data JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON marketing_form_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON marketing_form_submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON marketing_form_submissions(created_at DESC);

-- Create GIN index for JSONB columns to enable fast queries on JSON fields
CREATE INDEX IF NOT EXISTS idx_submissions_form_data_gin ON marketing_form_submissions USING GIN (form_data);
CREATE INDEX IF NOT EXISTS idx_submissions_strategy_data_gin ON marketing_form_submissions USING GIN (strategy_data);

-- Create trigger to auto-update updated_at timestamp
CREATE TRIGGER update_submissions_updated_at
    BEFORE UPDATE ON marketing_form_submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Add RLS (Row Level Security) policies
-- Uncomment these if you want users to only see their own submissions
-- ALTER TABLE marketing_form_submissions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own submissions
-- CREATE POLICY select_own_submissions ON marketing_form_submissions
--     FOR SELECT
--     USING (auth.uid() = user_id);

-- Policy: Users can insert their own submissions
-- CREATE POLICY insert_own_submissions ON marketing_form_submissions
--     FOR INSERT
--     WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own submissions
-- CREATE POLICY update_own_submissions ON marketing_form_submissions
--     FOR UPDATE
--     USING (auth.uid() = user_id);

-- Grant necessary permissions
-- GRANT SELECT, INSERT, UPDATE ON marketing_form_submissions TO authenticated;
-- GRANT ALL ON marketing_form_submissions TO service_role;

-- Add comments for documentation
COMMENT ON TABLE marketing_form_submissions IS 'Stores marketing strategy form submissions and AI-generated strategies';
COMMENT ON COLUMN marketing_form_submissions.form_data IS 'Raw form data from frontend (JSONB)';
COMMENT ON COLUMN marketing_form_submissions.strategy_data IS 'AI-generated marketing strategy (JSONB)';
COMMENT ON COLUMN marketing_form_submissions.status IS 'Submission status: pending, processing, completed, or failed';
