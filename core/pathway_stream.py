"""
Pathway Real-Time Streaming Engine

This module implements a TRUE streaming system using Pathway to:
- Poll PyPI every 30 seconds for package updates
- Maintain repository dependencies as stateful tables
- Perform streaming joins to detect breaking changes in real-time
- Trigger callbacks for code scanning, impact mapping, and AI fixes

This is a real streaming implementation, not a batch process.
"""

import pathway as pw
import requests
import time
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from datetime import datetime
from packaging import version as pkg_version
import threading
import queue
import json


class EventBroadcaster:
    """
    Thread-safe event broadcaster for streaming events to web clients.
    Used to send real-time updates to the web dashboard via Server-Sent Events.
    """
    
    def __init__(self):
        self.clients = []  # List of queue objects for each client
        self._lock = threading.Lock()
    
    def add_client(self):
        """Add a new client and return their event queue."""
        client_queue = queue.Queue(maxsize=100)
        with self._lock:
            self.clients.append(client_queue)
        return client_queue
    
    def remove_client(self, client_queue):
        """Remove a client's queue."""
        with self._lock:
            if client_queue in self.clients:
                self.clients.remove(client_queue)
    
    def broadcast(self, event_type: str, data: dict):
        """
        Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event ('poll_start', 'package_update', 'breaking_change', 'pipeline_step')
            data: Event data dictionary
        """
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with self._lock:
            # Remove full queues to prevent blocking
            self.clients = [q for q in self.clients if not q.full()]
            
            # Broadcast to all clients
            for client_queue in self.clients:
                try:
                    client_queue.put_nowait(json.dumps(event))
                except queue.Full:
                    pass  # Skip full queues


@dataclass
class PyPIEvent:
    """Represents a PyPI package update event."""
    package_name: str
    latest_version: str
    timestamp: datetime
    
    
@dataclass
class RepoDepRecord:
    """Represents a repository dependency record."""
    package_name: str
    current_version: str
    

@dataclass
class BreakingChangeEvent:
    """Represents a detected breaking change."""
    package_name: str
    current_version: str
    latest_version: str
    timestamp: datetime
    

class PyPIStreamSource:
    """
    Simulates a live PyPI feed by polling every 30 seconds.
    Emits events: {package, new_version, timestamp}
    """
    
    def __init__(self, packages: Set[str], poll_interval: int = 30, event_broadcaster: Optional[EventBroadcaster] = None):
        """
        Initialize PyPI stream source.
        
        Args:
            packages: Set of package names to monitor
            poll_interval: Polling interval in seconds (default: 30)
            event_broadcaster: Optional event broadcaster for web streaming
        """
        self.packages = packages
        self.poll_interval = poll_interval
        self.pypi_cache: Dict[str, str] = {}
        self._running = False
        self.event_broadcaster = event_broadcaster
        
    def fetch_latest_version(self, package_name: str) -> Optional[str]:
        """Fetch latest version from PyPI."""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data['info'].get('version')
            else:
                return None
        except Exception as e:
            print(f"[WARNING] Error fetching {package_name}: {e}")
            return None
    
    def generate_events(self):
        """
        Generator that yields PyPI events.
        This is called by Pathway's python connector.
        """
        print(f"[INFO] Starting PyPI stream for {len(self.packages)} packages")
        print(f"[INFO] Polling interval: {self.poll_interval} seconds")
        
        self._running = True
        
        while self._running:
            timestamp = datetime.now()
            print(f"\n[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Polling PyPI...")
            
            # Broadcast poll start event
            if self.event_broadcaster:
                self.event_broadcaster.broadcast('poll_start', {
                    'package_count': len(self.packages)
                })
            
            events = []
            for package_name in self.packages:
                latest_version = self.fetch_latest_version(package_name)
                
                if latest_version:
                    # Check if this is a new/changed version
                    cached_version = self.pypi_cache.get(package_name)
                    
                    if cached_version != latest_version:
                        # Display previous version or "first fetch" message
                        if cached_version:
                            print(f"  📦 {package_name}: {cached_version} → {latest_version}")
                            display_msg = f"{cached_version} → {latest_version}"
                        else:
                            print(f"  📦 {package_name}: {latest_version} (first fetch)")
                            display_msg = f"{latest_version} (first fetch)"
                        
                        self.pypi_cache[package_name] = latest_version
                        
                        # Broadcast version change with formatted display message
                        if self.event_broadcaster:
                            self.event_broadcaster.broadcast('package_update', {
                                'package_name': package_name,
                                'previous_version': cached_version if cached_version else '',
                                'latest_version': latest_version,
                                'display_message': display_msg,  # Formatted message for frontend
                                'is_first_fetch': cached_version is None
                            })
                    else:
                        # Version unchanged, just log for debugging
                        print(f"  - {package_name}: {latest_version} (unchanged)")
                    
                    # Always emit current state
                    events.append({
                        'package_name': package_name,
                        'latest_version': latest_version,
                        'timestamp': timestamp
                    })
                else:
                    print(f"  ✗ {package_name}: not found on PyPI")
                
                # Rate limiting
                time.sleep(0.5)
            
            # Yield all events (convert timestamp to int for Pathway)
            for event in events:
                # Convert datetime to Unix timestamp
                event_copy = event.copy()
                event_copy['timestamp'] = int(event['timestamp'].timestamp())
                yield event_copy
            
            print(f"[INFO] Emitted {len(events)} PyPI events. Waiting {self.poll_interval}s...")
            
            # Wait for next poll
            time.sleep(self.poll_interval)
    
    def stop(self):
        """Stop the stream."""
        self._running = False


