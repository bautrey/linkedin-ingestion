// Profiles List Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize page functionality
    initializeTableSorting();
    initializeBulkSelection();
    initializeFilters();
    
    // Update active sidebar navigation
    updateActiveNavigation('profiles');
});

// Table Sorting Functionality
function initializeTableSorting() {
    const sortableHeaders = document.querySelectorAll('.sortable');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortBy = this.getAttribute('data-sort');
            const currentUrl = new URL(window.location);
            const currentSort = currentUrl.searchParams.get('sort_by');
            const currentOrder = currentUrl.searchParams.get('sort_order');
            
            let newOrder = 'asc';
            if (currentSort === sortBy && currentOrder === 'asc') {
                newOrder = 'desc';
            }
            
            // Update URL parameters
            currentUrl.searchParams.set('sort_by', sortBy);
            currentUrl.searchParams.set('sort_order', newOrder);
            
            // Navigate to sorted page
            window.location.href = currentUrl.toString();
        });
        
        // Update sort icons based on current sort
        updateSortIcons();
    });
}

function updateSortIcons() {
    const urlParams = new URLSearchParams(window.location.search);
    const sortBy = urlParams.get('sort_by');
    const sortOrder = urlParams.get('sort_order');
    
    if (sortBy) {
        const activeHeader = document.querySelector(`[data-sort="${sortBy}"]`);
        if (activeHeader) {
            const icon = activeHeader.querySelector('.sort-icon');
            if (sortOrder === 'desc') {
                icon.className = 'bi bi-chevron-down sort-icon';
            } else {
                icon.className = 'bi bi-chevron-up sort-icon';
            }
            activeHeader.classList.add('table-active');
        }
    }
}

// Bulk Selection Functionality
function initializeBulkSelection() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const profileCheckboxes = document.querySelectorAll('.profile-checkbox');
    const bulkActionsBtn = document.getElementById('bulkActionsBtn');
    const selectedCountSpan = document.getElementById('selectedCount');
    const bulkSelectedCountSpan = document.getElementById('bulkSelectedCount');
    
    // Select All functionality
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            profileCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateBulkActionButton();
        });
    }
    
    // Individual checkbox functionality
    profileCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkActionButton();
            updateSelectAllCheckbox();
        });
    });
    
    function updateBulkActionButton() {
        const selectedCheckboxes = document.querySelectorAll('.profile-checkbox:checked');
        const count = selectedCheckboxes.length;
        
        if (selectedCountSpan) selectedCountSpan.textContent = count;
        if (bulkSelectedCountSpan) bulkSelectedCountSpan.textContent = count;
        
        if (bulkActionsBtn) {
            if (count > 0) {
                bulkActionsBtn.disabled = false;
                bulkActionsBtn.classList.remove('btn-outline-primary');
                bulkActionsBtn.classList.add('btn-primary');
            } else {
                bulkActionsBtn.disabled = true;
                bulkActionsBtn.classList.remove('btn-primary');
                bulkActionsBtn.classList.add('btn-outline-primary');
            }
        }
    }
    
    function updateSelectAllCheckbox() {
        if (!selectAllCheckbox) return;
        
        const totalCheckboxes = profileCheckboxes.length;
        const checkedCheckboxes = document.querySelectorAll('.profile-checkbox:checked').length;
        
        if (checkedCheckboxes === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCheckboxes === totalCheckboxes) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }
}

// Filter Management
function initializeFilters() {
    // Auto-submit form when dropdowns change
    const filterSelects = document.querySelectorAll('#filterForm select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            document.getElementById('filterForm').submit();
        });
    });
    
    // Search with debounce
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Auto-submit after 500ms of no typing
                if (this.value.length >= 3 || this.value.length === 0) {
                    document.getElementById('filterForm').submit();
                }
            }, 500);
        });
    }
}

function clearFilters() {
    const form = document.getElementById('filterForm');
    if (form) {
        form.reset();
        window.location.href = '/profiles';
    }
}

function resetFilters() {
    clearFilters();
}

// Profile Management Actions
function scoreProfile(profileId) {
    // Navigate to scoring interface for this profile
    window.location.href = `/scoring?profile_id=${profileId}`;
}

