
    // Tab switching functionality
    function switchTab(tabId) {
        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.style.display = 'none';
        });
        
        // Show selected tab content
        document.getElementById(tabId).style.display = 'block';
        
        // Update active menu item
        document.querySelectorAll('.menu-list a').forEach(item => {
            item.classList.remove('is-active');
        });
        
        // Find and activate current menu item
        document.querySelectorAll(`.menu-list a[href="#${tabId}"]`).forEach(item => {
            item.classList.add('is-active');
        });
    }
    
    // Helper function to add role tags
    function addRoleTag(container, roleName, colorClass) {
        const tagGroup = document.createElement('div');
        tagGroup.className = 'tags has-addons';
        
        const labelTag = document.createElement('span');
        labelTag.className = 'tag is-dark';
        labelTag.textContent = 'Роль';
        
        const roleTag = document.createElement('span');
        roleTag.className = `tag ${colorClass}`;
        roleTag.textContent = roleName;
        
        tagGroup.appendChild(labelTag);
        tagGroup.appendChild(roleTag);
        container.appendChild(tagGroup);
    }
    
    // Format date for display
    function formatDate(dateString) {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('uk-UA');
    }
    
    // Add donation records to table
    function populateDonationsTable(donations) {
        const tableBody = document.getElementById('donationsTableBody');
        tableBody.innerHTML = '';
        
        if (!donations || donations.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="6" class="has-text-centered">Немає записів про донації</td>';
            tableBody.appendChild(row);
            return;
        }
        
        donations.forEach(donation => {
            const row = document.createElement('tr');
            
            const statusClass = {
                'SCHEDULED': 'is-warning',
                'COMPLETED': 'is-success',
                'CANCELED': 'is-danger'
            }[donation.status] || '';
            
            row.innerHTML = `
                <td>${donation.id}</td>
                <td>${formatDate(donation.donation_date)}</td>
                <td>${donation.hospital ? donation.hospital.name : '-'}</td>
                <td>${donation.blood_amount_ml} мл</td>
                <td><span class="tag ${statusClass}">${donation.status}</span></td>
                <td>
                    <a href="/pages/donations/${donation.id}" class="button is-small is-info">
                        <span class="icon"><i class="fas fa-eye"></i></span>
                    </a>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }
    
    // Add blood requests to table
    function populateRequestsTable(requests) {
        const tableBody = document.getElementById('requestsTableBody');
        tableBody.innerHTML = '';
        
        if (!requests || requests.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="7" class="has-text-centered">Немає записів про запити на кров</td>';
            tableBody.appendChild(row);
            return;
        }
        
        requests.forEach(request => {
            const row = document.createElement('tr');
            
            const statusClass = {
                'ACTIVE': 'is-warning',
                'FULFILLED': 'is-success',
                'CANCELED': 'is-danger',
                'EXPIRED': 'is-light'
            }[request.status] || '';
            
            row.innerHTML = `
                <td>${request.id}</td>
                <td>${formatDate(request.created_at)}</td>
                <td>${request.blood_type}</td>
                <td>${request.blood_amount_ml} мл</td>
                <td><span class="tag ${statusClass}">${request.status}</span></td>
                <td>${request.donations ? request.donations.length : 0}</td>
                <td>
                    <a href="/pages/blood-requests/${request.id}" class="button is-small is-info">
                        <span class="icon"><i class="fas fa-eye"></i></span>
                    </a>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }
    
    // Load user data when page loads
    document.addEventListener('DOMContentLoaded', async function() {
        try {
            const response = await fetch('/auth/me/');
            
            if (!response.ok) {
                // If not authorized, redirect to login
                if (response.status === 401) {
                    console.error("Authorization failed, redirecting to login");
                    window.location.href = '/pages/login';
                    return;
                }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const userData = await response.json();
            console.log("User data received:", userData);
            
            // Fill in basic user data
            document.getElementById('fullName').value = `${userData.first_name} ${userData.last_name}`;
            document.getElementById('email').value = userData.email;
            document.getElementById('phone').value = userData.phone_number || '-';
            document.getElementById('sidebarUserName').textContent = `${userData.first_name} ${userData.last_name}`;
            
            // Fill in edit form data
            document.getElementById('first_name').value = userData.first_name;
            document.getElementById('last_name').value = userData.last_name;
            document.getElementById('email_edit').value = userData.email;
            document.getElementById('phone_edit').value = userData.phone_number || '';
            
            // Format created_at date if available
            if (userData.created_at) {
                document.getElementById('createdAt').value = formatDate(userData.created_at);
            } else {
                document.getElementById('createdAt').value = '-';
            }
            
            // Display user roles
            const rolesContainer = document.getElementById('userRolesArea');
            const sidebarRolesContainer = document.getElementById('sidebarRoleArea');
            rolesContainer.innerHTML = ''; // Clear existing content
            sidebarRolesContainer.innerHTML = ''; // Clear existing content
            
            // Create role tags based on boolean flags in the User model
            if (userData.is_user) {
                addRoleTag(rolesContainer, 'Користувач', 'is-info');
                addRoleTag(sidebarRolesContainer, 'Користувач', 'is-info');
            }
             
            // Donor role
            if (userData.is_donor) {
                addRoleTag(rolesContainer, 'Донор', 'is-danger');
                addRoleTag(sidebarRolesContainer, 'Донор', 'is-danger');
                
                // Show donor section data
                if (userData.donor_profile && userData.donor_profile.length > 0) {
                    const donorData = userData.donor_profile[0]; // Get first donor profile
                    
                    document.getElementById('bloodType').textContent = donorData.blood_type || '-';
                    document.getElementById('birthDate').value = formatDate(donorData.date_of_birth);
                    document.getElementById('gender').value = donorData.gender || '-';
                    document.getElementById('weight').value = donorData.weight ? `${donorData.weight} кг` : '-';
                    document.getElementById('height').value = donorData.height ? `${donorData.height} см` : '-';
                    document.getElementById('healthNotes').value = donorData.health_notes || 'Немає записів';
                    
                    document.getElementById('donorStatus').textContent = donorData.is_eligible ? 'Активний' : 'Не активний';
                    document.getElementById('donorStatus').parentElement.className = 
                        `title ${donorData.is_eligible ? 'has-text-success' : 'has-text-danger'}`;
                    
                    // Handle donations data if available
                    if (donorData.donations && Array.isArray(donorData.donations)) {
                        document.getElementById('totalDonations').textContent = donorData.donations.length;
                        
                        // Populate donations table
                        populateDonationsTable(donorData.donations);
                    }
                }
            }
            
            // Hospital staff role
            if (userData.is_hospital_staff) {
                addRoleTag(rolesContainer, 'Працівник лікарні', 'is-success');
                addRoleTag(sidebarRolesContainer, 'Працівник лікарні', 'is-success');
                
                // Show hospital staff section data
                if (userData.hospital_staff_profile && userData.hospital_staff_profile.length > 0) {
                    const staffData = userData.hospital_staff_profile[0]; // Get first staff profile
                    
                    if (staffData.hospital && staffData.hospital.name) {
                        document.getElementById('hospitalName').value = staffData.hospital.name;
                    }
                    
                    document.getElementById('position').value = staffData.role || '-';
                    document.getElementById('department').value = staffData.department || '-';
                    
                    // If available, show hospital statistics
                    // This would typically come from a separate API endpoint
                    fetchHospitalStats(staffData.hospital_id);
                    
                    // Populate blood requests table
                    fetchBloodRequests(staffData.hospital_id);
                }
            }
            
            // Admin role
            if (userData.is_admin) {
                addRoleTag(rolesContainer, 'Адміністратор', 'is-warning');
                addRoleTag(sidebarRolesContainer, 'Адміністратор', 'is-warning');
                
                // Fetch admin stats
                fetchAdminStats();
            }
            
            // Super admin role
            if (userData.is_super_admin) {
                addRoleTag(rolesContainer, 'Супер Адмін', 'is-primary');
                addRoleTag(sidebarRolesContainer, 'Супер Адмін', 'is-primary');
            }
            
        } catch (error) {
            console.error('Error fetching user data:', error);
            // Don't show alert immediately, wait a moment to see if it's just a timing issue
            setTimeout(() => {
                console.log("Checking if profile loaded correctly...");
                const nameElement = document.getElementById('fullName');
                // If still not loaded after delay, show the error
                if (!nameElement || !nameElement.value) {
                    alert('Не вдалося завантажити дані профілю. Будь ласка, спробуйте пізніше.');
                }
            }, 1000);
        }
    });
    
    // Fetch hospital statistics
    async function fetchHospitalStats(hospitalId) {
        try {
            const response = await fetch(`/api/hospitals/${hospitalId}/stats`);
            
            if (!response.ok) {
                console.error(`Failed to fetch hospital stats: ${response.status}`);
                return;
            }
            
            const stats = await response.json();
            
            // Update hospital stats in the UI
            document.getElementById('activeRequests').textContent = stats.active_requests || 0;
            document.getElementById('scheduledDonations').textContent = stats.scheduled_donations || 0;
            document.getElementById('completedDonations').textContent = stats.completed_donations || 0;
            
        } catch (error) {
            console.error('Error fetching hospital stats:', error);
        }
    }
    
    // Fetch blood requests for a hospital
    async function fetchBloodRequests(hospitalId) {
        try {
            const response = await fetch(`/api/hospitals/${hospitalId}/blood-requests`);
            
            if (!response.ok) {
                console.error(`Failed to fetch blood requests: ${response.status}`);
                return;
            }
            
            const requests = await response.json();
            
            // Populate the requests table
            populateRequestsTable(requests);
            
        } catch (error) {
            console.error('Error fetching blood requests:', error);
        }
    }
    
    // Fetch admin statistics
    async function fetchAdminStats() {
        try {
            const response = await fetch('/api/admin/stats');
            
            if (!response.ok) {
                console.error(`Failed to fetch admin stats: ${response.status}`);
                return;
            }
            
            const stats = await response.json();
            
            // Update admin stats in the UI
            document.getElementById('totalUsers').textContent = stats.user_count || 0;
            document.getElementById('totalHospitals').textContent = stats.hospital_count || 0;
            document.getElementById('totalRequests').textContent = stats.blood_request_count || 0;
            
        } catch (error) {
            console.error('Error fetching admin stats:', error);
        }
    }
    
    // Profile form submission
    document.getElementById('profile-form').addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const formData = new FormData(this);
        const data = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch('/auth/profile/update', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.detail || 'Помилка при оновленні профілю');
                return;
            }
            
            alert('Профіль успішно оновлено!');
            window.location.reload();
            
        } catch (error) {
            console.error('Error updating profile:', error);
            alert('Помилка при оновленні профілю. Спробуйте пізніше.');
        }
    });
    
    // Inside password form event listener, update it like this:
    document.getElementById('password-form').addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // Get form data
        const formData = new FormData(this);
        const data = Object.fromEntries(formData.entries());
        
        // Validate passwords match
        if (data.new_password !== data.confirm_password) {
            alert('Нові паролі не співпадають!');
            return;
        }
        
        try {
            const response = await fetch('/auth/profile/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_password: data.current_password,
                    new_password: data.new_password,
                    confirm_password: data.confirm_password 
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.detail || 'Помилка при зміні паролю');
                return;
            }
            
            alert('Пароль успішно змінено!');
            this.reset();
            switchTab('profile-overview');
            
        } catch (error) {
            console.error('Error changing password:', error);
            alert('Помилка при зміні паролю. Спробуйте пізніше.');
        }
    });
    
    // Download donation history
    document.getElementById('downloadDonationHistory').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/donors/me/donations/export');
            
            if (!response.ok) {
                alert('Помилка при завантаженні історії донацій');
                return;
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'donation_history.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Error downloading donation history:', error);
            alert('Помилка при завантаженні історії донацій. Спробуйте пізніше.');
        }
    });

