-- Create application database if it doesn't exist
SELECT 'CREATE DATABASE zabt'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'zabt')\gexec

-- Create test database (used by backend pytest suite — keeps prod and tests isolated)
SELECT 'CREATE DATABASE zabt_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'zabt_test')\gexec
