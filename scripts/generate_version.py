#!/usr/bin/env python3
"""
Generate version information at build time from git metadata.
This script eliminates the need for manual version file updates.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

def run_git_command(cmd: str) -> str:
    """Run a git command and return the output"""
    try:
        result = subprocess.run(
            cmd.split(), 
            capture_output=True, 
            text=True, 
            check=True,
            cwd=Path(__file__).parent.parent  # Ensure we're in project root
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

def generate_version_info() -> dict:
    """Generate comprehensive version information from git or Railway environment"""
    
    # Try git first, fallback to Railway environment variables
    commit_hash = run_git_command("git rev-parse HEAD")
    commit_short = run_git_command("git rev-parse --short HEAD")
    branch = run_git_command("git rev-parse --abbrev-ref HEAD")
    author = run_git_command("git log -1 --pretty=format:%an")
    commit_message = run_git_command("git log -1 --pretty=format:%s")
    
    # Railway fallbacks if git is not available
    if commit_hash == "unknown":
        commit_hash = os.getenv("RAILWAY_GIT_COMMIT_SHA", "unknown")
    if commit_short == "unknown" and commit_hash != "unknown":
        commit_short = commit_hash[:7]
    if branch == "unknown":
        branch = os.getenv("RAILWAY_GIT_BRANCH", "master")
    if author == "unknown":
        author = os.getenv("RAILWAY_GIT_AUTHOR", "Railway Deploy")
    if commit_message == "unknown":
        commit_message = os.getenv("RAILWAY_GIT_COMMIT_MESSAGE", "Railway deployment")
    
    # Generate version string
    base_version = "2.1.0"
    if commit_short != "unknown":
        version = f"{base_version}-development+{commit_short}"
    else:
        version = f"{base_version}-development+unknown"
    
    # Build timestamp
    build_time = datetime.now(timezone.utc).isoformat()
    
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development")
    platform = os.getenv("RAILWAY_ENVIRONMENT", "local")
    if platform != "local":
        platform = "railway"
    
    return {
        "version": version,
        "base_version": base_version,
        "build_time": build_time,
        "git": {
            "commit": commit_hash,
            "commit_short": commit_short,
            "branch": branch,
            "author": author,
            "message": commit_message
        },
        "deployment": {
            "service_id": os.getenv("RAILWAY_SERVICE_ID", "local"),
            "environment": environment,
            "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "local-build"),
            "platform": platform
        },
        "app": {
            "name": "linkedin-ingestion",
            "description": "LinkedIn Profile and Company Data Ingestion Service"
        }
    }

def write_version_files(version_info: dict):
    """Write version information to all required files"""
    
    # Get project root (script is in scripts/ subdirectory)
    project_root = Path(__file__).parent.parent
    
    # 1. Write VERSION file (simple version string)
    version_file = project_root / "VERSION"
    with open(version_file, 'w') as f:
        f.write(f"{version_info['version']}\n")
    
    # 2. Write version.json (complete version info)
    version_json = project_root / "version.json"
    with open(version_json, 'w') as f:
        json.dump(version_info, f, indent=2)
        f.write('\n')
    
    # 3. Update config.py with the version (but keep it as fallback)
    config_file = project_root / "app" / "core" / "config.py"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        # Replace the hardcoded version line
        import re
        pattern = r'VERSION: str = "[^"]*"'
        replacement = f'VERSION: str = "{version_info["version"]}"'
        
        updated_content = re.sub(pattern, replacement, config_content)
        
        with open(config_file, 'w') as f:
            f.write(updated_content)
    
    print(f"✅ Generated version files for: {version_info['version']}")
    print(f"   Git commit: {version_info['git']['commit_short']} ({version_info['git']['message']})")
    print(f"   Build time: {version_info['build_time']}")
    print(f"   Platform: {version_info['deployment']['platform']}")

def main():
    """Main entry point"""
    try:
        version_info = generate_version_info()
        write_version_files(version_info)
        print("✅ Version information generated successfully")
        return 0
    except Exception as e:
        print(f"❌ Error generating version information: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
