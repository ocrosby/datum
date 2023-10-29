const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

const pool = new Pool({
    user: process.env.POSTGRES_USER,
    password: process.env.POSTGRES_PASSWORD,
    host: process.env.POSTGRES_HOST,
    database: process.env.POSTGRES_DB,
    port: parseInt(process.env.POSTGRES_PORT)
});

// Read and execute the combined initialization script
const initSQL = fs.readFileSync(path.join(__dirname, 'initDB.sql'), 'utf8');

async function checkDatabaseExistence(dbName) {
    const client = await pool.connect();
    try {
        const query = `SELECT datname FROM pg_database WHERE datname = $1`;
        const result = await client.query(query, [dbName]);

        return result.rows.length > 0; // If there is a row, the database exists.
    } catch (error) {
        throw error;
    } finally {
        client.release();
    }
}

module.exports = {
    query: (text, params) => pool.query(text, params),
    initializeDatabase: async () => {
        try {
            // Check if the database already exists
            const dbExists = await checkDatabaseExistence(process.env.POSTGRES_DB);

            if (!dbExists) {
                // Connect to the database
                const client = await pool.connect();

                // Run the combined initialization script
                await client.query(initSQL);

                // Release the client back to the pool
                client.release();

                console.log('Database initialized successfully.');
            } else {
                console.log('Database already initialized.');
            }
        } catch (error) {
            console.error('Error initializing the database:', error);
        }
    },
    dropDatabase: async () => {
        try {
            // Check if the database already exists
            const dbExists = await checkDatabaseExistence(process.env.POSTGRES_DB);

            if (dbExists) {
                // Connect to the database
                const client = await pool.connect();

                // Run the combined initialization script
                await client.query(`DROP DATABASE ${process.env.POSTGRES_DB}`);

                // Release the client back to the pool
                client.release();

                console.log('Database dropped successfully.');
            } else {
                console.log('Database does not exist.');
            }
        } catch (error) {
            console.error('Error dropping the database:', error);
        }
    }
};