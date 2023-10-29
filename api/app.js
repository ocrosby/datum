'use strict';

const express = require('express');
const bodyParser = require('body-parser');

import RouteLoader from './system/RouteLoader';


// Constants
const PORT = 8080;
const HOST = '0.0.0.0';

// App
const app = express();

const routes = await RouteLoader('src/routes/*.js');

// parse application/json
app.use(bodyParser.json());

// parse application/x-www-form-urlencoded
app.use(
    bodyParser.urlencoded({
        extended: true
    })
);

app.get('/', (req, res) => {
    res.json({ info: 'Node.js, Express, and Postgres API' });
});

app.listen(PORT, HOST, () => {
    console.log(`Running on http://${HOST}:${PORT}`);
});
