"""
Real-Time Dependency Deprecation & Migration Intelligence System

Main application that orchestrates all modules to:
1. Fetch repository (GitHub or local)
2. Parse dependencies from requirements files
3. Stream live PyPI updates
4. Detect outdated and breaking changes
5. Scan code for package usage
6. Map breaking changes to impacted code
7. Generate AI-powered migration fixes

Usage:
    python app.py <repo_url_or_path>
    python app.py https://github.com/user/repo
    python app.py /path/to/local/repo
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List

# Import core modules
from core.repo_fetcher import RepoFetcher
from core.dep_parser import DependencyParser
from core.pathway_stream import PathwayStreamEngine
from core.code_scanner import CodeScanner
from core.impact_mapper import ImpactMapper
from core.ai_fixer import AIFixer


class DeprecationIntelligenceSystem:
    """
    Main orchestrator for the dependency deprecation intelligence system.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the system.
        
        Args:
            openai_api_key: Optional OpenAI API key for AI fixes
        """
        self.repo_fetcher = RepoFetcher()
        self.dep_parser = DependencyParser()
        self.stream_engine = PathwayStreamEngine()
        self.code_scanner = None  # Will be initialized after parsing deps
        self.impact_mapper = ImpactMapper()
        self.ai_fixer = AIFixer(api_key=openai_api_key)
        
        self.repo_path = None
        self.dependencies = {}
        self.updates = []
        self.usage_reports = {}
        self.impact_reports = {}
        self.ai_fixes = []
    
    def run(self, repo_input: str) -> Dict:
        """
        Run the complete analysis pipeline.
        
        Args:
            repo_input: GitHub URL or local repository path
            
        Returns:
            Complete analysis results
        """
        print("\n" + "=" * 70)
        print("REAL-TIME DEPENDENCY DEPRECATION & MIGRATION INTELLIGENCE SYSTEM")
        print("=" * 70)
        
        # Step 1: Fetch repository
        print("\n[STEP 1/7] Fetching repository...")
        success, repo_path, error = self.repo_fetcher.fetch(repo_input)
        if not success:
            print(f"[ERROR] Failed to fetch repository: {error}")
            return {'error': error}
        
        self.repo_path = repo_path
        print(f"[OK] Repository ready at: {repo_path}")
        
        # Step 2: Parse dependencies
        print("\n[STEP 2/7] Parsing dependencies...")
        self.dependencies = self.dep_parser.parse_repository(repo_path)
        
        if not self.dependencies:
            print("[WARNING] No dependencies found. Nothing to analyze.")
            return {'error': 'No dependencies found'}
        
        # Step 3: Stream PyPI updates
        print("\n[STEP 3/7] Streaming PyPI updates...")
        self.stream_engine.load_repo_dependencies(self.dependencies)
        self.stream_engine.fetch_pypi_updates()
        
        # Step 4: Detect outdated and breaking changes
        print("\n[STEP 4/7] Detecting outdated and breaking changes...")
        self.updates = self.stream_engine.perform_streaming_join()
        
        breaking_updates = self.stream_engine.get_breaking_packages()
        outdated_updates = self.stream_engine.get_outdated_packages()
        
        print(f"\n[SUMMARY] Found {len(breaking_updates)} breaking changes, {len(outdated_updates)} outdated packages")
        
        if not breaking_updates:
            print("[INFO] No breaking changes detected. Your dependencies are safe!")
            return self._generate_final_report()
        
        # Step 5: Scan code for package usage
        print("\n[STEP 5/7] Scanning code for package usage...")
        target_packages = {pkg.package_name for pkg in breaking_updates}
        self.code_scanner = CodeScanner(target_packages)
        self.usage_reports = self.code_scanner.scan_directory(repo_path)
        
        # Step 6: Map breaking changes to impacted code
        print("\n[STEP 6/7] Mapping breaking changes to impacted code...")
        self.impact_reports = self.impact_mapper.map_impacts(breaking_updates, self.usage_reports)
        
        # Step 7: Generate AI fixes
        print("\n[STEP 7/7] Generating AI-powered migration fixes...")
        for package_name, impact_report in self.impact_reports.items():
            fixes = self.ai_fixer.generate_fixes_for_impact(impact_report)
            self.ai_fixes.extend(fixes)
        
        # Generate final report
        return self._generate_final_report()
    
    def _generate_final_report(self) -> Dict:
        """
        Generate the final structured report.
        
        Returns:
            Complete analysis report
        """
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)
        
        # Build structured output
        results = []
        
        for update in self.updates:
            package_result = {
                'package': update.package_name,
                'current_version': update.current_version,
                'latest_version': update.latest_version,
                'status': update.status,
                'impacted_files': []
            }
            
            # Add impact information if this is a breaking change
            if update.status == 'breaking':
                impact_report = self.impact_reports.get(update.package_name)
                if impact_report:
                    # Group by file
                    by_file = {}
                    for code in impact_report.impacted_code:
                        if code.file_path not in by_file:
                            by_file[code.file_path] = []
                        by_file[code.file_path].append(code)
                    
                    # Build file impact list
                    for file_path, codes in by_file.items():
                        file_impact = {
                            'file': str(Path(file_path).relative_to(self.repo_path)),
                            'impacts': [
                                {
                                    'line': code.line_number,
                                    'api': code.api_element,
                                    'context': code.context
                                }
                                for code in codes
                            ]
                        }
                        
                        # Add AI fix if available
                        ai_fix = next((f for f in self.ai_fixes if f.file_path == file_path and f.line_number == codes[0].line_number), None)
                        if ai_fix:
                            file_impact['ai_fix'] = {
                                'explanation': ai_fix.explanation,
                                'fixed_code': ai_fix.fixed_code,
                                'migration_notes': ai_fix.migration_notes,
                                'confidence': ai_fix.confidence
                            }
                        
                        package_result['impacted_files'].append(file_impact)
            
            results.append(package_result)
        
        return {
            'repository': str(self.repo_path),
            'total_dependencies': len(self.dependencies),
            'total_updates': len(self.updates),
            'breaking_changes': len(self.stream_engine.get_breaking_packages()),
            'outdated_packages': len(self.stream_engine.get_outdated_packages()),
            'results': results
        }
    
    def print_report(self, report: Dict):
        """
        Print a human-readable report.
        
        Args:
            report: Report dictionary
        """
        print("\n" + "=" * 70)
        print("FINAL REPORT")
        print("=" * 70)
        
        print(f"\nRepository: {report['repository']}")
        print(f"Total dependencies: {report['total_dependencies']}")
        print(f"Total updates available: {report['total_updates']}")
        print(f"Breaking changes: {report['breaking_changes']}")
        print(f"Outdated packages: {report['outdated_packages']}")
        
        print("\n" + "-" * 70)
        print("PACKAGE DETAILS")
        print("-" * 70)
        
        for result in report['results']:
            print(f"\n{result['package']}:")
            print(f"  Current: {result['current_version']}")
            print(f"  Latest: {result['latest_version']}")
            print(f"  Status: {result['status'].upper()}")
            
            if result['impacted_files']:
                print(f"  Impacted files: {len(result['impacted_files'])}")
                for file_impact in result['impacted_files']:
                    print(f"\n    File: {file_impact['file']}")
                    for impact in file_impact['impacts']:
                        print(f"      Line {impact['line']}: {impact['api']}")
                        print(f"        {impact['context']}")
                    
                    if 'ai_fix' in file_impact:
                        fix = file_impact['ai_fix']
                        print(f"\n      AI Fix (confidence: {fix['confidence']:.2f}):")
                        print(f"        Explanation: {fix['explanation']}")
                        print(f"        Fixed code: {fix['fixed_code']}")
                        if fix['migration_notes']:
                            print(f"        Notes: {fix['migration_notes'][:100]}...")
        
        print("\n" + "=" * 70)
    
    def save_report(self, report: Dict, output_file: str = "migration_report.json"):
        """
        Save report to JSON file.
        
        Args:
            report: Report dictionary
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n[OK] Report saved to: {output_file}")


def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(
        description="Real-Time Dependency Deprecation & Migration Intelligence System"
    )
    parser.add_argument(
        'repo',
        help='GitHub repository URL or local repository path'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='migration_report.json',
        help='Output file for JSON report (default: migration_report.json)'
    )
    parser.add_argument(
        '--openai-key',
        help='OpenAI API key for AI-powered fixes (or set OPENAI_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Initialize and run system
    system = DeprecationIntelligenceSystem(openai_api_key=args.openai_key)
    report = system.run(args.repo)
    
    # Print report
    if 'error' not in report:
        system.print_report(report)
        system.save_report(report, args.output)
    else:
        print(f"\n[ERROR] {report['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
