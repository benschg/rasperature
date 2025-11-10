/**
 * Main Application Logic for Rasperature Dashboard
 */

let currentCustomer = null;
let autoRefreshTimer = null;

/**
 * Initialize app
 */
async function init() {
    // Setup navigation
    setupNavigation();

    // Setup customer selector
    setupCustomerSelector();

    // Setup settings form
    setupSettings();

    // Load initial data if API is configured
    if (config.apiUrl) {
        await loadCustomers();
        await refreshData();
        startAutoRefresh();
    } else {
        showPage('settings');
        alert('Please configure the API URL in Settings to get started.');
    }
}

/**
 * Setup navigation
 */
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            // Update active nav item
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Show corresponding page
            const page = item.dataset.page;
            showPage(page);

            // Update page title
            const titles = {
                'overview': 'Dashboard Overview',
                'sensors': 'Sensors',
                'analytics': 'Analytics',
                'settings': 'Settings'
            };
            document.getElementById('page-title').textContent = titles[page];

            // Load page-specific data
            if (page === 'sensors') {
                loadSensors();
            } else if (page === 'analytics') {
                loadAnalytics();
            }
        });
    });
}

/**
 * Show specific page
 */
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(`page-${pageId}`).classList.add('active');
}

/**
 * Setup customer selector
 */
function setupCustomerSelector() {
    document.getElementById('customer-select').addEventListener('change', async (e) => {
        currentCustomer = e.target.value || null;
        await refreshData();
    });
}

/**
 * Load customers
 */
async function loadCustomers() {
    try {
        const customers = await api.getCustomers();

        const select = document.getElementById('customer-select');
        select.innerHTML = '<option value="">All Customers</option>';

        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.customer_id;
            option.textContent = `${customer.customer_id} (${customer.sensor_count} sensors)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load customers:', error);
        showError('Failed to load customers');
    }
}

/**
 * Refresh all data
 */
async function refreshData() {
    showLoading(true);

    try {
        // Test connection
        await api.healthCheck();
        updateConnectionStatus(true);

        // Load overview data
        await loadOverviewData();

        // Update charts
        await charts.updateTemperatureChart(currentCustomer);
        await charts.updatePressureChart(currentCustomer);

        // Load recent readings
        await loadRecentReadings();

    } catch (error) {
        console.error('Failed to refresh data:', error);
        updateConnectionStatus(false);
        showError('Failed to refresh data: ' + error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Load overview data
 */
async function loadOverviewData() {
    try {
        const overview = await api.getDashboardOverview(currentCustomer);

        document.getElementById('stat-customers').textContent = overview.total_customers || '-';
        document.getElementById('stat-sensors').textContent = overview.total_sensors || '-';
        document.getElementById('stat-active').textContent = overview.active_sensors || '-';
        document.getElementById('stat-readings').textContent = overview.total_readings_24h ? overview.total_readings_24h.toLocaleString() : '-';
    } catch (error) {
        console.error('Failed to load overview data:', error);
    }
}

/**
 * Load recent readings
 */
async function loadRecentReadings() {
    try {
        const readings = await api.getRecentReadings(currentCustomer, 20);

        const container = document.getElementById('recent-readings');

        if (readings.length === 0) {
            container.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">No recent readings</p>';
            return;
        }

        container.innerHTML = readings.map(reading => `
            <div class="reading-item">
                <div class="reading-time">${new Date(reading.timestamp).toLocaleString()}</div>
                <div class="reading-sensor">
                    <div>${reading.sensor_id}</div>
                    <div style="color: #999; font-size: 12px;">${reading.location || 'No location'}</div>
                </div>
                <div class="reading-values">
                    ${reading.temperature !== null ? `
                        <div class="reading-value">
                            <span>🌡️</span>
                            <span>${reading.temperature.toFixed(1)}°C</span>
                        </div>
                    ` : ''}
                    ${reading.pressure !== null ? `
                        <div class="reading-value">
                            <span>🔽</span>
                            <span>${reading.pressure.toFixed(1)} hPa</span>
                        </div>
                    ` : ''}
                    ${reading.humidity !== null ? `
                        <div class="reading-value">
                            <span>💧</span>
                            <span>${reading.humidity.toFixed(1)}%</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load recent readings:', error);
    }
}

/**
 * Load sensors
 */
async function loadSensors() {
    try {
        showLoading(true);

        const sensors = await api.getSensors(currentCustomer);

        const container = document.getElementById('sensors-list');

        if (sensors.length === 0) {
            container.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">No sensors found</p>';
            return;
        }

        container.innerHTML = sensors.map(sensor => {
            const statusClass = sensor.is_active ? 'active' : 'inactive';
            const statusText = sensor.is_active ? 'Active' : 'Inactive';
            const lastSeen = sensor.last_seen ? new Date(sensor.last_seen).toLocaleString() : 'Never';

            return `
                <div class="sensor-card">
                    <div class="sensor-header">
                        <div>
                            <div class="sensor-name">${sensor.sensor_id}</div>
                            <div class="sensor-type">${sensor.sensor_type}</div>
                        </div>
                        <div class="sensor-status ${statusClass}">${statusText}</div>
                    </div>
                    <div class="sensor-readings">
                        <div class="sensor-reading">
                            <span class="reading-label">Location</span>
                            <span>${sensor.location || 'Not set'}</span>
                        </div>
                        <div class="sensor-reading">
                            <span class="reading-label">Device</span>
                            <span>${sensor.device_id}</span>
                        </div>
                        <div class="sensor-reading">
                            <span class="reading-label">Last Seen</span>
                            <span>${lastSeen}</span>
                        </div>
                        <div class="sensor-reading">
                            <span class="reading-label">Total Readings</span>
                            <span class="reading-number">${sensor.total_readings.toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Setup search functionality
        const searchInput = document.getElementById('sensor-search');
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.sensor-card').forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(query) ? 'block' : 'none';
            });
        });
    } catch (error) {
        console.error('Failed to load sensors:', error);
        showError('Failed to load sensors');
    } finally {
        showLoading(false);
    }
}

