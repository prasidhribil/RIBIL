/**
 * ============================================================================
 * Express Server - Node.js Queue Service
 * ============================================================================
 * Description: Main Express server for property verification queue API
 * Port: 3000 (default)
 * Integrates Bull queue with Express routes
 * ============================================================================
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const winston = require('winston');
require('dotenv').config();

const propertyRoutes = require('./routes/property');
const verifyQueue = require('./queues/verifyQueue');

// Configure Winston logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/server.log' })
  ]
});

// Initialize Express app
const app = express();

// Middleware
app.use(helmet()); // Security headers
app.use(cors()); // Enable CORS
app.use(compression()); // Gzip compression
app.use(express.json()); // Parse JSON bodies
app.use(express.urlencoded({ extended: true })); // Parse URL-encoded bodies

// Request logging middleware
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('user-agent')
  });
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'gis-queue-service',
    timestamp: new Date().toISOString()
  });
});

// Queue health check endpoint
app.get('/health/queue', async (req, res) => {
  try {
    const waiting = await verifyQueue.getWaiting();
    const active = await verifyQueue.getActive();
    const completed = await verifyQueue.getCompleted();
    const failed = await verifyQueue.getFailed();
    
    res.json({
      status: 'healthy',
      queue: {
        waiting: waiting.length,
        active: active.length,
        completed: completed.length,
        failed: failed.length
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Queue health check failed:', error);
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// API Routes
app.use('/api/property', propertyRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: 'The requested resource was not found'
  });
});

// Error handler
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message
  });
});

// Start server
const PORT = process.env.NODE_APP_PORT || 3000;
const HOST = process.env.APP_HOST || '0.0.0.0';

app.listen(PORT, HOST, () => {
  logger.info(`Queue service listening on ${HOST}:${PORT}`);
  logger.info('Health check: http://localhost:3000/health');
  logger.info('Queue health: http://localhost:3000/health/queue');
});

// Graceful shutdown
const gracefulShutdown = async () => {
  logger.info('Shutting down server gracefully...');
  
  try {
    await verifyQueue.close();
    logger.info('Queue closed successfully');
  } catch (error) {
    logger.error('Error closing queue:', error);
  }
  
  process.exit(0);
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

module.exports = app;
