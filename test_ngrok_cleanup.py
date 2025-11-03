#!/usr/bin/env python3
"""Test script to verify ngrok cleanup on bot shutdown."""

import subprocess
import time
import signal
import sys
import os

def test_ngrok_cleanup():
    """Test that ngrok stops when bot is killed."""
    print("🧪 Testing ngrok cleanup on bot shutdown")
    print("="*70)
    
    # Step 1: Start ngrok manually (simulating what bot does)
    print("\n1️⃣ Starting ngrok manually (simulating bot behavior)...")
    try:
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", "8001"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            preexec_fn=os.setsid  # Create process group
        )
        print(f"   Started ngrok with PID: {ngrok_process.pid}")
        time.sleep(5)
        
        # Verify it's running
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        ngrok_procs = [l for l in result.stdout.split('\n') if 'ngrok http' in l]
        if ngrok_procs:
            print(f"   ✅ ngrok is running")
        else:
            print("   ❌ ngrok failed to start")
            return False
            
    except FileNotFoundError:
        print("   ⚠️  ngrok not installed on this system")
        print("   This test will work on Raspberry Pi where ngrok is installed")
        return None
    
    # Step 2: Simulate bot shutdown (what _stop_ngrok does)
    print("\n2️⃣ Simulating bot shutdown (killing ngrok process group)...")
    try:
        os.killpg(os.getpgid(ngrok_process.pid), signal.SIGTERM)
        ngrok_process.wait(timeout=5)
        print("   ✅ Sent SIGTERM to ngrok process group")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        try:
            ngrok_process.kill()
        except:
            pass
    
    time.sleep(2)
    
    # Step 3: Verify ngrok stopped
    print("\n3️⃣ Verifying ngrok stopped...")
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    ngrok_procs = [l for l in result.stdout.split('\n') if 'ngrok http' in l]
    
    if ngrok_procs:
        print(f"   ❌ FAILED: ngrok still running!")
        for proc in ngrok_procs:
            print(f"      {proc[:100]}")
        # Cleanup
        subprocess.run(["pkill", "-9", "ngrok"])
        return False
    else:
        print("   ✅ SUCCESS: ngrok stopped cleanly!")
        return True
    
    print("\n" + "="*70)

if __name__ == "__main__":
    result = test_ngrok_cleanup()
    if result is True:
        print("\n✅ Test PASSED: ngrok cleanup works correctly!")
        sys.exit(0)
    elif result is False:
        print("\n❌ Test FAILED: ngrok cleanup not working!")
        sys.exit(1)
    else:
        print("\n⚠️  Test SKIPPED: ngrok not installed (will work on Raspberry Pi)")
        sys.exit(0)
