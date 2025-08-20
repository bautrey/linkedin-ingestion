const express = require('express');
const apiClient = require('../config/api');
const logger = require('../utils/logger');

const router = express.Router();

// GET /templates - List all templates
router.get('/', async (req, res) => {
    try {
        const response = await apiClient.get('/templates');
        
        res.render('templates/list', {
            title: 'Prompt Templates',
            templates: response.data?.templates || []
        });
    } catch (error) {
        logger.error('Error fetching templates:', error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to load templates',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

// GET /templates/new - Show template creation form
router.get('/new', (req, res) => {
    res.render('templates/form', {
        title: 'Create New Template',
        template: null,
        isEdit: false
    });
});

// GET /templates/:id - View template details
router.get('/:id', async (req, res) => {
    try {
        const response = await apiClient.get(`/templates/${req.params.id}`);
        
        res.render('templates/detail', {
            title: `Template: ${response.data.name}`,
            template: response.data
        });
    } catch (error) {
        logger.error(`Error fetching template ${req.params.id}:`, error);
        if (error.response && error.response.status === 404) {
            res.status(404).render('error', {
                title: 'Template Not Found',
                message: 'The requested template could not be found'
            });
        } else {
            res.status(500).render('error', {
                title: 'Error',
                message: 'Failed to load template',
                error: process.env.NODE_ENV === 'development' ? error : {}
            });
        }
    }
});

// GET /templates/:id/edit - Show template edit form
router.get('/:id/edit', async (req, res) => {
    try {
        const response = await apiClient.get(`/templates/${req.params.id}`);
        
        res.render('templates/form', {
            title: `Edit Template: ${response.data.name}`,
            template: response.data,
            isEdit: true
        });
    } catch (error) {
        logger.error(`Error fetching template for edit ${req.params.id}:`, error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to load template for editing',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

// GET /templates/:id/versions - View template version history
router.get('/:id/versions', async (req, res) => {
    try {
        const [templateResponse, versionsResponse] = await Promise.all([
            apiClient.get(`/templates/${req.params.id}`),
            apiClient.get(`/templates/${req.params.id}/versions`)
        ]);
        
        res.render('templates/versions', {
            title: `Version History: ${templateResponse.data.name}`,
            template: templateResponse.data,
            versions: versionsResponse.data || []
        });
    } catch (error) {
        logger.error(`Error fetching template versions ${req.params.id}:`, error);
        if (error.response && error.response.status === 404) {
            res.status(404).render('error', {
                title: 'Template Not Found',
                message: 'The requested template could not be found'
            });
        } else {
            res.status(500).render('error', {
                title: 'Error',
                message: 'Failed to load template versions',
                error: process.env.NODE_ENV === 'development' ? error : {}
            });
        }
    }
});

// GET /templates/:id/versions/:version/compare/:compareVersion - Compare template versions
router.get('/:id/versions/:version/compare/:compareVersion', async (req, res) => {
    try {
        const { id, version, compareVersion } = req.params;
        
        const [templateResponse, diffResponse] = await Promise.all([
            apiClient.get(`/templates/${id}`),
            apiClient.get(`/templates/${id}/versions/${version}/diff/${compareVersion}`)
        ]);
        
        res.render('templates/compare', {
            title: `Compare Versions: ${templateResponse.data.name}`,
            template: templateResponse.data,
            version: parseInt(version),
            compareVersion: parseInt(compareVersion),
            diff: diffResponse.data
        });
    } catch (error) {
        logger.error(`Error comparing template versions ${req.params.id}:`, error);
        res.status(500).render('error', {
            title: 'Error',
            message: 'Failed to compare template versions',
            error: process.env.NODE_ENV === 'development' ? error : {}
        });
    }
});

module.exports = router;