/**
 * Load analytics
 */
async function loadAnalytics() {
    showLoading(true);
    try {
        await charts.updateAnalyticsChart(currentCustomer);
    } catch (error) {
        console.error('Failed to load analytics:', error);
        showError('Failed to load analytics');
    } finally {
        showLoading(false);
    }
}

/**
 * Setup settings
 */
function setupSettings() {
    const form = document.getElementById('settings-form');
    const apiUrlInput = document.getElementById('api-url');
    const refreshIntervalInput = document.getElementById('refresh-interval');
    const autoRefreshCheckbox = document.getElementById('auto-refresh-enabled');

    // Load current settings
    apiUrlInput.value = config.apiUrl;
    refreshIntervalInput.value = config.refreshInterval / 1000;
    autoRefreshCheckbox.checked = config.autoRefreshEnabled;

    // Save settings
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        config.updateSettings({
            apiUrl: apiUrlInput.value,
            refreshInterval: parseInt(refreshIntervalInput.value),
            autoRefreshEnabled: autoRefreshCheckbox.checked
        });

        alert('Settings saved successfully!');

        // Reload customers and data
        await loadCustomers();
        await refreshData();

        // Restart auto-refresh
        stopAutoRefresh();
        startAutoRefresh();

        // Return to overview
        showPage('overview');
    });
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    if (!config.autoRefreshEnabled) return;

    stopAutoRefresh();

    autoRefreshTimer = setInterval(async () => {
        console.log('Auto-refreshing data...');
        await refreshData();
    }, config.refreshInterval);

    console.log(`Auto-refresh started (interval: ${config.refreshInterval / 1000}s)`);
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
    }
}

/**
 * Update connection status
 */
function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('connection-status');
    const statusText = document.getElementById('connection-text');

    if (connected) {
        statusDot.style.background = 'var(--success-color)';
        statusText.textContent = 'Connected';
    } else {
        statusDot.style.background = 'var(--danger-color)';
        statusText.textContent = 'Disconnected';
    }
}

/**
 * Show loading overlay
 */
function showLoading(show) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

/**
 * Show error message
 */
function showError(message) {
    // Simple alert for now, could be replaced with a toast notification
    console.error(message);
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', init);

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
    charts.destroyAll();
});