class VersionChecker:
    """Version comparison utilities."""
    
    @staticmethod
    def parse_version(version_str: str) -> Optional[pkg_version.Version]:
        """Parse a version string."""
        try:
            return pkg_version.parse(version_str)
        except Exception:
            return None
    
    @staticmethod
    def is_breaking_change(current: str, latest: str) -> bool:
        """
        Check if upgrade is a breaking change (major version bump).
        
        Args:
            current: Current version
            latest: Latest version
            
        Returns:
            True if breaking change
        """
        try:
            current_ver = VersionChecker.parse_version(current)
            latest_ver = VersionChecker.parse_version(latest)
            
            if not current_ver or not latest_ver:
                return False
            
            return latest_ver.major > current_ver.major
        except Exception:
            return False
    
    @staticmethod
    def compare_versions(current: str, latest: str) -> str:
        """
        Compare versions and return status.
        
        Returns:
            'up-to-date', 'outdated', or 'breaking'
        """
        try:
            current_ver = VersionChecker.parse_version(current)
            latest_ver = VersionChecker.parse_version(latest)
            
            if not current_ver or not latest_ver:
                return 'unknown'
            
            if current_ver == latest_ver:
                return 'up-to-date'
            elif current_ver < latest_ver:
                if VersionChecker.is_breaking_change(current, latest):
                    return 'breaking'
                else:
                    return 'outdated'
            else:
                return 'ahead'
        except Exception:
            return 'unknown'


