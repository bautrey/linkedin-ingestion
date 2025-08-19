const { chromium } = require('playwright');

async function testNewModal() {
    console.log('🧪 Testing new Bootstrap confirmation modal...');
    
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
        console.log(`🎯 Testing delete on profile: ${profileName.trim()}`);
        
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
        await deleteLink.click();
        
        // Wait for the modal to appear
        await page.waitForSelector('#deleteConfirmModal.show', { timeout: 3000 });
        console.log('🎭 Bootstrap modal appeared!');
        
        // Check scroll position after modal appears
        const afterDeleteScroll = await page.evaluate(() => window.scrollY);
        console.log(`📐 Scroll position after modal appears: ${afterDeleteScroll}`);
        
        // Check if page scroll remained stable
        const scrollDifference = Math.abs(beforeDeleteScroll - afterDeleteScroll);
        if (scrollDifference > 50) {
            console.log(`⚠️  Page scroll changed: ${beforeDeleteScroll}px → ${afterDeleteScroll}px`);
        } else {
            console.log('✅ Page scroll position remained stable');
        }
        
        // Check modal content
        const modalTitle = await page.locator('#deleteConfirmModal .modal-title').textContent();
        console.log(`📋 Modal title: "${modalTitle}"`);
        
        const modalProfileName = await page.locator('#deleteProfileName').textContent();
        console.log(`👤 Profile name in modal: "${modalProfileName}"`);
        
        // Check if the profile name matches
        const nameMatches = profileName.trim().includes(modalProfileName.trim()) || 
                          modalProfileName.trim().includes(profileName.trim());
        console.log(`🔍 Profile names match: ${nameMatches}`);
        
        // Check modal styling
        const modalHeader = page.locator('#deleteConfirmModal .modal-header');
        const headerClass = await modalHeader.getAttribute('class');
        const hasDangerStyle = headerClass.includes('bg-danger');
        console.log(`🎨 Modal has danger styling: ${hasDangerStyle}`);
        
        // Check for Bootstrap icons
        const trashIcon = await page.locator('#deleteConfirmModal .bi-trash').count();
        const warningIcon = await page.locator('#deleteConfirmModal .bi-exclamation-triangle').count();
        console.log(`🎯 Icons present - Trash: ${trashIcon}, Warning: ${warningIcon}`);
        
        // Test Cancel button
        console.log('🔘 Testing Cancel button...');
        const cancelBtn = page.locator('#deleteConfirmModal .btn-secondary');
        await cancelBtn.click();
        
        // Wait for modal to close (check for hidden state)
        await page.waitForFunction(() => {
            const modal = document.querySelector('#deleteConfirmModal');
            return !modal.classList.contains('show');
        }, { timeout: 5000 });
        console.log('❌ Modal closed via Cancel button');
        
        // Verify no DELETE request was made
        await page.waitForTimeout(500);
        console.log(`🌐 DELETE request was made: ${deleteRequestMade} (should be false)`);
        
        // Take a screenshot for visual verification
        await page.screenshot({ path: 'test-new-modal.png' });
        console.log('📸 Screenshot saved as test-new-modal.png');
        
        // Summary
        console.log('\n📊 Test Results:');
        console.log(`   ✓ Page scroll stable: ${scrollDifference <= 50 ? 'PASS' : 'FAIL'}`);
        console.log(`   ✓ Modal appeared: PASS`);
        console.log(`   ✓ Modal styling: ${hasDangerStyle ? 'PASS' : 'FAIL'}`);
        console.log(`   ✓ Profile name shown: ${modalProfileName.length > 0 ? 'PASS' : 'FAIL'}`);
        console.log(`   ✓ Icons present: ${(trashIcon > 0 && warningIcon > 0) ? 'PASS' : 'FAIL'}`);
        console.log(`   ✓ Cancel works: PASS`);
        console.log(`   ✓ No DELETE request: ${!deleteRequestMade ? 'PASS' : 'FAIL'}`);
        
        const allTestsPassed = scrollDifference <= 50 && 
                              hasDangerStyle && 
                              modalProfileName.length > 0 && 
                              trashIcon > 0 && 
                              warningIcon > 0 && 
                              !deleteRequestMade;
                              
        console.log(`\n🎯 Overall: ${allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
        console.log('🏁 Test completed');
    }
}

testNewModal();
