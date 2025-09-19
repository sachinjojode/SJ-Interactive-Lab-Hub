# Seasonal Clock - Time measured through seasons
# Winter: Evening to Night (6 PM - 6 AM)
# Fall: Noon to Evening (12 PM - 6 PM) 
# Summer: Morning to Noon (6 AM - 12 PM)
# Spring: Night to Morning (12 AM - 6 AM)

import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)

# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load font for text display
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Button setup (from screen_test.py)
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Seasonal colors and names
seasons = {
    'spring': {'color': (34, 139, 34), 'name': 'SPRING', 'symbol': '🌸'},  # Green
    'summer': {'color': (255, 165, 0), 'name': 'SUMMER', 'symbol': '☀️'},  # Orange
    'fall': {'color': (139, 69, 19), 'name': 'FALL', 'symbol': '🍂'},      # Brown
    'winter': {'color': (135, 206, 235), 'name': 'WINTER', 'symbol': '❄️'}  # Light Blue
}

def get_season_from_hour(hour):
    """Convert 24-hour time to season"""
    if 0 <= hour < 6:      # Night to Morning
        return 'spring'
    elif 6 <= hour < 12:   # Morning to Noon  
        return 'summer'
    elif 12 <= hour < 18:  # Noon to Evening
        return 'fall'
    else:                  # Evening to Night (18-23)
        return 'winter'

def get_seasonal_progress(hour):
    """Get progress within the current season (0.0 to 1.0)"""
    if 0 <= hour < 6:      # Spring: 0-6 hours
        return hour / 6.0
    elif 6 <= hour < 12:   # Summer: 6-12 hours
        return (hour - 6) / 6.0
    elif 12 <= hour < 18: # Fall: 12-18 hours
        return (hour - 12) / 6.0
    else:                  # Winter: 18-24 hours
        return (hour - 18) / 6.0

def draw_seasonal_clock(draw, season, progress, hour, minute, second):
    """Draw the seasonal clock visualization"""
    # Clear the screen with season color (dimmed)
    season_color = seasons[season]['color']
    bg_color = tuple(int(c * 0.1) for c in season_color)  # Dimmed background
    draw.rectangle((0, 0, width, height), outline=0, fill=bg_color)
    
    # Draw season name at top
    season_name = seasons[season]['name']
    draw.text((x + 10, top + 10), season_name, font=font, fill=season_color)
    
    # Draw season symbol
    symbol = seasons[season]['symbol']
    draw.text((x + 10, top + 35), symbol, font=font, fill=season_color)
    
    # Draw progress bar
    bar_width = width - 20
    bar_height = 20
    bar_x = 10
    bar_y = top + 60
    
    # Background bar
    draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), 
                   outline=season_color, fill=(0, 0, 0))
    
    # Progress fill
    fill_width = int(bar_width * progress)
    draw.rectangle((bar_x, bar_y, bar_x + fill_width, bar_y + bar_height), 
                   outline=season_color, fill=season_color)
    
    # Draw actual time (smaller, at bottom)
    time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
    draw.text((x + 10, bottom - 30), time_str, font=small_font, fill=(255, 255, 255))
    
    # Draw progress percentage
    progress_text = f"{int(progress * 100)}%"
    draw.text((x + 10, bottom - 50), progress_text, font=small_font, fill=season_color)

# Interactive mode variables
interactive_mode = False
speed_multiplier = 1.0

print("Seasonal Clock Started!")
print("Button A: Toggle interactive mode")
print("Button B: Change time speed")
print("Both buttons: Reset to real time")

while True:
    # Get current time
    current_time = time.localtime()
    hour = current_time.tm_hour
    minute = current_time.tm_min
    second = current_time.tm_sec
    
    # Check button states
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)
    
    # Handle button interactions
    if a_pressed and b_pressed:
        # Both buttons: Reset to real time
        interactive_mode = False
        speed_multiplier = 1.0
        print("Reset to real time")
    elif a_pressed and not b_pressed:
        # Button A: Toggle interactive mode
        interactive_mode = not interactive_mode
        print(f"Interactive mode: {'ON' if interactive_mode else 'OFF'}")
    elif b_pressed and not a_pressed:
        # Button B: Change speed
        if interactive_mode:
            speed_multiplier = speed_multiplier * 2.0
            if speed_multiplier > 8.0:
                speed_multiplier = 0.5
            print(f"Speed multiplier: {speed_multiplier}x")
    
    # Modify time if in interactive mode
    if interactive_mode:
        # Create a modified hour based on speed
        modified_hour = (hour + int(time.time() * speed_multiplier)) % 24
        season = get_season_from_hour(modified_hour)
        progress = get_seasonal_progress(modified_hour)
    else:
        # Use real time
        season = get_season_from_hour(hour)
        progress = get_seasonal_progress(hour)
    
    # Draw the seasonal clock
    draw_seasonal_clock(draw, season, progress, hour, minute, second)
    
    # Display image
    disp.image(image, rotation)
    
    # Small delay for button debouncing and display refresh
    time.sleep(0.1)
