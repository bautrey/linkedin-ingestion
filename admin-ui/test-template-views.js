#!/usr/bin/env node

const axios = require('axios');
const { performance } = require('perf_hooks');

const BASE_URL = 'http://localhost:3003';
const TIMEOUT = 10000; // 10 seconds

async function testTemplateViews() {
    console.log('🔍 Testing LinkedIn Ingestion Admin UI Template Views\n');
    
    const tests = [
        {
            name: 'Templates List Page',
            url: '/templates',
            expectHtml: ['Prompt Templates', 'templates available', 'btn-primary']
        },
        {
            name: 'Template Detail Page', 
            url: '/templates/3540af7c-29cb-4e4c-b04f-a64881f9975d',
            expectHtml: ['Enhanced CIO Evaluation Template', 'Version History', 'Usage Statistics']
        }
    ];
    
    let passed = 0;
    let failed = 0;
    
    for (const test of tests) {
        console.log(`📋 Testing: ${test.name}`);
        
        try {
            const startTime = performance.now();
            const response = await axios.get(`${BASE_URL}${test.url}`, {
                timeout: TIMEOUT,
                headers: {
                    'User-Agent': 'Test-Agent/1.0'
                }
            });
            const endTime = performance.now();
            const responseTime = Math.round(endTime - startTime);
            
            // Check status code
            if (response.status !== 200) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Check content type
            const contentType = response.headers['content-type'];
            if (!contentType || !contentType.includes('text/html')) {
                throw new Error(`Expected HTML, got ${contentType}`);
            }
            
            // Check expected content
            const html = response.data;
            const missingContent = [];
            
            for (const expectedContent of test.expectHtml) {
                if (!html.includes(expectedContent)) {
                    missingContent.push(expectedContent);
                }
            }
            
            if (missingContent.length > 0) {
                throw new Error(`Missing content: ${missingContent.join(', ')}`);
            }
            
            // Check for basic responsive elements
            const responsiveChecks = [
                'viewport',
                'bootstrap',
                'col-',
                'container-fluid'
            ];
            
            const missingResponsive = responsiveChecks.filter(check => !html.includes(check));
            
            if (missingResponsive.length > 0) {
                console.log(`   ⚠️  Missing responsive elements: ${missingResponsive.join(', ')}`);
            }
            
            console.log(`   ✅ PASS (${responseTime}ms)\n`);
            passed++;
            
        } catch (error) {
            console.log(`   ❌ FAIL: ${error.message}\n`);
            failed++;
        }
    }
    
    // Test server health
    console.log('📋 Testing: Server Health');
    try {
        const response = await axios.get(`${BASE_URL}/health`, { timeout: TIMEOUT });
        if (response.status === 200 && response.data.status === 'healthy') {
            console.log('   ✅ PASS - Server is healthy\n');
            passed++;
        } else {
            throw new Error('Server not healthy');
        }
    } catch (error) {
        console.log(`   ❌ FAIL: ${error.message}\n`);
        failed++;
    }
    
    // Summary
    console.log('📊 Test Summary:');
    console.log(`   ✅ Passed: ${passed}`);
    console.log(`   ❌ Failed: ${failed}`);
    console.log(`   📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%\n`);
    
    if (failed === 0) {
        console.log('🎉 All tests passed! Template views are production ready.\n');
        process.exit(0);
    } else {
        console.log('🚨 Some tests failed. Please review the issues above.\n');
        process.exit(1);
    }
}

// Run the tests
testTemplateViews().catch(error => {
    console.error('❌ Test runner error:', error.message);
    process.exit(1);
});
