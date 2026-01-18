# 🔍 Real-Time Dependency Deprecation & Migration Intelligence System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful tool that analyzes Python repositories, detects breaking dependency changes in real-time, and provides AI-powered migration suggestions.

![Web UI Preview](https://raw.githubusercontent.com/yogita-n/project_rebase/main/.github/preview.png)

## ✨ Features

- 🔍 **Automatic Dependency Detection** - Scans all `requirements*.txt` files
- 🌐 **Live PyPI Integration** - Fetches latest package versions in real-time
- ⚠️ **Breaking Change Detection** - Identifies major version bumps using semantic versioning
- 📊 **AST-Based Code Analysis** - Scans Python files to find exact usage locations
- 🎯 **Impact Mapping** - Links breaking changes to affected code with file and line numbers
- 🤖 **AI-Powered Fixes** - Generates migration suggestions using LLM (optional)
- 🌐 **Web Dashboard** - Modern, responsive UI with dark theme
- 📋 **Structured Output** - Exports detailed JSON reports
- 🚀 **Easy Deployment** - Ready for Render, Hugging Face Spaces, or Docker

## 🚀 Quick Start

### Web Interface (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yogita-n/project_rebase.git
   cd project_rebase
   ```

2. **Install dependencies**
   ```bash
   pip install flask flask-cors requests packaging
   ```

3. **Start the web server**
   ```bash
   python web_server.py
   ```

4. **Open in browser**
   ```
   http://localhost:5000
   ```

### Command Line Interface

```bash
# Analyze current directory
python app.py .

# Analyze a GitHub repository
python app.py https://github.com/psf/requests

# Generate JSON report
python app.py . --output report.json

# With AI-powered fixes (requires OpenAI API key)
python app.py . --openai-key sk-your-key
```

## 📸 Screenshots

### Dashboard Overview
Modern dark theme with real-time analysis and visual status indicators.

### Breaking Change Detection
Color-coded cards showing breaking changes (red), outdated packages (orange), and up-to-date dependencies (green).

### Fix Suggestions
Expandable sections with AI-generated code fixes, explanations, and step-by-step migration guides.

## 🎯 How It Works

1. **Repository Fetching** - Clones GitHub repos or validates local paths
2. **Dependency Parsing** - Auto-detects and parses all `requirements*.txt` files
3. **PyPI Streaming** - Fetches latest versions from PyPI for all dependencies
4. **Version Comparison** - Detects outdated packages and breaking changes (major version bumps)
5. **Code Scanning** - Uses Python AST to find all package usage locations
6. **Impact Mapping** - Links breaking changes to specific code locations
7. **AI Fix Generation** - Optionally generates migration suggestions using LLM

## 📋 Example Output

```json
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
      ],
      "ai_fix": {
        "explanation": "Breaking change detected...",
        "fixed_code": "# Updated code...",
        "confidence": 0.85
      }
    }
  ]
}
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git (for cloning repositories)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yogita-n/project_rebase.git
cd project_rebase

# Install production dependencies
pip install -r requirements-prod.txt

# Or install all dependencies (including dev tools)
pip install -r requirements-system.txt
```

### Pathway Engine Installation (Windows Users)
Pathway does not support native Windows installation. You must use **WSL (Windows Subsystem for Linux)**.

1. **Enable WSL**:
   Open PowerShell as Administrator and run:
   ```powershell
   wsl --install
   ```
   (Restart if prompted, then open "Ubuntu" from Start menu)

2. **Set up Python Environment in WSL**:
   Run these commands inside your **WSL terminal**:
   ```bash
   # Update package lists
   sudo apt update

   # Install pip and venv
   sudo apt install -y python3-pip python3-venv

   # Create a virtual environment (recommended in your home dir)
   mkdir ~/my_pathway_project
   cd ~/my_pathway_project
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Pathway & Project Dependencies**:
   ```bash
   # Install Pathway
   pip install pathway

   # Access your project files (replace with your actual username/path)
   cd /mnt/c/Users/YOUR_USERNAME/Desktop/project_rebase

   # Install web server requirements into this Linux venv
   pip install flask flask-cors requests packaging
   ```

