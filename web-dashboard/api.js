/**
 * API Client for Rasperature Dashboard
 */

const api = {
    /**
     * Make API request
     */
    async request(endpoint, options = {}) {
        if (!config.apiUrl) {
            throw new Error('API URL not configured. Please set it in Settings.');
        }

        const url = `${config.apiUrl}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    },

    /**
     * Health check
     */
    async healthCheck() {
        return await this.request('/health');
    },

    /**
     * Get dashboard overview
     */
    async getDashboardOverview(customerId = null) {
        const params = customerId ? `?customer_id=${customerId}` : '';
        return await this.request(`/api/dashboard/overview${params}`);
    },

    /**
     * Get recent readings
     */
    async getRecentReadings(customerId = null, limit = 100) {
        const params = new URLSearchParams();
        if (customerId) params.append('customer_id', customerId);
        params.append('limit', limit);

        return await this.request(`/api/dashboard/recent?${params}`);
    },

    /**
     * Get aggregated data
     */
    async getAggregatedData(customerId = null, period = 'hour', hours = 24) {
        const params = new URLSearchParams();
        if (customerId) params.append('customer_id', customerId);
        params.append('period', period);
        params.append('hours', hours);

        return await this.request(`/api/dashboard/aggregates?${params}`);
    },

    /**
     * Get customers
     */
    async getCustomers() {
        return await this.request('/api/customers');
    },

    /**
     * Get all sensors
     */
    async getSensors(customerId = null) {
        const params = customerId ? `?customer_id=${customerId}` : '';
        return await this.request(`/api/sensors${params}`);
    },

    /**
     * Get specific sensor
     */
    async getSensor(sensorId) {
        return await this.request(`/api/sensors/${sensorId}`);
    },

    /**
     * Get latest reading for sensor
     */
    async getLatestReading(sensorId) {
        return await this.request(`/api/sensors/${sensorId}/latest`);
    },

    /**
     * Get sensor readings
     */
    async getSensorReadings(sensorId, hours = 24, limit = 1000) {
        const params = new URLSearchParams();
        params.append('hours', hours);
        params.append('limit', limit);

        return await this.request(`/api/sensors/${sensorId}/readings?${params}`);
    },

    /**
     * Get sensor stats
     */
    async getSensorStats(sensorId, hours = 24) {
        return await this.request(`/api/sensors/${sensorId}/stats?hours=${hours}`);
    },

    /**
     * Get customer stats
     */
    async getCustomerStats(customerId, days = 7) {
        return await this.request(`/api/customers/${customerId}/stats?days=${days}`);
    }
};
