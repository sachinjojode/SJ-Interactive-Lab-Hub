#!/usr/bin/env python3
"""
Robust I2C scan script that handles errors gracefully
"""
import board
import busio
import time

def scan_i2c_devices():
    """Scan for I2C devices with error handling"""
    try:
        # Initialize I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        print("I2C initialized successfully")
        
        # Try to scan devices
        print("Scanning for I2C devices...")
        
        # Get the lock
        while not i2c.try_lock():
            pass
        
        # Scan addresses
        found_devices = []
        for address in range(0x08, 0x78):  # Valid I2C address range
            try:
                i2c.writeto(address, b'')
                found_devices.append(address)
                print(f"Device found at address: 0x{address:02X}")
            except OSError:
                # No device at this address
                pass
        
        i2c.unlock()
        
        if found_devices:
            print(f"\nFound {len(found_devices)} I2C device(s):")
            for addr in found_devices:
                print(f"  - 0x{addr:02X}")
        else:
            print("\nNo I2C devices found!")
            print("Check your connections:")
            print("1. Make sure Qwiic connector is fully seated")
            print("2. Verify power to the device")
            print("3. Check if device LED is lit")
            
    except Exception as e:
        print(f"I2C scan failed: {e}")
        print("Possible issues:")
        print("1. I2C not enabled (run: sudo raspi-config)")
        print("2. Hardware connection problem")
        print("3. Device not powered")

if __name__ == "__main__":
    scan_i2c_devices()
