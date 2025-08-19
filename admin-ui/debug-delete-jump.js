const { chromium } = require('playwright');

async function debugDeleteJump() {
    console.log('🧪 Starting delete link jump investigation...');
    
    const browser = await chromium.launch({ 
        headless: false,  // Show the browser
        slowMo: 1000      // Slow down interactions
    });
    
    try {
        const page = await browser.newPage();
        
        // Navigate to profiles page
        await page.goto('http://localhost:3003/profiles');
        console.log('📄 Navigated to profiles page');
        
        // Wait for page to fully load
        await page.waitForSelector('#profilesTable');
        
        // Get initial scroll position
        const initialScrollY = await page.evaluate(() => window.scrollY);
        console.log(`📐 Initial scroll position: ${initialScrollY}`);
        
        // Scroll down to make the jump more obvious
        await page.evaluate(() => window.scrollTo(0, 500));
        const scrolledPosition = await page.evaluate(() => window.scrollY);
        console.log(`📐 Scrolled to position: ${scrolledPosition}`);
        
        // Find all profile rows
        const profileRows = await page.locator('#profilesTable tbody tr[data-profile-id]').count();
        console.log(`👥 Found ${profileRows} profile rows`);
        
        if (profileRows === 0) {
            console.log('❌ No profiles found to test delete functionality');
            return;
        }
        
        // Look for the last row (John Doe should be at the bottom)
        const lastRowIndex = profileRows - 1;
        const lastRow = page.locator('#profilesTable tbody tr[data-profile-id]').nth(lastRowIndex);
        
        // Get profile name from the last row
        const profileName = await lastRow.locator('td:nth-child(2) a.text-decoration-none.text-dark').textContent();
        console.log(`🎯 Testing delete on profile: ${profileName}`);
        
        // Click the dropdown button for the last profile
        const dropdownBtn = lastRow.locator('.dropdown-toggle');
        await dropdownBtn.click();
        console.log('🔽 Opened dropdown menu');
        
        // Wait for dropdown to be visible
        await page.waitForSelector('.dropdown-menu.show');
        
        // Monitor scroll position before clicking delete
        const beforeDeleteScroll = await page.evaluate(() => window.scrollY);
        console.log(`📐 Scroll position before delete click: ${beforeDeleteScroll}`);
        
        // Track network requests to see if delete actually gets called
        let deleteRequestMade = false;
        page.on('request', request => {
            if (request.method() === 'DELETE' && request.url().includes('/profiles/')) {
                deleteRequestMade = true;
                console.log(`🌐 DELETE request intercepted: ${request.url()}`);
            }
        });
        
        // Click the delete link in the currently open dropdown
        const deleteLink = page.locator('.dropdown-menu.show .dropdown-item.text-danger').filter({ hasText: 'Delete' });
        
        // Click delete and immediately check scroll position
        await Promise.all([
            deleteLink.click(),
            // Wait a bit to see if scroll position changes
            page.waitForTimeout(100)
        ]);
        
        const afterDeleteScroll = await page.evaluate(() => window.scrollY);
        console.log(`📐 Scroll position after delete click: ${afterDeleteScroll}`);
        
        // Check if page jumped to top
        if (beforeDeleteScroll > 100 && afterDeleteScroll < 50) {
            console.log('⚠️  ISSUE CONFIRMED: Page jumped to top after clicking delete!');
            console.log(`   Before: ${beforeDeleteScroll}px, After: ${afterDeleteScroll}px`);
        } else {
            console.log('✅ No significant page jump detected');
        }
        
        // Wait for potential confirmation dialog
        await page.waitForTimeout(500);
        
        // Check if confirmation dialog appeared
        const confirmDialog = await page.evaluate(() => {
            // Check if browser confirm dialog is showing (this is tricky to detect)
            return document.hasFocus();
        });
        
        console.log(`💬 Page still has focus (no confirm dialog blocking): ${confirmDialog}`);
        
        // Wait a bit more to see if any network request was made
        await page.waitForTimeout(1000);
        console.log(`🌐 DELETE request was made: ${deleteRequestMade}`);
        
        // Take a screenshot for debugging
        await page.screenshot({ path: 'debug-delete-jump.png' });
        console.log('📸 Screenshot saved as debug-delete-jump.png');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
        console.log('🏁 Test completed');
    }
}

debugDeleteJump();
