const { chromium } = require('playwright');

async function testAdminUI() {
    const browser = await chromium.launch({ headless: false, slowMo: 1000 });
    const page = await browser.newPage();
    
    try {
        console.log('🧪 Testing Admin UI at http://localhost:3003');
        
        // Test 1: Check if home page loads
        console.log('📄 Testing home page...');
        await page.goto('http://localhost:3003', { timeout: 10000 });
        await page.waitForLoadState('domcontentloaded');
        
        const title = await page.title();
        console.log(`✅ Home page loaded. Title: ${title}`);
        
        // Test 2: Navigate to profiles page
        console.log('👥 Testing profiles page...');
        await page.goto('http://localhost:3003/profiles', { timeout: 10000 });
        await page.waitForSelector('#profilesTable', { timeout: 10000 });
        
        const profilesTitle = await page.$eval('h2', el => el.textContent);
        console.log(`✅ Profiles page loaded. Header: ${profilesTitle}`);
        
        // Test 3: Check if bulk actions button exists
        const bulkActionsBtn = await page.$('#bulkActionsBtn');
        if (bulkActionsBtn) {
            console.log('✅ Bulk actions button found');
        } else {
            console.log('❌ Bulk actions button not found');
        }
        
        // Test 4: Check if profile dropdowns work
        const dropdowns = await page.$$('.dropdown-toggle');
        console.log(`✅ Found ${dropdowns.length} dropdown menus`);
        
        if (dropdowns.length > 0) {
            console.log('🔽 Testing first dropdown...');
            await dropdowns[0].click();
            await page.waitForTimeout(500); // Wait for dropdown to open
            
            const dropdownItems = await page.$$('.dropdown-item');
            console.log(`✅ Dropdown opened with ${dropdownItems.length} items`);
            
            // Look for delete action
            const deleteAction = await page.$('.dropdown-item[onclick*="deleteProfile"]');
            if (deleteAction) {
                console.log('✅ Delete profile action found');
            } else {
                console.log('❌ Delete profile action not found');
            }
            
            // Click elsewhere to close dropdown
            await page.click('h2');
        }
        
        // Test 5: Check export functionality
        console.log('📤 Testing export functionality...');
        const exportUrl = 'http://localhost:3003/api/profiles/export?profile_ids=test';
        const exportResponse = await page.request.get(exportUrl);
        console.log(`📊 Export endpoint status: ${exportResponse.status()}`);
        
        // Test 6: Check scoring page
        console.log('⭐ Testing scoring page...');
        await page.goto('http://localhost:3003/scoring', { timeout: 10000 });
        const scoringContent = await page.textContent('body');
        if (scoringContent.includes('Scoring Dashboard') || scoringContent.includes('scoring')) {
            console.log('✅ Scoring page loads successfully');
        } else {
            console.log('❌ Scoring page has issues');
        }
        
        console.log('🎉 All tests completed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        
        // Take a screenshot for debugging
        await page.screenshot({ path: 'test-failure.png', fullPage: true });
        console.log('📸 Screenshot saved as test-failure.png');
        
    } finally {
        await browser.close();
    }
}

// Run the test
testAdminUI().catch(console.error);
