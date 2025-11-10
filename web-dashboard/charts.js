/**
 * Chart Management for Rasperature Dashboard
 */

const charts = {
    instances: {},

    /**
     * Create or update line chart
     */
    createLineChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        // Destroy existing chart
        if (this.instances[canvasId]) {
            this.instances[canvasId].destroy();
        }

        // Create new chart
        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'hour',
                            displayFormats: {
                                hour: 'HH:mm',
                                day: 'MMM DD'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: options.yAxisLabel || 'Value'
                        }
                    }
                },
                ...options
            }
        });

        return this.instances[canvasId];
    },

    /**
     * Prepare temperature chart data
     */
    prepareTemperatureData(aggregatedData) {
        // Group by sensor
        const sensorMap = {};

        aggregatedData.forEach(reading => {
            if (!sensorMap[reading.sensor_id]) {
                sensorMap[reading.sensor_id] = {
                    label: reading.sensor_id,
                    data: [],
                    borderColor: config.chartColors[Object.keys(sensorMap).length % config.chartColors.length],
                    backgroundColor: config.chartColors[Object.keys(sensorMap).length % config.chartColors.length] + '20',
                    tension: 0.4,
                    fill: false
                };
            }

            sensorMap[reading.sensor_id].data.push({
                x: new Date(reading.timestamp),
                y: reading.temperature_avg
            });
        });

        return {
            datasets: Object.values(sensorMap)
        };
    },

    /**
     * Prepare pressure chart data
     */
    preparePressureData(aggregatedData) {
        // Group by sensor
        const sensorMap = {};

        aggregatedData.forEach(reading => {
            if (!sensorMap[reading.sensor_id]) {
                sensorMap[reading.sensor_id] = {
                    label: reading.sensor_id,
                    data: [],
                    borderColor: config.chartColors[Object.keys(sensorMap).length % config.chartColors.length],
                    backgroundColor: config.chartColors[Object.keys(sensorMap).length % config.chartColors.length] + '20',
                    tension: 0.4,
                    fill: false
                };
            }

            sensorMap[reading.sensor_id].data.push({
                x: new Date(reading.timestamp),
                y: reading.pressure_avg
            });
        });

        return {
            datasets: Object.values(sensorMap)
        };
    },

    /**
     * Update temperature chart
     */
    async updateTemperatureChart(customerId = null) {
        try {
            const data = await api.getAggregatedData(customerId, 'hour', 24);
            const chartData = this.prepareTemperatureData(data);

            this.createLineChart('temp-chart', chartData, {
                yAxisLabel: 'Temperature (°C)'
            });
        } catch (error) {
            console.error('Failed to update temperature chart:', error);
        }
    },

    /**
     * Update pressure chart
     */
    async updatePressureChart(customerId = null) {
        try {
            const data = await api.getAggregatedData(customerId, 'hour', 24);
            const chartData = this.preparePressureData(data);

            this.createLineChart('pressure-chart', chartData, {
                yAxisLabel: 'Pressure (hPa)'
            });
        } catch (error) {
            console.error('Failed to update pressure chart:', error);
        }
    },

    /**
     * Update analytics chart
     */
    async updateAnalyticsChart(customerId = null) {
        try {
            const period = document.getElementById('analytics-period').value;
            const aggregation = document.getElementById('analytics-aggregation').value;

            const data = await api.getAggregatedData(customerId, aggregation, parseInt(period));

            // Create multi-metric chart
            const datasets = [];
            const sensorMap = {};

            // Group by sensor and metric
            data.forEach(reading => {
                if (!sensorMap[reading.sensor_id]) {
                    sensorMap[reading.sensor_id] = {
                        temp: [],
                        pressure: [],
                        humidity: []
                    };
                }

                sensorMap[reading.sensor_id].temp.push({
                    x: new Date(reading.timestamp),
                    y: reading.temperature_avg
                });

                if (reading.pressure_avg) {
                    sensorMap[reading.sensor_id].pressure.push({
                        x: new Date(reading.timestamp),
                        y: reading.pressure_avg
                    });
                }

                if (reading.humidity_avg) {
                    sensorMap[reading.sensor_id].humidity.push({
                        x: new Date(reading.timestamp),
                        y: reading.humidity_avg
                    });
                }
            });

            // Create datasets
            Object.entries(sensorMap).forEach(([sensorId, metrics], index) => {
                const color = config.chartColors[index % config.chartColors.length];

                datasets.push({
                    label: `${sensorId} - Temperature`,
                    data: metrics.temp,
                    borderColor: color,
                    backgroundColor: color + '20',
                    yAxisID: 'y',
                    tension: 0.4
                });

                if (metrics.pressure.length > 0) {
                    datasets.push({
                        label: `${sensorId} - Pressure`,
                        data: metrics.pressure,
                        borderColor: color,
                        backgroundColor: color + '20',
                        borderDash: [5, 5],
                        yAxisID: 'y1',
                        tension: 0.4
                    });
                }
            });

            this.createLineChart('analytics-chart', { datasets }, {
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Pressure (hPa)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Failed to update analytics chart:', error);
        }
    },

    /**
     * Destroy all charts
     */
    destroyAll() {
        Object.values(this.instances).forEach(chart => chart.destroy());
        this.instances = {};
    }
};
