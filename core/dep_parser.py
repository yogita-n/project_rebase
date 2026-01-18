"""
Enhanced Dependency Parser Module

Supports multiple dependency file formats:
- requirements.txt
- pyproject.toml
- setup.py
- Pipfile
- setup.cfg
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Optional: for TOML parsing
try:
    import tomli as toml  # Python < 3.11
except ImportError:
    try:
        import tomllib as toml  # Python 3.11+
    except ImportError:
        toml = None


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
        source_file: File where this dependency was found
        line_number: Line number in the source file
        source_type: Type of dependency file (requirements, pyproject, setup, pipfile)
    """
    name: str
    raw_name: str
    version_spec: Optional[str]
    version: Optional[str]
    operator: Optional[str]
    source_file: str
    line_number: int
    source_type: str = "requirements"
    
    def __repr__(self):
        if self.version_spec:
            return f"{self.name}{self.version_spec}"
        return self.name


class DependencyParser:
    """
    Enhanced parser for Python dependency files.
    
    Supports:
    - requirements.txt
    - pyproject.toml (Poetry, PDM, Hatch)
    - setup.py
    - Pipfile
    - setup.cfg
    """
    
    REQUIREMENT_PATTERN = re.compile(
        r'^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)'
        r'(\[[a-zA-Z0-9,_-]+\])?'
        r'\s*'
        r'([=<>!~]=?)?'
        r'\s*'
        r'([0-9a-zA-Z.*+-]+)?'
    )
    
    def __init__(self):
        """Initialize the DependencyParser."""
        self.dependencies: Dict[str, Dependency] = {}
    
    def find_dependency_files(self, repo_path: Path) -> Dict[str, List[Path]]:
        """
        Find all dependency files in the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary mapping file types to paths
        """
        files = {
            'requirements': [],
            'pyproject': [],
            'setup_py': [],
            'setup_cfg': [],
            'pipfile': []
        }
        
        # requirements.txt files
        for pattern in ["requirements.txt", "requirements-*.txt", "requirements/*.txt"]:
            files['requirements'].extend(repo_path.glob(pattern))
        
        # pyproject.toml
        files['pyproject'].extend(repo_path.glob("pyproject.toml"))
        
        # setup.py
        files['setup_py'].extend(repo_path.glob("setup.py"))
        
        # setup.cfg
        files['setup_cfg'].extend(repo_path.glob("setup.cfg"))
        
        # Pipfile
        files['pipfile'].extend(repo_path.glob("Pipfile"))
        
        # Remove duplicates and sort
        for key in files:
            files[key] = sorted(set(files[key]))
        
        return files
    
    # ========================================================================
    # REQUIREMENTS.TXT PARSING
    # ========================================================================
    
    def parse_requirements_file(self, file_path: Path) -> List[Dependency]:
        """Parse a requirements.txt file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    dep = self._parse_requirement_line(line, str(file_path), line_num)
                    if dep:
                        dependencies.append(dep)
        except Exception as e:
            print(f"[WARNING] Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def _parse_requirement_line(self, line: str, source_file: str, line_number: int) -> Optional[Dependency]:
        """Parse a single line from requirements.txt."""
        line = line.split('#')[0].strip()
        
        if not line or line.startswith('-') or line.startswith('--'):
            return None
        
        if any(line.startswith(prefix) for prefix in ['git+', 'http://', 'https://', 'svn+', 'hg+']):
            return None
        
        match = self.REQUIREMENT_PATTERN.match(line)
        if not match:
            return None
        
        raw_name = match.group(1)
        operator = match.group(4)
        version = match.group(5)
        
        normalized_name = self._normalize_package_name(raw_name)
        version_spec = f"{operator}{version}" if operator and version else None
        
        return Dependency(
            name=normalized_name,
            raw_name=raw_name,
            version_spec=version_spec,
            version=version,
            operator=operator,
            source_file=source_file,
            line_number=line_number,
            source_type="requirements"
        )
    
    # ========================================================================
    # PYPROJECT.TOML PARSING
    # ========================================================================
    
    def parse_pyproject_toml(self, file_path: Path) -> List[Dependency]:
        """Parse a pyproject.toml file."""
        if toml is None:
            print(f"[WARNING] tomli/tomllib not available, skipping {file_path}")
            print("  Install with: pip install tomli")
            return []
        
        dependencies = []
        
        try:
            with open(file_path, 'rb') as f:
                data = toml.load(f)
            
            # Poetry format: [tool.poetry.dependencies]
            if 'tool' in data and 'poetry' in data['tool']:
                poetry_deps = data['tool']['poetry'].get('dependencies', {})
                for name, version_spec in poetry_deps.items():
                    if name == 'python':  # Skip python version
                        continue
                    
                    dep = self._parse_poetry_dependency(name, version_spec, str(file_path))
                    if dep:
                        dependencies.append(dep)
            
            # PEP 621 format: [project.dependencies]
            if 'project' in data and 'dependencies' in data['project']:
                for dep_string in data['project']['dependencies']:
                    dep = self._parse_pep621_dependency(dep_string, str(file_path))
                    if dep:
                        dependencies.append(dep)
            
            # PDM format: [tool.pdm.dependencies]
            if 'tool' in data and 'pdm' in data['tool']:
                pdm_deps = data['tool']['pdm'].get('dependencies', [])
                for dep_string in pdm_deps:
                    dep = self._parse_pep621_dependency(dep_string, str(file_path))
                    if dep:
                        dependencies.append(dep)
        
        except Exception as e:
            print(f"[WARNING] Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def _parse_poetry_dependency(self, name: str, version_spec, source_file: str) -> Optional[Dependency]:
        """Parse a Poetry dependency entry."""
        # Poetry version can be a string or a dict
        if isinstance(version_spec, dict):
            version_spec = version_spec.get('version', '*')
        
        if isinstance(version_spec, str):
            # Convert Poetry ^ and ~ to standard operators
            if version_spec.startswith('^'):
                operator = '>='
                version = version_spec[1:]
            elif version_spec.startswith('~'):
                operator = '~='
                version = version_spec[1:]
            elif version_spec == '*':
                return None  # Skip wildcard dependencies
            else:
                # Try to extract operator
                match = re.match(r'^([=<>!~]+)(.+)$', version_spec)
                if match:
                    operator = match.group(1)
                    version = match.group(2)
                else:
                    operator = '=='
                    version = version_spec
            
            normalized_name = self._normalize_package_name(name)
            
            return Dependency(
                name=normalized_name,
                raw_name=name,
                version_spec=f"{operator}{version}" if operator else version,
                version=version,
                operator=operator,
                source_file=source_file,
                line_number=0,  # TOML doesn't have line numbers easily
                source_type="pyproject"
            )
        
        return None
    
    def _parse_pep621_dependency(self, dep_string: str, source_file: str) -> Optional[Dependency]:
        """Parse a PEP 621 dependency string."""
        match = self.REQUIREMENT_PATTERN.match(dep_string)
        if not match:
            return None
        
        raw_name = match.group(1)
        operator = match.group(4)
        version = match.group(5)
        
        normalized_name = self._normalize_package_name(raw_name)
        version_spec = f"{operator}{version}" if operator and version else None
        
        return Dependency(
            name=normalized_name,
            raw_name=raw_name,
            version_spec=version_spec,
            version=version,
            operator=operator,
            source_file=source_file,
            line_number=0,
            source_type="pyproject"
        )
    
    # ========================================================================
    # SETUP.PY PARSING
    # ========================================================================
    
    def parse_setup_py(self, file_path: Path) -> List[Dependency]:
        """Parse a setup.py file using AST."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            # Look for setup() call
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if it's a setup() call
                    if isinstance(node.func, ast.Name) and node.func.id == 'setup':
                        # Look for install_requires keyword
                        for keyword in node.keywords:
                            if keyword.arg == 'install_requires':
                                deps = self._extract_list_from_ast(keyword.value)
                                for dep_string in deps:
                                    dep = self._parse_requirement_line(
                                        dep_string, 
                                        str(file_path), 
                                        0
                                    )
                                    if dep:
                                        dep.source_type = "setup_py"
                                        dependencies.append(dep)
        
        except Exception as e:
            print(f"[WARNING] Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def _extract_list_from_ast(self, node) -> List[str]:
        """Extract string values from an AST List node."""
        if isinstance(node, ast.List):
            return [
                elt.value for elt in node.elts 
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
        return []
    
    # ========================================================================
    # PIPFILE PARSING
    # ========================================================================
    
    def parse_pipfile(self, file_path: Path) -> List[Dependency]:
        """Parse a Pipfile."""
        if toml is None:
            print(f"[WARNING] tomli not available, skipping {file_path}")
            return []
        
        dependencies = []
        
        try:
            with open(file_path, 'rb') as f:
                data = toml.load(f)
            
            # Parse [packages] section
            packages = data.get('packages', {})
            for name, version_spec in packages.items():
                dep = self._parse_pipfile_dependency(name, version_spec, str(file_path))
                if dep:
                    dependencies.append(dep)
        
        except Exception as e:
            print(f"[WARNING] Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def _parse_pipfile_dependency(self, name: str, version_spec, source_file: str) -> Optional[Dependency]:
        """Parse a Pipfile dependency entry."""
        if isinstance(version_spec, dict):
            version_spec = version_spec.get('version', '*')
        
        if isinstance(version_spec, str):
            if version_spec == '*':
                version = None
                operator = None
                version_spec_str = None
            else:
                # Pipfile uses == by default
                match = re.match(r'^([=<>!~]+)(.+)$', version_spec)
                if match:
                    operator = match.group(1)
                    version = match.group(2)
                    version_spec_str = version_spec
                else:
                    operator = '=='
                    version = version_spec
                    version_spec_str = f"=={version}"
            
            normalized_name = self._normalize_package_name(name)
            
            return Dependency(
                name=normalized_name,
                raw_name=name,
                version_spec=version_spec_str,
                version=version,
                operator=operator,
                source_file=source_file,
                line_number=0,
                source_type="pipfile"
            )
        
        return None
    
    # ========================================================================
    # MAIN PARSING LOGIC
    # ========================================================================
    
    def parse_repository(self, repo_path: Path) -> Dict[str, Dependency]:
        """
        Parse all dependency files in a repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary mapping package names to Dependency objects
        """
        self.dependencies = {}
        
        # Find all dependency files
        files = self.find_dependency_files(repo_path)
        
        total_files = sum(len(file_list) for file_list in files.values())
        
        if total_files == 0:
            print("[WARNING] No dependency files found in repository")
            return self.dependencies
        
        print(f"[INFO] Found {total_files} dependency file(s):")
        
        # Parse requirements.txt files
        for req_file in files['requirements']:
            print(f"  - {req_file.relative_to(repo_path)} (requirements)")
            deps = self.parse_requirements_file(req_file)
            self._merge_dependencies(deps)
        
        # Parse pyproject.toml files
        for toml_file in files['pyproject']:
            print(f"  - {toml_file.relative_to(repo_path)} (pyproject.toml)")
            deps = self.parse_pyproject_toml(toml_file)
            self._merge_dependencies(deps)
        
        # Parse setup.py files
        for setup_file in files['setup_py']:
            print(f"  - {setup_file.relative_to(repo_path)} (setup.py)")
            deps = self.parse_setup_py(setup_file)
            self._merge_dependencies(deps)
        
        # Parse Pipfile
        for pipfile in files['pipfile']:
            print(f"  - {pipfile.relative_to(repo_path)} (Pipfile)")
            deps = self.parse_pipfile(pipfile)
            self._merge_dependencies(deps)
        
        print(f"\n[OK] Parsed {len(self.dependencies)} unique dependencies")
        return self.dependencies
    
    def _merge_dependencies(self, deps: List[Dependency]):
        """Merge dependencies into the main dictionary."""
        for dep in deps:
            if dep.name in self.dependencies:
                existing = self.dependencies[dep.name]
                print(f"[INFO] Duplicate dependency '{dep.name}':")
                print(f"  - {existing.source_file} ({existing.source_type})")
                print(f"  - {dep.source_file} ({dep.source_type})")
                print(f"  Using: {dep.source_file}")
            
            self.dependencies[dep.name] = dep
    
    def _normalize_package_name(self, name: str) -> str:
        """Normalize package name according to PEP 503."""
        return re.sub(r'[-_.]+', '-', name).lower()
    
    # ========================================================================
    # UTILITY METHODS (keep existing ones)
    # ========================================================================
    
    def get_dependency(self, package_name: str) -> Optional[Dependency]:
        """Get a specific dependency by name."""
        normalized = self._normalize_package_name(package_name)
        return self.dependencies.get(normalized)
    
    def get_all_dependencies(self) -> List[Dependency]:
        """Get all parsed dependencies."""
        return list(self.dependencies.values())
    
    def get_pinned_dependencies(self) -> List[Dependency]:
        """Get only dependencies with pinned versions (==)."""
        return [dep for dep in self.dependencies.values() if dep.operator == '==']
    
    def get_unpinned_dependencies(self) -> List[Dependency]:
        """Get dependencies without version specifications."""
        return [dep for dep in self.dependencies.values() if dep.operator != '==']
    
    def export_summary(self) -> Dict:
        """Export a summary of parsed dependencies."""
        all_deps = self.get_all_dependencies()
        pinned = self.get_pinned_dependencies()
        unpinned = self.get_unpinned_dependencies()
        
        # Group by source type
        by_source = {}
        for dep in all_deps:
            source_type = dep.source_type
            if source_type not in by_source:
                by_source[source_type] = []
            by_source[source_type].append(dep.name)
        
        return {
            'total_dependencies': len(all_deps),
            'pinned_dependencies': len(pinned),
            'unpinned_dependencies': len(unpinned),
            'by_source_type': {k: len(v) for k, v in by_source.items()},
            'dependencies': [
                {
                    'name': dep.name,
                    'version_spec': dep.version_spec,
                    'source': dep.source_file,
                    'source_type': dep.source_type,
                    'line': dep.line_number
                }
                for dep in all_deps
            ]
        }


def main():
    """Test the enhanced DependencyParser."""
    print("=" * 70)
    print("Testing Enhanced DependencyParser")
    print("=" * 70)
    
    test_dir = Path(".")
    
    # Parse the repository
    parser = DependencyParser()
    dependencies = parser.parse_repository(test_dir)
    
    # Display results
    print("\n" + "=" * 70)
    print("Parsed Dependencies:")
    print("=" * 70)
    
    for dep in parser.get_all_dependencies():
        print(f"\n{dep.name}:")
        print(f"  Version: {dep.version_spec or 'not specified'}")
        print(f"  Source: {dep.source_file} ({dep.source_type})")
    
    # Display summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    summary = parser.export_summary()
    print(f"Total dependencies: {summary['total_dependencies']}")
    print(f"Pinned (==): {summary['pinned_dependencies']}")
    print(f"Unpinned: {summary['unpinned_dependencies']}")
    print(f"\nBy source type:")
    for source_type, count in summary['by_source_type'].items():
        print(f"  {source_type}: {count}")


if __name__ == "__main__":
    main()