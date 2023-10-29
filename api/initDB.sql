-- Create the states table
CREATE TABLE IF NOT EXISTS states (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  abbreviation VARCHAR(2) NOT NULL
);

-- Insert initial data into all tables
\i ./initialData.sql