#!/usr/bin/env python3
"""
Structure Verification Script

This script verifies that the API has been properly restructured and all
required files are in place for standalone deployment.
"""

import os
import sys
from pathlib import Path


def check_file(path, description):
    """Check if a file exists."""
    if path.exists():
        size = path.stat().st_size
        print(f"  ✅ {description}: {path} ({size:,} bytes)")
        return True
    else:
        print(f"  ❌ {description}: {path} NOT FOUND")
        return False


def check_directory(path, description):
    """Check if a directory exists."""
    if path.exists() and path.is_dir():
        files = list(path.iterdir())
        print(f"  ✅ {description}: {path} ({len(files)} items)")
        return True
    else:
        print(f"  ❌ {description}: {path} NOT FOUND")
        return False


def main():
    """Run verification checks."""
    print("=" * 80)
    print("Citation Intent API - Structure Verification")
    print("=" * 80)
    
    # Get API root directory
    api_root = Path(__file__).parent.parent
    print(f"\nAPI Root: {api_root}\n")
    
    all_checks_passed = True
    
    # Check directories
    print("1. Directory Structure:")
    all_checks_passed &= check_directory(api_root / "config", "Config directory")
    all_checks_passed &= check_directory(api_root / "data", "Data directory")
    all_checks_passed &= check_directory(api_root / "data" / "scicite", "SciCite data")
    all_checks_passed &= check_directory(api_root / "data" / "acl-arc", "ACL-ARC data")
    all_checks_passed &= check_directory(api_root / "src", "Source code directory")
    all_checks_passed &= check_directory(api_root / "scripts", "Scripts directory")
    all_checks_passed &= check_directory(api_root / "docs", "Documentation directory")
    all_checks_passed &= check_directory(api_root / "tests", "Tests directory")
    
    # Check configuration files
    print("\n2. Configuration Files:")
    all_checks_passed &= check_file(api_root / "config" / "config.json", "Main config")
    all_checks_passed &= check_file(api_root / "config" / "system_prompts.json", "System prompts")
    
    # Check data files
    print("\n3. Training Data:")
    all_checks_passed &= check_file(api_root / "data" / "scicite" / "train.csv", "SciCite training data")
    all_checks_passed &= check_file(api_root / "data" / "acl-arc" / "train.csv", "ACL-ARC training data")
    
    # Check source code
    print("\n4. Source Code:")
    all_checks_passed &= check_file(api_root / "src" / "main.py", "FastAPI application")
    all_checks_passed &= check_file(api_root / "src" / "classifier.py", "Classifier module")
    
    # Check scripts
    print("\n5. Scripts:")
    all_checks_passed &= check_file(api_root / "scripts" / "gunicorn.sh", "Gunicorn startup")
    all_checks_passed &= check_file(api_root / "scripts" / "stop.sh", "Shutdown script")
    all_checks_passed &= check_file(api_root / "scripts" / "verify_prompting.py", "Verification script")
    
    # Check documentation
    print("\n6. Documentation:")
    all_checks_passed &= check_file(api_root / "README.md", "Main README")
    all_checks_passed &= check_file(api_root / "docs" / "STANDALONE.md", "Standalone guide")
    all_checks_passed &= check_file(api_root / "docs" / "QUICKSTART.md", "Quick start")
    all_checks_passed &= check_file(api_root / "docs" / "VERIFICATION_GUIDE.md", "Verification guide")
    
    # Check tests
    print("\n7. Tests:")
    all_checks_passed &= check_file(api_root / "tests" / "test_api.py", "Test suite")
    all_checks_passed &= check_file(api_root / "tests" / "example_input.json", "Example input")
    
    # Check other required files
    print("\n8. Other Files:")
    all_checks_passed &= check_file(api_root / "requirements.txt", "Python dependencies")
    
    # Path verification in source files
    print("\n9. Verifying Path References in Source Code:")
    
    try:
        # Check classifier.py imports and paths
        classifier_path = api_root / "src" / "classifier.py"
        with open(classifier_path, 'r') as f:
            classifier_content = f.read()
            
        # Check for old path references
        bad_patterns = [
            "sys.path.append",
            "experimental-configs",
            "datasets/formatted",
            "../experimental-configs",
            "../datasets"
        ]
        
        found_issues = []
        for pattern in bad_patterns:
            if pattern in classifier_content:
                found_issues.append(pattern)
        
        if found_issues:
            print(f"  ❌ classifier.py contains old path references: {found_issues}")
            all_checks_passed = False
        else:
            print("  ✅ classifier.py: No old path references found")
        
        # Check for correct new paths
        if "config/config.json" in classifier_content:
            print("  ✅ classifier.py: Uses new config path")
        else:
            print("  ⚠️  classifier.py: May not use new config path")
        
        if "config/system_prompts.json" in classifier_content:
            print("  ✅ classifier.py: Uses new system_prompts path")
        else:
            print("  ⚠️  classifier.py: May not use new system_prompts path")
            
        if "data/" in classifier_content and "train.csv" in classifier_content:
            print("  ✅ classifier.py: Uses new data path")
        else:
            print("  ⚠️  classifier.py: May not use new data path")
            
    except Exception as e:
        print(f"  ❌ Error checking classifier.py: {e}")
        all_checks_passed = False
    
    # Final result
    print("\n" + "=" * 80)
    if all_checks_passed:
        print("✅ All checks passed! API is properly structured for standalone deployment.")
        print("\nTo start the API:")
        print("  cd api")
        print("  python src/main.py")
    else:
        print("❌ Some checks failed. Please review the errors above.")
        sys.exit(1)
    print("=" * 80)


if __name__ == "__main__":
    main()
