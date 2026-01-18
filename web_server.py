"""
Web API Server for Dependency Analysis System

Provides REST API endpoints for the frontend to interact with the analysis system.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import threading
import json
from pathlib import Path

# Import the main system
from app import DeprecationIntelligenceSystem

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Store analysis results temporarily
analysis_cache = {}


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_repository():
    """
    Analyze a repository.
    
    Request body:
    {
        "repo_url": "https://github.com/user/repo or /path/to/local"
    }
    
    Response:
    {
        "status": "success" | "error",
        "message": "...",
        "data": {...}  // Analysis results
    }
    """
    try:
        data = request.get_json()
        repo_url = data.get('repo_url', '').strip()
        
        if not repo_url:
            return jsonify({
                'status': 'error',
                'message': 'Repository URL is required'
            }), 400
        
        # Initialize the system
        system = DeprecationIntelligenceSystem()
        
        # Run analysis
        report = system.run(repo_url)
        
        # Check for errors
        if 'error' in report:
            return jsonify({
                'status': 'error',
                'message': report['error']
            }), 400
        
        # Return success with data
        return jsonify({
            'status': 'success',
            'message': 'Analysis completed successfully',
            'data': report
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Dependency Analysis API'
    })


if __name__ == '__main__':
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    print("\n" + "=" * 70)
    print("Starting Dependency Analysis Web Server")
    print("=" * 70)
    print("\nServer running at: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
