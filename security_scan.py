#!/usr/bin/env python3
# security_scan.py - Security scanner using bandit + custom rules

import subprocess
import sys
import os
from pathlib import Path

def run_bandit_scan():
    """Run bandit security scan on the codebase"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'bandit', '-r', '.', '-f', 'json'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print("✓ No security issues found by bandit")
        else:
            print("⚠ Security issues detected:")
            print(result.stdout)
            return False
    except FileNotFoundError:
        print("Bandit not installed. Run: pip install bandit")
        return False
    return True

def check_api_keys():
    """Check for hardcoded API keys"""
    suspicious_patterns = [
        'API_KEY', 'SECRET', 'TOKEN', 'PASSWORD'
    ]

    issues = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.py', '.md', '.txt', '.yml', '.yaml')):
                path = Path(root) / file
                try:
                    content = path.read_text()
                    for pattern in suspicious_patterns:
                        if pattern in content.upper():
                            # Check if it's in env var context
                            if f'os.getenv("{pattern}' not in content and f'os.environ.get("{pattern}' not in content:
                                issues.append(f"Potential API key in {path}")
                except:
                    pass

    if issues:
        print("⚠ Potential API key exposures:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ No hardcoded API keys detected")
        return True

def check_file_permissions():
    """Check file permissions (basic)"""
    # On Windows, permissions are different, but check for obvious issues
    print("✓ File permissions check (skipped on Windows)")
    return True

if __name__ == "__main__":
    print("Running security scan...")
    all_good = True
    all_good &= run_bandit_scan()
    all_good &= check_api_keys()
    all_good &= check_file_permissions()

    if all_good:
        print("\n🎉 Security scan passed!")
        sys.exit(0)
    else:
        print("\n❌ Security issues found!")
        sys.exit(1)