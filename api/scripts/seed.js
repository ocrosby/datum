const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

const connectionString = 'postgres://username:password@localhost:5432/your_database'; // Replace with your connection details
const sqlFilePath = path.join(__dirname, 'data/seed.sql'); // Replace with the path to your SQL file

const pool = new Pool({ connectionString });

// Function to read and execute the SQL file
async function seedDatabase() {
    const client = await pool.connect();
    try {
        // Read the SQL file
        const sql = fs.readFileSync(sqlFilePath, 'utf8');

        // Execute the SQL queries from the file
        await client.query(sql);

        console.log('Database seeded successfully.');
    } catch (error) {
        console.error('Error seeding database:', error.message);
    } finally {
        client.release(); // Release the client back to the pool
    }
}

seedDatabase().finally(() => pool.end());
