const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// GET /scoring - Show scoring dashboard or profile scoring interface
router.get('/', async (req, res) => {
    try {
        const { profile_id, profile_ids } = req.query;
        
        // If profile_id or profile_ids are provided, show the scoring interface
        if (profile_id || profile_ids) {
            let profilesData = [];
            let templatesData = [];
            
            try {
                // Fetch templates for scoring selection
                const templatesResponse = await apiClient.get('/templates');
                // Handle nested response structure: response.data.data.templates
                templatesData = templatesResponse.data?.data?.templates || templatesResponse.data?.templates || templatesResponse.data || [];
                logger.info(`Fetched ${templatesData.length} templates for scoring`);
                logger.debug('Templates data:', templatesData);
                
                if (profile_id) {
                    // Single profile scoring
                    const profileResponse = await apiClient.get(`/profiles/${profile_id}`);
                    // Handle nested response structure for single profile
                    const profileData = profileResponse.data?.data || profileResponse.data;
                    profilesData = [profileData];
                    logger.info(`Fetched profile: ${profileData?.name || profileData?.full_name || 'Unknown'}`);
                } else if (profile_ids) {
                    // Bulk profile scoring
                    const idsArray = profile_ids.split(',');
                    const profilePromises = idsArray.map(id => 
                        apiClient.get(`/profiles/${id}`).catch(error => {
                            logger.warn(`Failed to fetch profile ${id}:`, error.message);
                            return null;
                        })
                    );
                    const profileResponses = await Promise.all(profilePromises);
                    // Handle nested response structure for each profile
                    profilesData = profileResponses.filter(Boolean).map(response => response.data?.data || response.data);
                    logger.info(`Fetched ${profilesData.length} profiles for bulk scoring`);
                }
                
                const title = profilesData.length === 1 
                    ? `Score Profile: ${profilesData[0].full_name || profilesData[0].name}` 
                    : `Score ${profilesData.length} Profiles`;
                
                res.render('scoring/score-profiles', {
                    title,
                    profiles: profilesData,
                    templates: templatesData,
                    isBulk: profilesData.length > 1,
                    currentPage: 'scoring'
                });
                
            } catch (error) {
                logger.error('Error loading profiles for scoring:', error);
                res.status(500).render('error', {
                    title: 'Error',
                    message: 'Failed to load profiles for scoring',
                    error: process.env.NODE_ENV === 'development' ? error : {}
                });
            }
        } else {
            // Show scoring dashboard
            // Note: Jobs endpoint doesn't exist yet, so we'll show empty jobs for now
            const jobs = [];
            const stats = {
                total_jobs: 0,
                pending_jobs: 0,
                completed_jobs: 0,
                failed_jobs: 0
            };
            
            res.render('scoring/dashboard', {
                title: 'Scoring Dashboard',
                jobs: jobs,
                stats: stats,
                currentPage: 'scoring'
            });
        }
    } catch (error) {
        logger.error('Error loading scoring interface:', error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to load scoring interface',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

// GET /scoring/jobs/:id - View scoring job details
router.get('/jobs/:id', async (req, res) => {
    try {
        // Use the correct API endpoint for scoring jobs
        const response = await apiClient.get(`/scoring-jobs/${req.params.id}`);
        
        res.render('scoring/job-detail', {
            title: `Scoring Job: ${req.params.id}`,
            job: response.data,
            currentPage: 'scoring'
        });
    } catch (error) {
        logger.error(`Error fetching scoring job ${req.params.id}:`, error);
        if (error.response && error.response.status === 404) {
            res.status(404).render('error', {
                title: 'Job Not Found',
                message: 'The requested scoring job could not be found',
                error: {}
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
