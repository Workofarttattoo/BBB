/**
 * Main Application Logic
 */

// Global State
const State = {
    user: null,
    businesses: [],
    activeBusinessId: null,
    ws: null,
    currentView: 'dashboard'
};

// --- UI Utilities ---

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    let bgColor = 'bg-blue-500';
    let icon = 'fa-info-circle';
    if (type === 'success') { bgColor = 'bg-green-500'; icon = 'fa-check-circle'; }
    if (type === 'error') { bgColor = 'bg-red-500'; icon = 'fa-exclamation-circle'; }
    if (type === 'warning') { bgColor = 'bg-yellow-500'; icon = 'fa-exclamation-triangle'; }

    toast.className = `toast flex items-center p-4 text-white rounded shadow-lg min-w-[300px] ${bgColor}`;
    toast.innerHTML = `<i class="fa-solid ${icon} mr-3"></i><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function showMainLoader(show) {
    const loader = document.getElementById('main-loader');
    if (show) {
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
    }
}

function setLoadingState(button, isLoading, originalText) {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = `<span class="spinner"></span> Processing...`;
    } else {
        button.disabled = false;
        button.innerHTML = originalText;
    }
}

// --- Navigation and Routing ---

function switchView(viewName) {
    // Update State
    State.currentView = viewName;

    // Hide all views
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));

    // Show target view
    const viewEl = document.getElementById(`view-${viewName}`);
    if (viewEl) viewEl.classList.remove('hidden');

    // Update Nav Links
    document.querySelectorAll('.nav-link').forEach(el => {
        if (el.dataset.view === viewName) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // Update Title
    const titles = {
        'dashboard': 'Dashboard',
        'businesses': 'My Businesses',
        'ai-tools': 'AI Tools',
        'campaigns': 'Campaigns',
        'settings': 'Account Settings'
    };
    document.getElementById('current-view-title').textContent = titles[viewName] || 'Dashboard';

    // Load data specific to view if needed
    if (viewName === 'businesses' && State.businesses.length === 0) {
        loadBusinesses();
    }
}

// --- Data Fetching ---

async function loadUserData() {
    try {
        State.user = await Auth.getMe();

        // Update UI
        const nameParts = (State.user.full_name || State.user.email).split(' ');
        const initials = nameParts.length > 1
            ? nameParts[0][0] + nameParts[1][0]
            : nameParts[0][0];

        document.getElementById('user-avatar').textContent = initials.toUpperCase();
        document.getElementById('user-name').textContent = State.user.full_name || State.user.email;

        // Populate settings
        document.getElementById('set-email').textContent = State.user.email;
        document.getElementById('set-name').textContent = State.user.full_name || 'Not provided';
        document.getElementById('set-tier').textContent = State.user.subscription_tier;
        document.getElementById('set-license').textContent = State.user.license_status;

    } catch (error) {
        showToast("Failed to load user profile", "error");
    }
}

async function loadBusinesses() {
    showMainLoader(true);
    try {
        const response = await Auth.fetchWithAuth('/api/businesses');
        if (response.ok) {
            State.businesses = await response.json();
            renderBusinessList();
            updateBusinessSelector();

            // Auto-select first business if none selected
            if (State.businesses.length > 0 && !State.activeBusinessId) {
                const selector = document.getElementById('business-selector');
                selector.value = State.businesses[0].id;
                handleBusinessSelection(State.businesses[0].id);
            }
        }
    } catch (error) {
        showToast("Failed to load businesses", "error");
    } finally {
        showMainLoader(false);
    }
}

function renderBusinessList() {
    const tbody = document.getElementById('business-list-body');
    if (!tbody) return;

    if (State.businesses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">No businesses found. Create one to get started.</td></tr>`;
        return;
    }

    // Use DOM creation instead of innerHTML to prevent XSS
    tbody.innerHTML = '';
    State.businesses.forEach(b => {
        const tr = document.createElement('tr');

        const tdName = document.createElement('td');
        tdName.className = 'px-6 py-4 whitespace-nowrap';
        const divName = document.createElement('div');
        divName.className = 'text-sm font-medium text-gray-900';
        divName.textContent = b.business_name;
        tdName.appendChild(divName);

        const tdIndustry = document.createElement('td');
        tdIndustry.className = 'px-6 py-4 whitespace-nowrap';
        const divIndustry = document.createElement('div');
        divIndustry.className = 'text-sm text-gray-500';
        divIndustry.textContent = b.industry;
        tdIndustry.appendChild(divIndustry);

        const tdStatus = document.createElement('td');
        tdStatus.className = 'px-6 py-4 whitespace-nowrap';
        const spanStatus = document.createElement('span');
        spanStatus.className = 'px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800';
        spanStatus.textContent = b.status;
        tdStatus.appendChild(spanStatus);

        const tdAction = document.createElement('td');
        tdAction.className = 'px-6 py-4 whitespace-nowrap text-sm font-medium';
        const btnSelect = document.createElement('button');
        btnSelect.className = 'text-primary hover:text-blue-900';
        btnSelect.textContent = 'Select';
        btnSelect.onclick = () => handleBusinessSelection(b.id);
        tdAction.appendChild(btnSelect);

        tr.appendChild(tdName);
        tr.appendChild(tdIndustry);
        tr.appendChild(tdStatus);
        tr.appendChild(tdAction);

        tbody.appendChild(tr);
    });
}