function deleteProfile(profileId, profileName) {
    if (confirm(`Are you sure you want to delete ${profileName}?\n\nThis action cannot be undone.`)) {
        showLoadingOverlay();
        
        fetch(`/profiles/${profileId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoadingOverlay();
            if (data.success) {
                showNotification('Profile deleted successfully', 'success');
                // Remove the row from the table
                const row = document.querySelector(`tr[data-profile-id="${profileId}"]`);
                if (row) {
                    row.remove();
                }
                // Update counts
                updateProfileCounts();
            } else {
                showNotification('Failed to delete profile: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            hideLoadingOverlay();
            console.error('Error deleting profile:', error);
            showNotification('An error occurred while deleting the profile', 'danger');
        });
    }
}

// Bulk Actions
function bulkScore() {
    const selectedIds = getSelectedProfileIds();
    if (selectedIds.length === 0) {
        showNotification('Please select profiles to score', 'warning');
        return;
    }
    
    // Navigate to bulk scoring interface
    const idsParam = selectedIds.join(',');
    window.location.href = `/scoring?profile_ids=${idsParam}`;
}

function bulkExport() {
    const selectedIds = getSelectedProfileIds();
    if (selectedIds.length === 0) {
        showNotification('Please select profiles to export', 'warning');
        return;
    }
    
    showLoadingOverlay();
    
    const idsParam = selectedIds.join(',');
    window.open(`/api/profiles/export?profile_ids=${idsParam}`, '_blank');
    
    hideLoadingOverlay();
    showNotification(`Exporting ${selectedIds.length} profiles...`, 'info');
}

function bulkDelete() {
    const selectedIds = getSelectedProfileIds();
    if (selectedIds.length === 0) {
        showNotification('Please select profiles to delete', 'warning');
        return;
    }
    
    if (confirm(`Are you sure you want to delete ${selectedIds.length} selected profiles?\n\nThis action cannot be undone.`)) {
        showLoadingOverlay();
        
        const deletePromises = selectedIds.map(id => {
            return fetch(`/profiles/${id}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
        });
        
        Promise.all(deletePromises)
            .then(responses => Promise.all(responses.map(r => r.json())))
            .then(results => {
                hideLoadingOverlay();
                const successCount = results.filter(r => r.success).length;
                const failureCount = results.length - successCount;
                
                if (successCount > 0) {
                    showNotification(`Successfully deleted ${successCount} profiles`, 'success');
                    // Remove successful deletions from table
                    selectedIds.forEach(id => {
                        const row = document.querySelector(`tr[data-profile-id="${id}"]`);
                        if (row) row.remove();
                    });
                    updateProfileCounts();
                }
                
                if (failureCount > 0) {
                    showNotification(`Failed to delete ${failureCount} profiles`, 'warning');
                }
                
                // Close modal and reset selection
                const modal = bootstrap.Modal.getInstance(document.getElementById('bulkActionsModal'));
                if (modal) modal.hide();
                resetBulkSelection();
            })
            .catch(error => {
                hideLoadingOverlay();
                console.error('Error deleting profiles:', error);
                showNotification('An error occurred during bulk delete', 'danger');
            });
    }
}

// Utility Functions
function getSelectedProfileIds() {
    const selectedCheckboxes = document.querySelectorAll('.profile-checkbox:checked');
    return Array.from(selectedCheckboxes).map(cb => cb.value);
}

function resetBulkSelection() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const profileCheckboxes = document.querySelectorAll('.profile-checkbox');
    
    if (selectAllCheckbox) selectAllCheckbox.checked = false;
    profileCheckboxes.forEach(cb => cb.checked = false);
    
    const bulkActionsBtn = document.getElementById('bulkActionsBtn');
    if (bulkActionsBtn) {
        bulkActionsBtn.disabled = true;
        bulkActionsBtn.classList.remove('btn-primary');
        bulkActionsBtn.classList.add('btn-outline-primary');
    }
    
    const selectedCountSpan = document.getElementById('selectedCount');
    if (selectedCountSpan) selectedCountSpan.textContent = '0';
}

function updateProfileCounts() {
    // Update the header counts
    const remainingRows = document.querySelectorAll('#profilesTable tbody tr[data-profile-id]').length;
    const headerText = document.querySelector('h2').nextElementSibling;
    if (headerText && remainingRows === 0) {
        headerText.textContent = 'No profiles found';
        // Could reload page or show empty state
        setTimeout(() => window.location.reload(), 1000);
    }
}

// Column Resizing (Advanced Feature)
function initializeColumnResizing() {
    // This would implement draggable column resizing
    // For now, we'll rely on CSS min-width and the user's browser
    // Could be enhanced with a library like ResizeObserver
}

// Export to CSV functionality
function exportToCSV() {
    const selectedIds = getSelectedProfileIds();
    if (selectedIds.length === 0) {
        // Export all visible profiles
        const allIds = Array.from(document.querySelectorAll('#profilesTable tbody tr[data-profile-id]'))
            .map(row => row.getAttribute('data-profile-id'));
        
        if (allIds.length === 0) {
            showNotification('No profiles to export', 'warning');
            return;
        }
        
        const idsParam = allIds.join(',');
        window.open(`/api/profiles/export?format=csv&profile_ids=${idsParam}`, '_blank');
    } else {
        bulkExport();
    }
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + A to select all
    if ((e.ctrlKey || e.metaKey) && e.key === 'a' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        const selectAllCheckbox = document.getElementById('selectAll');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = !selectAllCheckbox.checked;
            selectAllCheckbox.dispatchEvent(new Event('change'));
        }
    }
    
    // Delete key for bulk delete (when items are selected)
    if (e.key === 'Delete' && getSelectedProfileIds().length > 0 && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        bulkDelete();
    }
    
    // Escape to clear selection
    if (e.key === 'Escape') {
        resetBulkSelection();
    }
});

// URL Helper Functions (needed for pagination)
function buildPageUrl(page) {
    const url = new URL(window.location);
    url.searchParams.set('page', page);
    return url.toString();
}

// Auto-refresh functionality for real-time updates
let autoRefreshInterval;

function startAutoRefresh(intervalMs = 30000) {
    stopAutoRefresh();
    autoRefreshInterval = setInterval(() => {
        // Only refresh if no modals are open and no selections are made
        const openModals = document.querySelectorAll('.modal.show');
        const selectedProfiles = getSelectedProfileIds();
        
        if (openModals.length === 0 && selectedProfiles.length === 0) {
            // Silent refresh - could be implemented with fetch and DOM updates
            // For now, we'll do a full page refresh
            window.location.reload();
        }
    }, intervalMs);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Start auto-refresh when page loads
// startAutoRefresh(60000); // Refresh every minute - commented out for now
