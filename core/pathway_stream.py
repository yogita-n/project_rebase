"""
Pathway Streaming Engine Module

Implements streaming data processing using Pathway to:
- Create streaming table for PyPI releases
- Create static table for repository dependencies
- Perform streaming joins to detect outdated and breaking changes
"""

# Pathway is optional for this simplified implementation
try:
    import pathway as pw
    PATHWAY_AVAILABLE = True
except ImportError:
    PATHWAY_AVAILABLE = False
    print("[INFO] Pathway not installed. Using simplified streaming simulation.")

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import requests
import time
from datetime import datetime
from packaging import version as pkg_version


@dataclass
class PackageUpdate:
    """
    Represents a package update event.
    
    Attributes:
        package_name: Name of the package
        current_version: Current version in repository
        latest_version: Latest version on PyPI
        status: 'up-to-date', 'outdated', or 'breaking'
        is_breaking: Whether this is a breaking change (major version bump)
        timestamp: When this update was detected
    """
    package_name: str
    current_version: Optional[str]
    latest_version: str
    status: str
    is_breaking: bool
    timestamp: datetime


class PyPIClient:
    """
    Client for fetching package information from PyPI.
    """
    
    BASE_URL = "https://pypi.org/pypi"
    
    @staticmethod
    def get_package_info(package_name: str) -> Optional[Dict]:
        """
        Fetch package information from PyPI.
        
        Args:
            package_name: Name of the package
            
        Returns:
            Package info dict or None if not found
        """
        try:
            url = f"{PyPIClient.BASE_URL}/{package_name}/json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"[WARNING] Package '{package_name}' not found on PyPI")
                return None
            else:
                print(f"[WARNING] Failed to fetch {package_name}: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"[WARNING] Error fetching {package_name}: {e}")
            return None
    
    @staticmethod
    def get_latest_version(package_name: str) -> Optional[str]:
        """
        Get the latest version of a package from PyPI.
        
        Args:
            package_name: Name of the package
            
        Returns:
            Latest version string or None if not found
        """
        info = PyPIClient.get_package_info(package_name)
        if info and 'info' in info:
            return info['info'].get('version')
        return None
    
    @staticmethod
    def get_all_versions(package_name: str) -> List[str]:
        """
        Get all available versions of a package from PyPI.
        
        Args:
            package_name: Name of the package
            
        Returns:
            List of version strings
        """
        info = PyPIClient.get_package_info(package_name)
        if info and 'releases' in info:
            return list(info['releases'].keys())
        return []


class VersionChecker:
    """
    Handles version comparison and breaking change detection.
    """
    
    @staticmethod
    def parse_version(version_str: str) -> Optional[pkg_version.Version]:
        """
        Parse a version string into a Version object.
        
        Args:
            version_str: Version string (e.g., "1.2.3")
            
        Returns:
            Version object or None if invalid
        """
        try:
            return pkg_version.parse(version_str)
        except Exception:
            return None
    
    @staticmethod
    def is_breaking_change(current: str, latest: str) -> bool:
        """
        Determine if upgrading from current to latest is a breaking change.
        Breaking change = major version bump (1.x.x -> 2.x.x)
        
        Args:
            current: Current version string
            latest: Latest version string
            
        Returns:
            True if breaking change, False otherwise
        """
        try:
            current_ver = VersionChecker.parse_version(current)
            latest_ver = VersionChecker.parse_version(latest)
            
            if not current_ver or not latest_ver:
                return False
            
            # Extract major version
            # For versions like "1.2.3", major is 1
            # For versions like "0.1.2", major is 0 (special case)
            current_major = current_ver.major
            latest_major = latest_ver.major
            
            # Breaking change if major version increased
            return latest_major > current_major
            
        except Exception:
            return False
    
    @staticmethod
    def compare_versions(current: str, latest: str) -> str:
        """
        Compare two versions and return status.
        
        Args:
            current: Current version string
            latest: Latest version string
            
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
                return 'ahead'  # Current version is ahead of PyPI (unusual)
                
        except Exception:
            return 'unknown'


class PathwayStreamEngine:
    """
    Pathway-based streaming engine for dependency monitoring.
    
    Note: This is a simplified implementation that simulates streaming behavior.
    In a production environment, this would use Pathway's full streaming capabilities
    with real-time data sources.
    """
    
    def __init__(self):
        """Initialize the streaming engine."""
        self.repo_dependencies: Dict[str, str] = {}
        self.pypi_cache: Dict[str, str] = {}
        self.updates: List[PackageUpdate] = []
    
    def load_repo_dependencies(self, dependencies: Dict) -> None:
        """
        Load repository dependencies into the engine.
        
        Args:
            dependencies: Dict mapping package names to Dependency objects
        """
        print("[INFO] Loading repository dependencies...")
        self.repo_dependencies = {}
        
        for name, dep in dependencies.items():
            if dep.version:
                self.repo_dependencies[name] = dep.version
                print(f"  - {name}: {dep.version}")
            else:
                print(f"  - {name}: (no version specified)")
        
        print(f"[OK] Loaded {len(self.repo_dependencies)} dependencies with versions")
    
    def fetch_pypi_updates(self) -> None:
        """
        Fetch latest versions from PyPI for all dependencies.
        This simulates a streaming data source.
        """
        print("\n[INFO] Fetching latest versions from PyPI...")
        self.pypi_cache = {}
        
        for package_name in self.repo_dependencies.keys():
            print(f"  - Checking {package_name}...", end=" ")
            latest = PyPIClient.get_latest_version(package_name)
            
            if latest:
                self.pypi_cache[package_name] = latest
                print(f"latest: {latest}")
            else:
                print("not found")
            
            # Rate limiting to avoid overwhelming PyPI
            time.sleep(0.5)
        
        print(f"[OK] Fetched {len(self.pypi_cache)} package versions from PyPI")
    
    def perform_streaming_join(self) -> List[PackageUpdate]:
        """
        Perform a streaming join between repo dependencies and PyPI data.
        Detects outdated and breaking changes.
        
        Returns:
            List of PackageUpdate objects
        """
        print("\n[INFO] Performing streaming join: repo_deps × pypi_feed")
        self.updates = []
        
        for package_name, current_version in self.repo_dependencies.items():
            latest_version = self.pypi_cache.get(package_name)
            
            if not latest_version:
                # Package not found on PyPI
                continue
            
            # Compare versions
            status = VersionChecker.compare_versions(current_version, latest_version)
            is_breaking = VersionChecker.is_breaking_change(current_version, latest_version)
            
            update = PackageUpdate(
                package_name=package_name,
                current_version=current_version,
                latest_version=latest_version,
                status=status,
                is_breaking=is_breaking,
                timestamp=datetime.now()
            )
            
            self.updates.append(update)
            
            # Log the result
            if status == 'breaking':
                print(f"  [BREAKING] {package_name}: {current_version} -> {latest_version}")
            elif status == 'outdated':
                print(f"  [OUTDATED] {package_name}: {current_version} -> {latest_version}")
            elif status == 'up-to-date':
                print(f"  [OK] {package_name}: {current_version} (up-to-date)")
        
        print(f"\n[OK] Detected {len(self.updates)} package updates")
        return self.updates
    
    def get_outdated_packages(self) -> List[PackageUpdate]:
        """Get all outdated packages (non-breaking)."""
        return [u for u in self.updates if u.status == 'outdated']
    
    def get_breaking_packages(self) -> List[PackageUpdate]:
        """Get all packages with breaking changes."""
        return [u for u in self.updates if u.status == 'breaking']
    
    def get_uptodate_packages(self) -> List[PackageUpdate]:
        """Get all up-to-date packages."""
        return [u for u in self.updates if u.status == 'up-to-date']
    
    def export_summary(self) -> Dict:
        """
        Export a summary of the streaming analysis.
        
        Returns:
            Dictionary with update statistics
        """
        return {
            'total_packages': len(self.updates),
            'up_to_date': len(self.get_uptodate_packages()),
            'outdated': len(self.get_outdated_packages()),
            'breaking': len(self.get_breaking_packages()),
            'updates': [
                {
                    'package': u.package_name,
                    'current_version': u.current_version,
                    'latest_version': u.latest_version,
                    'status': u.status,
                    'is_breaking': u.is_breaking
                }
                for u in self.updates
            ]
        }


def main():
    """
    Test the Pathway Streaming Engine.
    """
    print("=" * 60)
    print("Testing Pathway Streaming Engine")
    print("=" * 60)
    
    # Create mock dependencies for testing
    # Import locally to avoid circular import issues
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
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
    
    # Initialize engine
    engine = PathwayStreamEngine()
    
    # Load dependencies
    engine.load_repo_dependencies(mock_deps)
    
    # Fetch PyPI updates
    engine.fetch_pypi_updates()
    
    # Perform streaming join
    updates = engine.perform_streaming_join()
    
    # Display summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    summary = engine.export_summary()
    print(f"Total packages: {summary['total_packages']}")
    print(f"Up-to-date: {summary['up_to_date']}")
    print(f"Outdated: {summary['outdated']}")
    print(f"Breaking changes: {summary['breaking']}")


if __name__ == "__main__":
    main()
