#!/usr/bin/env python3
"""
Setup Verification Script

TEACHING: Pre-flight Checks
============================================================================
Before running experiments, we should verify that all dependencies and
infrastructure are properly configured. This script checks:

1. Python dependencies (torch, unsloth, transformers)
2. GPU availability and CUDA setup
3. Docker and Ollama container status
4. Ollama API responsiveness
5. Directory structure

This is a good practice in ML engineering - fail fast with clear error
messages rather than waiting for experiments to crash.
============================================================================
"""

import os
import sys
import subprocess
import json
from typing import Tuple, List

# ANSI color codes for pretty terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")


def check_mark(passed: bool) -> str:
    """Return a checkmark or X based on status"""
    return f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"


def run_command(cmd: List[str], capture_output: bool = True) -> Tuple[bool, str]:
    """
    Run a shell command and return (success, output)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_python_version() -> bool:
    """Check if Python version is 3.10+"""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 10
    print(f"{check_mark(is_valid)} Python version: {version.major}.{version.minor}.{version.micro}")
    if not is_valid:
        print(f"   {YELLOW}⚠️  Python 3.10+ recommended (you have {version.major}.{version.minor}){RESET}")
    return is_valid


def check_import(module_name: str, display_name: str = None) -> bool:
    """Check if a Python module can be imported"""
    display_name = display_name or module_name
    try:
        __import__(module_name)
        print(f"{check_mark(True)} {display_name} installed")
        return True
    except ImportError:
        print(f"{check_mark(False)} {display_name} not found")
        print(f"   Install: pip install {module_name}")
        return False


def check_gpu() -> bool:
    """Check CUDA availability and GPU info"""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"{check_mark(cuda_available)} CUDA available: {cuda_available}")

        if cuda_available:
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"   📊 GPU: {gpu_name}")
            print(f"   💾 VRAM: {gpu_memory:.1f} GB")
            print(f"   🔢 Count: {gpu_count}")
            return True
        else:
            print(f"   {YELLOW}⚠️  No GPU detected. Training will be slow.{RESET}")
            return False
    except ImportError:
        print(f"{check_mark(False)} Cannot check GPU (torch not installed)")
        return False


def check_docker() -> bool:
    """Check if Docker is running"""
    success, output = run_command(["docker", "ps"])
    print(f"{check_mark(success)} Docker daemon running")
    if not success:
        print(f"   {RED}Start Docker: sudo systemctl start docker{RESET}")
    return success


def check_ollama_container() -> bool:
    """Check if Ollama container is running"""
    success, output = run_command(["docker", "ps", "--filter", "name=ollama", "--format", "{{.Names}}"])
    is_running = success and "ollama" in output
    print(f"{check_mark(is_running)} Ollama container running")
    if not is_running:
        print(f"   {YELLOW}Start Ollama: docker-compose up -d{RESET}")
    return is_running


def check_ollama_api() -> bool:
    """Check if Ollama API is responsive"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        is_ok = response.status_code == 200
        print(f"{check_mark(is_ok)} Ollama API responding")

        if is_ok:
            data = response.json()
            models = data.get("models", [])
            print(f"   📦 Models registered: {len(models)}")
            if models:
                for model in models[:3]:  # Show first 3
                    print(f"      • {model['name']}")
        return is_ok
    except Exception as e:
        print(f"{check_mark(False)} Ollama API not responding")
        print(f"   {RED}Error: {e}{RESET}")
        return False


def check_directory_structure() -> bool:
    """Check if required directories exist"""
    required_dirs = [
        "scripts",
        "benchmark",
        "experiments",
        "datasets",
        "docs/agents"
    ]

    all_exist = True
    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        print(f"{check_mark(exists)} {dir_path}/")
        if not exists:
            all_exist = False

    return all_exist


def check_required_files() -> bool:
    """Check if critical files exist"""
    required_files = [
        "docker-compose.yml",
        "requirements.txt",
        "scripts/export_to_ollama.py",
        "docs/agents/agent5_teaching.md"
    ]

    all_exist = True
    for file_path in required_files:
        exists = os.path.isfile(file_path)
        print(f"{check_mark(exists)} {file_path}")
        if not exists:
            all_exist = False

    return all_exist


def main():
    print(f"\n{BOLD}{GREEN}🔍 DGX Fast Fine-tuning System - Setup Verification{RESET}")

    results = {}

    # Python & Dependencies
    print_header("Python & Dependencies")
    results["python_version"] = check_python_version()
    results["torch"] = check_import("torch", "PyTorch")
    results["transformers"] = check_import("transformers", "Transformers")
    results["unsloth"] = check_import("unsloth", "Unsloth")
    results["requests"] = check_import("requests", "Requests")
    results["pandas"] = check_import("pandas", "Pandas")

    # GPU & CUDA
    print_header("GPU & CUDA")
    results["gpu"] = check_gpu()

    # Docker & Ollama
    print_header("Docker & Ollama")
    results["docker"] = check_docker()
    results["ollama_container"] = check_ollama_container()
    if results["ollama_container"]:
        results["ollama_api"] = check_ollama_api()
    else:
        results["ollama_api"] = False

    # File Structure
    print_header("Project Structure")
    results["directories"] = check_directory_structure()
    print()
    results["files"] = check_required_files()

    # Summary
    print_header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    percentage = (passed / total) * 100

    if percentage == 100:
        print(f"{GREEN}{BOLD}✅ All checks passed! ({passed}/{total}){RESET}")
        print(f"\n{GREEN}🚀 You're ready to start training!{RESET}\n")
        return 0
    elif percentage >= 70:
        print(f"{YELLOW}{BOLD}⚠️  Most checks passed ({passed}/{total}){RESET}")
        print(f"\n{YELLOW}You can proceed, but fix the issues above for best results.{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}❌ Setup incomplete ({passed}/{total} checks passed){RESET}")
        print(f"\n{RED}Please fix the issues above before proceeding.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