class PathwayStreamEngine:
    """
    Real-time streaming engine using Pathway.
    
    Maintains:
    - Static table of repo dependencies
    - Streaming table of PyPI updates
    - Streaming join to detect breaking changes
    """
    
    def __init__(self, poll_interval: int = 30, event_broadcaster: Optional[EventBroadcaster] = None):
        """
        Initialize the streaming engine.
        
        Args:
            poll_interval: PyPI polling interval in seconds
            event_broadcaster: Optional event broadcaster for web streaming
        """
        self.poll_interval = poll_interval
        self.repo_dependencies: Dict[str, str] = {}
        self.pypi_source: Optional[PyPIStreamSource] = None
        self.breaking_change_callback: Optional[Callable] = None
        self.event_broadcaster = event_broadcaster
        self._initialized = False
        
    def load_repo_dependencies(self, dependencies: Dict) -> None:
        """
        Load repository dependencies.
        
        Args:
            dependencies: Dict mapping package names to Dependency objects or version strings
        """
        print("\n[INFO] Loading repository dependencies into Pathway...")
        self.repo_dependencies = {}
        
        for name, dep in dependencies.items():
            # Handle both Dependency objects and version strings
            if hasattr(dep, 'version'):
                version = dep.version
            else:
                version = dep  # Assume it's already a version string
            
            if version and version != "N/A":
                self.repo_dependencies[name] = version
                print(f"  ✓ {name}: {version}")
            else:
                print(f"  ✗ {name}: version not specified (N/A)")
                # Use a placeholder version for packages without version
                # This is important for the streaming join to work
                self.repo_dependencies[name] = "0.0.0"
        
        print(f"[OK] Loaded {len(self.repo_dependencies)} dependencies into Pathway")
    
    def fetch_pypi_updates(self) -> None:
        """
        Fetch latest versions from PyPI for all dependencies (batch mode).
        This is a one-time fetch, not continuous streaming.
        """
        print("[INFO] Fetching latest versions from PyPI...")
        
        if not self.repo_dependencies:
            raise ValueError("No dependencies loaded. Call load_repo_dependencies() first.")
        
        # Create PyPI source without continuous polling (just one fetch)
        package_names = set(self.repo_dependencies.keys())
        temp_source = PyPIStreamSource(package_names, poll_interval=0)
        
        # Store updates for batch mode
        self._batch_updates = []
        
        for package_name in package_names:
            latest_version = temp_source.fetch_latest_version(package_name)
            if latest_version:
                current_version = self.repo_dependencies[package_name]
                print(f"  ✓ {package_name}: {current_version} → {latest_version}")
                self._batch_updates.append({
                    'package_name': package_name,
                    'latest_version': latest_version,
                    'current_version': current_version
                })
            else:
                print(f"  ✗ {package_name}: not found on PyPI")
        
        print(f"[OK] Fetched {len(self._batch_updates)} package updates")
    
    def perform_streaming_join(self) -> List:
        """
        Perform version comparison (batch mode equivalent of streaming join).
        
        Returns:
            List of PackageUpdate objects with version comparison results
        """
        if not hasattr(self, '_batch_updates'):
            raise ValueError("No updates available. Call fetch_pypi_updates() first.")
        
        from dataclasses import dataclass
        
        @dataclass
        class PackageUpdate:
            package_name: str
            current_version: str
            latest_version: str
            status: str
            is_breaking: bool
        
        results = []
        
        for update in self._batch_updates:
            status = VersionChecker.compare_versions(
                update['current_version'], 
                update['latest_version']
            )
            is_breaking = VersionChecker.is_breaking_change(
                update['current_version'], 
                update['latest_version']
            )
            
            results.append(PackageUpdate(
                package_name=update['package_name'],
                current_version=update['current_version'],
                latest_version=update['latest_version'],
                status=status,
                is_breaking=is_breaking
            ))
        
        return results
    
    def get_breaking_packages(self) -> List:
        """
        Get list of packages with breaking changes (batch mode).
        
        Returns:
            List of PackageUpdate objects with breaking changes
        """
        if not hasattr(self, '_batch_updates'):
            return []
        
        all_updates = self.perform_streaming_join()
        return [u for u in all_updates if u.is_breaking]
    
    def get_outdated_packages(self) -> List:
        """
        Get list of outdated packages (non-breaking) (batch mode).
        
        Returns:
            List of PackageUpdate objects that are outdated but not breaking
        """
        if not hasattr(self, '_batch_updates'):
            return []
        
        all_updates = self.perform_streaming_join()
        return [u for u in all_updates if u.status == 'outdated']
        
    def register_breaking_change_callback(self, callback: Callable[[BreakingChangeEvent], None]) -> None:
        """
        Register callback for breaking change events.
        
        Args:
            callback: Function to call when breaking change is detected
        """
        self.breaking_change_callback = callback
        print("[INFO] Registered breaking change callback")
    
    def start_streaming(self) -> None:
        """
        Start the Pathway streaming computation.
        This blocks and runs continuously until interrupted.
        """
        if not self.repo_dependencies:
            raise ValueError("No dependencies loaded. Call load_repo_dependencies() first.")
        
        print("\n" + "=" * 70)
        print("STARTING REAL-TIME PATHWAY STREAMING SYSTEM")
        print("=" * 70)
        print(f"Monitoring {len(self.repo_dependencies)} packages:")
        for pkg, ver in self.repo_dependencies.items():
            if ver == "0.0.0":
                print(f"  - {pkg}: version not specified (using 0.0.0)")
            else:
                print(f"  - {pkg}: {ver}")
        print(f"\nPoll interval: {self.poll_interval} seconds")
        print("Press CTRL+C to stop")
        print("=" * 70)
        
        # Create PyPI stream source
        package_names = set(self.repo_dependencies.keys())
        self.pypi_source = PyPIStreamSource(package_names, self.poll_interval, self.event_broadcaster)
        
        # Define Pathway schema classes
        class RepoDepSchema(pw.Schema):
            package_name: str
            current_version: str
        
        class PyPIUpdateSchema(pw.Schema):
            package_name: str
            latest_version: str
            timestamp: int  # Unix timestamp
        
        # Create static table for repo dependencies
        repo_data = [
            (pkg, ver)
            for pkg, ver in self.repo_dependencies.items()
        ]
        print(f"\n[DEBUG] Creating repo_deps_table with {len(repo_data)} entries:")
        for pkg, ver in repo_data:
            print(f"  - {pkg}: {ver}")
        
        repo_deps_table = pw.debug.table_from_rows(
            schema=RepoDepSchema,
            rows=repo_data
        )
        
        # Create streaming table for PyPI updates using a custom connector
        class PyPIConnector(pw.io.python.ConnectorSubject):
            def __init__(self, source: PyPIStreamSource):
                super().__init__()
                self.source = source
            
            def run(self):
                """Implementation of the abstract run method."""
                for event in self.source.generate_events():
                    self.next(**event)
        
        connector = PyPIConnector(self.pypi_source)
        
        pypi_stream_table = pw.io.python.read(
            connector,
            schema=PyPIUpdateSchema,
            autocommit_duration_ms=1000
        )
        
        # Perform streaming join
        joined = repo_deps_table.join(
            pypi_stream_table,
            repo_deps_table.package_name == pypi_stream_table.package_name
        ).select(
            repo_deps_table.package_name,
            current_version=repo_deps_table.current_version,
            latest_version=pypi_stream_table.latest_version,
            timestamp=pypi_stream_table.timestamp
        )
        
        # Add computed columns for version comparison
        def compute_status(current: str, latest: str) -> str:
            result = VersionChecker.compare_versions(current, latest)
            return result
        
        def compute_is_breaking(current: str, latest: str) -> bool:
            result = VersionChecker.is_breaking_change(current, latest)
            return result
        
        result = joined.select(
            *pw.this,
            status=pw.apply(compute_status, pw.this.current_version, pw.this.latest_version),
            is_breaking=pw.apply(compute_is_breaking, pw.this.current_version, pw.this.latest_version)
        )
        
        # Filter for breaking changes only
        breaking_changes = result.filter(pw.this.is_breaking == True)
        
        # Define output handler
        def on_change(key, row, time, is_addition):
            """Handler called by Pathway on every table update."""
            if is_addition and row is not None:
                # Convert Unix timestamp back to datetime
                timestamp = datetime.fromtimestamp(row['timestamp'])
                
                # Get the actual current version from dependencies
                current_version = self.repo_dependencies.get(row['package_name'], "0.0.0")
                if current_version == "0.0.0":
                    # Try to find it from the app's parsed dependencies
                    current_version = row['current_version']
                
                event = BreakingChangeEvent(
                    package_name=row['package_name'],
                    current_version=current_version,
                    latest_version=row['latest_version'],
                    timestamp=timestamp
                )
                
                # Log the breaking change
                print(f"\n{'='*70}")
                print(f"🚨 BREAKING CHANGE DETECTED!")
                print(f"{'='*70}")
                print(f"[{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]")
                print(f"Package: {event.package_name}")
                print(f"Current: {event.current_version}")
                print(f"Latest: {event.latest_version}")
                print(f"Status: BREAKING")
                print(f"{'='*70}\n")
                
                # Broadcast breaking change to web clients
                if self.event_broadcaster:
                    self.event_broadcaster.broadcast('breaking_change', {
                        'package_name': event.package_name,
                        'current_version': event.current_version,
                        'latest_version': event.latest_version,
                        'timestamp': event.timestamp.isoformat(),
                        'display_message': f"{event.current_version} → {event.latest_version}"
                    })
                
                # Trigger callback pipeline
                if self.breaking_change_callback:
                    try:
                        self.breaking_change_callback(event)
                    except Exception as e:
                        print(f"[ERROR] Callback failed: {e}")
                        import traceback
                        traceback.print_exc()
        
        # Subscribe to changes
        pw.io.subscribe(breaking_changes, on_change)
        
        # Also output all results for debugging
        pw.io.jsonlines.write(result, "/dev/null")  # Dummy output to keep computation active
        
        # Run the streaming computation (blocks here)
        try:
            pw.run()
        except KeyboardInterrupt:
            print("\n\n[INFO] Shutting down gracefully...")
            if self.pypi_source:
                self.pypi_source.stop()
            print("[OK] Streaming engine stopped")


def main():
    """Test the streaming engine."""
    print("Testing Pathway Streaming Engine")
    
    # Mock dependencies for testing
    from core.dep_parser import Dependency
    
    mock_deps = {
        'requests': Dependency(
            name='requests',
            raw_name='requests',
            version_spec='==2.28.0',
            version='2.28.0',
            operator='==',
            source_file='requirements.txt',
            line_number=1
        ),
        'flask': Dependency(
            name='flask',
            raw_name='flask',
            version_spec='==2.0.0',
            version='2.0.0',
            operator='==',
            source_file='requirements.txt',
            line_number=2
        ),
    }
    
    def test_callback(event: BreakingChangeEvent):
        print(f"[CALLBACK] Triggered for {event.package_name}")
        print(f"[CALLBACK] Current: {event.current_version}, Latest: {event.latest_version}")
    
    # Initialize engine with shorter interval for testing
    engine = PathwayStreamEngine(poll_interval=10)
    engine.load_repo_dependencies(mock_deps)
    engine.register_breaking_change_callback(test_callback)
    
    # Start streaming (will run forever)
    engine.start_streaming()


if __name__ == "__main__":
    main()