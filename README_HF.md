---
title: Dependency Analysis System
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 5000
---

# 🔍 Dependency Analysis System

**Real-time detection of breaking changes in Python dependencies**

## What it does

This tool analyzes Python repositories and:
- ✅ Detects all dependencies from `requirements.txt` files
- ✅ Checks PyPI for latest versions
- ✅ Identifies breaking changes (major version bumps)
- ✅ Scans your code to find exact usage locations
- ✅ Shows which files and lines will be affected

## How to use

1. Enter a GitHub repository URL (e.g., `https://github.com/psf/requests`)
2. Click "Analyze"
3. View results with color-coded status indicators:
   - 🔴 **Breaking Changes**: Major version bumps that may break your code
   - 🟠 **Outdated**: Minor/patch updates available
   - 🟢 **Up-to-date**: Already using latest version

## Example

Try analyzing: `https://github.com/psf/requests`

## Features

- Modern dark theme UI
- Real-time PyPI integration
- AST-based code analysis
- File-level impact details
- Responsive design

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **Analysis**: Python AST, PyPI API
- **Deployment**: Docker, Gunicorn

---

Built with ❤️ for the Python community
