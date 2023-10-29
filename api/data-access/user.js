const db = require('../db');

module.exports = {
    getAll: async () => {
        const query = 'SELECT * FROM users';
        const { rows } = await db.query(query);

        return rows;
    },

    getUserById: async (userId) => {
        const query = 'SELECT * FROM users WHERE id = $1';
        const params = [userId];

        const { rows } = await db.query(query, params);

        return rows[0];
    },

    createUser: async (user) => {
        const query = 'INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *';
        const params = [user.name, user.email];

        const { rows } = await db.query(query, params);

        return rows[0];
    },

    updateUser: async (userId, updatedUserData) => {
        const query = 'UPDATE users SET name = $1, email = $2 WHERE id = $3 RETURNING *';
        const params = [updatedUserData.name, updatedUserData.email, userId];

        const { rows } = await db.query(query, params);

        return rows[0];
    },

    deleteUserById: async (userId) => {
        const query = 'DELETE FROM users WHERE id = $1';
        const params = [userId];

        const { rows } = await db.query(query, params);

        return rows[0];
    }
};
