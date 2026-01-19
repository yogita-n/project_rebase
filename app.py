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
import signal
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

# Import core modules
from core.repo_fetcher import RepoFetcher
from core.dep_parser import DependencyParser
from core.pathway_stream import PathwayStreamEngine, BreakingChangeEvent
from core.code_scanner import CodeScanner
from core.impact_mapper import ImpactMapper
from core.ai_fixer import AIFixer


class DeprecationIntelligenceSystem:
    """
    Main orchestrator for the dependency deprecation intelligence system.
    Supports both batch mode (legacy) and streaming mode (real-time).
    """
    def __init__(self, openai_api_key: str = None, poll_interval: int = 30, event_broadcaster=None):
        """
        Initialize the system.
        
        Args:
            openai_api_key: Optional OpenAI API key for AI fixes
            poll_interval: PyPI polling interval in seconds (for streaming mode)
            event_broadcaster: Optional event broadcaster for web streaming
        """
        self.repo_fetcher = RepoFetcher()
        self.dep_parser = DependencyParser()
        self.stream_engine = PathwayStreamEngine(poll_interval=poll_interval, event_broadcaster=event_broadcaster)
        self.code_scanner = None  # Will be initialized after parsing deps
        self.impact_mapper = ImpactMapper()
        self.ai_fixer = AIFixer(api_key=openai_api_key)
    
        self.repo_path = None
        self.dependencies = {}
        self.updates = []
        self.usage_reports = {}
        self.impact_reports = {}
        self.ai_fixes = []
    
        # For streaming mode shutdown control
        self.shutdown_event = threading.Event()
    
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
        
        print(f"[OK] Found {len(self.dependencies)} dependencies:")
        for pkg, version in self.dependencies.items():
            print(f"  - {pkg}: {version}")
        
        # Step 3: Stream PyPI updates
        print("\n[STEP 3/7] Streaming PyPI updates...")
        
        # Format dependencies for streaming engine
        formatted_deps = self._format_dependencies(self.dependencies)
        self.stream_engine.load_repo_dependencies(formatted_deps)
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
    
    def _format_dependencies(self, dependencies: Dict) -> Dict:
        """
        Format dependencies for the streaming engine.
        Replaces "N/A" with "0.0.0" for packages without version constraints.
        
        Args:
            dependencies: Raw dependencies dictionary
            
        Returns:
            Formatted dependencies dictionary
        """
        formatted = {}
        for pkg, version in dependencies.items():
            if isinstance(version, str):
                formatted[pkg] = version if version != "N/A" else "0.0.0"
            elif hasattr(version, 'version'):
                # Handle Dependency objects
                v = version.version if version.version != "N/A" else "0.0.0"
                formatted[pkg] = v
            else:
                formatted[pkg] = "0.0.0"
        return formatted
    
    def run_streaming(self, repo_input: str, shutdown_event: Optional[threading.Event] = None) -> None:
        """
        Run the system in continuous streaming mode.
        This will run indefinitely until interrupted (CTRL+C) or shutdown_event is set.
        
        Args:
            repo_input: GitHub URL or local repository path
            shutdown_event: Optional threading.Event to control graceful shutdown
        """
        print("\n" + "=" * 70)
        print("REAL-TIME DEPENDENCY DEPRECATION STREAMING SYSTEM")
        print("=" * 70)
        
        # Store shutdown event for use in callbacks
        if shutdown_event:
            self.shutdown_event = shutdown_event
        
        # Step 1: Fetch repository (one-time)
        print("\n[SETUP 1/3] Fetching repository...")
        success, repo_path, error = self.repo_fetcher.fetch(repo_input)
        if not success:
            print(f"[ERROR] Failed to fetch repository: {error}")
            sys.exit(1)
        
        self.repo_path = repo_path
        print(f"[OK] Repository ready at: {repo_path}")
        
        # Step 2: Parse dependencies (one-time)
        print("\n[SETUP 2/3] Parsing dependencies...")
        self.dependencies = self.dep_parser.parse_repository(repo_path)
        
        if not self.dependencies:
            print("[WARNING] No dependencies found. Nothing to monitor.")
            sys.exit(1)
        
        print(f"[OK] Found {len(self.dependencies)} dependencies:")
        for pkg, version in self.dependencies.items():
            print(f"  - {pkg}: {version}")
        
        # Step 3: Initialize code scanner for all packages
        print("\n[SETUP 3/3] Initializing code scanner...")
        all_package_names = {name for name in self.dependencies.keys()}
        self.code_scanner = CodeScanner(all_package_names)
        print(f"[OK] Code scanner ready for {len(all_package_names)} packages")
        
        # Load dependencies into streaming engine WITH PROPER VERSION FORMATTING
        print("\n[SETUP] Loading dependencies into streaming engine...")
        formatted_deps = self._format_dependencies(self.dependencies)
        
        print(f"[DEBUG] Loading {len(formatted_deps)} packages with versions:")
        for pkg, version in formatted_deps.items():
            original_version = self.dependencies.get(pkg, "N/A")
            if version == "0.0.0" and original_version == "N/A":
                print(f"  {pkg}: {version} (no version specified in requirements)")
            else:
                print(f"  {pkg}: {version}")
        
        self.stream_engine.load_repo_dependencies(formatted_deps)
        
        # Register callback for breaking changes
        self.stream_engine.register_breaking_change_callback(self._on_breaking_change)
        
        # Pass shutdown event to streaming engine if it supports it
        if hasattr(self.stream_engine, 'set_shutdown_event'):
            self.stream_engine.set_shutdown_event(self.shutdown_event)
        
        print("\n" + "=" * 70)
        print("STREAMING STARTED")
        print("=" * 70)
        print("\n[INFO] Monitoring for breaking changes in real-time...")
        print("[INFO] Press Ctrl+C to stop streaming\n")
        
        # Start streaming (blocks here)
        try:
            if hasattr(self.stream_engine, 'start_streaming_with_shutdown'):
                # If streaming engine supports shutdown events
                self.stream_engine.start_streaming_with_shutdown(self.shutdown_event)
            else:
                # Fallback: try to handle KeyboardInterrupt
                try:
                    self.stream_engine.start_streaming()
                except KeyboardInterrupt:
                    print("\n[INFO] Stream interrupted by user")
        except KeyboardInterrupt:
            print("\n[INFO] Stream interrupted by user")
        except Exception as e:
            print(f"\n[ERROR] Error in streaming engine: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n[INFO] Streaming stopped. Cleaning up...")
    
    def _on_breaking_change(self, event: BreakingChangeEvent) -> None:
        """
        Callback triggered when a breaking change is detected.
        Runs the full pipeline: scan → map → fix → log.
        
        Args:
            event: Breaking change event
        """
        timestamp = event.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        package_name = event.package_name
        
        # Get current version from our parsed dependencies
        current_version = self.dependencies.get(package_name, "N/A")
        
        # If current version is N/A, use the version from event (which should be 0.0.0 for unspecified)
        if current_version == "N/A":
            current_version = event.current_version
        
        latest_version = event.latest_version
        
        # BROADCAST BREAKING CHANGE TO WEB CLIENTS
        if hasattr(self.stream_engine, 'event_broadcaster') and self.stream_engine.event_broadcaster:
            # Send initial breaking change detection
            self.stream_engine.event_broadcaster.broadcast('breaking_change', {
                'package_name': package_name,
                'current_version': current_version,
                'latest_version': latest_version,
                'timestamp': timestamp,
                'display_message': f"{current_version} → {latest_version}",
                'severity': 'breaking',
                'stage': 'detected'
            })
        
        print(f"\n{'─'*70}")
        print(f"[PIPELINE] Processing breaking change for {package_name}")
        print(f"{'─'*70}")
        
        # Step 1: Scan code for package usage
        print(f"[1/3] Scanning code for {package_name} usage...")
        
        # Broadcast scanning stage
        if hasattr(self.stream_engine, 'event_broadcaster') and self.stream_engine.event_broadcaster:
            self.stream_engine.event_broadcaster.broadcast('pipeline_step', {
                'step': 'scanning',
                'message': f'Scanning code for {package_name} usage',
                'package_name': package_name
            })
        
        usage_report = self.code_scanner.get_package_report(package_name)
        
        if not usage_report:
            # Need to scan if not cached
            print(f"  Scanning repository: {self.repo_path}")
            reports = self.code_scanner.scan_directory(self.repo_path)
            usage_report = reports.get(package_name)
        
        if not usage_report or not usage_report.usages:
            print(f"  [INFO] No code usage found for {package_name}")
            
            # Broadcast no usage found
            if hasattr(self.stream_engine, 'event_broadcaster') and self.stream_engine.event_broadcaster:
                self.stream_engine.event_broadcaster.broadcast('breaking_change', {
                    'package_name': package_name,
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'timestamp': timestamp,
                    'display_message': f"{current_version} → {latest_version} (no code usage)",
                    'severity': 'breaking',
                    'stage': 'no_usage'
                })
            
            print(f"\n{'='*70}")
            print(f"📋 BREAKING CHANGE REPORT")
            print(f"{'='*70}")
            print(f"[{timestamp}]")
            print(f"Package: {package_name}")
            print(f"Status: BREAKING")
            print(f"Current Version: {current_version}")
            print(f"Latest Version: {latest_version}")
            print(f"Impact: NO CODE USAGE DETECTED")
            print(f"Note: Package is in requirements but not used in code")
            print(f"{'='*70}\n")
            return
        
        print(f"  Found {usage_report.total_usages} usages in {len(usage_report.files_affected)} files")
        
        # Step 2: Map impacts
        print(f"[2/3] Mapping breaking change impacts...")
        
        # Broadcast mapping stage
        if hasattr(self.stream_engine, 'event_broadcaster') and self.stream_engine.event_broadcaster:
            self.stream_engine.event_broadcaster.broadcast('pipeline_step', {
                'step': 'mapping',
                'message': f'Mapping impacts for {usage_report.total_usages} usages',
                'package_name': package_name,
                'usage_count': usage_report.total_usages
            })
        
        # Create a mock PackageUpdate for the mapper
        from core.pathway_stream import VersionChecker
        from dataclasses import dataclass as dc
        
        @dc
        class MockUpdate:
            package_name: str
            current_version: str
            latest_version: str
            status: str = 'breaking'
            is_breaking: bool = True
        
        mock_update = MockUpdate(
            package_name=package_name,
            current_version=current_version,
            latest_version=latest_version
        )
        
        impact_report = self.impact_mapper.map_impacts(
            [mock_update],
            {package_name: usage_report}
        ).get(package_name)
        
        if not impact_report:
            print(f"  [WARNING] Could not generate impact report")
            
            # Broadcast mapping failed
            if hasattr(self.stream_engine, 'event_broadcaster') and self.stream_engine.event_broadcaster:
                self.stream_engine.event_broadcaster.broadcast('pipeline_step', {
                    'step': 'mapping_failed',
                    'message': f'Could not generate impact report for {package_name}',
                    'package_name': package_name
                })
            return
        
        # Handle both list and count for files_affected
        if hasattr(impact_report, 'files_affected'):
            if isinstance(impact_report.files_affected, int):
                files_affected_count = impact_report.files_affected
                files_affected_list = []
            else:
                files_affected_count = len(impact_report.files_affected)
                files_affected_list = impact_report.files_affected
        else:
            files_affected_count = 0
            files_affected_list = []
        
        print(f"  Found {impact_report.total_impacts} impacted code locations in {files_affected_count} files")
        
        # Step 3: Generate AI fixes
        print(f"[3/3] Generating AI-powered migration fixes...")
        
        # Broadcast AI fix generation stage
        if hasattr(self.stream_engine, 'event_broadcaster') and self.stream_engine.event_broadcaster:
            self.stream_engine.event_broadcaster.broadcast('pipeline_step', {
                'step': 'ai_fixes',
                'message': f'Generating AI fixes for {impact_report.total_impacts} impacts',
                'package_name': package_name,
                'impact_count': impact_report.total_impacts
            })
        
        ai_fixes = self.ai_fixer.generate_fixes_for_impact(impact_report)
        print(f"  Generated {len(ai_fixes)} AI fixes")
        
        # Broadcast completion
        if hasattr(self.stream_engine, 'event_broadcaster') and self.stream_engine.event_broadcaster:
            self.stream_engine.event_broadcaster.broadcast('breaking_change', {
                'package_name': package_name,
                'current_version': current_version,
                'latest_version': latest_version,
                'timestamp': timestamp,
                'display_message': f"{current_version} → {latest_version} ({impact_report.total_impacts} impacts)",
                'severity': 'breaking',
                'stage': 'completed',
                'impact_count': impact_report.total_impacts,
                'file_count': files_affected_count,
                'ai_fixes_count': len(ai_fixes)
            })
        
        # Output results in required format
        print(f"\n{'='*70}")
        print(f"📋 BREAKING CHANGE REPORT")
        print(f"{'='*70}")
        print(f"[{timestamp}]")
        print(f"Package: {package_name}")
        print(f"Status: BREAKING")
        print(f"Current Version: {current_version}")
        print(f"Latest Version: {latest_version}")
        print(f"Impacted Files: {files_affected_count}")
        print(f"Total Impacts: {impact_report.total_impacts}")
        print(f"AI Fixes Generated: {len(ai_fixes)}")
        
        # Show detailed impacts if available
        if hasattr(impact_report, 'impacted_code') and impact_report.impacted_code:
            # Show first 5 impacts
            for impacted_code in impact_report.impacted_code[:5]:
                # Extract file path safely
                file_path = getattr(impacted_code, 'file_path', 'Unknown file')
                relative_path = Path(file_path).relative_to(self.repo_path) if self.repo_path and Path(file_path).is_relative_to(self.repo_path) else file_path
                
                print(f"\n  File: {relative_path}")
                print(f"  Line: {getattr(impacted_code, 'line_number', 'N/A')}")
                print(f"  API: {getattr(impacted_code, 'api_element', 'N/A')}")
                
                # Handle context safely
                context = getattr(impacted_code, 'context', '')
                if context and len(context) > 80:
                    print(f"  Context: {context[:80]}...")
                elif context:
                    print(f"  Context: {context}")
                
                # Find corresponding AI fix
                if ai_fixes:
                    matching_fix = next(
                        (fix for fix in ai_fixes 
                        if hasattr(fix, 'file_path') and fix.file_path == file_path 
                        and hasattr(fix, 'line_number') and fix.line_number == getattr(impacted_code, 'line_number', None)),
                        None
                    )
                    
                    if matching_fix:
                        print(f"  Suggested Fix: {getattr(matching_fix, 'explanation', 'No explanation')}")
                        fix_code = getattr(matching_fix, 'fixed_code', '')
                        if fix_code and len(fix_code) > 100:
                            print(f"  Fixed Code: {fix_code[:100]}...")
                        elif fix_code:
                            print(f"  Fixed Code: {fix_code}")
                        
                        confidence = getattr(matching_fix, 'confidence', 0)
                        print(f"  Confidence: {confidence:.0%}")
            
            if len(impact_report.impacted_code) > 5:
                print(f"\n  ... and {len(impact_report.impacted_code) - 5} more impacts")
        
        print(f"{'='*70}\n")
    
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
    
    def stop_streaming(self):
        """
        Gracefully stop the streaming mode.
        """
        self.shutdown_event.set()
        print("\n[INFO] Shutdown signal sent to streaming system...")
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
        '--mode',
        choices=['streaming', 'batch'],
        default='streaming',
        help='Run mode: streaming (continuous) or batch (one-time). Default: streaming'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=30,
        help='PyPI polling interval in seconds (streaming mode only). Default: 30'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='migration_report.json',
        help='Output file for JSON report (batch mode only). Default: migration_report.json'
    )
    parser.add_argument(
        '--openai-key',
        help='OpenAI API key for AI-powered fixes (or set OPENAI_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Initialize system
    system = DeprecationIntelligenceSystem(
        openai_api_key=args.openai_key,
        poll_interval=args.poll_interval
    )
    
    if args.mode == 'streaming':
        # Run in continuous streaming mode
        print("\n[MODE] Starting in STREAMING mode (continuous)")
        print("       Use --mode batch for one-time analysis\n")
        
        # Create shutdown event for graceful termination
        shutdown_event = threading.Event()
        
        # Define signal handler function
        def signal_handler(sig, frame):
            print("\n\n[INFO] Received interrupt signal. Shutting down gracefully...")
            shutdown_event.set()
            # Give system time to clean up
            time.sleep(0.5)
            sys.exit(0)
        
        # Set up signal handler in main thread
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Run streaming in main thread
            system.run_streaming(args.repo, shutdown_event)
        except KeyboardInterrupt:
            print("\n[INFO] Keyboard interrupt received. Shutting down...")
            shutdown_event.set()
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Run in batch mode (legacy)
        print("\n[MODE] Starting in BATCH mode (one-time)\n")
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