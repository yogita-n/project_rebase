"""
Repository Fetcher Module

Handles cloning GitHub repositories and validating local repositories.
Implements smart caching to avoid re-cloning existing repositories.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse


class RepoFetcher:
    """
    Fetches and validates Git repositories from GitHub or local paths.
    
    Features:
    - Clone GitHub repositories
    - Validate existing local repositories
    - Smart caching (don't re-clone if exists)
    - Repository health checks
    """
    
    def __init__(self, cache_dir: str = ".repo_cache"):
        """
        Initialize the RepoFetcher.
        
        Args:
            cache_dir: Directory to store cloned repositories
        """
        self.cache_dir = Path(cache_dir).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch(self, repo_input: str) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Fetch a repository from GitHub URL or validate local path.
        
        Args:
            repo_input: GitHub URL or local repository path
            
        Returns:
            Tuple of (success, repo_path, error_message)
        """
        # Check if input is a local path
        if os.path.exists(repo_input):
            return self._validate_local_repo(repo_input)
        
        # Otherwise, treat as GitHub URL
        return self._clone_github_repo(repo_input)
    
    def _validate_local_repo(self, repo_path: str) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Validate a local repository.
        
        Args:
            repo_path: Path to local repository
            
        Returns:
            Tuple of (success, repo_path, error_message)
        """
        repo_path = Path(repo_path).resolve()
        
        # Check if path exists
        if not repo_path.exists():
            return False, None, f"Path does not exist: {repo_path}"
        
        # Check if it's a directory
        if not repo_path.is_dir():
            return False, None, f"Path is not a directory: {repo_path}"
        
        # Check for .git directory (optional but recommended)
        has_git = (repo_path / ".git").exists()
        
        # Check for Python files
        has_python_files = self._has_python_files(repo_path)
        
        if not has_git and not has_python_files:
            return False, None, f"Path does not appear to be a valid repository (no .git or .py files): {repo_path}"
        
        return True, repo_path, None
    
    def _clone_github_repo(self, github_url: str) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Clone a GitHub repository or use cached version.
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Tuple of (success, repo_path, error_message)
        """
        # Parse the GitHub URL to extract repo name
        repo_name = self._extract_repo_name(github_url)
        if not repo_name:
            return False, None, f"Invalid GitHub URL: {github_url}"
        
        # Determine cache path
        cached_repo_path = self.cache_dir / repo_name
        
        # Check if already cloned
        if cached_repo_path.exists():
            print(f"[OK] Repository already cached at: {cached_repo_path}")
            # Validate the cached repo
            is_valid, path, error = self._validate_local_repo(str(cached_repo_path))
            if is_valid:
                return True, path, None
            else:
                # Cached repo is invalid, remove and re-clone
                print(f"[WARNING] Cached repository is invalid, removing and re-cloning...")
                shutil.rmtree(cached_repo_path)
        
        # Clone the repository
        print(f"[CLONE] Cloning repository: {github_url}")
        try:
            result = subprocess.run(
                ["git", "clone", github_url, str(cached_repo_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                return False, None, f"Git clone failed: {result.stderr}"
            
            print(f"[OK] Successfully cloned to: {cached_repo_path}")
            return True, cached_repo_path, None
            
        except subprocess.TimeoutExpired:
            return False, None, "Git clone timed out after 5 minutes"
        except FileNotFoundError:
            return False, None, "Git is not installed or not in PATH"
        except Exception as e:
            return False, None, f"Unexpected error during clone: {str(e)}"
    
    def _extract_repo_name(self, github_url: str) -> Optional[str]:
        """
        Extract repository name from GitHub URL.
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Repository name or None if invalid
        """
        try:
            # Handle various GitHub URL formats:
            # - https://github.com/user/repo
            # - https://github.com/user/repo.git
            # - git@github.com:user/repo.git
            
            if github_url.startswith("git@"):
                # SSH format: git@github.com:user/repo.git
                parts = github_url.split(":")
                if len(parts) == 2:
                    repo_path = parts[1].replace(".git", "")
                    return repo_path.replace("/", "_")
            else:
                # HTTPS format
                parsed = urlparse(github_url)
                path = parsed.path.strip("/").replace(".git", "")
                if path:
                    return path.replace("/", "_")
            
            return None
        except Exception:
            return None
    
    def _has_python_files(self, repo_path: Path) -> bool:
        """
        Check if repository contains Python files.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            True if Python files found, False otherwise
        """
        try:
            # Search for .py files (limit depth to avoid performance issues)
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and common non-code directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
                
                # Check for Python files
                if any(f.endswith('.py') for f in files):
                    return True
                
                # Limit search depth
                depth = len(Path(root).relative_to(repo_path).parts)
                if depth >= 5:
                    break
            
            return False
        except Exception:
            return False
    
    def cleanup_cache(self):
        """
        Remove all cached repositories.
        """
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Cleaned cache directory: {self.cache_dir}")


def main():
    """
    Test the RepoFetcher module.
    """
    fetcher = RepoFetcher()
    
    # Test with a sample GitHub repo
    print("=" * 60)
    print("Testing RepoFetcher")
    print("=" * 60)
    
    # Example: Test with a local path
    test_local = "."
    print(f"\n[LOCAL] Testing local path: {test_local}")
    success, path, error = fetcher.fetch(test_local)
    if success:
        print(f"[OK] Success: {path}")
    else:
        print(f"[ERROR] Error: {error}")
    
    # Example: Test with GitHub URL (uncomment to test)
    # test_github = "https://github.com/psf/requests"
    # print(f"\n[GITHUB] Testing GitHub URL: {test_github}")
    # success, path, error = fetcher.fetch(test_github)
    # if success:
    #     print(f"[OK] Success: {path}")
    # else:
    #     print(f"[ERROR] Error: {error}")


if __name__ == "__main__":
    main()
