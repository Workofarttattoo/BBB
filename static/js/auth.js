/**
 * Authentication and Token Management Logic
 */

const TOKEN_KEY = 'bbb_access_token';
const REFRESH_TOKEN_KEY = 'bbb_refresh_token';

const Auth = {
    // Store tokens in localStorage
    setTokens: (accessToken, refreshToken) => {
        localStorage.setItem(TOKEN_KEY, accessToken);
        if (refreshToken) {
            localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
        }
    },

    // Get the current access token
    getToken: () => {
        return localStorage.getItem(TOKEN_KEY);
    },

    // Check if user is logged in
    isAuthenticated: () => {
        return !!localStorage.getItem(TOKEN_KEY);
    },

    // Clear tokens
    logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        window.location.reload();
    },

    // Generic fetch wrapper that adds Authorization header
    fetchWithAuth: async (url, options = {}) => {
        const token = Auth.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                // If unauthorized, clear token and reload to show login
                console.warn("Unauthorized request, logging out...");
                Auth.logout();
                throw new Error("Unauthorized");
            }

            return response;
        } catch (error) {
            throw error;
        }
    },

    // Login API Call
    login: async (email, password) => {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            Auth.setTokens(data.access_token, data.refresh_token);
            return true;
        } catch (error) {
            throw error;
        }
    },

    // Register API Call
    register: async (fullName, email, password) => {
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    full_name: fullName
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Registration failed');
            }

            const data = await response.json();
            Auth.setTokens(data.access_token, data.refresh_token);
            return true;
        } catch (error) {
            throw error;
        }
    },

    // Get current user info
    getMe: async () => {
        try {
            const response = await Auth.fetchWithAuth('/api/auth/me');
            if (!response.ok) throw new Error('Failed to fetch user');
            return await response.json();
        } catch (error) {
            throw error;
        }
    }
};

window.Auth = Auth;
