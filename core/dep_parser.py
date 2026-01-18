"""
Dependency Parser Module

Automatically detects and parses all requirements*.txt files in a repository.
Extracts Python dependencies with their pinned versions.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Dependency:
    """
    Represents a Python package dependency.
    
    Attributes:
        name: Package name (normalized)
        raw_name: Original package name as specified
        version_spec: Version specifier (e.g., ==1.2.3, >=2.0.0)
        version: Extracted version number
        operator: Comparison operator (==, >=, <=, ~=, etc.)
        source_file: Requirements file where this dependency was found
        line_number: Line number in the source file
    """
    name: str
    raw_name: str
    version_spec: Optional[str]
    version: Optional[str]
    operator: Optional[str]
    source_file: str
    line_number: int
    
    def __repr__(self):
        if self.version_spec:
            return f"{self.name}{self.version_spec}"
        return self.name


class DependencyParser:
    """
    Parses Python requirements files and extracts dependencies.
    
    Features:
    - Auto-detect all requirements*.txt files
    - Parse various version specifier formats
    - Normalize package names
    - Handle comments and blank lines
    - Merge dependencies from multiple files
    """
    
    # Regex pattern for parsing requirement lines
    # Matches: package-name==1.2.3, package>=2.0, package[extra]==1.0, etc.
    REQUIREMENT_PATTERN = re.compile(
        r'^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)'  # Package name
        r'(\[[a-zA-Z0-9,_-]+\])?'                        # Optional extras [dev,test]
        r'\s*'                                            # Optional whitespace
        r'([=<>!~]=?)?'                                   # Optional operator
        r'\s*'                                            # Optional whitespace
        r'([0-9a-zA-Z.*+-]+)?'                           # Optional version
    )
    
    def __init__(self):
        """Initialize the DependencyParser."""
        self.dependencies: Dict[str, Dependency] = {}
    
    def find_requirements_files(self, repo_path: Path) -> List[Path]:
        """
        Find all requirements*.txt files in the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            List of paths to requirements files
        """
        requirements_files = []
        
        # Common requirements file patterns
        patterns = [
            "requirements.txt",
            "requirements-*.txt",
            "requirements/*.txt",
        ]
        
        for pattern in patterns:
            requirements_files.extend(repo_path.glob(pattern))
        
        # Sort for consistent ordering
        requirements_files = sorted(set(requirements_files))
        
        return requirements_files
    
    def parse_file(self, file_path: Path) -> List[Dependency]:
        """
        Parse a single requirements file.
        
        Args:
            file_path: Path to requirements file
            
        Returns:
            List of dependencies found in the file
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    dep = self._parse_line(line, str(file_path), line_num)
                    if dep:
                        dependencies.append(dep)
        except Exception as e:
            print(f"[WARNING] Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def _parse_line(self, line: str, source_file: str, line_number: int) -> Optional[Dependency]:
        """
        Parse a single line from a requirements file.
        
        Args:
            line: Line to parse
            source_file: Source file path
            line_number: Line number in source file
            
        Returns:
            Dependency object or None if line is invalid/comment
        """
        # Remove comments
        line = line.split('#')[0].strip()
        
        # Skip empty lines
        if not line:
            return None
        
        # Skip -r, -e, --index-url, etc.
        if line.startswith('-') or line.startswith('--'):
            return None
        
        # Skip git+, http://, https:// URLs
        if any(line.startswith(prefix) for prefix in ['git+', 'http://', 'https://', 'svn+', 'hg+']):
            return None
        
        # Match the requirement pattern
        match = self.REQUIREMENT_PATTERN.match(line)
        if not match:
            return None
        
        raw_name = match.group(1)
        extras = match.group(3)  # [extra] part
        operator = match.group(4)
        version = match.group(5)
        
        # Normalize package name (lowercase, replace _ with -)
        normalized_name = self._normalize_package_name(raw_name)
        
        # Build version spec
        version_spec = None
        if operator and version:
            version_spec = f"{operator}{version}"
        
        return Dependency(
            name=normalized_name,
            raw_name=raw_name,
            version_spec=version_spec,
            version=version,
            operator=operator,
            source_file=source_file,
            line_number=line_number
        )
    
    def _normalize_package_name(self, name: str) -> str:
        """
        Normalize package name according to PEP 503.
        
        Args:
            name: Package name
            
        Returns:
            Normalized package name
        """
        # Convert to lowercase and replace _ with -
        return re.sub(r'[-_.]+', '-', name).lower()
    
    def parse_repository(self, repo_path: Path) -> Dict[str, Dependency]:
        """
        Parse all requirements files in a repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary mapping package names to Dependency objects
        """
        self.dependencies = {}
        
        # Find all requirements files
        requirements_files = self.find_requirements_files(repo_path)
        
        if not requirements_files:
            print("[WARNING] No requirements files found in repository")
            return self.dependencies
        
        print(f"[INFO] Found {len(requirements_files)} requirements file(s):")
        for req_file in requirements_files:
            print(f"  - {req_file.relative_to(repo_path)}")
        
        # Parse each file
        for req_file in requirements_files:
            deps = self.parse_file(req_file)
            
            # Merge dependencies (later files override earlier ones)
            for dep in deps:
                if dep.name in self.dependencies:
                    # Dependency already exists, check if we should override
                    existing = self.dependencies[dep.name]
                    print(f"[INFO] Duplicate dependency '{dep.name}' found:")
                    print(f"  - {existing.source_file}:{existing.line_number} -> {existing.version_spec}")
                    print(f"  - {dep.source_file}:{dep.line_number} -> {dep.version_spec}")
                    print(f"  Using: {dep.source_file}")
                
                self.dependencies[dep.name] = dep
        
        print(f"\n[OK] Parsed {len(self.dependencies)} unique dependencies")
        return self.dependencies
    
    def get_dependency(self, package_name: str) -> Optional[Dependency]:
        """
        Get a specific dependency by name.
        
        Args:
            package_name: Package name (will be normalized)
            
        Returns:
            Dependency object or None if not found
        """
        normalized = self._normalize_package_name(package_name)
        return self.dependencies.get(normalized)
    
    def get_all_dependencies(self) -> List[Dependency]:
        """
        Get all parsed dependencies.
        
        Returns:
            List of all dependencies
        """
        return list(self.dependencies.values())
    
    def get_pinned_dependencies(self) -> List[Dependency]:
        """
        Get only dependencies with pinned versions (==).
        
        Returns:
            List of pinned dependencies
        """
        return [dep for dep in self.dependencies.values() if dep.operator == '==']
    
    def get_unpinned_dependencies(self) -> List[Dependency]:
        """
        Get dependencies without version specifications or with flexible versions.
        
        Returns:
            List of unpinned dependencies
        """
        return [dep for dep in self.dependencies.values() if dep.operator != '==']
    
    def export_summary(self) -> Dict:
        """
        Export a summary of parsed dependencies.
        
        Returns:
            Dictionary with dependency statistics
        """
        all_deps = self.get_all_dependencies()
        pinned = self.get_pinned_dependencies()
        unpinned = self.get_unpinned_dependencies()
        
        return {
            'total_dependencies': len(all_deps),
            'pinned_dependencies': len(pinned),
            'unpinned_dependencies': len(unpinned),
            'dependencies': [
                {
                    'name': dep.name,
                    'version_spec': dep.version_spec,
                    'source': dep.source_file,
                    'line': dep.line_number
                }
                for dep in all_deps
            ]
        }


def main():
    """
    Test the DependencyParser module.
    """
    print("=" * 60)
    print("Testing DependencyParser")
    print("=" * 60)
    
    # Create a test requirements file
    test_dir = Path(".")
    test_req_file = test_dir / "requirements.txt"
    
    # Create sample requirements file if it doesn't exist
    if not test_req_file.exists():
        print("\n[INFO] Creating sample requirements.txt for testing...")
        with open(test_req_file, 'w') as f:
            f.write("""# Sample requirements file
requests==2.28.1
numpy>=1.24.0
pandas==1.5.3
flask~=2.0.0
# Development dependencies
pytest>=7.0.0
black==22.10.0
""")
        print(f"[OK] Created {test_req_file}")
    
    # Parse the repository
    parser = DependencyParser()
    dependencies = parser.parse_repository(test_dir)
    
    # Display results
    print("\n" + "=" * 60)
    print("Parsed Dependencies:")
    print("=" * 60)
    
    for dep in parser.get_all_dependencies():
        print(f"\n{dep.name}:")
        print(f"  Version: {dep.version_spec or 'not specified'}")
        print(f"  Source: {dep.source_file}:{dep.line_number}")
    
    # Display summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    summary = parser.export_summary()
    print(f"Total dependencies: {summary['total_dependencies']}")
    print(f"Pinned (==): {summary['pinned_dependencies']}")
    print(f"Unpinned: {summary['unpinned_dependencies']}")


if __name__ == "__main__":
    main()