4. **Run the Project**:
   ```bash
   python3 web_server.py
   ```

### Docker

```bash
# Build the image
docker build -t dep-analyzer .

# Run the container
docker run -p 5000:5000 dep-analyzer

# Visit http://localhost:5000
```

## 🌐 Deployment

### Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Select "Docker" runtime
5. Deploy!

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Deploy to Hugging Face Spaces

1. Create a new Space with Docker SDK
2. Clone your Space repository
3. Copy project files
4. Push to deploy

See [DEPLOY_QUICK.md](DEPLOY_QUICK.md) for step-by-step guide.

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Optional | For AI-powered migration fixes |

### OpenAI API Key (Optional)

The system works perfectly without an API key, showing manual fix instructions. To enable AI-powered fixes:

**Local Development:**
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

**Deployment:**
Set as environment variable in your deployment platform (Render, Hugging Face, etc.)

## 📚 Documentation

- [Web Setup Guide](WEB_SETUP.md) - Detailed web interface documentation
- [Deployment Guide](DEPLOYMENT.md) - Deploy to Render or Hugging Face
- [Quick Deploy](DEPLOY_QUICK.md) - Fast deployment instructions
- [Usage Examples](USAGE_EXAMPLES.sh) - Common usage patterns

## 🏗️ Project Structure

```
project_rebase/
├── core/                      # Core analysis modules
│   ├── repo_fetcher.py       # Repository handling
│   ├── dep_parser.py         # Dependency parsing
│   ├── pathway_stream.py     # PyPI streaming
│   ├── code_scanner.py       # AST analysis
│   ├── impact_mapper.py      # Impact mapping
│   └── ai_fixer.py           # AI fix generation
├── static/                    # Web frontend
│   ├── index.html            # HTML structure
│   ├── styles.css            # Premium styling
│   └── script.js             # Interactive logic
├── app.py                     # CLI application
├── web_server.py             # Flask API server
├── Dockerfile                # Container configuration
└── requirements-prod.txt     # Production dependencies
```

## 🧪 Testing

Each module can be tested independently:

```bash
# Test repository fetcher
python core/repo_fetcher.py

# Test dependency parser
python core/dep_parser.py

# Test streaming engine
python core/pathway_stream.py

# Test code scanner
python core/code_scanner.py

# Test impact mapper
python core/impact_mapper.py

# Test AI fixer
python core/ai_fixer.py
```

## 🎨 Tech Stack

- **Backend**: Python, Flask, Gunicorn
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Analysis**: Python AST, PyPI JSON API
- **AI**: OpenAI GPT (optional)
- **Deployment**: Docker, Render, Hugging Face Spaces

## 📊 Performance

- **Initial Load**: < 1 second
- **Analysis Time**: 30-120 seconds (depends on repository size)
- **API Response**: Real-time
- **UI Updates**: Instant

## ⚠️ Limitations

- **Python Only**: Currently supports Python projects only
- **PyPI Only**: Only checks PyPI for package updates
- **Requirements Files**: Only parses `requirements*.txt` (not `poetry`, `pipenv`, etc.)
- **Breaking Change Detection**: Based on semantic versioning (major version bumps)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python AST for accurate code analysis
- PyPI JSON API for package information
- OpenAI GPT for AI-powered migration suggestions
- Flask for the web framework
- Inspired by the need for safer dependency upgrades

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yogita-n/project_rebase/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yogita-n/project_rebase/discussions)

## 🚀 Roadmap

- [ ] Support for `poetry.lock` and `Pipfile.lock`
- [ ] Multi-language support (JavaScript, Java, etc.)
- [ ] Real-time monitoring mode
- [ ] CI/CD pipeline integration
- [ ] Automated PR generation
- [ ] Custom migration rule engine
- [ ] Dark/Light theme toggle

---

**Made with ❤️ for the Python community**

⭐ Star this repo if you find it helpful!
