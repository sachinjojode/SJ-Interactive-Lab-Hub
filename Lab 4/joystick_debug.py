#!/usr/bin/env python3
"""
Simple joystick test with error handling
"""
import qwiic_joystick
import time
import sys

def test_joystick():
    """Test joystick connection with detailed error reporting"""
    print("Testing SparkFun Qwiic Joystick...")
    
    try:
        # Create joystick object
        myJoystick = qwiic_joystick.QwiicJoystick()
        print("Joystick object created")
        
        # Check connection
        if myJoystick.connected == False:
            print("ERROR: Joystick not connected!")
            print("Troubleshooting steps:")
            print("1. Check Qwiic connector is fully seated")
            print("2. Verify power to joystick (LED should be lit)")
            print("3. Try unplugging and reconnecting")
            return False
        
        print("SUCCESS: Joystick connected!")
        
        # Initialize
        if myJoystick.begin() == False:
            print("ERROR: Failed to initialize joystick")
            return False
        
        print("SUCCESS: Joystick initialized!")
        print(f"Firmware Version: {myJoystick.version}")
        
        # Test reading values
        print("\nTesting joystick readings...")
        for i in range(5):
            try:
                x_val = myJoystick.horizontal
                y_val = myJoystick.vertical
                button_state = myJoystick.button
                print(f"X: {x_val:4d}, Y: {y_val:4d}, Button: {button_state}")
                time.sleep(0.5)
            except Exception as e:
                print(f"ERROR: Error reading joystick: {e}")
                return False
        
        print("SUCCESS: Joystick test successful!")
        return True
        
    except Exception as e:
        print(f"ERROR: Joystick test failed: {e}")
        print("Possible issues:")
        print("1. I2C bus problem")
        print("2. Hardware connection issue")
        print("3. Power problem")
        return False

if __name__ == "__main__":
    success = test_joystick()
    if success:
        print("\nSUCCESS: Joystick is working correctly!")
    else:
        print("\nFAILED: Joystick test failed - check connections")
