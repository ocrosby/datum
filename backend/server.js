const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const http = require('http');
const WebSocket = require('ws');
const cron = require('node-cron');
require('dotenv').config();

const app = express();
const server = http.createServer(app);

// WebSocket server for real-time updates
const wss = new WebSocket.Server({ server });

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
app.use(compression());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

// Import routes
const rpiRoutes = require('./routes/rpi');
const teamsRoutes = require('./routes/teams');
const matchesRoutes = require('./routes/matches');
const analyticsRoutes = require('./routes/analytics');
const settingsRoutes = require('./routes/settings');
const statusRoutes = require('./routes/status');

// Import services
const RPIService = require('./services/rpiService');
const WebSocketService = require('./services/websocketService');

// Initialize services
const rpiService = new RPIService();
const wsService = new WebSocketService(wss);

// Routes
app.use('/api/rpi', rpiRoutes);
app.use('/api/teams', teamsRoutes);
app.use('/api/matches', matchesRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/settings', settingsRoutes);
app.use('/api/status', statusRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// WebSocket connection handling
wss.on('connection', (ws, req) => {
  console.log('New WebSocket connection');
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      wsService.handleMessage(ws, data);
    } catch (error) {
      console.error('WebSocket message error:', error);
    }
  });

  ws.on('close', () => {
    console.log('WebSocket connection closed');
    wsService.removeClient(ws);
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

// Scheduled tasks
cron.schedule('*/5 * * * *', async () => {
  // Check for new RPI data every 5 minutes
  try {
    const hasNewData = await rpiService.checkForNewData();
    if (hasNewData) {
      wsService.broadcastToAll({
        type: 'rpi_update',
        data: { message: 'New RPI data available' }
      });
    }
  } catch (error) {
    console.error('Scheduled RPI check error:', error);
  }
});

cron.schedule('0 */6 * * *', async () => {
  // Refresh data every 6 hours
  try {
    await rpiService.refreshData();
    wsService.broadcastToAll({
      type: 'data_refresh',
      data: { message: 'Data refreshed' }
    });
  } catch (error) {
    console.error('Scheduled data refresh error:', error);
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: 'Something went wrong!',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

const PORT = process.env.PORT || 3001;

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`WebSocket server ready`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});

module.exports = { app, server, wss }; 