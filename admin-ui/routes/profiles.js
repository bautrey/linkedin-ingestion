const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// GET /profiles - List all profiles
router.get('/', async (req, res) => {
    try {
        const { page = 1, limit = 50, search, company, location, score_range, sort_by, sort_order } = req.query;
        
        const params = {
            page: parseInt(page),
            limit: parseInt(limit)
        };
        
        // Handle search/filter parameters
        if (search) params.name = search;  // API uses 'name' parameter for search
        if (company) params.company = company;
        if (location) params.location = location;
        if (score_range) params.score_range = score_range;
        if (sort_by) params.sort_by = sort_by;
        if (sort_order) params.sort_order = sort_order;
        
        const response = await apiClient.get('/profiles', { params });
        
        // Build base URL for pagination
        const baseUrl = req.originalUrl.split('?')[0];
        const queryString = new URLSearchParams(req.query);
        
        res.render('profiles/list', {
            title: 'LinkedIn Profiles',
            profiles: response.data.data || [],
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
            title: `Profile: ${response.data.name}`,
            profile: response.data,
            currentPage: 'profiles'
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

// GET /profiles/:id/scoring-history - View scoring history for profile
router.get('/:id/scoring-history', async (req, res) => {
    try {
        // Fetch profile info and scoring history
        const [profileResponse, historyResponse] = await Promise.allSettled([
            apiClient.get(`/profiles/${req.params.id}`),
            // For now we'll mock scoring history since the endpoint might not exist yet
            Promise.resolve({ data: [] })
        ]);
        
        if (profileResponse.status === 'fulfilled') {
            const profile = profileResponse.value.data;
            const history = historyResponse.status === 'fulfilled' ? historyResponse.value.data : [];
            
            res.render('profiles/scoring-history', {
                title: `Scoring History: ${profile.name}`,
                profile: profile,
                history: history,
                currentPage: 'profiles'
            });
        } else {
            throw profileResponse.reason;
        }
    } catch (error) {
        logger.error(`Error fetching scoring history for profile ${req.params.id}:`, error);
        if (error.response && error.response.status === 404) {
            res.status(404).render('error', {
                title: 'Profile Not Found',
                message: 'The requested profile could not be found'
            });
        } else {
            res.status(500).render('error', {
                title: 'Error',
                message: 'Failed to load scoring history',
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
