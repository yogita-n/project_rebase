"""
Impact Mapper Module

Maps breaking dependency changes to impacted code locations.
Combines data from:
- Pathway streaming engine (breaking changes)
- Code scanner (code usage locations)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImpactedCode:
    """
    Represents code impacted by a breaking change.
    
    Attributes:
        file_path: Path to the affected file
        line_number: Line number of the affected code
        api_element: API element being used
        usage_type: Type of usage (import, call, attribute)
        context: Code context (the actual line)
        package_name: Name of the package
        current_version: Current version in use
        latest_version: Latest version available
    """
    file_path: str
    line_number: int
    api_element: str
    usage_type: str
    context: str
    package_name: str
    current_version: str
    latest_version: str
    
    def __repr__(self):
        return f"{Path(self.file_path).name}:{self.line_number} - {self.api_element}"


@dataclass
class BreakingChangeImpact:
    """
    Complete impact report for a breaking change.
    
    Attributes:
        package_name: Name of the package with breaking change
        current_version: Current version
        latest_version: Latest version
        total_impacts: Total number of code locations affected
        files_affected: Number of unique files affected
        impacted_code: List of all impacted code locations
    """
    package_name: str
    current_version: str
    latest_version: str
    total_impacts: int = 0
    files_affected: int = 0
    impacted_code: List[ImpactedCode] = field(default_factory=list)


class ImpactMapper:
    """
    Maps breaking changes to impacted code locations.
    
    Combines streaming engine updates with code scanner results
    to identify exactly which code will be affected by breaking changes.
    """
    
    def __init__(self):
        """Initialize the impact mapper."""
        self.impact_reports: Dict[str, BreakingChangeImpact] = {}
    
    def map_impacts(self, breaking_updates: List, usage_reports: Dict) -> Dict[str, BreakingChangeImpact]:
        """
        Map breaking changes to impacted code.
        
        Args:
            breaking_updates: List of PackageUpdate objects with breaking changes
            usage_reports: Dict of PackageUsageReport objects from code scanner
            
        Returns:
            Dictionary mapping package names to BreakingChangeImpact objects
        """
        print("[INFO] Mapping breaking changes to impacted code...")
        self.impact_reports = {}
        
        for update in breaking_updates:
            package_name = update.package_name
            
            # Get usage report for this package
            usage_report = usage_reports.get(package_name)
            
            if not usage_report:
                print(f"  [WARNING] No code usage found for {package_name}")
                continue
            
            # Create impact report
            impact = BreakingChangeImpact(
                package_name=package_name,
                current_version=update.current_version,
                latest_version=update.latest_version
            )
            
            # Map each usage to an impacted code location
            for usage in usage_report.usages:
                impacted = ImpactedCode(
                    file_path=usage.file_path,
                    line_number=usage.line_number,
                    api_element=usage.api_element,
                    usage_type=usage.usage_type,
                    context=usage.context,
                    package_name=package_name,
                    current_version=update.current_version,
                    latest_version=update.latest_version
                )
                impact.impacted_code.append(impacted)
            
            # Calculate statistics
            impact.total_impacts = len(impact.impacted_code)
            impact.files_affected = len(usage_report.files_affected)
            
            self.impact_reports[package_name] = impact
            
            print(f"  [BREAKING] {package_name}: {impact.total_impacts} impacts in {impact.files_affected} files")
        
        print(f"[OK] Mapped {len(self.impact_reports)} breaking changes")
        return self.impact_reports
    
    def get_impact_report(self, package_name: str) -> Optional[BreakingChangeImpact]:
        """
        Get impact report for a specific package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            BreakingChangeImpact or None if not found
        """
        return self.impact_reports.get(package_name)
    
    def get_all_impacted_files(self) -> List[str]:
        """
        Get list of all files affected by breaking changes.
        
        Returns:
            List of unique file paths
        """
        files = set()
        for impact in self.impact_reports.values():
            for code in impact.impacted_code:
                files.add(code.file_path)
        return sorted(list(files))
    
    def export_summary(self) -> Dict:
        """
        Export a summary of all impacts.
        
        Returns:
            Dictionary with impact statistics
        """
        total_impacts = sum(impact.total_impacts for impact in self.impact_reports.values())
        all_files = self.get_all_impacted_files()
        
        return {
            'total_breaking_packages': len(self.impact_reports),
            'total_code_impacts': total_impacts,
            'total_files_affected': len(all_files),
            'breaking_changes': [
                {
                    'package': impact.package_name,
                    'current_version': impact.current_version,
                    'latest_version': impact.latest_version,
                    'total_impacts': impact.total_impacts,
                    'files_affected': impact.files_affected,
                    'impacted_code': [
                        {
                            'file': code.file_path,
                            'line': code.line_number,
                            'api': code.api_element,
                            'type': code.usage_type,
                            'context': code.context
                        }
                        for code in impact.impacted_code
                    ]
                }
                for impact in self.impact_reports.values()
            ]
        }
    
    def generate_text_report(self) -> str:
        """
        Generate a human-readable text report.
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 70)
        lines.append("BREAKING CHANGE IMPACT REPORT")
        lines.append("=" * 70)
        
        summary = self.export_summary()
        lines.append(f"\nTotal breaking packages: {summary['total_breaking_packages']}")
        lines.append(f"Total code impacts: {summary['total_code_impacts']}")
        lines.append(f"Total files affected: {summary['total_files_affected']}")
        
        for impact in self.impact_reports.values():
            lines.append("\n" + "-" * 70)
            lines.append(f"Package: {impact.package_name}")
            lines.append(f"Version: {impact.current_version} -> {impact.latest_version}")
            lines.append(f"Impacts: {impact.total_impacts} locations in {impact.files_affected} files")
            lines.append("")
            
            # Group by file
            by_file = {}
            for code in impact.impacted_code:
                if code.file_path not in by_file:
                    by_file[code.file_path] = []
                by_file[code.file_path].append(code)
            
            for file_path, codes in sorted(by_file.items()):
                lines.append(f"  File: {Path(file_path).name}")
                for code in sorted(codes, key=lambda c: c.line_number):
                    lines.append(f"    Line {code.line_number}: {code.api_element} ({code.usage_type})")
                    lines.append(f"      {code.context}")
                lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)


