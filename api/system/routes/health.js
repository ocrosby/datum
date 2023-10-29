const express = require('express');
const router = express.Router();

/**
 * @swagger
 * /health:
 *   get:
 *     summary: Health check
 *     description: Check the health status of the API and database connection.
 *     responses:
 *       200:
 *         description: Health status.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                 message:
 *                   type: string
 *                 uptime:
 *                   type: number
 *     tags:
 *       - General
 */
router.get('/', async (req, res) => {
    // Check your database connection here, and include its status in the response.
    res.json({
        status: 'OK',
        message: 'Service is up and running',
        uptime: process.uptime(), // Uptime in seconds
    });
});

module.exports = router;