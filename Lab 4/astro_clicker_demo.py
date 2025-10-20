from __future__ import print_function
import qwiic_joystick
import time
import sys
import subprocess
import random
import argparse

# --- Global Output Mode Control ---
OUTPUT_MODE = 'speaker'

# --- Text-to-Speech Function ---
def speak_text(text):
    """
    Simple text-to-speech using espeak.
    Checks the global OUTPUT_MODE; if 'silent', it only prints the text.
    """
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Always print the text to the console as a log, regardless of mode
    print(f"Assistant: {clean_text}")

    if OUTPUT_MODE == 'speaker':
        # Execute text-to-speech via espeak - NON-BLOCKING
        try:
            subprocess.Popen(['espeak', f'"{clean_text}"'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"TTS Error: {e}")


# --- Night Sky Data Structure (Data Grouped by Layer) ---

# Layer 0: Closest (Move Down to get here from 1)
CONSTELLATION_DATA = [
    {"name": "Orion the Hunter", "type": "Constellation", "fact": "Contains the bright stars Rigel and Betelgeuse, and its easily recognized belt consists of three stars in a straight line."},
    {"name": "Ursa Major", "type": "Constellation", "fact": "Home to the famous Big Dipper asterism. In Greek mythology, it represents the nymph Callisto, transformed into a bear."},
    {"name": "Cassiopeia", "type": "Constellation", "fact": "Easily identified by its distinct 'W' or 'M' shape, named after a vain queen of ancient Ethiopia."},
    {"name": "Cygnus the Swan", "type": "Constellation", "fact": "Also known as the Northern Cross, it flies down the path of the Milky Way and contains the bright star Deneb."},
    {"name": "Taurus the Bull", "type": "Constellation", "fact": "One of the oldest constellations, it contains the famous Pleiades and Hyades star clusters."},
    {"name": "Canis Major", "type": "Constellation", "fact": "The 'Greater Dog' constellation, it contains Sirius, the brightest star in the night sky."},
    {"name": "Hercules", "type": "Constellation", "fact": "A massive, kneeling figure that contains M13, the spectacular Great Globular Cluster of Hercules."},
    {"name": "Lyra the Harp", "type": "Constellation", "fact": "The small constellation that hosts Vega, one of the three stars of the Summer Triangle, and the famous Ring Nebula (M57)."},
    {"name": "Scorpius the Scorpion", "type": "Constellation", "fact": "A distinctive 'J' shape in the southern sky, featuring the brilliant red supergiant star Antares at its heart."},
]

# Layer 1: Middle Distance (INITIAL)
SOLAR_SYSTEM_DATA = [
    {"name": "Mercury", "type": "Solar System", "fact": "The smallest planet in our solar system and the closest to the Sun. A day on Mercury is longer than its year!"},
    {"name": "Venus", "type": "Solar System", "fact": "Known as Earth's 'sister planet' due to its similar size, but its surface temperature is hot enough to melt lead due to an extreme greenhouse effect."},
    {"name": "Earth", "type": "Solar System", "fact": "The only known planet to support life. Its atmosphere is crucial, acting like a blanket and shield."},
    {"name": "Mars", "type": "Solar System", "fact": "The Red Planet. Its surface features the largest volcano, Olympus Mons, and the deepest canyon, Valles Marineris, in the solar system."},
    {"name": "Jupiter", "type": "Solar System", "fact": "The largest planet, a massive gas giant. Its Great Red Spot is a perpetual storm larger than Earth."},
    {"name": "Saturn", "type": "Solar System", "fact": "Famous for its spectacular ring system, which is composed of billions of chunks of ice and rock."},
    {"name": "Uranus", "type": "Solar System", "fact": "An ice giant that is unique for orbiting on its side, likely due to a massive ancient collision."},
    {"name": "Neptune", "type": "Solar System", "fact": "The most distant major planet. It has the fastest winds in the solar system, which can exceed 1,200 miles per hour."},
    {"name": "Pluto", "type": "Solar System", "fact": "Once a full planet, now a dwarf planet. Its large moon, Charon, is so big that the two are often considered a binary system."},
    {"name": "Ceres", "type": "Solar System", "fact": "The largest object in the asteroid belt between Mars and Jupiter and the only dwarf planet in the inner solar system."},
]

# Layer 2: Farthest (Move Up to get here from 1)
DEEP_SKY_DATA = [
    {"name": "Andromeda Galaxy (M31)", "type": "Deep Sky", "fact": "Our closest major galaxy, it is speeding towards the Milky Way for a collision expected in about 4.5 billion years."},
    {"name": "Orion Nebula (M42)", "type": "Deep Sky", "fact": "A huge stellar nursery where thousands of new stars are currently being formed from collapsing clouds of gas and dust."},
    {"name": "Pleiades Star Cluster (M45)", "type": "Deep Sky", "fact": "Also known as the Seven Sisters, this open cluster is one of the nearest to Earth and is easily visible to the naked eye."},
    {"name": "Ring Nebula (M57)", "type": "Deep Sky", "fact": "A classic planetary nebula, the glowing remnants of a sun-like star that shed its outer layers late in its life."},
    {"name": "Triangulum Galaxy (M33)", "type": "Deep Sky", "fact": "The third-largest member of the Local Group of galaxies, after the Milky Way and Andromeda."},
    {"name": "Crab Nebula (M1)", "type": "Deep Sky", "fact": "The gaseous remnant of a massive star that exploded as a supernova in the year 1054, visible even in the daytime sky at the time."},
]

# Map layers to data: Constellation (0) -> Solar System (1) -> Deep Sky (2)
CELESTIAL_LAYERS = [
    CONSTELLATION_DATA,     # Index 0
    SOLAR_SYSTEM_DATA,      # Index 1
    DEEP_SKY_DATA,          # Index 2
]

# --- Navigation State ---
class SkyNavigator:
    def __init__(self):
        # We use a set of objects for faster check and removal
        self.all_targets = set(item['name'] for layer in CELESTIAL_LAYERS for item in layer)
        self.unseen_targets = list(self.all_targets) # List to track which names have been used
        self.current_target = None
        # Start in the middle layer (Solar System) as per your test/initialization
        self.layer_index = 1 

        self._set_new_target(layer_index=self.layer_index)

    def _set_new_target(self, layer_index):
        """Picks an unseen target from the specified layer."""
        
        target_layer = CELESTIAL_LAYERS[layer_index]
        
        # Filter for targets in this layer that have not yet been seen
        available_targets = [
            t for t in target_layer if t['name'] in self.unseen_targets
        ]
        
        # If all targets in this layer have been seen, reset the layer's targets
        if not available_targets:
            # Add back all names from the current layer to the unseen list
            for t in target_layer:
                if t['name'] not in self.unseen_targets:
                    self.unseen_targets.append(t['name'])
            
            # Repopulate the available targets list
            available_targets = [
                t for t in target_layer if t['name'] in self.unseen_targets
            ]
        
        if not available_targets:
            # Fallback (shouldn't happen with the logic above)
            return None 
            
        # Select the new target
        new_target = random.choice(available_targets)
        
        # Update state
        self.unseen_targets.remove(new_target['name'])
        self.current_target = new_target
        self.layer_index = layer_index
        
        return new_target

    def get_current_target(self):
        """Returns the current object."""
        return self.current_target

    def move(self, direction):
        """Moves deterministically between layers (up/down) or randomly within a layer (left/right)."""
        
        # Current layer index for reference
        curr_dist_level = self.layer_index 
        
        # Default target layer index is the current one (used for left/right)
        new_layer_index = curr_dist_level

        # --- Handle Vertical Movement (Level Change) ---
        if direction == 'up':
            # Up (Zoom Out) -> Go to a higher index (farthest distance = Deep Sky, Index 2)
            if curr_dist_level < 2:
                new_layer_index += 1
            else:
                speak_text("Maximum zoom out reached! You cannot travel further from the Milky Way.")
                return # Do not change target or update last_move_time

        elif direction == 'down':
            # Down (Zoom In) -> Go to a lower index (closest distance = Constellation, Index 0)
            if curr_dist_level > 0:
                new_layer_index -= 1
            else:
                speak_text("Maximum zoom in reached! You are already pointing at the Constellations.")
                return # Do not change target or update last_move_time

        # --- Handle Horizontal Movement (Target Change within Current Level) ---
        # If the index didn't change, we are performing a left/right scan within the same layer
        
        new_target = self._set_new_target(layer_index=new_layer_index)
        
        # Define movement phrases based on actual action
        if new_layer_index > curr_dist_level:
            move_message = "You zoomed out to explore deeper into space."
        elif new_layer_index < curr_dist_level:
            move_message = "You zoomed back in towards the familiar."
        elif direction == 'left':
            move_message = "You scanned left to a new region."
        elif direction == 'right':
            move_message = "You scanned right across the celestial sphere."
        else:
            # Should not happen if logic is correct
            move_message = "Exploring a new object."
        
        # Announce the new target
        speech = f"{move_message} Your new target is the **{new_target['type']}**: {new_target['name']}."
        speak_text(speech)


# --- Main Loop ---
def runExample(mode):
    global OUTPUT_MODE
    OUTPUT_MODE = mode 

    print("\n--- SparkFun qwiic Joystick Astro Clicker (Randomized) ---\n")

    myJoystick = qwiic_joystick.QwiicJoystick()
    navigator = SkyNavigator()

    if myJoystick.connected == False:
        print("The Qwiic Joystick device isn't connected to the system. Please check your connection", \
            file=sys.stderr)
        return

    myJoystick.begin()

    print("Initialized. Firmware Version: %s" % myJoystick.version)

    # --- Thresholds & Debounce ---
    THRESHOLD_LOW = 400
    THRESHOLD_HIGH = 600
    MOVE_DEBOUNCE_TIME = 0.5 
    
    # --- Initial State (Clean Print) ---
    print("Welcome to Astro Clicker. Ready to explore the night sky.")

    # 1. Initialization Speech 
    initial_target = navigator.get_current_target()
    
    welcome_message = (
        f"Welcome to Astro Clicker, your companion that narrates the night sky. "
        f"You are currently pointed at the **{initial_target['type']}**: {initial_target['name']}. "
        "Click the joystick to learn more about it, or move in any direction to explore a new target."
    )
    
    speak_text(welcome_message)
    
    last_button_state = myJoystick.button
    last_move_time = 0
    
    while True:
        # Read joystick state
        x_val = myJoystick.horizontal
        y_val = myJoystick.vertical
        button_state = myJoystick.button
        current_time = time.time()
        
        # ----------------------------------------
        # --- 1. Button Press (Click) Detection ---
        # ----------------------------------------
        if last_button_state == 1 and button_state == 0:
            target = navigator.get_current_target()
            
            # Combine both messages into one
            combined_speech = (
                f"You are currently looking at {target['name']}. {target['fact']} "
                "You can move left or right to explore more targets "
                "at a similar distance level, or move up or down to travel "
                "to the farthest galaxies, or return to the observable night sky."
            )
    
            speak_text(combined_speech)

        # -------------------------------------------
        # --- 2. Joystick Movement Detection (X/Y) ---
        # -------------------------------------------
        if current_time - last_move_time > MOVE_DEBOUNCE_TIME:
            direction = None
            
            # Horizontal Movement (Left/Right) - X-AXIS FLIPPED (Low X=Right, High X=Left)
            if x_val < THRESHOLD_LOW:
                direction = 'right'
            elif x_val > THRESHOLD_HIGH:
                direction = 'left'

            # Vertical Movement (Up/Down) - Y-AXIS FLIPPED (Low Y=Closer, High Y=Farther)
            # LOW Y value (e.g., 0) -> Up movement on stick. Should be CLOSER (DOWN)
            elif y_val < THRESHOLD_LOW:
                direction = 'down' 
            # HIGH Y value (e.g., 1023) -> Down movement on stick. Should be FARTHER (UP)
            elif y_val > THRESHOLD_HIGH:
                direction = 'up'

            if direction:
                navigator.move(direction)
                last_move_time = current_time # Reset the debounce timer

        last_button_state = button_state # Update state for next loop
        time.sleep(.05) # Small sleep to reduce CPU load

# --- Entry Point ---
def main():
    # Setup argparse
    parser = argparse.ArgumentParser(
        description="Astro Clicker: An interactive narrator for the night sky."
    )
    
    # Define the optional mode argument with a default value
    parser.add_argument(
        '--mode',
        type=str,
        choices=['speaker', 'silent'], # Restrict choices to ensure valid input
        default='speaker',             # Default to 'speaker' if not provided
        help="Set the output mode. 'speaker' (default) uses text-to-speech (espeak). 'silent' uses print() only."
    )

    args = parser.parse_args()
    
    # Run the main example using the parsed mode
    try:
        runExample(args.mode)
    except (KeyboardInterrupt, SystemExit):
        print("\nEnding Astro Clicker")
        sys.exit(0)

if __name__ == '__main__':
    main()