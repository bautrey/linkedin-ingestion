const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// GET /ingestion - Show ingestion dashboard
router.get('/', async (req, res) => {
    try {
        // Get recent ingestion jobs
        const jobsResponse = await apiClient.get('/jobs', { 
            params: { limit: 20, type: 'ingestion' } 
        }).catch(() => ({ data: { jobs: [] } }));
        
        res.render('ingestion/dashboard', {
            title: 'LinkedIn Ingestion',
            jobs: jobsResponse.data.jobs || []
        });
    } catch (error) {
        logger.error('Error loading ingestion dashboard:', error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to load ingestion dashboard',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

// GET /ingestion/new - Show ingestion form
router.get('/new', (req, res) => {
    res.render('ingestion/form', {
        title: 'Ingest LinkedIn Profiles'
    });
});

// GET /ingestion/jobs/:id - View ingestion job details
router.get('/jobs/:id', async (req, res) => {
    try {
        const response = await apiClient.get(`/jobs/${req.params.id}`);
        
        res.render('ingestion/job-detail', {
            title: `Ingestion Job: ${req.params.id}`,
            job: response.data
        });
    } catch (error) {
        logger.error(`Error fetching ingestion job ${req.params.id}:`, error);
        if (error.response && error.response.status === 404) {
            res.status(404).render('error', {
                title: 'Job Not Found',
                message: 'The requested ingestion job could not be found'
            });
        } else {
            res.status(500).render('error', {
                title: 'Error',
                message: 'Failed to load ingestion job',
                error: process.env.NODE_ENV === 'development' ? error : {}
            });
        }
    }
});

module.exports = router;
