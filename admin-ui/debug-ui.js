const { chromium } = require('playwright');

async function debugUI() {
    console.log('🚀 Starting Playwright UI debugging...');
    
    // Launch browser with visible UI
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000 // Slow down actions so we can see them
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    // Enable console logging from the browser
    page.on('console', msg => console.log(`🌐 Browser: ${msg.text()}`));
    page.on('pageerror', error => console.log(`❌ Page Error: ${error.message}`));
    
    try {
        console.log('📄 Navigating to profiles page...');
        await page.goto('http://localhost:3003/profiles');
        
        // Wait for page to load
        await page.waitForSelector('#profilesTable', { timeout: 10000 });
        console.log('✅ Profiles table loaded');
        
        // Check if there are any JavaScript errors
        console.log('🔍 Checking for JavaScript errors...');
        
        // Take a screenshot to see current state
        await page.screenshot({ path: 'debug-profiles-loaded.png', fullPage: true });
        console.log('📸 Screenshot saved: debug-profiles-loaded.png');
        
        // Check if Bootstrap is loaded
        const bootstrapLoaded = await page.evaluate(() => {
            return typeof bootstrap !== 'undefined';
        });
        console.log(`🅱️ Bootstrap loaded: ${bootstrapLoaded}`);
        
        // Check if dropdowns exist
        const dropdownButtons = await page.$$('.dropdown-toggle');
        console.log(`📋 Found ${dropdownButtons.length} dropdown buttons`);
        
        if (dropdownButtons.length > 0) {
            console.log('🖱️ Attempting to click first dropdown...');
            
            // Try to click the first dropdown
            await dropdownButtons[0].click();
            await page.waitForTimeout(2000); // Wait to see if dropdown opens
            
            // Check if dropdown menu is visible
            const dropdownMenu = await page.$('.dropdown-menu.show');
            if (dropdownMenu) {
                console.log('✅ Dropdown opened successfully!');
            } else {
                console.log('❌ Dropdown did not open');
                
                // Check for any Bootstrap dropdown instances
                const dropdownInstances = await page.evaluate(() => {
                    const buttons = document.querySelectorAll('.dropdown-toggle');
                    return Array.from(buttons).map(btn => {
                        const instance = bootstrap.Dropdown.getInstance(btn);
                        return {
                            hasInstance: !!instance,
                            buttonText: btn.textContent.trim(),
                            buttonId: btn.id,
                            buttonClasses: btn.className
                        };
                    });
                });
                
                console.log('🔍 Dropdown instances:', JSON.stringify(dropdownInstances, null, 2));
            }
            
            await page.screenshot({ path: 'debug-after-click.png', fullPage: true });
            console.log('📸 Screenshot after click: debug-after-click.png');
        }
        
        // Check bulk actions functionality
        console.log('🔍 Testing bulk actions...');
        
        // Try to check a checkbox
        const firstCheckbox = await page.$('.profile-checkbox');
        if (firstCheckbox) {
            console.log('☑️ Clicking first profile checkbox...');
            await firstCheckbox.click();
            await page.waitForTimeout(1000);
            
            // Check if bulk actions button is enabled
            const bulkActionBtn = await page.$('#bulkActionsBtn');
            if (bulkActionBtn) {
                const isEnabled = await bulkActionBtn.evaluate(btn => !btn.disabled);
                console.log(`🎯 Bulk actions button enabled: ${isEnabled}`);
                
                if (isEnabled) {
                    console.log('🖱️ Clicking bulk actions button...');
                    await bulkActionBtn.click();
                    await page.waitForTimeout(2000);
                    
                    // Check if modal opens
                    const modal = await page.$('.modal.show');
                    if (modal) {
                        console.log('✅ Bulk actions modal opened!');
                    } else {
                        console.log('❌ Bulk actions modal did not open');
                    }
                }
            }
        }
        
        await page.screenshot({ path: 'debug-bulk-actions.png', fullPage: true });
        console.log('📸 Screenshot after bulk actions test: debug-bulk-actions.png');
        
        // Get any console errors from the page
        const consoleErrors = await page.evaluate(() => {
            return window.console.error ? 'No errors captured' : 'Console errors may exist';
        });
        
        console.log('📋 Browser console status:', consoleErrors);
        
    } catch (error) {
        console.error('❌ Debug failed:', error);
        await page.screenshot({ path: 'debug-error.png', fullPage: true });
    }
    
    console.log('⏳ Keeping browser open for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);
    
    await browser.close();
    console.log('✅ Debugging complete');
}

debugUI().catch(console.error);
