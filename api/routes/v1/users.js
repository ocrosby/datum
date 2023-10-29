// routes/v1/users.js
const express = require('express');
const router = express.Router();
const UserDAO = require('../../data-access/user'); // Import the User model

// Get all users
router.get('/', async (req, res) => {
    try {
        const users = await UserDAO.getAll()
        res.json(users);
    } catch (error) {
        console.error('Error fetching users', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }

    res.json({ message: 'List of users' });
});

// Get a user
router.get('/:id', async (req, res) => {
    const userId = req.params.id;

    try {
        const user = await User.getById(userId);

        if (user) {
            res.json(user);
        } else {
            res.status(404).json({ error: 'User not found'})
        }
    } catch (error) {
        console.error('Error fetching user', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

// Create a user
router.post('/', async (req, res) => {
    // Handle user creation
    try {
        const {username, email, password} = req.body;

        // Perform input validation here if needed

        // Insert the new user into the database
        const newUser = await User.create(username, email, password);

        res.status(201).json(newUser);
    } catch (error) {
        console.error('Error creating user', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

// Update a user
router.put('/:id', async (req, res) => {
    // Handle user update
    try {
        const userId = req.params.id;
        const {username, email, password} = req.body;

        // Perform input validation here if needed

        // Check if the user exists
        const existingUser = await User.getById(userId);
        if (!existingUser) {
            return res.status(404).json({ error: 'User not found' });
        }

        // Update the user's information
        const updatedUser = await User.update(userId, username, email, password);

        res.json(updatedUser);
    } catch (error) {
        console.error('Error updating user', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

// Delete a user
router.delete('/:id', async (req, res) => {
    // Handle user deletion
    const userId = req.params.id;

    try {
        const result = await User.deleteById(userId);
        res.json(result);
    } catch (error) {
        console.error('Error deleting user', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

module.exports = router;