def main():
    """
    Test the ImpactMapper module.
    """
    print("=" * 60)
    print("Testing ImpactMapper")
    print("=" * 60)
    
    # Mock data for testing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from core.pathway_stream import PackageUpdate
    from core.code_scanner import PackageUsageReport, CodeUsage
    from datetime import datetime
    
    # Create mock breaking updates
    breaking_updates = [
        PackageUpdate(
            package_name='flask',
            current_version='2.0.0',
            latest_version='3.1.2',
            status='breaking',
            is_breaking=True,
            timestamp=datetime.now()
        )
    ]
    
    # Create mock usage reports
    usage_reports = {
        'flask': PackageUsageReport(
            package_name='flask',
            total_usages=4,
            files_affected={'test_code.py'},
            usages=[
                CodeUsage(
                    file_path='test_code.py',
                    line_number=3,
                    package_name='flask',
                    api_element='flask.Flask',
                    usage_type='import',
                    context='from flask import Flask, jsonify'
                ),
                CodeUsage(
                    file_path='test_code.py',
                    line_number=6,
                    package_name='flask',
                    api_element='Flask',
                    usage_type='call',
                    context='app = Flask(__name__)'
                )
            ]
        )
    }
    
    # Map impacts
    mapper = ImpactMapper()
    impacts = mapper.map_impacts(breaking_updates, usage_reports)
    
    # Display report
    print("\n" + mapper.generate_text_report())


if __name__ == "__main__":
    main()
