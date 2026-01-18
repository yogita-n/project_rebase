"""
Code Scanner Module

Uses Python AST (Abstract Syntax Tree) to scan Python files and detect:
- Package imports
- Function calls
- Class usage
- Exact file locations and line numbers
"""

import ast
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CodeUsage:
    """
    Represents a code usage instance.
    
    Attributes:
        file_path: Path to the file
        line_number: Line number where usage occurs
        package_name: Name of the package being used
        api_element: Specific API element (function, class, method)
        usage_type: Type of usage ('import', 'call', 'attribute')
        context: Code context (the actual line of code)
    """
    file_path: str
    line_number: int
    package_name: str
    api_element: str
    usage_type: str
    context: str = ""
    
    def __repr__(self):
        return f"{self.package_name}.{self.api_element} at {Path(self.file_path).name}:{self.line_number}"


@dataclass
class PackageUsageReport:
    """
    Report of all usages for a specific package.
    
    Attributes:
        package_name: Name of the package
        total_usages: Total number of usages found
        files_affected: Set of files that use this package
        usages: List of all CodeUsage instances
    """
    package_name: str
    total_usages: int = 0
    files_affected: Set[str] = field(default_factory=set)
    usages: List[CodeUsage] = field(default_factory=list)


class ASTVisitor(ast.NodeVisitor):
    """
    Custom AST visitor to extract package usage information.
    """
    
    def __init__(self, file_path: str, target_packages: Set[str]):
        """
        Initialize the AST visitor.
        
        Args:
            file_path: Path to the file being analyzed
            target_packages: Set of package names to track
        """
        self.file_path = file_path
        self.target_packages = target_packages
        self.usages: List[CodeUsage] = []
        self.imported_modules: Dict[str, str] = {}  # alias -> full_name
        self.source_lines: List[str] = []
    
    def set_source_lines(self, source_lines: List[str]):
        """Set the source code lines for context extraction."""
        self.source_lines = source_lines
    
    def _get_context(self, line_number: int) -> str:
        """Get the source code line for context."""
        if 0 < line_number <= len(self.source_lines):
            return self.source_lines[line_number - 1].strip()
        return ""
    
    def _is_target_package(self, module_name: str) -> Optional[str]:
        """
        Check if a module name matches any target package.
        
        Args:
            module_name: Module name to check
            
        Returns:
            Matched package name or None
        """
        if not module_name:
            return None
        
        # Direct match
        if module_name in self.target_packages:
            return module_name
        
        # Check if it's a submodule of a target package
        for package in self.target_packages:
            if module_name.startswith(f"{package}."):
                return package
        
        return None
    
    def visit_Import(self, node: ast.Import):
        """Visit import statements: import package"""
        for alias in node.names:
            package = self._is_target_package(alias.name)
            if package:
                import_name = alias.asname if alias.asname else alias.name
                self.imported_modules[import_name] = alias.name
                
                usage = CodeUsage(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    package_name=package,
                    api_element=alias.name,
                    usage_type='import',
                    context=self._get_context(node.lineno)
                )
                self.usages.append(usage)
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statements: from package import item"""
        if node.module:
            package = self._is_target_package(node.module)
            if package:
                for alias in node.names:
                    import_name = alias.asname if alias.asname else alias.name
                    self.imported_modules[import_name] = f"{node.module}.{alias.name}"
                    
                    usage = CodeUsage(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        package_name=package,
                        api_element=f"{node.module}.{alias.name}",
                        usage_type='import',
                        context=self._get_context(node.lineno)
                    )
                    self.usages.append(usage)
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function/method calls"""
        # Extract the function name
        func_name = self._extract_name(node.func)
        
        if func_name:
            # Check if it's a call to an imported module
            base_name = func_name.split('.')[0]
            if base_name in self.imported_modules:
                full_name = self.imported_modules[base_name]
                package = self._is_target_package(full_name)
                
                if package:
                    usage = CodeUsage(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        package_name=package,
                        api_element=func_name,
                        usage_type='call',
                        context=self._get_context(node.lineno)
                    )
                    self.usages.append(usage)
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Visit attribute access: obj.attr"""
        full_name = self._extract_name(node)
        
        if full_name:
            base_name = full_name.split('.')[0]
            if base_name in self.imported_modules:
                module_name = self.imported_modules[base_name]
                package = self._is_target_package(module_name)
                
                if package:
                    usage = CodeUsage(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        package_name=package,
                        api_element=full_name,
                        usage_type='attribute',
                        context=self._get_context(node.lineno)
                    )
                    self.usages.append(usage)
        
        self.generic_visit(node)
    
    def _extract_name(self, node) -> Optional[str]:
        """
        Extract the full name from an AST node.
        
        Args:
            node: AST node
            
        Returns:
            Full name string or None
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._extract_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Call):
            return self._extract_name(node.func)
        return None