function updateBusinessSelector() {
    const selector = document.getElementById('business-selector');
    if (!selector) return;

    const currentVal = selector.value;

    // Clear existing and use DOM creation to prevent XSS
    selector.innerHTML = '';
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a business...';
    selector.appendChild(defaultOption);

    State.businesses.forEach(b => {
        const option = document.createElement('option');
        option.value = b.id;
        option.textContent = b.business_name;
        selector.appendChild(option);
    });

    if (currentVal && State.businesses.find(b => b.id === currentVal)) {
        selector.value = currentVal;
    } else if (State.activeBusinessId) {
        selector.value = State.activeBusinessId;
    }
}

function handleBusinessSelection(businessId) {
    if (!businessId) return;

    State.activeBusinessId = businessId;
    const selector = document.getElementById('business-selector');
    if (selector) selector.value = businessId;

    showToast(`Switched to business context`, "success");

    // Switch to dashboard if on businesses view
    if (State.currentView === 'businesses') {
        switchView('dashboard');
    }

    // Clear stats
    document.getElementById('stat-customers').textContent = '0';
    document.getElementById('stat-revenue').textContent = '$0';
    document.getElementById('stat-campaigns').textContent = '0';
    document.getElementById('stat-tasks').textContent = '0';
    document.getElementById('activity-feed').innerHTML = '';

    // Reconnect WebSocket
    connectWebSocket(businessId);
}

// --- WebSocket ---

