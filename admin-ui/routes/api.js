const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// POST /api/profiles/:id/score - Score a profile
router.post('/profiles/:id/score', async (req, res) => {
    try {
        const { template_id, prompt } = req.body;
        const profileId = req.params.id;
        
        // Prepare scoring request
        const scoringRequest = {};
        if (template_id) {
            scoringRequest.template_id = template_id;
        } else if (prompt) {
            scoringRequest.prompt = prompt;
        } else {
            return res.status(400).json({
                success: false,
                message: 'Either template_id or prompt is required'
            });
        }
        
        const response = await apiClient.post(`/scoring/score-profile/${profileId}`, scoringRequest);
        
        // Emit real-time update if socket is available
        if (req.io) {
            req.io.emit('scoring-started', {
                profile_id: profileId,
                job_id: response.data.job_id,
                timestamp: new Date().toISOString()
            });
        }
        
        res.json({
            success: true,
            data: response.data
        });
    } catch (error) {
        logger.error(`Error scoring profile ${req.params.id}:`, error);
        res.status(500).json({
            success: false,
            message: 'Failed to start scoring',
            error: error.message
        });
    }
});

// GET /api/profiles/:id/scoring-results - Get scoring results
router.get('/profiles/:id/scoring-results', async (req, res) => {
    try {
        const response = await apiClient.get(`/scoring/results/${req.params.id}`);
        res.json({
            success: true,
            data: response.data
        });
    } catch (error) {
        logger.error(`Error fetching scoring results for profile ${req.params.id}:`, error);
        res.status(500).json({
            success: false,
            message: 'Failed to fetch scoring results',
            error: error.message
        });
    }
});

// GET /api/templates - Get all templates
router.get('/templates', async (req, res) => {
    try {
        const response = await apiClient.get('/templates');
        res.json({
            success: true,
            data: response.data
        });
    } catch (error) {
        logger.error('Error fetching templates:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to fetch templates',
            error: error.message
        });
    }
});

// POST /api/templates - Create new template
router.post('/templates', async (req, res) => {
    try {
        const response = await apiClient.post('/templates', req.body);
        res.json({
            success: true,
            data: response.data
        });
    } catch (error) {
        logger.error('Error creating template:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to create template',
            error: error.message
        });
    }
});

// PUT /api/templates/:id - Update template
router.put('/templates/:id', async (req, res) => {
    try {
        const response = await apiClient.put(`/templates/${req.params.id}`, req.body);
        res.json({
            success: true,
            data: response.data
        });
    } catch (error) {
        logger.error(`Error updating template ${req.params.id}:`, error);
        res.status(500).json({
            success: false,
            message: 'Failed to update template',
            error: error.message
        });
    }
});

// DELETE /api/templates/:id - Delete template
router.delete('/templates/:id', async (req, res) => {
    try {
        await apiClient.delete(`/templates/${req.params.id}`);
        res.json({
            success: true,
            message: 'Template deleted successfully'
        });
    } catch (error) {
        logger.error(`Error deleting template ${req.params.id}:`, error);
        res.status(500).json({
            success: false,
            message: 'Failed to delete template',
            error: error.message
        });
    }
});

// POST /api/ingestion - Start LinkedIn profile ingestion
router.post('/ingestion', async (req, res) => {
    try {
        const { urls } = req.body;
        
        if (!urls || !Array.isArray(urls) || urls.length === 0) {
            return res.status(400).json({
                success: false,
                message: 'URLs array is required'
            });
        }
        
        const results = [];
        
        // Process each URL
        for (const url of urls) {
            try {
                const response = await apiClient.post('/profiles/ingest', { linkedin_url: url });
                results.push({
                    url,
                    success: true,
                    data: response.data
                });
                
                // Emit real-time update
                if (req.io) {
                    req.io.emit('ingestion-started', {
                        url,
                        job_id: response.data.job_id,
                        timestamp: new Date().toISOString()
                    });
                }
            } catch (error) {
                results.push({
                    url,
                    success: false,
                    error: error.message
                });
            }
        }
        
        res.json({
            success: true,
            data: results
        });
    } catch (error) {
        logger.error('Error starting ingestion:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to start ingestion',
            error: error.message
        });
    }
});

// GET /api/system/stats - Get system statistics
router.get('/system/stats', async (req, res) => {
    try {
        const [profilesResponse, jobsResponse] = await Promise.all([
            apiClient.get('/profiles/stats'),
            apiClient.get('/jobs/stats')
        ]);
        
        res.json({
            success: true,
            data: {
                profiles: profilesResponse.data,
                jobs: jobsResponse.data,
                uptime: process.uptime(),
                timestamp: new Date().toISOString()
            }
        });
    } catch (error) {
        logger.error('Error fetching system stats:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to fetch system statistics',
            error: error.message
        });
    }
});

module.exports = router;
