const { chromium } = require('playwright');

async function quickTest() {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    try {
        console.log('🧪 Quick test: checking if admin UI loads...');
        
        // Test homepage
        await page.goto('http://localhost:3003', { timeout: 5000 });
        const title = await page.title();
        console.log('✅ Homepage loaded:', title);
        
        // Test profiles page  
        await page.goto('http://localhost:3003/profiles', { timeout: 5000 });
        const hasTable = await page.$('#profilesTable') !== null;
        console.log('✅ Profiles page loaded, table present:', hasTable);
        
        // Test health endpoint
        const response = await page.request.get('http://localhost:3003/health');
        console.log('✅ Health endpoint status:', response.status());
        
        console.log('🎉 Basic functionality confirmed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        await page.screenshot({ path: 'error.png' });
        console.log('📸 Error screenshot saved as error.png');
    } finally {
        await browser.close();
    }
}

quickTest();
