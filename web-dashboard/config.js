/**
 * Configuration for Rasperature Dashboard
 */

const config = {
    // API Configuration
    apiUrl: localStorage.getItem('apiUrl') || '',

    // Auto-refresh settings
    autoRefreshEnabled: localStorage.getItem('autoRefreshEnabled') !== 'false',
    refreshInterval: parseInt(localStorage.getItem('refreshInterval') || '30') * 1000,

    // Chart configuration
    chartColors: [
        '#667eea',
        '#764ba2',
        '#f093fb',
        '#4facfe',
        '#43e97b',
        '#fa709a',
        '#fee140',
        '#30cfd0'
    ],

    // Update settings
    updateSettings: function(newSettings) {
        if (newSettings.apiUrl !== undefined) {
            this.apiUrl = newSettings.apiUrl;
            localStorage.setItem('apiUrl', newSettings.apiUrl);
        }
        if (newSettings.autoRefreshEnabled !== undefined) {
            this.autoRefreshEnabled = newSettings.autoRefreshEnabled;
            localStorage.setItem('autoRefreshEnabled', newSettings.autoRefreshEnabled);
        }
        if (newSettings.refreshInterval !== undefined) {
            this.refreshInterval = newSettings.refreshInterval * 1000;
            localStorage.setItem('refreshInterval', newSettings.refreshInterval);
        }
    }
};
