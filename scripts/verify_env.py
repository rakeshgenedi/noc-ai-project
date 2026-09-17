#!/usr/bin/env python3
"""
NOC Environment Verification Script
Validates system prerequisites, directory structure, and configuration files.
Zero external dependencies (uses standard library only).
"""

import sys
import os
import platform
import shutil
import subprocess

REQUIRED_DIRS = [
    "monitoring",
    "exporters",
    "logs",
    "backend",
    "ai",
    "alerts",
    "automation",
    "dashboard",
    "incidents",
    "notifications",
    "docker",
    "configs",
    "scripts",
    "tests",
    "documentation"
]

REQUIRED_FILES = [
    ".env.example",
    ".env",
    "requirements.txt"
]

def print_header(title):
    print("\n" + "=" * 60)
    print(f" [NOC PRE-FLIGHT CHECK] {title}")
    print("=" * 60)

def check_python_version():
    major, minor, micro = sys.version_info[:3]
    version_str = f"{major}.{minor}.{micro}"
    if major >= 3 and minor >= 10:
        print(f"  [PASS] Python Version: {version_str} (>= 3.10 required)")
        return True
    else:
        print(f"  [FAIL] Python Version: {version_str} (Python 3.10+ required)")
        return False

def check_system_resources():
    print(f"  [INFO] Operating System: {platform.system()} {platform.release()} ({platform.machine()})")
    
    # Check disk space in current working directory
    total, used, free = shutil.disk_usage(os.getcwd())
    free_gb = round(free / (1024 ** 3), 2)
    if free_gb >= 5.0:
        print(f"  [PASS] Free Disk Space: {free_gb} GB (minimum 5.0 GB)")
        disk_ok = True
    else:
        print(f"  [WARN] Free Disk Space: {free_gb} GB (< 5.0 GB recommended)")
        disk_ok = False
        
    return disk_ok

def check_directories():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_ok = True
    print("\n  Verifying Project Directory Structure:")
    for d in REQUIRED_DIRS:
        full_path = os.path.join(base_dir, d)
        if os.path.isdir(full_path):
            print(f"    [OK] Directory: /{d}")
        else:
            print(f"    [MISSING] Directory: /{d}")
            all_ok = False
            
    print("\n  Verifying Base Configuration Files:")
    for f in REQUIRED_FILES:
        full_path = os.path.join(base_dir, f)
        if os.path.isfile(full_path):
            print(f"    [OK] File: {f}")
        else:
            print(f"    [MISSING] File: {f}")
            all_ok = False
            
    return all_ok

def check_docker():
    print("\n  Checking Containerization Runtime:")
    docker_found = shutil.which("docker") is not None
    if docker_found:
        try:
            res = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            print(f"    [PASS] Docker found: {res.stdout.strip()}")
            return "docker"
        except Exception:
            print("    [WARN] Docker binary found but failed to respond.")
            return "native"
    else:
        print("    [NOTE] Docker not detected in PATH.")
        print("           Platform will support Native Portable Binaries (Prometheus.exe, Grafana, Loki)")
        print("           or you may install Docker Desktop with WSL2.")
        return "native"

def main():
    print_header("ENVIRONMENT & PREREQUISITES VERIFICATION")
    
    py_ok = check_python_version()
    res_ok = check_system_resources()
    dirs_ok = check_directories()
    runtime_mode = check_docker()
    
    print_header("VERIFICATION SUMMARY")
    if py_ok and dirs_ok:
        print("  STATUS: [SUCCESS] Phase 1 Environment Skeleton is fully validated!")
        print(f"  Selected Runtime Mode: {runtime_mode.upper()} MODE")
        print("  Ready to proceed with dependency installation and Phase 2.")
        return 0
    else:
        print("  STATUS: [FAILED] Some prerequisites or files are missing. Please inspect output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
