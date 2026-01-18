# Web Frontend for Dependency Analysis System

![Web UI Preview](file:///C:/Users/yogita/.gemini/antigravity/brain/466b43d3-55de-4a5e-a717-e37567e6a2fb/web_ui_mockup_1768722728705.png)

## 🌟 Features

- **Modern Dark Theme UI** - Premium design with gradients and glassmorphism
- **Real-time Analysis** - Instant feedback on repository dependencies
- **Visual Status Indicators** - Color-coded breaking changes, outdated, and up-to-date packages
- **Detailed Impact Reports** - See exactly which files and lines are affected
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Smooth Animations** - Professional transitions and hover effects

## 🚀 Quick Start

### 1. Start the Web Server

```bash
python web_server.py
```

You should see:
```
======================================================================
Starting Dependency Analysis Web Server
======================================================================

Server running at: http://localhost:5000
Press Ctrl+C to stop
```

### 2. Open in Browser

Navigate to: **http://localhost:5000**

### 3. Analyze a Repository

1. Enter a GitHub repository URL:
   - Example: `https://github.com/psf/requests`
   - Or use `.` for the current directory

2. Click the **Analyze** button

3. Wait for analysis to complete (may take 30-60 seconds)

4. View results with:
   - Summary statistics
   - Breaking changes highlighted in red
   - Outdated packages in orange
   - Up-to-date packages in green
   - File-level impact details

## 📁 File Structure

```
static/
├── index.html      # Main HTML structure
├── styles.css      # Premium dark theme styles
└── script.js       # Interactive functionality

web_server.py       # Flask API server
```

## 🎨 Design Features

### Color Scheme
- **Background**: Deep blue gradient (#0f172a → #1a1f3a)
- **Primary**: Purple (#6366f1)
- **Breaking**: Red (#ef4444)
- **Outdated**: Orange (#f59e0b)
- **Success**: Green (#10b981)

### UI Components
- **Glassmorphism cards** with backdrop blur
- **Gradient buttons** with hover animations
- **Smooth transitions** on all interactions
- **Loading spinner** during analysis
- **Error states** with retry functionality

## 🔌 API Endpoints

### POST /api/analyze
Analyzes a repository and returns dependency information.

**Request:**
```json
{
  "repo_url": "https://github.com/user/repo"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Analysis completed successfully",
  "data": {
    "repository": "/path/to/repo",
    "total_dependencies": 12,
    "breaking_changes": 3,
    "outdated_packages": 5,
    "results": [
      {
        "package": "flask",
        "current_version": "2.0.0",
        "latest_version": "3.1.2",
        "status": "breaking",
        "impacted_files": [
          {
            "file": "app.py",
            "impacts": [
              {
                "line": 10,
                "api": "Flask",
                "context": "app = Flask(__name__)"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Dependency Analysis API"
}
```

## 💡 Usage Tips

### Example Repositories to Try

1. **Small Project**: `https://github.com/psf/requests`
2. **Current Directory**: `.`
3. **Local Path**: `/path/to/your/project`

### Understanding Results

- **Breaking Changes** 🔴: Major version bumps that may break your code
- **Outdated Packages** 🟠: Minor/patch updates available
- **Up-to-date** 🟢: Already using the latest version

### Impact Details

For breaking changes, you'll see:
- **File name**: Which file uses the package
- **Line number**: Exact location in the file
- **Code context**: The actual line of code
- **API element**: What function/class is being used

## 🛠️ Troubleshooting

### Server won't start
```bash
# Check if Flask is installed
python -c "import flask; print('Flask OK')"

# Install if needed
pip install flask flask-cors
```

### Port 5000 already in use
Edit `web_server.py` and change the port:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Use port 8080
```

### Analysis takes too long
- Large repositories may take 1-2 minutes
- The system needs to:
  1. Clone/validate the repository
  2. Parse all requirements files
  3. Fetch data from PyPI for each package
  4. Scan all Python files
  5. Generate impact reports

### CORS errors
Make sure `flask-cors` is installed:
```bash
pip install flask-cors
```

## 🎯 Advanced Features

### Custom Styling
Edit `static/styles.css` to customize:
- Colors (`:root` CSS variables)
- Spacing and layout
- Animations and transitions

### API Integration
The frontend uses `fetch()` API to communicate with the backend:
```javascript
const response = await fetch('http://localhost:5000/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl })
});
```

## 📱 Responsive Design

The UI automatically adapts to different screen sizes:
- **Desktop**: Full grid layout with 4 summary cards
- **Tablet**: 2-column grid
- **Mobile**: Single column, stacked layout

## 🔐 Security Notes

- The server runs on localhost by default
- For production use, add authentication
- Validate and sanitize user inputs
- Use HTTPS in production
- Set appropriate CORS policies

## 🚀 Deployment

For production deployment:

1. **Disable debug mode**:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

2. **Use a production server** (e.g., Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_server:app
```

3. **Set up reverse proxy** (e.g., Nginx)

4. **Enable HTTPS** with SSL certificates

## 📊 Performance

- Initial load: < 1 second
- Analysis time: 30-120 seconds (depends on repo size)
- API response: Real-time
- UI updates: Instant

## 🎨 Screenshots

The web interface includes:
- Clean, modern header with gradient text
- Large input field with example buttons
- Real-time loading spinner
- Color-coded summary cards
- Expandable package details
- File-level impact visualization

---

**Built with**: HTML5, CSS3, Vanilla JavaScript, Flask, Python
