const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// GET /profiles - List all profiles
router.get('/', async (req, res) => {
    try {
        const { page = 1, limit = 50, search, sort_by, sort_order } = req.query;
        
        const params = {
            page: parseInt(page),
            limit: parseInt(limit)
        };
        
        if (search) params.search = search;
        if (sort_by) params.sort_by = sort_by;
        if (sort_order) params.sort_order = sort_order;
        
        const response = await apiClient.get('/profiles', { params });
        
        // Build base URL for pagination
        const baseUrl = req.originalUrl.split('?')[0];
        const queryString = new URLSearchParams(req.query);
        
        res.render('profiles/list', {
            title: 'LinkedIn Profiles',
            profiles: response.data.profiles || [],
            pagination: response.data.pagination || {},
            query: req.query,
            currentPage: 'profiles',
            baseUrl: baseUrl,
            queryParams: queryString.toString()
        });
    } catch (error) {
        logger.error('Error fetching profiles:', error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to load profiles',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

// GET /profiles/:id - View single profile
router.get('/:id', async (req, res) => {
    try {
        const response = await apiClient.get(`/profiles/${req.params.id}`);
        
        res.render('profiles/detail', {
            title: `Profile: ${response.data.full_name}`,
            profile: response.data
        });
    } catch (error) {
        logger.error(`Error fetching profile ${req.params.id}:`, error);
        if (error.response && error.response.status === 404) {
            res.status(404).render('error', {
                title: 'Profile Not Found',
                message: 'The requested profile could not be found'
            });
        } else {
            res.status(500).render('error', {
                title: 'Error',
                message: 'Failed to load profile',
                error: process.env.NODE_ENV === 'development' ? error : {}
            });
        }
    }
});

// DELETE /profiles/:id - Delete profile
router.delete('/:id', async (req, res) => {
    try {
        await apiClient.delete(`/profiles/${req.params.id}`);
        res.json({ success: true, message: 'Profile deleted successfully' });
    } catch (error) {
        logger.error(`Error deleting profile ${req.params.id}:`, error);
        res.status(500).json({
            success: false,
            message: 'Failed to delete profile',
            error: error.message
        });
    }
});

module.exports = router;
