#!/usr/bin/env python3
"""
Expert System Installation Verification
========================================

Quick verification script to check expert system installation and dependencies.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    print("="*80)
    print("EXPERT SYSTEM INSTALLATION VERIFICATION")
    print("="*80)
    print("\n1. Checking Dependencies...")
    print("-" * 80)

    dependencies = {
        "numpy": "Core numerical operations",
        "chromadb": "Vector database (optional but recommended)",
        "faiss": "High-performance vector search (optional)",
        "torch": "Deep learning for fine-tuning (optional)",
    }

    results = {}
    for package, description in dependencies.items():
        try:
            if package == "faiss":
                # Try both faiss-cpu and faiss-gpu
                try:
                    import faiss
                    results[package] = True
                except ImportError:
                    results[package] = False
            else:
                __import__(package)
                results[package] = True
        except ImportError:
            results[package] = False

        status = "✓" if results[package] else "✗"
        print(f"{status} {package:15} - {description}")

    # Check if at least one vector store is available
    vector_store_available = results.get("chromadb", False) or results.get("faiss", False)

    print("\n" + "-" * 80)
    if not results.get("numpy", False):
        print("✗ CRITICAL: numpy is required")
        return False
    elif not vector_store_available:
        print("✗ CRITICAL: At least one vector store (chromadb or faiss) is required")
        return False
    else:
        print("✓ Minimum dependencies satisfied")
        return True


def check_files():
    """Check if expert system files are present."""
    print("\n2. Checking Files...")
    print("-" * 80)

    base_path = Path(__file__).parent

    required_files = {
        "Core System": "src/blank_business_builder/expert_system.py",
        "Fine-Tuning": "src/blank_business_builder/expert_finetuning.py",
        "Integration": "src/blank_business_builder/expert_integration.py",
        "Demo": "demo_expert_system.py",
        "Tests": "test_expert_system.py",
        "Requirements": "requirements_expert_system.txt",
    }

    all_present = True
    for name, filepath in required_files.items():
        full_path = base_path / filepath
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {name:15} - {filepath}")
        if not exists:
            all_present = False

    print("\n" + "-" * 80)
    if all_present:
        print("✓ All required files present")
        return True
    else:
        print("✗ Some files are missing")
        return False


def check_imports():
    """Check if expert system modules can be imported."""
    print("\n3. Checking Module Imports...")
    print("-" * 80)

    sys.path.insert(0, str(Path(__file__).parent / "src"))

    modules = {
        "expert_system": "blank_business_builder.expert_system",
        "expert_finetuning": "blank_business_builder.expert_finetuning",
        "expert_integration": "blank_business_builder.expert_integration",
    }

    all_imported = True
    for name, module_path in modules.items():
        try:
            __import__(module_path)
            print(f"✓ {name:20} - Successfully imported")
        except Exception as e:
            print(f"✗ {name:20} - Import failed: {e}")
            all_imported = False

    print("\n" + "-" * 80)
    if all_imported:
        print("✓ All modules imported successfully")
        return True
    else:
        print("✗ Some modules failed to import")
        return False


def check_system_initialization():
    """Check if expert system can be initialized."""
    print("\n4. Checking System Initialization...")
    print("-" * 80)

    sys.path.insert(0, str(Path(__file__).parent / "src"))

    try:
        from blank_business_builder.expert_system import (
            MultiDomainExpertSystem,
            ExpertDomain,
            CHROMADB_AVAILABLE,
            FAISS_AVAILABLE
        )

        print(f"  ChromaDB Available: {CHROMADB_AVAILABLE}")
        print(f"  FAISS Available: {FAISS_AVAILABLE}")

        # Try to initialize system
        use_chromadb = CHROMADB_AVAILABLE
        print(f"\n  Initializing with {'ChromaDB' if use_chromadb else 'FAISS'}...")

        system = MultiDomainExpertSystem(use_chromadb=use_chromadb)

        print(f"  ✓ System initialized")
        print(f"  ✓ {len(system.experts)} domain experts created")
        print(f"  ✓ Vector store: {type(system.vector_store).__name__}")

        # Check experts
        expected_domains = [
            ExpertDomain.CHEMISTRY,
            ExpertDomain.BIOLOGY,
            ExpertDomain.PHYSICS,
            ExpertDomain.MATERIALS_SCIENCE
        ]

        for domain in expected_domains:
            if domain in system.experts:
                expert = system.experts[domain]
                print(f"  ✓ {domain.value:20} - {expert.expert_id}")

        print("\n" + "-" * 80)
        print("✓ System initialization successful")
        return True

    except Exception as e:
        print(f"✗ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "-" * 80)
        print("✗ System initialization failed")
        return False


def print_next_steps():
    """Print next steps for user."""
    print("\n5. Next Steps")
    print("-" * 80)
    print("""
Quick Start:

  1. Run the demo:
     python demo_expert_system.py

  2. Run the tests:
     python test_expert_system.py

  3. Try a simple query:
     python -c "
     import asyncio
     from blank_business_builder.expert_system import *

     async def test():
         system = MultiDomainExpertSystem(use_chromadb=True)
         query = ExpertQuery(query='What is chemistry?', domain=ExpertDomain.CHEMISTRY)
         response = await system.query(query)
         print(f'Answer: {response.answer}')

     asyncio.run(test())
     "

  4. Read the documentation:
     - EXPERT_SYSTEM_README.md (full documentation)
     - EXPERT_SYSTEM_QUICKSTART.md (quick start guide)
     - EXPERT_SYSTEM_ARCHITECTURE.md (architecture diagrams)

  5. Integrate with BBB:
     python -m blank_business_builder.expert_integration "Your Business" "Your Name" 0.1
""")


def main():
    """Run all verification checks."""
    checks = [
        ("Dependencies", check_dependencies),
        ("Files", check_files),
        ("Imports", check_imports),
        ("Initialization", check_system_initialization),
    ]

    results = {}
    for check_name, check_func in checks:
        results[check_name] = check_func()

    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} - {check_name}")

    all_passed = all(results.values())

    print("\n" + "="*80)
    if all_passed:
        print("✓✓✓ ALL CHECKS PASSED ✓✓✓")
        print("\nExpert system is properly installed and ready to use!")
        print_next_steps()
        return 0
    else:
        print("✗✗✗ SOME CHECKS FAILED ✗✗✗")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements_expert_system.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
