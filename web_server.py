"""
Web API Server for Dependency Analysis System

Provides REST API endpoints for the frontend to interact with the analysis system.
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import threading
import json
from pathlib import Path

# Import the main system
from app import DeprecationIntelligenceSystem
from core.pathway_stream import EventBroadcaster

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Global event broadcaster for SSE
event_broadcaster = EventBroadcaster()

# Store analysis results temporarily
analysis_cache = {}


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/stream')
def stream():
    """
    Server-Sent Events (SSE) endpoint for real-time updates.
    Streams PyPI polling events and breaking changes to the browser.
    """
    def event_stream():
        """Generator that yields SSE formatted events."""
        client_queue = event_broadcaster.add_client()
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE connection established'})}\n\n"
            
            # Stream events as they come
            while True:
                try:
                    # Wait for event with timeout
                    event_data = client_queue.get(timeout=30)
                    yield f"data: {event_data}\n\n"
                except:
                    # Send keepalive ping every 30 seconds
                    yield f": keepalive\n\n"
        finally:
            event_broadcaster.remove_client(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/api/streaming/start', methods=['POST'])
def start_streaming():
    """
    Start the streaming system in a background thread.
    
    Request body:
    {
        "repo_url": "https://github.com/user/repo or /path/to/local",
        "poll_interval": 30  # optional
    }
    """
    try:
        data = request.get_json()
        repo_url = data.get('repo_url', '').strip()
        poll_interval = data.get('poll_interval', 30)
        
        if not repo_url:
            return jsonify({
                'status': 'error',
                'message': 'Repository URL is required'
            }), 400
        
        # Start streaming in background thread
        def run_streaming():
            # Initialize system WITH event broadcaster
            system = DeprecationIntelligenceSystem(
                poll_interval=poll_interval,
                event_broadcaster=event_broadcaster  # Pass the event bro   adcaster here
            )
            
            # Run streaming
            system.run_streaming(repo_url)
        
        # Start streaming in background thread
        thread = threading.Thread(target=run_streaming, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Streaming started successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start streaming: {str(e)}'
        }), 500


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
