/**
 * ============================================================================
 * Property Verification Routes
 * ============================================================================
 * Description: Express routes for property verification job management
 * Integrates with Bull queue for background job processing
 * ============================================================================
 */

const express = require('express');
const router = express.Router();
const verifyQueue = require('../queues/verifyQueue');
const { authenticateToken } = require('../middleware/auth');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

/**
 * POST /api/property/verify
 * 
 * Submit a property verification job to the queue.
 * Returns immediately with job_id for polling status.
 * 
 * Request body:
 * {
 *   lat: number,
 *   lng: number,
 *   property_id: string
 * }
 * 
 * Response (202 Accepted):
 * {
 *   job_id: string,
 *   status: 'queued',
 *   message: 'Verification started. Poll status endpoint.'
 * }
 */
router.post('/verify', authenticateToken, async (req, res) => {
  try {
    const { lat, lng, property_id } = req.body;
    
    // Validate input
    if (!lat || !lng || !property_id) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Missing required fields: lat, lng, property_id'
      });
    }
    
    if (typeof lat !== 'number' || typeof lng !== 'number') {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'lat and lng must be numbers'
      });
    }
    
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Invalid coordinates'
      });
    }
    
    logger.info(`Submitting verification job for property ${property_id}`);
    
    // Add job to queue with payload
    const job = await verifyQueue.add({
      lat,
      lng,
      property_id,
      submitted_by: req.user.id || req.user.username,
      submitted_at: new Date().toISOString()
    });
    
    // Return immediately with job_id - DO NOT await processing
    res.status(202).json({
      job_id: job.id,
      status: 'queued',
      message: 'Verification started. Poll status endpoint.'
    });
    
    logger.info(`Job ${job.id} queued successfully`);
    
  } catch (error) {
    logger.error('Error submitting verification job:', error);
    res.status(500).json({
      error: 'Internal Server Error',
      message: 'Failed to submit verification job'
    });
  }
});

/**
 * GET /api/property/verify/status/:job_id
 * 
 * Poll the status of a verification job.
 * Returns current job state including progress and logs.
 * 
 * Response:
 * {
 *   job_id: string,
 *   status: 'waiting' | 'active' | 'completed' | 'failed',
 *   progress: {
 *     steps_completed: number,
 *     steps_total: number,
 *     current_step: number,
 *     logs: array
 *   },
 *   result: object, // Only if completed
 *   error: string, // Only if failed
 *   created_at: string,
 *   processed_at: string, // Only if processed
 *   finished_at: string // Only if finished
 * }
 */
router.get('/verify/status/:job_id', authenticateToken, async (req, res) => {
  try {
    const { job_id } = req.params;
    
    logger.info(`Polling status for job ${job_id}`);
    
    // Fetch job state from queue
    const job = await verifyQueue.getJob(job_id);
    
    if (!job) {
      return res.status(404).json({
        error: 'Not Found',
        message: 'Job not found or has expired'
      });
    }
    
    // Get job state
    const state = await job.getState();
    const progress = job.progress();
    
    // Build response
    const response = {
      job_id: job.id,
      status: state,
      progress: {
        steps_completed: progress?.steps_completed || 0,
        steps_total: progress?.steps_total || 14,
        current_step: progress?.current_step || 0,
        logs: progress?.logs || []
      },
      created_at: new Date(job.timestamp).toISOString()
    };
    
    // Add result if job completed successfully
    if (state === 'completed') {
      const result = job.returnvalue;
      response.result = result;
      response.processed_at = new Date(job.processedOn).toISOString();
      response.finished_at = new Date(job.finishedOn).toISOString();
    }
    
    // Add error if job failed
    if (state === 'failed') {
      const failedReason = job.failedReason;
      response.error = failedReason;
      response.processed_at = new Date(job.processedOn).toISOString();
      response.finished_at = new Date(job.finishedOn).toISOString();
    }
    
    res.json(response);
    
    logger.info(`Job ${job_id} status: ${state}`);
    
  } catch (error) {
    logger.error('Error polling job status:', error);
    res.status(500).json({
      error: 'Internal Server Error',
      message: 'Failed to retrieve job status'
    });
  }
});

module.exports = router;
