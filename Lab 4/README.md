# Ph-UI!!!

## Lab Overview
**Nikhil Gangaram (ng544), Viha Srinivas (vs544), Arya Prasad (ap2535), Jaspreet Lal (jl4536)**

## Part A
### Capacitive Sensing, a.k.a. Human-Twizzler Interaction 

All sensor testing videos are in the **Lab 4/assets/videos/sensors** folder.

Video link: [twizzler.mov](assets/videos/sensors/twizzler.mov)

<video width="300" height="600" controls>
  <source src="assets/videos/sensors/twizzler.mov" type="video/mp4">
</video>

### Part B

#### Light/Proximity/Gesture sensor (APDS-9960)

Video link: [proximity_test.mov](assets/videos/sensors/proximity_test.mov)

<video width="300" height="600" controls>
  <source src="assets/videos/sensors/proximity_test.mov" type="video/mp4">
</video>

Video link: [color_sensor.mov](assets/videos/sensors/color_sensor.mov)

<video width="300" height="600" controls>
  <source src="assets/videos/sensors/color_sensor.mov" type="video/mp4">
</video>

Video link: [gesture_sensor.mov](assets/videos/sensors/gesture_sensor.mov)

<video width="300" height="600" controls>
  <source src="assets/videos/sensors/gesture_sensor.mov" type="video/mp4">
</video>

#### Rotary Encoder 

Video link: [rotary_encoder.mov](assets/videos/sensors/rotary_encoder.mov)

<video width="300" height="600" controls>
  <source src="assets/videos/sensors/rotary_encoder.mov" type="video/mp4">
</video>

#### Joystick 

Video link: [joystick.mov](assets/videos/sensors/joystick.mov)

<video width="300" height="600" controls>
  <source src="assets/videos/sensors/joystick.mov" type="video/mp4">
</video>

#### Distance Sensor

Video link: [proximity_2.mov](assets/videos/sensors/proximity_2.mov)

<video width="300" height="600" controls>
  <source src="assets/videos/sensors/proximity_2.mov" type="video/mp4">
</video>

### Part C
### Physical considerations for sensing

Our 5 ideas:

First up, we came up with the AstroClicker, a basically a device to help you navigate the night sky. The joystick would be the main way to interact with it, letting you select what you want to look at and zoom in or out to see different levels of detail.

![AstroClicker](assets/images/ideas/astro_clicker.png "AstroClicker")

Next, we thought about a City Explorer that could help you discover new places in unfamiliar cities or even find hidden gems in your own city. The joystick would let you pick your next destination, and the device would remember all the places you've already visited.

![City Explorer](assets/images/ideas/city_explorer.png "City Explorer")

Then we brainstormed a Remote Play device for pet owners. Imagine being able to play with your pet even when you're not home! This one combines joystick controls with a gyroscopic ball that moves around based on your commands.

![Remote Play](assets/images/ideas/remote_play.png "Remote Play")

