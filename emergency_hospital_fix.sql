-- EMERGENCY SQL FIX for missing accounts_hospital columns
-- Run this in your PostgreSQL database shell if migration fails
-- 
-- HOW TO RUN:
-- 1. In Render Shell: python manage.py dbshell
-- 2. Copy and paste these commands one by one
-- 3. Or save as .sql file and run: psql -f emergency_hospital_fix.sql

-- Add missing column: has_blood_bank
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS has_blood_bank BOOLEAN DEFAULT TRUE;

-- Add missing column: blood_groups_available
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS blood_groups_available JSONB DEFAULT '[]'::jsonb;

-- Add missing column: verified_by_id (THIS IS THE ONE CAUSING YOUR ERROR!)
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS verified_by_id BIGINT REFERENCES accounts_user(id) DEFERRABLE INITIALLY DEFERRED;

-- Add missing column: verified_at
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE;

-- Add missing column: verification_documents
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS verification_documents VARCHAR(100);

-- Add missing column: total_donations_processed
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS total_donations_processed INTEGER DEFAULT 0;

-- Add missing column: active_requests
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS active_requests INTEGER DEFAULT 0;

-- Add missing column: trust_score
ALTER TABLE accounts_hospital 
ADD COLUMN IF NOT EXISTS trust_score INTEGER DEFAULT 50;

-- Remove deprecated column if it exists
ALTER TABLE accounts_hospital 
DROP COLUMN IF EXISTS is_active;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS accounts_hospital_city_status_idx 
ON accounts_hospital(city, verification_status);

CREATE INDEX IF NOT EXISTS accounts_hospital_trust_score_idx 
ON accounts_hospital(trust_score);

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'accounts_hospital' 
ORDER BY ordinal_position;

-- You should see all columns including:
-- has_blood_bank, blood_groups_available, verified_by_id, etc.
