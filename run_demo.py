#!/usr/bin/env python
"""
AquaWatch NRW Detection System - Demo Runner
=============================================

Run all demos to test the enterprise platform.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"🌊 {title}")
    print("=" * 70)

def run_enterprise_summary():
    """Run enterprise summary."""
    print_header("ENTERPRISE PLATFORM OVERVIEW")
    try:
        from enterprise import print_enterprise_summary
        print_enterprise_summary()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_waas_demo():
    """Run Water-as-a-Service demo."""
    print_header("WATER-AS-A-SERVICE (WaaS) PLATFORM")
    try:
        from enterprise.waas_platform import demo_waas
        demo_waas()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_insurance_demo():
    """Run Water Insurance demo."""
    print_header("WATER INSURANCE & RISK TRANSFER")
    try:
        from enterprise.water_insurance import demo_insurance
        demo_insurance()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_trading_demo():
    """Run Water Trading demo."""
    print_header("WATER TRADING PLATFORM")
    try:
        from enterprise.water_trading import demo_trading
        demo_trading()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_consulting_demo():
    """Run Consulting Services demo."""
    print_header("CONSULTING SERVICES")
    try:
        from enterprise.consulting_services import demo_consulting
        demo_consulting()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_smart_building_demo():
    """Run Smart Building demo."""
    print_header("SMART BUILDING WATER MANAGEMENT")
    try:
        from enterprise.smart_building import demo_smart_building
        demo_smart_building()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main demo runner."""
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║     🌊 AQUAWATCH NRW DETECTION SYSTEM - ENTERPRISE PLATFORM 🌊      ║
    ║                                                                      ║
    ║         AI-Powered Water Intelligence for Africa & Beyond            ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    demos = [
        ("Enterprise Overview", run_enterprise_summary),
        ("Water-as-a-Service", run_waas_demo),
        ("Water Insurance", run_insurance_demo),
        ("Water Trading", run_trading_demo),
        ("Consulting Services", run_consulting_demo),
        ("Smart Building", run_smart_building_demo),
    ]
    
    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos)+1}. Run ALL demos")
    print("  0. Exit")
    
    try:
        choice = input("\nSelect demo to run (0-{0}): ".format(len(demos)+1))
        choice = int(choice)
        
        if choice == 0:
            print("Goodbye!")
            return
        elif choice == len(demos) + 1:
            # Run all
            results = []
            for name, func in demos:
                success = func()
                results.append((name, success))
            
            print("\n" + "=" * 70)
            print("📊 DEMO RESULTS")
            print("=" * 70)
            for name, success in results:
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  {status} - {name}")
        elif 1 <= choice <= len(demos):
            name, func = demos[choice - 1]
            func()
        else:
            print("Invalid choice")
    except ValueError:
        print("Please enter a number")
    except KeyboardInterrupt:
        print("\n\nDemo cancelled.")


if __name__ == "__main__":
    main()
