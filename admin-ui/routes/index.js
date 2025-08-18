const express = require('express');
const router = express.Router();
const apiClient = require('../config/api');
const logger = require('../utils/logger');

// Dashboard route
router.get('/', async (req, res) => {
    try {
        // Fetch dashboard statistics
        const [profilesResponse, companiesResponse, healthResponse] = await Promise.allSettled([
            apiClient.get('/api/v1/profiles', { params: { limit: 20, skip: 0 } }),
            apiClient.get('/api/v1/companies', { params: { limit: 10, skip: 0 } }),
            apiClient.get('/api/v1/health')
        ]);

        // Extract data with fallbacks
        const profiles = profilesResponse.status === 'fulfilled' ? profilesResponse.value.data : { items: [], total: 0 };
        const companies = companiesResponse.status === 'fulfilled' ? companiesResponse.value.data : { items: [], total: 0 };
        const health = healthResponse.status === 'fulfilled' ? healthResponse.value.data : { status: 'unknown' };

        // Recent profiles (last 10 for quick view)
        const recentProfiles = profiles.items ? profiles.items.slice(0, 10) : [];

        res.render('dashboard', {
            title: 'Dashboard',
            statistics: {
                profileCount: profiles.total || 0,
                companyCount: companies.total || 0,
                recentCount: recentProfiles.length
            },
            recentProfiles: recentProfiles,
            systemHealth: health,
            pageScript: 'dashboard'
        });

    } catch (error) {
        logger.error('Dashboard error:', error);
        res.render('error', {
            title: 'Dashboard Error',
            error: { 
                message: 'Failed to load dashboard data. Please try again later.',
                details: process.env.NODE_ENV === 'development' ? error.message : undefined
            }
        });
    }
});

module.exports = router;
