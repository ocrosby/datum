'use strict';

// Load environment variables from .env file
const swaggerJSDoc = require("swagger-jsdoc");
const swaggerUi = require("swagger-ui-express");
const express = require("express");
const morgan = require("morgan");

const fs = require('fs');
const path = require('path');


require('dotenv').config();

function readVersion() {
    const versionFilePath = path.join(__dirname, 'VERSION');

    let version = '0.0.0';

    try {
        const versionFileContent = fs.readFileSync(versionFilePath, 'utf-8');
        version = versionFileContent.trim();
    } catch (error) {
        console.error('Error reading VERSION file:', error);
    }

    console.log('Version read from VERSION file:', version);

    return version;
}

function setupSwagger(app, version) {
    // Define an OpenAPI Specification configuration
    const swaggerDefinition = {
        openapi: '3.0.0',
        info: {
            title: 'Datum API',
            description: 'An API for the Datum application',
            version: version,
            contact: {
                name: process.env.CONTACT_NAME,
                email: process.env.CONTACT_EMAIL,
            }
        },
        servers: [
            {
                url: 'http://127.0.0.1:8080',
                description: 'Development Server',
            },
            {
                url: 'https://api.datumapp.io',
                description: 'Production Server',
            }
        ],
    }

    const options = {

        swaggerDefinition,
        apis: [
            './system/routes/*.js',
            './routes/v1/*.js'
        ], // Paths to your Express routes files
    }

    const swaggerSpec = swaggerJSDoc(options)

    // Serve Swagger UI at /api-docs
    app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
}

function configureRoutes(app) {
    // Create a parent router with the /api prefix
    const apiRouter = express.Router();

    const defaultRoute = require('./system/routes/default');
    const healthCheckRoute = require('./system/routes/health');
    const v1Routes = require('./routes/v1/index')

    apiRouter.use('/v1', v1Routes);

    app.use('/', defaultRoute);
    app.use('/api', apiRouter);
    app.use('/health', healthCheckRoute);
}

function configureMiddleware(app) {
    // Middleware
    app.use(express.json()); // Parse JSON data
    app.use(express.urlencoded({ extended: true })); // Parse URL-encoded data

    // Logging middleware
    app.use(morgan('dev')); // Log requests to the console
}

// Use a self-calling function, so we can use async / await.
(async () => {
    const version = readVersion()
    const { initializeDatabase } = require('./db');

    // Constants
    const HOST = process.env.HOST || '127.0.0.1'; // Default to localhost if HOST env variable is not set
    const PORT = process.env.PORT || 8080; // Default to 8080 if not defined

    // Create the Express app
    const app = express();

    configureMiddleware(app);
    setupSwagger(app, version)
    configureRoutes(app);

    try {
        await initializeDatabase();

        app.listen(PORT, HOST, () => {
            console.log(`Running on http://${HOST}:${PORT}`);
        });
    } catch (error) {
        console.error('Error creating the database:', error);
    }
})();
