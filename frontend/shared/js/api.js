// API Service for AroundU Backend
class ApiService {
    constructor() {
        this.baseUrl = 'http://127.0.0.1:8000/api';
    }

    // Token Management
    getToken() {
        return localStorage.getItem('access_token');
    }

    saveToken(token) {
        localStorage.setItem('access_token', token);
    }

    removeToken() {
        localStorage.removeItem('access_token');
    }

    // HTTP Request Helper
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = this.getToken();

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        if (token && !options.skipAuth) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // Auth Endpoints
    async register(email, password, fullName) {
        const data = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                email,
                password,
                full_name: fullName,
            }),
            skipAuth: true,
        });
        this.saveToken(data.access_token);
        return data;
    }

    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                email,
                password,
            }),
            skipAuth: true,
        });
        this.saveToken(data.access_token);
        return data;
    }

    async getProfile() {
        return await this.request('/auth/profile');
    }

    logout() {
        this.removeToken();
        window.location.href = 'index.html';
    }

    // Categories Endpoints
    async getCategories(skip = 0, limit = 100) {
        return await this.request(`/categories?skip=${skip}&limit=${limit}`, {
            skipAuth: true,
        });
    }

    async createCategory(name, description, icon) {
        return await this.request('/categories', {
            method: 'POST',
            body: JSON.stringify({
                name,
                description,
                icon,
            }),
        });
    }

    // Places Endpoints
    async getPlaces(skip = 0, limit = 100, categoryId = null) {
        let url = `/places?skip=${skip}&limit=${limit}`;
        if (categoryId) {
            url += `&category_id=${categoryId}`;
        }
        return await this.request(url, { skipAuth: true });
    }

    async createPlace(placeData) {
        return await this.request('/places', {
            method: 'POST',
            body: JSON.stringify(placeData),
        });
    }

    // Search Endpoints
    async search(query = null, category = null) {
        let url = '/search?';
        if (query) url += `q=${encodeURIComponent(query)}&`;
        if (category) url += `category=${encodeURIComponent(category)}`;

        return await this.request(url, {
            skipAuth: true, // Optional auth
        });
    }

    async getRecentSearches() {
        return await this.request('/search/recent');
    }

    async getTrendingSearches() {
        return await this.request('/search/trending', { skipAuth: true });
    }

    // Chat Endpoints
    async sendMessage(message) {
        return await this.request('/chat/message', {
            method: 'POST',
            body: JSON.stringify({
                message,
            }),
        });
    }
}

// Create global instance
const api = new ApiService();
