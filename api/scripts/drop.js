'use strict';

require('dotenv').config();

const { Pool } = require('pg');

const connectionString = process.env.POSTGRES_CONNECTION_STRING;
const databaseName = process.env.POSTGRES_DB;

const pool = new Pool({ connectionString });

// Attempt to drop the database
async function dropDatabase() {
    const client = await pool.connect();
    try {
        // Ensure that the database is not in use
        await client.query('SELECT pg_terminate_backend (pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = $1', [databaseName]);

        // Drop the database
        await client.query(`DROP DATABASE ${databaseName}`);

        console.log(`Database '${databaseName}' dropped successfully.`);
    } catch (error) {
        console.error(`Error dropping database '${databaseName}': ${error.message}`);
    } finally {
        client.release(); // Release the client back to the pool
    }
}

dropDatabase().finally(() => pool.end());
