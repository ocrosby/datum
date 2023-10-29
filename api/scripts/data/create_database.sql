-- Create the database named "datum"
CREATE DATABASE datum;

-- Create the "states" table
CREATE TABLE IF NOT EXISTS states (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  abbreviation VARCHAR(2) NOT NULL
);