We also got inspired by learning devices like [Anki](https://www.ankiremote.com/) and came up with our own take on flashcards. Instead of just using buttons, users would navigate through flashcards using the joystick, making the learning experience more interactive.

![Flashcard Master](assets/images/ideas/flashcard_master.png "Flashcard Master")

Finally, we designed a Store Navigator to help people navigate those confusing grocery store layouts. The device would come preloaded with maps of different stores, and you could use it to find specific aisles and check if items are actually in stock.

![Store Navigator](assets/images/ideas/store_navigator.png "Store Navigator")

These sketches got us thinking about some important questions:
* What other cool ways can we interact with users beyond just displays?
* How do we make this thing comfortable to hold and use?
* How can we make sure people with different abilities can use it too?
* How do we strike the right balance between being helpful and being annoying?

After thinking it over, we decided to keep working on the AstroClicker.


### Part D
These were the different designs we came up with for the AstroClicker:

![AstroClicker Prototype 1](assets/images/prototypes/prototype_1.jpeg "AstroClicker Prototype 1")
![AstroClicker Prototype 2](assets/images/prototypes/prototype_2.jpeg "AstroClicker Prototype 2")
![AstroClicker Prototype 3](assets/images/prototypes/prototype_3.jpeg "AstroClicker Prototype 3")
![AstroClicker Prototype 4](assets/images/prototypes/prototype_4.jpeg "AstroClicker Prototype 4")
![AstroClicker Prototype 5](assets/images/prototypes/prototype_5.jpeg "AstroClicker Prototype 5")

Here's our thinking behind the initial design (we went with Prototype 1):
* Since it's going to be handheld, we wanted to put the joystick in a comfortable spot for your thumb
* The speaker needs to point toward you, otherwise the audio will sound muffled and weird
* We had to make sure the Raspberry Pi has room to breathe so it doesn't overheat, plus we needed space for a battery

We built a cardboard prototype to test our ideas. As you'll see in the walkthrough, we incorporated most of our design rationale into the final version. We used an Altoids tin as a placeholder for the battery, and cut out the top section for ventilation around the Raspberry Pi.

Here is a video walk-around of the AstroClicker prototype. You can also view it in the **assets/videos/prototype_video** folder for the mov called **cardboard_prototype.mov**.

<video width="300" height="600" controls>
  <source src="assets/videos/prototype_video/cardboard_prototype.mov" type="video/mp4">
</video>

# LAB PART 2

### Part 2

### Part E

#### Software

We first started prototyping the software for the AstroClicker, which you can find in the [astro_clicker_demo.py](astro_clicker_demo.py) file. Our main goal when designing the script was to make it user-friendly without being too overwhelming. After lots of testing and tweaking, here's the code structure we ended up with:

#### 1. Initialization and Data Structure

* **Imports** all the libraries we need for hardware control, timing, running external programs, and handling command line arguments.
* The **`speak_text`** function handles text-to-speech using the `espeak` program, and it logs everything to the console whether we're in **`OUTPUT_MODE`** (`'speaker'` or `'silent'`).
* We organized our celestial data into three layers based on how far they are from Earth:
    * **Layer 0 (Closest):** `CONSTELLATION_DATA`
    * **Layer 1 (Middle/Starting point):** `SOLAR_SYSTEM_DATA`
    * **Layer 2 (Farthest):** `DEEP_SKY_DATA`

---

#### 2. The SkyNavigator State Machine

* The **`SkyNavigator`** class keeps track of where the user is, managing the **`layer_index`** (starts at 1/Solar System) and which objects they've already discovered using a list called **`unseen_targets`**.
* The `_set_new_target` method picks a random object from the current layer that hasn't been seen yet; if all objects in a layer have been explored, it resets that layer so everything becomes available again.
* The **`move(direction)`** method updates everything based on what the joystick is trying to do:
    * **'up' / 'down'**: Changes the **`layer_index`** to zoom in or out, switching between the three celestial layers. We added boundary checks so you can't go past Layer 0 or Layer 2.
    * **'left' / 'right'**: Stays in the current layer and picks a **new random target** from that layer.
    * After any successful movement, the new location/target gets announced through `speak_text`.

##### 3. Main Loop and Input Handling

* The **`runExample`** function sets up the joystick and creates our `SkyNavigator`.
* It plays a welcome message and tells you about the first target.
* An **infinite `while` loop** continuously reads the joystick's horizontal (`x_val`), vertical (`y_val`), and button state. We use a **debounce timer** (`MOVE_DEBOUNCE_TIME`) to prevent accidental rapid inputs.

##### Inputs and Outputs

| Input Action | Resulting Action | Output/Narration |
| :--- | :--- | :--- |
| **Joystick Button Click (Release)** | Stays at current target. | Reads the **`name`** and **`fact`** of the current target, followed by a prompt for the next action. |
| **Joystick Up** ($\text{y\_val} > 600$) | Calls `navigator.move('up')` (Zoom Out/Farther). | Announces the zoom-out and the new target's name/type, or a boundary message. |
| **Joystick Down** ($\text{y\_val} < 400$) | Calls `navigator.move('down')` (Zoom In/Closer). | Announces the zoom-in and the new target's name/type, or a boundary message. |
| **Joystick Left** ($\text{x\_val} > 600$) | Calls `navigator.move('left')` (Scan/New Target). | Announces a scan left and the new target's name/type. |
| **Joystick Right** ($\text{x\_val} < 400$) | Calls `navigator.move('right')` (Scan/New Target). | Announces a scan right and the new target's name/type. |

#### 4. Entry Point

* The **`main()`** function uses **`argparse`** so users can choose the output mode (`--mode speaker` or `--mode silent`) when they run the script.
* You can exit the program cleanly by pressing **Ctrl+C**.

#### Hardware

We then got started on the hardware prototype, for which, these were out main considerations:

* The device will be handheld, and so the joystick should be placed in ergonomic position.
* The speaker should be facing at the user since otherwise, sound will appear to be muffled.
* The raspberry pi should have enough ventilation as to not overheat and there should be space for a battery

### Part F

Here are our two final videos with a walkthrough of the AstroClicker prototype in both software and hardware:

<video width="300" height="600" controls>
  <source src="assets/videos/prototype_video/software_final.mov" type="video/mp4">
</video>

<video width="300" height="600" controls>
  <source src="assets/videos/prototype_video/final_prototype.mov" type="video/mp4">
</video>

### AI Contributions 

Throughout this lab, we got help from Gemini and ChatGPT with: 

* Generating "final" images throughout the lab. We would often sketch a rough idea on paper, and then use Gemini to refine it into a presentable image. 
* Developing and documenting the code for the AstroClicker prototype.

Everything else (ideating, eliciting feedback, designing and building the prototypes) was done by ourselves.