/**
 * ============================================================================
 * Authentication Middleware
 * ============================================================================
 * Description: JWT token verification middleware for Express routes
 * Mock implementation for development - replace with real auth in production
 * ============================================================================
 */

const jwt = require('jsonwebtoken');
const winston = require('winston');
require('dotenv').config();

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

/**
 * Authenticate JWT token from Authorization header
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN
  
  if (!token) {
    logger.warn('Authentication failed: No token provided');
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Access token is required'
    });
  }
  
  // Development bypass for test-token
  if (process.env.NODE_ENV === 'development' && token === 'test-token') {
    req.user = {
      id: 'test-user',
      role: 'admin',
      email: 'test@alstonaire.com',
      username: 'test-user'
    };
    logger.info('Development bypass: test-token authenticated');
    next();
    return;
  }
  
  // Verify JWT token
  jwt.verify(token, process.env.JWT_SECRET || 'your_jwt_secret_key_here', (err, user) => {
    if (err) {
      logger.warn('Authentication failed: Invalid token', err.message);
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Invalid or expired token'
      });
    }
    
    // Attach user info to request object
    req.user = user;
    logger.info(`User authenticated: ${user.username || user.id}`);
    next();
  });
};

module.exports = { authenticateToken };
