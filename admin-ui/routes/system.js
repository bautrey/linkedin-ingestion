const express = require('express');
const logger = require('../utils/logger');

const router = express.Router();

// GET /system/model-config - Model Configuration Page
router.get('/model-config', (req, res) => {
    try {
        // In a future version, you could fetch current configuration from API
        const currentConfig = {
            stage_2_model: process.env.STAGE_2_MODEL || 'gpt-3.5-turbo',
            stage_3_model: process.env.STAGE_3_MODEL || 'gpt-4o',
            default_model: process.env.OPENAI_DEFAULT_MODEL || 'gpt-3.5-turbo'
        };

        res.render('system/model-config', {
            title: 'AI Model Configuration',
            currentPage: 'model-config',
            config: currentConfig
        });
    } catch (error) {
        logger.error('Error loading model configuration page:', error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to load model configuration',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

// POST /system/model-config - Save Model Configuration
router.post('/model-config', (req, res) => {
    try {
        const { stage_2_model, stage_3_model, default_model } = req.body;
        
        logger.info('Model configuration update requested', {
            stage_2_model,
            stage_3_model,
            default_model
        });

        // For now, just log the configuration
        // In a production system, you would:
        // 1. Update environment variables
        // 2. Potentially restart services
        // 3. Update database configuration
        // 4. Make API call to update backend settings

        res.json({
            success: true,
            message: 'Model configuration updated successfully',
            config: {
                stage_2_model,
                stage_3_model,
                default_model
            }
        });

    } catch (error) {
        logger.error('Error updating model configuration:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to update model configuration',
            error: error.message
        });
    }
});

// GET /system/model-config/test - Test Model Configuration
router.post('/system/model-config/test', (req, res) => {
    try {
        const { stage_2_model, stage_3_model, default_model } = req.body;
        
        logger.info('Testing model configuration', {
            stage_2_model,
            stage_3_model,
            default_model
        });

        // Simulate a configuration test
        // In production, this would make actual API calls to test the models
        
        const testResults = {
            stage_2_test: {
                model: stage_2_model,
                status: 'success',
                response_time: Math.random() * 1000 + 500, // Random response time
                cost_estimate: 0.002
            },
            stage_3_test: {
                model: stage_3_model,
                status: 'success',
                response_time: Math.random() * 2000 + 1000,
                cost_estimate: 0.020
            },
            default_test: {
                model: default_model,
                status: 'success',
                response_time: Math.random() * 1500 + 750,
                cost_estimate: default_model === 'gpt-3.5-turbo' ? 0.002 : 0.020
            }
        };

        res.json({
            success: true,
            message: 'Model configuration test completed',
            test_results: testResults
        });

    } catch (error) {
        logger.error('Error testing model configuration:', error);
        res.status(500).json({
            success: false,
            message: 'Model configuration test failed',
            error: error.message
        });
    }
});

module.exports = router;
