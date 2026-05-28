/**
 * Enterprise Ops & Knowledge Vault UI Module
 * Viktor-Style Autonomous Business Controls
 * 
 * Features:
 * - Knowledge Vault browser & search
 * - Firebase sync controls
 * - Agent ops settings
 * - Paperclip issue sync
 */

class EnterpriseOpsUI {
    constructor() {
        this.apiBase = '/api/v1';
        this.init();
    }

    init() {
        // Only initialize if we're on the main dashboard
        if (document.getElementById('enterprise-panel')) {
            this.loadSettings();
            this.loadKnowledgeVault();
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        // Knowledge Vault Search
        const searchBtn = document.getElementById('kv-search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.searchKnowledge());
        }
        
        const searchInput = document.getElementById('kv-search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.searchKnowledge();
            });
        }

        // Firebase Sync
        const firebaseUploadBtn = document.getElementById('firebase-upload-btn');
        if (firebaseUploadBtn) {
            firebaseUploadBtn.addEventListener('click', () => this.syncToFirebase());
        }

        const firebaseDownloadBtn = document.getElementById('firebase-download-btn');
        if (firebaseDownloadBtn) {
            firebaseDownloadBtn.addEventListener('click', () => this.syncFromFirebase());
        }

        const firebaseStatusBtn = document.getElementById('firebase-status-btn');
        if (firebaseStatusBtn) {
            firebaseStatusBtn.addEventListener('click', () => this.checkFirebaseStatus());
        }

        // Paperclip Sync
        const paperclipSyncBtn = document.getElementById('paperclip-sync-btn');
        if (paperclipSyncBtn) {
            paperclipSyncBtn.addEventListener('click', () => this.syncPaperclipIssues());
        }

