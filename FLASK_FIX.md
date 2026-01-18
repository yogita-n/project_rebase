# Quick Fix for Flask/Werkzeug Compatibility Issue

## Problem
Flask 2.0.0 is incompatible with Werkzeug 3.x (which was installed as a dependency).

## Solution

Run these commands in order:

```bash
# Option 1: Upgrade to Flask 3.x (Recommended)
pip uninstall flask werkzeug -y
pip install flask>=3.0.0 flask-cors>=4.0.0

# Option 2: Downgrade Werkzeug to 2.x
pip uninstall werkzeug -y
pip install "werkzeug<3.0"
pip install flask-cors
```

## After fixing, run:
```bash
python web_server.py
```

The server should start successfully at http://localhost:5000