// Profile form submission with improved error handling and element checking
function setupProfileUpdateHandler() {
    const profileForm = document.getElementById('profile-form');
    
    if (!profileForm) {
        console.error('Profile form not found in the DOM');
        return;
    }
    
    profileForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // Show loading state
        const submitButton = this.querySelector('button[type="submit"]');
        const originalButtonText = submitButton ? submitButton.innerHTML : '';
        
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="icon is-loading"><i class="fas fa-spinner fa-spin"></i></span><span>Оновлення...</span>';
        }
        
        try {
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            console.log('Sending profile update:', data);
            
            const response = await fetch('/auth/profile/update', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            // Reset button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            }
            
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.detail || 'Помилка при оновленні профілю';
                alert(errorMessage);
                console.error('Profile update error:', errorData);
                return;
            }
            
            const result = await response.json();
            console.log('Profile updated successfully:', result);
            
            // Update displayed values without reloading the page
            updateDisplayedUserInfo(result);
            
            alert('Профіль успішно оновлено!');
            
        } catch (error) {
            // Reset button state on error
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            }
            
            console.error('Error updating profile:', error);
            alert('Помилка при оновленні профілю. Спробуйте пізніше.');
        }
    });
}

// Function to update displayed user information after a successful profile update
function updateDisplayedUserInfo(userData) {
    // Safely update an element if it exists
    function safelyUpdateElement(id, value, property = 'value') {
        const element = document.getElementById(id);
        if (element) {
            if (property === 'value') {
                element.value = value;
            } else if (property === 'textContent') {
                element.textContent = value;
            }
        }
    }
    
    // Update basic profile information displayed on the page
    safelyUpdateElement('fullName', `${userData.first_name} ${userData.last_name}`);
    safelyUpdateElement('email', userData.email);
    safelyUpdateElement('phone', userData.phone_number || '-');
    safelyUpdateElement('sidebarUserName', `${userData.first_name} ${userData.last_name}`, 'textContent');
}

