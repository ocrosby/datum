'use strict';

require('dotenv').config();

const path = require('path');
const fs = require('fs');

const { Pool } = require('pg');

const connectionString = process.env.POSTGRES_CONNECTION_STRING;
const databaseName = process.env.POSTGRES_DB;
const sqlFilePath = path.join(__dirname, 'data/create_database.sql'); // Replace with the path to your SQL file

const pool = new Pool({ connectionString });

// Function to create the database
async function createDatabase() {
    const client = await pool.connect();
    try {
        // Read the SQL file
        const sql = fs.readFileSync(sqlFilePath, 'utf8');

        // Execute the SQL commands from the file
        await client.query(sql);

        console.log('Database created successfully.');
    } catch (error) {
        console.error('Error creating database:', error.message);
    } finally {
        client.release(); // Release the client back to the pool
    }
}

createDatabase().finally(() => pool.end());
