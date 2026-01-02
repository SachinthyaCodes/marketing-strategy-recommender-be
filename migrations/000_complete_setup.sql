-- COMPLETE DATABASE SETUP FOR MARKETING STRATEGY RECOMMENDER
-- Run this ENTIRE script in your Supabase SQL Editor
-- This will create all necessary tables, indexes, triggers, and functions

-- ============================================================================
-- STEP 1: Create helper function for updating timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- STEP 2: Create users table (Authentication)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add table comment
COMMENT ON TABLE users IS 'User accounts with JWT authentication';
COMMENT ON COLUMN users.email IS 'Unique user email address';
COMMENT ON COLUMN users.hashed_password IS 'Bcrypt hashed password';

-- ============================================================================
-- STEP 3: Create marketing_form_submissions table
-- ============================================================================

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

-- Create GIN indexes for JSONB columns (enables fast JSON queries)
CREATE INDEX IF NOT EXISTS idx_submissions_form_data_gin ON marketing_form_submissions USING GIN (form_data);
CREATE INDEX IF NOT EXISTS idx_submissions_strategy_data_gin ON marketing_form_submissions USING GIN (strategy_data);

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_submissions_updated_at
    BEFORE UPDATE ON marketing_form_submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add table comments
COMMENT ON TABLE marketing_form_submissions IS 'Marketing strategy form submissions with AI-generated strategies';
COMMENT ON COLUMN marketing_form_submissions.form_data IS 'Raw form data from frontend (JSONB)';
COMMENT ON COLUMN marketing_form_submissions.strategy_data IS 'AI-generated marketing strategy (JSONB)';
COMMENT ON COLUMN marketing_form_submissions.status IS 'Submission status: pending, processing, completed, or failed';

-- ============================================================================
-- STEP 4: Grant permissions (adjust based on your Supabase setup)
-- ============================================================================

-- Grant permissions to authenticated users
-- GRANT SELECT, INSERT, UPDATE ON users TO authenticated;
-- GRANT SELECT, INSERT, UPDATE ON marketing_form_submissions TO authenticated;

-- Grant full permissions to service role (for backend API)
-- GRANT ALL ON users TO service_role;
-- GRANT ALL ON marketing_form_submissions TO service_role;

-- ============================================================================
-- STEP 5: Optional - Enable Row Level Security (RLS)
-- ============================================================================

-- Uncomment these if you want to enable RLS for additional security

-- Enable RLS on tables
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
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

-- ============================================================================
-- VERIFICATION QUERIES (Run these to verify setup)
-- ============================================================================

-- Check if tables exist
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('users', 'marketing_form_submissions');

-- Check indexes
-- SELECT tablename, indexname FROM pg_indexes 
-- WHERE schemaname = 'public' 
-- AND tablename IN ('users', 'marketing_form_submissions');

-- Check triggers
-- SELECT trigger_name, event_object_table 
-- FROM information_schema.triggers 
-- WHERE event_object_schema = 'public';

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Insert test user (password is 'testpassword123' hashed with bcrypt)
-- Note: Use your backend's register endpoint instead of manually inserting
-- INSERT INTO users (email, hashed_password) VALUES 
-- ('test@example.com', '$2b$12$example_hashed_password_here');

-- Insert test submission
-- INSERT INTO marketing_form_submissions (user_id, form_data, status) VALUES 
-- (
--     (SELECT id FROM users WHERE email = 'test@example.com'),
--     '{"business_name": "Test Cafe", "industry": "food_beverage"}'::jsonb,
--     'pending'
-- );

-- ============================================================================
-- CLEANUP (Run this only if you want to delete everything and start over)
-- ============================================================================

-- WARNING: This will delete all data!
-- DROP TABLE IF EXISTS marketing_form_submissions CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
