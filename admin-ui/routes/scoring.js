const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// GET /scoring - Show scoring dashboard
router.get('/', async (req, res) => {
    try {
        // Get recent scoring jobs and statistics
        const [jobsResponse, statsResponse] = await Promise.all([
            apiClient.get('/jobs', { params: { limit: 20, type: 'scoring' } }).catch(() => ({ data: [] })),
            apiClient.get('/jobs/stats').catch(() => ({ data: {} }))
        ]);
        
        res.render('scoring/dashboard', {
            title: 'Scoring Dashboard',
            jobs: jobsResponse.data.jobs || [],
            stats: statsResponse.data || {}
        });
    } catch (error) {
        logger.error('Error loading scoring dashboard:', error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to load scoring dashboard',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

// GET /scoring/jobs/:id - View scoring job details
router.get('/jobs/:id', async (req, res) => {
    try {
        const response = await apiClient.get(`/jobs/${req.params.id}`);
        
        res.render('scoring/job-detail', {
            title: `Scoring Job: ${req.params.id}`,
            job: response.data
        });
    } catch (error) {
        logger.error(`Error fetching scoring job ${req.params.id}:`, error);
        if (error.response && error.response.status === 404) {
            res.status(404).render('error', {
                title: 'Job Not Found',
                message: 'The requested scoring job could not be found'
            });
        } else {
            res.status(500).render('error', {
                title: 'Error',
                message: 'Failed to load scoring job',
                error: process.env.NODE_ENV === 'development' ? error : {}
            });
        }
    }
});

module.exports = router;