// Function to switch between tabs
function switchTab(tabId) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Show the selected tab
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Update active state in the menu
    document.querySelectorAll('.menu-list a').forEach(link => {
        link.classList.remove('is-active');
    });
    
    // Find the link with the corresponding href and mark it as active
    const activeLink = document.querySelector(`.menu-list a[href="#${tabId}"]`);
    if (activeLink) {
        activeLink.classList.add('is-active');
    }
}

// Initialize profile page functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up profile update handler
    setupProfileUpdateHandler();
    
    // Set up password change handler
    setupPasswordChangeHandler();
    
    // Load user data
    loadUserData();
    
    // Make the switchTab function globally available
    window.switchTab = switchTab;
});

// Function to set up password change handler (implementation not shown here)
function setupPasswordChangeHandler() {
    const passwordForm = document.getElementById('password-form');
    if (!passwordForm) {
        console.error('Password form not found in the DOM');
        return;
    }
    
    // Your existing password change form event handler...
}

// Function to load user data
async function loadUserData() {
    try {
        const response = await fetch('/auth/me/');
        
        if (!response.ok) {
            if (response.status === 401) {
                // Not authenticated
                window.location.href = '/pages/login';
                return;
            }
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const userData = await response.json();
        console.log("User data received:", userData);
        
        // Fill profile form with user data
        fillProfileForm(userData);
        
        // Your existing code to display roles and other sections...
        
    } catch (error) {
        console.error('Error fetching user data:', error);
        // Don't show alert immediately, wait a moment to see if it's just a timing issue
        setTimeout(() => {
            console.log("Checking if profile loaded correctly...");
            const nameElement = document.getElementById('fullName');
            // If still not loaded after delay, show the error
            if (!nameElement || !nameElement.value) {
                alert('Не вдалося завантажити дані профілю. Будь ласка, спробуйте пізніше.');
            }
        }, 1000);
    }
}

// Function to fill profile form with user data
function fillProfileForm(userData) {
    // Safely set form values
    function safelySetFormValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value || '';
        }
    }
    
    // Fill user info section
    safelySetFormValue('fullName', `${userData.first_name} ${userData.last_name}`);
    safelySetFormValue('email', userData.email);
    safelySetFormValue('phone', userData.phone_number || '-');
    
    // Fill sidebar
    const sidebarUserName = document.getElementById('sidebarUserName');
    if (sidebarUserName) {
        sidebarUserName.textContent = `${userData.first_name} ${userData.last_name}`;
    }
    
    // Fill edit form
    safelySetFormValue('first_name', userData.first_name);
    safelySetFormValue('last_name', userData.last_name);
    safelySetFormValue('email_edit', userData.email);
    safelySetFormValue('phone_edit', userData.phone_number || '');
    
    // Format created_at date if available
    if (userData.created_at) {
        safelySetFormValue('createdAt', formatDate(userData.created_at));
    } else {
        safelySetFormValue('createdAt', '-');
    }
}

// Helper function to format dates
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('uk-UA');
}