class CodeScanner:
    """
    Scans Python files to detect package usage.
    
    Features:
    - AST-based analysis
    - Tracks imports, function calls, and attribute access
    - Records exact file and line numbers
    - Provides detailed usage reports
    """
    
    def __init__(self, target_packages: Set[str]):
        """
        Initialize the code scanner.
        
        Args:
            target_packages: Set of package names to track
        """
        self.target_packages = {pkg.lower().replace('_', '-') for pkg in target_packages}
        self.usage_reports: Dict[str, PackageUsageReport] = {}
    
    def scan_file(self, file_path: Path) -> List[CodeUsage]:
        """
        Scan a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of CodeUsage instances
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                source_lines = source.splitlines()
            
            # Parse the AST
            tree = ast.parse(source, filename=str(file_path))
            
            # Visit the AST
            visitor = ASTVisitor(str(file_path), self.target_packages)
            visitor.set_source_lines(source_lines)
            visitor.visit(tree)
            
            return visitor.usages
            
        except SyntaxError as e:
            print(f"[WARNING] Syntax error in {file_path}: {e}")
            return []
        except Exception as e:
            print(f"[WARNING] Failed to scan {file_path}: {e}")
            return []
    
    def scan_directory(self, directory: Path, exclude_dirs: Optional[Set[str]] = None) -> Dict[str, PackageUsageReport]:
        """
        Scan all Python files in a directory.
        
        Args:
            directory: Directory to scan
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            Dictionary mapping package names to usage reports
        """
        if exclude_dirs is None:
            exclude_dirs = {
                '__pycache__', '.git', '.venv', 'venv', 'env',
                'node_modules', '.tox', 'build', 'dist', '.eggs'
            }
        
        print(f"[INFO] Scanning directory: {directory}")
        
        # Find all Python files
        python_files = []
        for root, dirs, files in directory.walk():
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(root / file)
        
        print(f"[INFO] Found {len(python_files)} Python files")
        
        # Scan each file
        all_usages = []
        for py_file in python_files:
            usages = self.scan_file(py_file)
            all_usages.extend(usages)
        
        # Build usage reports
        self.usage_reports = {}
        for usage in all_usages:
            if usage.package_name not in self.usage_reports:
                self.usage_reports[usage.package_name] = PackageUsageReport(
                    package_name=usage.package_name
                )
            
            report = self.usage_reports[usage.package_name]
            report.usages.append(usage)
            report.files_affected.add(usage.file_path)
            report.total_usages += 1
        
        print(f"[OK] Scanned {len(python_files)} files, found {len(all_usages)} usages")
        
        return self.usage_reports
    
    def get_package_report(self, package_name: str) -> Optional[PackageUsageReport]:
        """
        Get usage report for a specific package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            PackageUsageReport or None if not found
        """
        normalized = package_name.lower().replace('_', '-')
        return self.usage_reports.get(normalized)
    
    def export_summary(self) -> Dict:
        """
        Export a summary of all scanned packages.
        
        Returns:
            Dictionary with scan statistics
        """
        return {
            'total_packages_found': len(self.usage_reports),
            'packages': [
                {
                    'name': report.package_name,
                    'total_usages': report.total_usages,
                    'files_affected': len(report.files_affected),
                    'usages': [
                        {
                            'file': usage.file_path,
                            'line': usage.line_number,
                            'api': usage.api_element,
                            'type': usage.usage_type,
                            'context': usage.context
                        }
                        for usage in report.usages
                    ]
                }
                for report in self.usage_reports.values()
            ]
        }


def main():
    """
    Test the CodeScanner module.
    """
    print("=" * 60)
    print("Testing CodeScanner")
    print("=" * 60)
    
    # Create a test Python file
    test_dir = Path(".")
    test_file = test_dir / "test_code.py"
    
    if not test_file.exists():
        print("\n[INFO] Creating test_code.py for testing...")
        with open(test_file, 'w') as f:
            f.write("""# Test file for code scanner
import requests
from flask import Flask, jsonify
import numpy as np

app = Flask(__name__)

@app.route('/')
def hello():
    response = requests.get('https://api.example.com')
    data = np.array([1, 2, 3])
    return jsonify({'message': 'Hello', 'data': data.tolist()})

if __name__ == '__main__':
    app.run()
""")
        print(f"[OK] Created {test_file}")
    
    # Scan for specific packages
    target_packages = {'requests', 'flask', 'numpy'}
    scanner = CodeScanner(target_packages)
    
    # Scan the current directory
    reports = scanner.scan_directory(test_dir)
    
    # Display results
    print("\n" + "=" * 60)
    print("Package Usage Report:")
    print("=" * 60)
    
    for package_name, report in reports.items():
        print(f"\n{package_name}:")
        print(f"  Total usages: {report.total_usages}")
        print(f"  Files affected: {len(report.files_affected)}")
        print(f"  Usages:")
        for usage in report.usages:
            print(f"    - {Path(usage.file_path).name}:{usage.line_number} - {usage.usage_type} - {usage.api_element}")
            print(f"      Context: {usage.context}")


if __name__ == "__main__":
    main()
