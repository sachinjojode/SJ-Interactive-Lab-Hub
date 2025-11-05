# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility

# Initialize I2C with retry logic and proper locking
max_retries = 10
i2c = None
apds = None

for attempt in range(max_retries):
    try:
        # Use busio.I2C() for more control
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Wait for lock with timeout
        lock_acquired = False
        for _ in range(100):  # Try 100 times with 0.1s delay = 10s max wait
            if i2c.try_lock():
                lock_acquired = True
                break
            time.sleep(0.1)
        
        if not lock_acquired:
            raise BlockingIOError("Could not acquire I2C lock")
        
        # Release lock - sensor library will handle locking internally
        i2c.unlock()
        
        # Small delay before sensor init
        time.sleep(0.2)
        
        # Initialize sensor
        apds = APDS9960(i2c)
        apds.enable_color = True
        print("Sensor initialized successfully!")
        break
        
    except (BlockingIOError, OSError, ValueError) as e:
        if i2c:
            try:
                if i2c.locked:
                    i2c.unlock()
            except:
                pass
        if attempt < max_retries - 1:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(0.5)
        else:
            print(f"\nFailed to initialize sensor after {max_retries} attempts")
            print("Troubleshooting steps:")
            print("1. Check sensor is connected (power LED should be on)")
            print("2. Verify I2C connections (SDA/SCL)")
            print("3. Try: sudo i2cdetect -y 1")
            print("4. Check if other processes are using I2C")
            raise

if apds is None:
    raise RuntimeError("Sensor initialization failed")


while True:
    # create some variables to store the color data in

    # wait for color data to be ready
    while not apds.color_data_ready:
        time.sleep(0.005)

    # get the data and print the different channels
    r, g, b, c = apds.color_data
    print("red: ", r)
    print("green: ", g)
    print("blue: ", b)
    print("clear: ", c)

    print("color temp {}".format(colorutility.calculate_color_temperature(r, g, b)))
    print("light lux {}".format(colorutility.calculate_lux(r, g, b)))
    time.sleep(0.5)