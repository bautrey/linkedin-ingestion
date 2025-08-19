const { chromium } = require('playwright');

async function testDeleteFix() {
    console.log('🧪 Testing delete link fix...');
    
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
        
        // Scroll down to make the behavior more obvious
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
        
        // Test the last profile (John Doe should be at the bottom)
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
        
        // Set up dialog handler for confirmation
        let confirmDialogAppeared = false;
        let confirmDialogMessage = '';
        page.on('dialog', async dialog => {
            confirmDialogAppeared = true;
            confirmDialogMessage = dialog.message();
            console.log(`💬 Confirmation dialog appeared: "${confirmDialogMessage}"`);
            // Cancel the deletion for this test
            await dialog.dismiss();
        });
        
        // Click the delete link in the currently open dropdown
        const deleteLink = page.locator('.dropdown-menu.show .dropdown-item.text-danger').filter({ hasText: 'Delete' });
        await deleteLink.click();
        
        // Wait a moment for the dialog to appear
        await page.waitForTimeout(500);
        
        const afterDeleteScroll = await page.evaluate(() => window.scrollY);
        console.log(`📐 Scroll position after delete click: ${afterDeleteScroll}`);
        
        // Check if page jumped to top
        const scrollDifference = Math.abs(beforeDeleteScroll - afterDeleteScroll);
        if (scrollDifference > 50) {
            console.log(`⚠️  Page scroll changed significantly: ${beforeDeleteScroll}px → ${afterDeleteScroll}px`);
        } else {
            console.log('✅ Page scroll position remained stable');
        }
        
        // Check if confirmation dialog appeared
        if (confirmDialogAppeared) {
            console.log('✅ Confirmation dialog appeared as expected');
            console.log(`   Message: "${confirmDialogMessage}"`);
        } else {
            console.log('❌ Confirmation dialog did not appear');
        }
        
        // Wait to see if any network request was made (there shouldn't be since we dismissed)
        await page.waitForTimeout(500);
        console.log(`🌐 DELETE request was made: ${deleteRequestMade}`);
        
        // Take a screenshot for debugging
        await page.screenshot({ path: 'test-delete-fix.png' });
        console.log('📸 Screenshot saved as test-delete-fix.png');
        
        // Summary
        console.log('\n📊 Test Results:');
        console.log(`   ✓ Page scroll stable: ${scrollDifference <= 50 ? 'PASS' : 'FAIL'}`);
        console.log(`   ✓ Confirmation dialog: ${confirmDialogAppeared ? 'PASS' : 'FAIL'}`);
        console.log(`   ✓ No DELETE request: ${!deleteRequestMade ? 'PASS' : 'FAIL'} (expected since we cancelled)`);
        
        const allTestsPassed = scrollDifference <= 50 && confirmDialogAppeared && !deleteRequestMade;
        console.log(`\n🎯 Overall: ${allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
        console.log('🏁 Test completed');
    }
}

testDeleteFix();