        // Agent Ops Settings Save
        const saveSettingsBtn = document.getElementById('save-agent-ops-btn');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => this.saveAgentOpsSettings());
        }

        // Reload Knowledge Vault
        const reloadKvBtn = document.getElementById('reload-kv-btn');
        if (reloadKvBtn) {
            reloadKvBtn.addEventListener('click', () => this.reloadKnowledgeVault());
        }
    }

    // ========== Knowledge Vault ==========

    async loadKnowledgeVault() {
        try {
            const response = await fetch(`${this.apiBase}/knowledge-vault/context`);
            const data = await response.json();
            
            const contextDiv = document.getElementById('kv-context');
            if (contextDiv && data.context) {
                contextDiv.innerHTML = `<pre class="text-xs bg-gray-900 text-green-400 p-4 rounded overflow-auto max-h-96">${this.escapeHtml(data.context)}</pre>`;
            }
        } catch (error) {
            console.error('Failed to load Knowledge Vault:', error);
        }
    }

    async searchKnowledge() {
        const query = document.getElementById('kv-search-input').value.trim();
        if (!query) {
            this.showToast('Please enter a search query', 'warning');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/knowledge-vault/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, limit: 10 })
            });
            const data = await response.json();
            
            const resultsDiv = document.getElementById('kv-search-results');
            if (resultsDiv) {
                if (data.results && data.results.length > 0) {
                    resultsDiv.innerHTML = `
                        <h4 class="font-semibold mb-2">Search Results for "${query}"</h4>
                        <div class="space-y-2">
                            ${data.results.map(r => `
                                <div class="bg-white p-3 rounded border border-gray-200">
                                    <div class="text-xs text-blue-600 font-medium">${r.source}</div>
                                    <div class="text-sm text-gray-700 mt-1">${r.snippet}</div>
                                    <div class="text-xs text-gray-400 mt-1">Score: ${(r.score * 100).toFixed(0)}%</div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="text-gray-500 text-sm">No results found for "${query}"</div>`;
                }
            }
        } catch (error) {
            console.error('Search failed:', error);
            this.showToast('Search failed: ' + error.message, 'error');
        }
    }

    async reloadKnowledgeVault() {
        try {
            const response = await fetch(`${this.apiBase}/knowledge-vault/reload`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.status === 'reloaded') {
                this.showToast(`Knowledge Vault reloaded (${data.files} files)`, 'success');
                this.loadKnowledgeVault();
            }
        } catch (error) {
            console.error('Reload failed:', error);
            this.showToast('Reload failed: ' + error.message, 'error');
        }
    }

    // ========== Firebase Sync ==========

    async checkFirebaseStatus() {
        try {
            const response = await fetch(`${this.apiBase}/knowledge-vault/firebase/status`);
            const data = await response.json();
            
            const statusDiv = document.getElementById('firebase-status');
            if (statusDiv) {
                if (data.enabled) {
                    statusDiv.innerHTML = `
                        <div class="flex items-center gap-2">
                            <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                            <span class="text-sm text-green-700">Connected</span>
                            <span class="text-xs text-gray-500 ml-2">Last sync: ${data.remote_version || 'Never'}</span>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div class="flex items-center gap-2">
                            <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                            <span class="text-sm text-gray-600">Not configured</span>
                            <span class="text-xs text-gray-400 ml-2">Set FIREBASE_CREDENTIALS_PATH env var</span>
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('Status check failed:', error);
        }
    }

    async syncToFirebase() {
        const btn = document.getElementById('firebase-upload-btn');
        if (btn) btn.disabled = true;

        try {
            const response = await fetch(`${this.apiBase}/knowledge-vault/sync/firebase/upload`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showToast(`Uploaded ${data.files_uploaded} files to Firebase`, 'success');
                this.checkFirebaseStatus();
            } else {
                this.showToast('Upload failed: ' + (data.reason || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Upload failed:', error);
            this.showToast('Upload failed: ' + error.message, 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    async syncFromFirebase() {
        const btn = document.getElementById('firebase-download-btn');
        if (btn) btn.disabled = true;

        try {
            const response = await fetch(`${this.apiBase}/knowledge-vault/sync/firebase/download`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showToast(`Downloaded ${data.files_downloaded} files from Firebase`, 'success');
                this.loadKnowledgeVault();
            } else {
                this.showToast('Download failed: ' + (data.reason || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Download failed:', error);
            this.showToast('Download failed: ' + error.message, 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    // ========== Agent Ops Settings ==========

    async loadSettings() {
        try {
            const response = await fetch(`${this.apiBase}/agent-ops/settings`);
            const settings = await response.json();
            
            // Populate form fields
            const viktorToggle = document.getElementById('viktor-mode-toggle');
            if (viktorToggle) viktorToggle.checked = settings.viktor_mode_enabled;
            
            const assumeForwardToggle = document.getElementById('assume-forward-toggle');
            if (assumeForwardToggle) assumeForwardToggle.checked = settings.assume_forward;
            
            const maxRevisesInput = document.getElementById('max-revises-input');
            if (maxRevisesInput) maxRevisesInput.value = settings.max_revises || 3;
            
            const scheduleInput = document.getElementById('proactive-schedule-input');
            if (scheduleInput) scheduleInput.value = settings.proactive_schedule || '07:00 UTC';
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    async saveAgentOpsSettings() {
        const settings = {
            viktor_mode_enabled: document.getElementById('viktor-mode-toggle')?.checked || false,
            assume_forward: document.getElementById('assume-forward-toggle')?.checked || false,
            max_revises: parseInt(document.getElementById('max-revises-input')?.value || '3'),
            proactive_schedule: document.getElementById('proactive-schedule-input')?.value || '07:00 UTC'
        };

        try {
            const response = await fetch(`${this.apiBase}/agent-ops/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showToast('Agent Ops settings saved', 'success');
            } else {
                this.showToast('Failed to save settings', 'error');
            }
        } catch (error) {
            console.error('Save failed:', error);
            this.showToast('Save failed: ' + error.message, 'error');
        }
    }

    // ========== Paperclip Sync ==========

    async syncPaperclipIssues() {
        const jsonInput = document.getElementById('paperclip-json-input');
        const issuesJson = jsonInput?.value.trim();
        
        if (!issuesJson) {
            this.showToast('Please paste Paperclip issue JSON', 'warning');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/enterprise/paperclip/sync-issues`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    issues_json: issuesJson,
                    business_id: 'saas-micro-tools'
                })
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showToast(`Synced ${data.synced} issues to task queue`, 'success');
                // Clear input
                if (jsonInput) jsonInput.value = '';
                // Refresh tasks
                if (window.app && window.app.loadTasks) {
                    window.app.loadTasks();
                }
            } else {
                this.showToast('Sync failed: ' + (data.message || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Sync failed:', error);
            this.showToast('Sync failed: ' + error.message, 'error');
        }
    }

    // ========== Utilities ==========

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `px-4 py-2 rounded shadow-lg text-white text-sm ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' :
            'bg-blue-500'
        }`;
        toast.textContent = message;
        
        const container = document.getElementById('toast-container');
        if (container) {
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.enterpriseOps = new EnterpriseOpsUI();
    });
} else {
    window.enterpriseOps = new EnterpriseOpsUI();
}
