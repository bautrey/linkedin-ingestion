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
        
        const response = await apiClient.post(`/profiles/${profileId}/score-enhanced`, scoringRequest);
        
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

// POST /api/templates/:id/test - Test template with sample data
router.post('/templates/:id/test', async (req, res) => {
    try {
        const templateId = req.params.id;
        const { use_sample_data } = req.body;
        
        // First get the template
        const templateResponse = await apiClient.get(`/templates/${templateId}`);
        const template = templateResponse.data;
        
        // Sample profile data for testing
        const sampleData = {
            full_name: 'John Smith',
            position: 'Senior Software Engineer',
            current_company: {
                name: 'TechCorp Inc.',
                size: '1000-5000',
                industry: 'Software Development'
            },
            location: 'San Francisco, CA',
            experience: [
                {
                    title: 'Senior Software Engineer',
                    company: 'TechCorp Inc.',
                    duration: '2022-Present',
                    description: 'Lead a team of 5 engineers developing cloud-native applications'
                },
                {
                    title: 'Software Engineer',
                    company: 'StartupXYZ',
                    duration: '2019-2022',
                    description: 'Full-stack development using React and Node.js'
                }
            ],
            education: [
                {
                    degree: 'BS Computer Science',
                    school: 'Stanford University',
                    year: '2019'
                }
            ],
            skills: ['JavaScript', 'Python', 'React', 'Node.js', 'AWS', 'Docker', 'Kubernetes'],
            summary: 'Experienced software engineer with expertise in full-stack development and cloud technologies'
        };
        
        // Generate the prompt by replacing placeholders
        let generatedPrompt = template.prompt_text;
        generatedPrompt = generatedPrompt.replace('{{profile_data}}', JSON.stringify(sampleData, null, 2));
        generatedPrompt = generatedPrompt.replace('{{profile_name}}', sampleData.full_name);
        generatedPrompt = generatedPrompt.replace('{{current_title}}', sampleData.position);
        generatedPrompt = generatedPrompt.replace('{{current_company}}', sampleData.current_company.name);
        
        // For testing purposes, we'll return the generated prompt and sample response
        // In a real implementation, you'd send this to an AI service
        const mockAiResponse = {
            technical_leadership: { score: 7, reasoning: 'Strong technical background with team leadership experience' },
            strategic_vision: { score: 6, reasoning: 'Good understanding of modern technologies but limited strategic experience shown' },
            team_management: { score: 8, reasoning: 'Currently leading a team of 5 engineers, demonstrating management capabilities' },
            industry_experience: { score: 7, reasoning: 'Solid experience in software development with both startup and established company exposure' },
            cultural_fit: { score: 8, reasoning: 'Background suggests adaptability and growth mindset' },
            overall_score: 7.2,
            summary: 'Strong technical candidate with leadership experience. Good fit for senior technical roles requiring team management.'
        };
        
        res.json({
            success: true,
            sample_data: sampleData,
            generated_prompt: generatedPrompt,
            ai_response: JSON.stringify(mockAiResponse, null, 2),
            score: mockAiResponse.overall_score,
            template_id: templateId,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error(`Error testing template ${req.params.id}:`, error);
        res.status(500).json({
            success: false,
            message: 'Failed to test template',
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

// GET /api/profiles/export - Export profiles to CSV
router.get('/profiles/export', async (req, res) => {
    try {
        const { profile_ids, format = 'csv' } = req.query;
        
        if (!profile_ids) {
            return res.status(400).json({
                success: false,
                message: 'profile_ids parameter is required'
            });
        }
        
        const idsArray = profile_ids.split(',');
        
        // Fetch all profiles by IDs
        const profilePromises = idsArray.map(id => apiClient.get(`/profiles/${id}`));
        const profileResponses = await Promise.all(profilePromises);
        const profiles = profileResponses.map(response => response.data);
        
        if (format === 'csv') {
            // Generate CSV content
            const csvHeader = [
                'Name',
                'Position', 
                'Company',
                'Location',
                'LinkedIn URL',
                'Score',
                'Created Date',
                'Email',
                'Phone'
            ].join(',');
            
            const csvRows = profiles.map(profile => [
                `"${(profile.full_name || profile.name || '').replace(/"/g, '""')}"`,
                `"${(profile.position || '').replace(/"/g, '""')}"`,
                `"${(profile.current_company?.name || '').replace(/"/g, '""')}"`,
                `"${[profile.city, profile.country_code].filter(Boolean).join(', ').replace(/"/g, '""')}"`,
                `"${(profile.url || profile.linkedin_url || '').replace(/"/g, '""')}"`,
                profile.score || '',
                profile.created_at ? new Date(profile.created_at).toLocaleDateString() : '',
                `"${(profile.email || '').replace(/"/g, '""')}"`,
                `"${(profile.phone || '').replace(/"/g, '""')}"`
            ].join(','));
            
            const csvContent = [csvHeader, ...csvRows].join('\n');
            
            const timestamp = new Date().toISOString().split('T')[0];
            const filename = `linkedin-profiles-${timestamp}.csv`;
            
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
            res.send(csvContent);
        } else {
            // Return JSON format
            res.json({
                success: true,
                data: profiles
            });
        }
    } catch (error) {
        logger.error('Error exporting profiles:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to export profiles',
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
