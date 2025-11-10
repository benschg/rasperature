# Rasperature Web Dashboard

Modern, responsive web dashboard for monitoring and managing Rasperature sensor data.

## Features

- **Real-time Monitoring**: Live sensor data with auto-refresh
- **Interactive Charts**: Temperature, pressure, and humidity visualization
- **Multi-Customer Support**: Filter and view data by customer
- **Sensor Management**: View all sensors, their status, and readings
- **Analytics**: Detailed analytics with customizable time periods
- **Responsive Design**: Works on desktop, tablet, and mobile

## Quick Start

### 1. Configure API URL

1. Open `index.html` in a web browser
2. Navigate to Settings (⚙️)
3. Enter your Cloud Run API URL
4. Configure auto-refresh settings
5. Click "Save Settings"

### 2. Deploy

#### Option A: Static Hosting (Recommended for Production)

**Firebase Hosting:**
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize project
firebase init hosting

# Deploy
firebase deploy --only hosting
```

**Google Cloud Storage (Static Website):**
```bash
# Create bucket
gsutil mb gs://your-dashboard-bucket

# Upload files
gsutil -m cp -r * gs://your-dashboard-bucket/

# Make public
gsutil iam ch allUsers:objectViewer gs://your-dashboard-bucket

# Enable website configuration
gsutil web set -m index.html gs://your-dashboard-bucket
```

**Netlify:**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=.
```

#### Option B: Local Development

Simply open `index.html` in a web browser.

Or use a local server:
```bash
# Python
python3 -m http.server 8000

# Node.js
npx http-server -p 8000
```

Then visit: `http://localhost:8000`

## Configuration

### API Settings

Configure in Settings page or directly in `config.js`:

```javascript
const config = {
    apiUrl: 'https://your-api.run.app',  // Your Cloud Run API URL
    autoRefreshEnabled: true,
    refreshInterval: 30  // seconds
};
```

### Customization

#### Colors

Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    /* ... */
}
```

#### Chart Colors

Edit in `config.js`:
```javascript
chartColors: [
    '#667eea',
    '#764ba2',
    // Add more colors...
]
```

## Architecture

```
web-dashboard/
├── index.html       # Main HTML structure
├── styles.css       # Styling
├── config.js        # Configuration
├── api.js           # API client
├── charts.js        # Chart management
├── app.js           # Main application logic
└── README.md        # This file
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari 12+, Chrome Mobile

## Dependencies

- **Chart.js 4.4.1**: Data visualization (loaded from CDN)
- No build tools or npm packages required!

## Features

### Overview Page
- System statistics (customers, sensors, readings)
- Temperature and pressure trend charts
- Recent readings list

### Sensors Page
- List of all sensors with status
- Search functionality
- Sensor details (location, device, last seen)

### Analytics Page
- Customizable time periods (1h to 7 days)
- Multiple aggregation options (minute, hour, day)
- Multi-axis charts for different metrics

### Settings Page
- API configuration
- Auto-refresh settings
- About information

## Troubleshooting

### Dashboard shows "API URL not configured"

1. Go to Settings page
2. Enter your Cloud Run API URL
3. Save settings

### Data not loading

1. Check API URL in Settings
2. Verify API is running: `curl https://your-api.run.app/health`
3. Check browser console for errors
4. Ensure CORS is enabled on API

### Charts not displaying

1. Ensure Chart.js is loading from CDN
2. Check browser console for errors
3. Verify data is being returned from API

## Security

### Production Deployment

For production, consider:

1. **HTTPS Only**: Ensure dashboard is served over HTTPS
2. **API Authentication**: Add authentication to Cloud Run API
3. **Content Security Policy**: Add CSP headers
4. **Rate Limiting**: Implement on API side

### API Key Authentication (Optional)

If your API requires authentication, modify `api.js`:

```javascript
async request(endpoint, options = {}) {
    return await fetch(url, {
        ...options,
        headers: {
            'Authorization': 'Bearer YOUR_API_KEY',
            ...options.headers
        }
    });
}
```

## Performance

- Minimal dependencies (only Chart.js)
- Optimized asset loading
- Efficient data refresh
- Responsive caching

## License

Same as main Rasperature project

## Support

For issues or questions:
- Check main Rasperature documentation
- Open an issue on GitHub
- Review API documentation at `/docs` endpoint
