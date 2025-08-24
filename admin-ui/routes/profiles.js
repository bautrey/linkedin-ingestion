const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// GET /profiles - List all profiles
router.get('/', async (req, res) => {
    try {
        logger.info('Processing profiles request', { query: req.query, originalUrl: req.originalUrl });
        
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
        
        logger.info('Making API call with params', { params });
        
        const response = await apiClient.get('/profiles', { params });
        
        logger.info('API response received', { 
            dataLength: response.data?.data?.length || 0,
            pagination: response.data?.pagination
        });
        
        // Build base URL for pagination
        const baseUrl = req.originalUrl.split('?')[0];
        const queryString = new URLSearchParams(req.query);
        
        logger.info('Rendering template', { 
            baseUrl, 
            queryParams: queryString.toString(),
            hasProfiles: !!(response.data?.data?.length)
        });
        
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
        logger.error('Error fetching profiles:', {
            error: error.message,
            status: error.response?.status,
            statusText: error.response?.statusText,
            data: error.response?.data,
            config: {
                url: error.config?.url,
                method: error.config?.method,
                params: error.config?.params
            }
        });
        
        // In case of API error, still render the page but with empty results
        // This prevents losing the URL parameters
        const baseUrl = req.originalUrl.split('?')[0];
        const queryString = new URLSearchParams(req.query);
        
        res.render('profiles/list', {
            title: 'LinkedIn Profiles',
            profiles: [],
            pagination: {},
            query: req.query,
            currentPage: 'profiles',
            baseUrl: baseUrl,
            queryParams: queryString.toString(),
            error: 'Failed to load profiles. Please try again.'
        });
    }
});

// GET /profiles/:id - View single profile
router.get('/:id', async (req, res) => {
    try {
        const response = await apiClient.get(`/profiles/${req.params.id}`);
        const profile = response.data;
        
        // Extract company names from profile experience
        const companyNames = new Set();
        
        // Add current company
        if (profile.current_company && profile.current_company.name) {
            companyNames.add(profile.current_company.name);
        }
        
        // Add companies from experience
        if (profile.experience && profile.experience.length > 0) {
            profile.experience.forEach(exp => {
                if (exp.company) {
                    companyNames.add(exp.company);
                }
            });
        }
        
        // Map company names to our internal company records
        const companyMapping = {};
        
        // Search for each company in our database
        for (const companyName of companyNames) {
            try {
                const companyResponse = await apiClient.get('/companies', {
                    params: { name: companyName, limit: 1 }
                });
                
                if (companyResponse.data.data && companyResponse.data.data.length > 0) {
                    const company = companyResponse.data.data[0];
                    // Only map if the company name is a close match
                    if (company.company_name.toLowerCase().includes(companyName.toLowerCase()) || 
                        companyName.toLowerCase().includes(company.company_name.toLowerCase())) {
                        companyMapping[companyName] = {
                            id: company.id,
                            name: company.company_name,
                            url: `/companies/${company.id}`
                        };
                    }
                }
            } catch (companyError) {
                // If company search fails, continue without mapping
                logger.debug(`Company search failed for ${companyName}:`, companyError.message);
            }
        }
        
        res.render('profiles/detail', {
            title: `Profile: ${profile.name}`,
            profile: profile,
            companyMapping: companyMapping,
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
