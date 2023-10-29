// routes/v1/index.js
const express = require('express');
const router = express.Router();

// Import routes for v1
const usersRoutes = require('./users');

// Define version 1 routes
router.use('/users', usersRoutes);

module.exports = router;
