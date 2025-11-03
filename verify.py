#!/usr/bin/env python3
"""
Deployment Verification Script for Options Scalping Bot
Validates configuration, connectivity, and system readiness.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_header(text: str) -> None:
    """Print formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_result(check: str, passed: bool, message: str = "") -> None:
    """Print check result with color coding."""
    status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
    print(f"{status} {check}")
    if message:
        prefix = "  " if passed else f"  {YELLOW}→{RESET} "
        print(f"{prefix}{message}")


def check_python_version() -> Tuple[bool, str]:
    """Verify Python version is 3.9 or higher."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)"


def check_dependencies() -> Tuple[bool, str]:
    """Check if required Python packages are installed."""
    required = [
        "alpaca_trade_api",
        "pandas",
        "numpy",
        "yaml",
        "requests",
        "apscheduler",
        "pytz",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, f"All {len(required)} packages installed"


def check_file_structure() -> Tuple[bool, str]:
    """Verify required files and directories exist."""
    base_dir = Path(__file__).parent
    required_files = [
        "main.py",
        "broker.py",
        "scan.py",
        "signals.py",
        "monitor.py",
        "notifications.py",
        "utils.py",
        "requirements.txt",
    ]
    
    required_dirs = ["tests", "data", "logs"]
    
    missing_files = [f for f in required_files if not (base_dir / f).exists()]
    missing_dirs = [d for d in required_dirs if not (base_dir / d).is_dir()]
    
    if missing_files or missing_dirs:
        items = missing_files + missing_dirs
        return False, f"Missing: {', '.join(items)}"
    return True, "All required files and directories present"


def check_configuration() -> Tuple[bool, str]:
    """Validate configuration file."""
    try:
        from utils import load_config
        
        config = load_config()
        
        # Check mode
        mode = config.get("mode")
        if mode not in ["paper", "live"]:
            return False, f"Invalid mode: {mode} (must be 'paper' or 'live')"
        
        # Check Alpaca config
        alpaca = config.get("alpaca", {})
        mode_cfg = alpaca.get(mode, {})
        
        api_key = mode_cfg.get("api_key_id", "")
        api_secret = mode_cfg.get("api_secret_key", "")
        
        if not api_key or not api_secret:
            return False, "Alpaca API keys not configured"
        
        if "YOUR_" in api_key or "YOUR_" in api_secret:
            return False, "Placeholder API keys detected - update config.yaml"
        
        # Check watchlist
        symbols = config.get("watchlist", {}).get("symbols", [])
        if not symbols:
            return False, "Watchlist is empty"
        
        return True, f"Valid ({mode} mode, {len(symbols)} symbols in watchlist)"
        
    except FileNotFoundError:
        return False, "config.yaml not found - copy from config.yaml.example"
    except Exception as e:
        return False, f"Config error: {e}"


def check_broker_connectivity() -> Tuple[bool, str]:
    """Test connection to Alpaca API."""
    try:
        from broker import BrokerClient
        from utils import load_config
        
        config = load_config()
        broker = BrokerClient(config)
        
        # Try to get account info
        account = broker.get_account()
        cash = float(account.get("cash", 0))
        
        return True, f"Connected (${cash:,.2f} cash available)"
        
    except ValueError as e:
        return False, f"Configuration error: {e}"
    except Exception as e:
        return False, f"Connection failed: {e}"


def check_discord_webhook() -> Tuple[bool, str]:
    """Test Discord webhook."""
    try:
        from notifications import DiscordNotifier
        from utils import load_config
        
        config = load_config()
        webhook_url = config.get("notifications", {}).get("discord_webhook_url", "")
        
        if not webhook_url:
            return False, "Discord webhook not configured (optional)"
        
        if "your_webhook" in webhook_url.lower():
            return False, "Placeholder webhook detected"
        
        notifier = DiscordNotifier(webhook_url)
        
        # Try to send test message
        try:
            notifier.send("✅ Verification test from scalp-bot")
            return True, "Webhook configured and tested"
        except Exception as send_error:
            return False, f"Webhook invalid: {send_error}"
            
    except Exception as e:
        return False, f"Error: {e}"


def check_timezone() -> Tuple[bool, str]:
    """Verify system timezone configuration."""
    try:
        import pytz
        from datetime import datetime
        
        # Check if US/Eastern is available
        eastern = pytz.timezone("US/Eastern")
        now_et = datetime.now(eastern)
        
        return True, f"Timezone support OK (current ET: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')})"
        
    except Exception as e:
        return False, f"Timezone error: {e}"


def check_permissions() -> Tuple[bool, str]:
    """Check write permissions for data and logs directories."""
    base_dir = Path(__file__).parent
    
    try:
        # Try to write to data dir
        test_file = base_dir / "data" / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        
        # Try to write to logs dir
        test_file = base_dir / "logs" / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        
        return True, "Read/write permissions OK"
        
    except Exception as e:
        return False, f"Permission error: {e}"


def check_tests() -> Tuple[bool, str]:
    """Verify tests can run."""
    try:
        import pytest
        
        # Count test files
        base_dir = Path(__file__).parent
        test_files = list((base_dir / "tests").glob("test_*.py"))
        
        if not test_files:
            return False, "No test files found"
        
        return True, f"{len(test_files)} test modules found"
        
    except ImportError:
        return False, "pytest not installed"
    except Exception as e:
        return False, f"Error: {e}"


def run_verification() -> bool:
    """Run all verification checks."""
    print_header("Options Scalping Bot - Deployment Verification")
    
    checks: List[Tuple[str, Tuple[bool, str]]] = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()),
        ("File Structure", check_file_structure()),
        ("Configuration", check_configuration()),
        ("Broker Connectivity", check_broker_connectivity()),
        ("Discord Webhook", check_discord_webhook()),
        ("Timezone Support", check_timezone()),
        ("File Permissions", check_permissions()),
        ("Test Suite", check_tests()),
    ]
    
    all_passed = True
    
    for check_name, (passed, message) in checks:
        print_result(check_name, passed, message)
        if not passed:
            all_passed = False
    
    # Summary
    print_header("Verification Summary")
    
    if all_passed:
        print(f"{GREEN}✓ All checks passed! Bot is ready for deployment.{RESET}\n")
        print("Next steps:")
        print("1. Review configuration in config.yaml")
        print("2. Run tests: pytest")
        print("3. Start bot: python main.py")
        print("4. Monitor logs: tail -f logs/bot.log\n")
        return True
    else:
        print(f"{RED}✗ Some checks failed. Please fix the issues above.{RESET}\n")
        print("Common fixes:")
        print("- Run setup.sh to install dependencies")
        print("- Copy config.yaml.example to config.yaml and configure")
        print("- Ensure API keys are valid\n")
        return False


if __name__ == "__main__":
    try:
        success = run_verification()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Verification cancelled by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{RED}Verification failed with error: {e}{RESET}")
        sys.exit(1)
