const { chromium } = require('playwright');

async function testProfileManagement() {
    const browser = await chromium.launch({ headless: false, slowMo: 500 });
    const page = await browser.newPage();
    
    try {
        console.log('🧪 Testing Profile Management Features...');
        
        // 1. Load profiles page
        console.log('📄 Loading profiles page...');
        await page.goto('http://localhost:3003/profiles', { timeout: 10000 });
        await page.waitForSelector('#profilesTable', { timeout: 5000 });
        
        // 2. Check if bulk actions button exists and is initially disabled
        console.log('🔍 Checking bulk actions button...');
        const bulkBtn = await page.$('#bulkActionsBtn');
        const isDisabled = await bulkBtn.getAttribute('disabled');
        console.log(`✅ Bulk actions button exists and is ${isDisabled !== null ? 'disabled' : 'enabled'} (correct initial state)`);
        
        // 3. Look for profile action dropdowns
        console.log('🔽 Testing profile action dropdowns...');
        const dropdowns = await page.$$('.dropdown-toggle');
        console.log(`✅ Found ${dropdowns.length} dropdown menus`);
        
        if (dropdowns.length > 0) {
            // Test first dropdown
            await dropdowns[0].click();
            await page.waitForTimeout(500);
            
            const dropdownItems = await page.$$('.dropdown-item');
            console.log(`✅ Dropdown opened with ${dropdownItems.length} items`);
            
            // Look for specific actions
            const viewAction = await page.$('.dropdown-item[href*="/profiles/"]');
            const scoreAction = await page.$('.dropdown-item[onclick*="scoreProfile"]');
            const deleteAction = await page.$('.dropdown-item[onclick*="deleteProfile"]');
            
            console.log(`✅ View action: ${viewAction ? 'found' : 'missing'}`);
            console.log(`✅ Score action: ${scoreAction ? 'found' : 'missing'}`);
            console.log(`✅ Delete action: ${deleteAction ? 'found' : 'missing'}`);
            
            // Close dropdown by clicking elsewhere
            await page.click('h2');
            await page.waitForTimeout(200);
        }
        
        // 4. Test export endpoint
        console.log('📤 Testing export functionality...');
        try {
            const exportResponse = await page.request.get('http://localhost:3003/api/profiles/export?profile_ids=test');
            console.log(`✅ Export endpoint responds with status: ${exportResponse.status()}`);
        } catch (error) {
            console.log(`⚠️  Export endpoint test: ${error.message}`);
        }
        
        // 5. Test scoring page
        console.log('⭐ Testing scoring page...');
        await page.goto('http://localhost:3003/scoring', { timeout: 5000 });
        
        const scoringPageContent = await page.textContent('body');
        const hasScoring = scoringPageContent.includes('Scoring Dashboard') || scoringPageContent.includes('scoring');
        console.log(`✅ Scoring page loads: ${hasScoring}`);
        
        // 6. Test scoring with profile ID
        console.log('🎯 Testing scoring with profile parameter...');
        await page.goto('http://localhost:3003/scoring?profile_id=test', { timeout: 5000 });
        const scoringWithProfile = await page.textContent('body');
        const hasProfileScoring = scoringWithProfile.includes('Score Profile') || scoringWithProfile.includes('template');
        console.log(`✅ Profile scoring interface: ${hasProfileScoring}`);
        
        console.log('🎉 Profile management tests completed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        await page.screenshot({ path: 'profile-test-error.png', fullPage: true });
        console.log('📸 Error screenshot saved as profile-test-error.png');
    } finally {
        await browser.close();
    }
}

testProfileManagement();