function connectWebSocket(businessId) {
    // Close existing
    if (State.ws) {
        State.ws.close();
    }

    const token = Auth.getToken();
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/${businessId}?token=${token}`;

    State.ws = new WebSocket(wsUrl);

    const statusEl = document.getElementById('ws-status');

    State.ws.onopen = () => {
        statusEl.innerHTML = '<div class="w-2 h-2 rounded-full bg-green-500 mr-2"></div> Connected';
        statusEl.classList.replace('text-gray-500', 'text-green-600');
        statusEl.classList.replace('bg-gray-100', 'bg-green-50');
    };

    State.ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error("WS Parse error", e);
        }
    };

    State.ws.onclose = () => {
        statusEl.innerHTML = '<div class="w-2 h-2 rounded-full bg-red-500 mr-2"></div> Disconnected';
        statusEl.classList.replace('text-green-600', 'text-red-600');
        statusEl.classList.replace('bg-green-50', 'bg-red-50');
    };
}

function handleWebSocketMessage(data) {
    // Update Dashboard Stats if type is metrics
    if (data.type === 'dashboard_update') {
        const payload = data.data || {};

        // These keys depend on what backend sends, mapping generic names
        if (payload.customers !== undefined) document.getElementById('stat-customers').textContent = payload.customers;
        if (payload.revenue !== undefined) document.getElementById('stat-revenue').textContent = `$${payload.revenue}`;
        if (payload.active_campaigns !== undefined) document.getElementById('stat-campaigns').textContent = payload.active_campaigns;
        if (payload.pending_tasks !== undefined) document.getElementById('stat-tasks').textContent = payload.pending_tasks;

        // Add to activity feed if there's a recent activity message
        if (payload.recent_activity) {
            addActivityItem(payload.recent_activity);
        }
    }
    else if (data.type === 'activity') {
        addActivityItem(data.data.message || data.data);
    }
}

function addActivityItem(message) {
    const feed = document.getElementById('activity-feed');
    // Remove empty placeholder
    if (feed.querySelector('.text-center')) {
        feed.innerHTML = '';
    }

    const item = document.createElement('div');
    item.className = 'activity-item bg-white p-3 rounded shadow-sm border border-gray-100 mb-2 flex items-start';

    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

    item.innerHTML = `
        <div class="mt-1 mr-3 text-primary"><i class="fa-solid fa-bolt"></i></div>
        <div>
            <div class="text-sm text-gray-800">${message}</div>
            <div class="text-xs text-gray-400 mt-1">${time}</div>
        </div>
    `;

    feed.prepend(item);

    // Keep only last 20
    if (feed.children.length > 20) {
        feed.removeChild(feed.lastChild);
    }
}


// --- Initialization and Event Listeners ---

document.addEventListener('DOMContentLoaded', () => {

    // 1. Check Authentication
    if (!Auth.isAuthenticated()) {
        document.getElementById('auth-view').classList.remove('hidden');
        document.getElementById('app-view').classList.add('hidden');
    } else {
        document.getElementById('auth-view').classList.add('hidden');
        document.getElementById('app-view').classList.remove('hidden');
        initApp();
    }

    // --- Auth View Listeners ---

    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
        document.getElementById('auth-subtitle').textContent = "Create a new account";
    });

    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('auth-subtitle').textContent = "Sign in to your account";
    });

    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        setLoadingState(btn, true, 'Sign In');

        try {
            const email = document.getElementById('login-email').value;
            const pass = document.getElementById('login-password').value;
            await Auth.login(email, pass);

            // Success, switch view
            document.getElementById('auth-view').classList.add('hidden');
            document.getElementById('app-view').classList.remove('hidden');
            initApp();
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            setLoadingState(btn, false, 'Sign In');
        }
    });

    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        setLoadingState(btn, true, 'Register');

        try {
            const name = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const pass = document.getElementById('reg-password').value;
            await Auth.register(name, email, pass);

            // Success, switch view
            document.getElementById('auth-view').classList.add('hidden');
            document.getElementById('app-view').classList.remove('hidden');
            initApp();
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            setLoadingState(btn, false, 'Register');
        }
    });


    // --- App View Listeners ---

    // Logout
    document.getElementById('logout-btn').addEventListener('click', () => {
        Auth.logout();
    });

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = e.currentTarget.dataset.view;
            switchView(view);
        });
    });

    // Business Selector
    document.getElementById('business-selector').addEventListener('change', (e) => {
        handleBusinessSelection(e.target.value);
    });

    // Create Business Modal
    const cbModal = document.getElementById('create-business-modal');
    document.getElementById('btn-show-create-business').addEventListener('click', () => {
        cbModal.classList.remove('hidden');
    });
    document.getElementById('btn-cancel-create-business').addEventListener('click', () => {
        cbModal.classList.add('hidden');
    });

    document.getElementById('form-create-business').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        setLoadingState(btn, true, 'Create');

        const payload = {
            business_name: document.getElementById('cb-name').value,
            industry: document.getElementById('cb-industry').value,
            description: document.getElementById('cb-description').value
        };

        try {
            const response = await Auth.fetchWithAuth('/api/businesses', {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to create business');
            }

            showToast("Business created successfully!", "success");
            cbModal.classList.add('hidden');
            e.target.reset();

            // Reload businesses
            await loadBusinesses();

        } catch (err) {
            showToast(err.message, "error");
        } finally {
            setLoadingState(btn, false, 'Create');
        }
    });

    // --- AI Tools Listeners ---

    document.getElementById('form-ai-plan').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!State.activeBusinessId) return showToast("Select a business first", "warning");

        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        setLoadingState(btn, true, '');

        try {
            const response = await Auth.fetchWithAuth('/api/ai/generate-business-plan', {
                method: 'POST',
                body: JSON.stringify({
                    business_id: State.activeBusinessId,
                    target_market: document.getElementById('ai-plan-market').value || undefined
                })
            });

            if (!response.ok) throw new Error("Failed to generate plan");

            const data = await response.json();
            const resultDiv = document.getElementById('ai-plan-result');
            resultDiv.classList.remove('hidden');
            resultDiv.querySelector('div').textContent = JSON.stringify(data.plan_data, null, 2);
            showToast("Plan generated successfully!", "success");

        } catch (err) {
            showToast(err.message, "error");
        } finally {
            setLoadingState(btn, false, originalText);
        }
    });

    document.getElementById('form-ai-copy').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!State.activeBusinessId) return showToast("Select a business first", "warning");

        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        setLoadingState(btn, true, '');

        try {
            const response = await Auth.fetchWithAuth('/api/ai/generate-marketing-copy', {
                method: 'POST',
                body: JSON.stringify({
                    business_id: State.activeBusinessId,
                    platform: document.getElementById('ai-copy-platform').value,
                    campaign_goal: document.getElementById('ai-copy-goal').value,
                    target_audience: document.getElementById('ai-copy-audience').value,
                    tone: "professional"
                })
            });

            if (!response.ok) throw new Error("Failed to generate copy");

            const data = await response.json();
            const resultDiv = document.getElementById('ai-copy-result');
            resultDiv.classList.remove('hidden');
            resultDiv.querySelector('div').textContent = data.copy;
            showToast("Copy generated successfully!", "success");

        } catch (err) {
            showToast(err.message, "error");
        } finally {
            setLoadingState(btn, false, originalText);
        }
    });

    document.getElementById('form-ai-email').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!State.activeBusinessId) return showToast("Select a business first", "warning");

        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        setLoadingState(btn, true, '');

        try {
            const keyPointsRaw = document.getElementById('ai-email-points').value;
            const keyPoints = keyPointsRaw ? keyPointsRaw.split(',').map(p => p.trim()) : [];

            const response = await Auth.fetchWithAuth('/api/ai/generate-email-campaign', {
                method: 'POST',
                body: JSON.stringify({
                    business_id: State.activeBusinessId,
                    campaign_goal: document.getElementById('ai-email-goal').value,
                    target_audience: document.getElementById('ai-email-audience').value,
                    key_points: keyPoints
                })
            });

            if (!response.ok) throw new Error("Failed to generate email");

            const data = await response.json();
            const resultDiv = document.getElementById('ai-email-result');
            resultDiv.classList.remove('hidden');
            resultDiv.querySelector('div').textContent = JSON.stringify(data, null, 2);
            showToast("Email generated successfully!", "success");

        } catch (err) {
            showToast(err.message, "error");
        } finally {
            setLoadingState(btn, false, originalText);
        }
    });

});

// App Entry Point
async function initApp() {
    showMainLoader(true);
    try {
        await Promise.all([
            loadUserData(),
            loadBusinesses()
        ]);
        switchView('dashboard');
    } catch (e) {
        console.error("App init failed", e);
    } finally {
        showMainLoader(false);
    }
}
