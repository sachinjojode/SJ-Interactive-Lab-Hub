# Observant Systems

**Nikhil Gangaram (ng544), Viha Srinivas (vs544), Arya Prasad (ap2535)**

### Part B
### Construct a simple interaction.

Our goal is to create a personalized ASL learning system for abled learners. The north star is to classify the user’s gesture and use MoonDream to provide personalized feedback. Initially, we trained a classical gesture classifier in Teachable Machine, but it showed high variance. Even in our best run, the model didn’t generalize well. Below is a screenshot from what we considered a "good" result:

![Good Result](good_result.png "Good Result")

Given the limitations of Teachable Machine, we pivoted to MoonDream, which better suited our task. The interaction flow:

TTS prompts the user to sign a gesture.
The user signs, and the image is sent to MoonDream.
MoonDream classifies the gesture and generates feedback.
TTS reads the feedback aloud.
The process repeats in an iterative loop.

Here is an image of the prototype flow:

![Prototype Flow](prototype_flow.png "Prototype Flow")

### Part C
### Test the interaction prototype

Now flight test your interactive prototype and **note down your observations**:

After testing our prototype, we found that lighting conditions and timing of image capture had the largest impact on performance. If the image is captured too early or lighting isn't the best, MoonDream struggles to classify gestures accurately. We also noticed that the interaction doesn't map well to natural human communication. When learning from a teacher, interactions have more subtlety and temporal variation, which is absent from our current rigid exchange. The prototype code is at [moondream_sign.py](moondream_sign.py).

**Think about someone using the system. Describe how you think this will work.**

In the case of someone using the system, we found that there is already implicit frustration when trying to learn a new language and any system error can cause a lost of trust with the user. In experimenting with other platforms, we came across [Google AI Live](https://aistudio.google.com/live) which performed much better than our initial prototype. The key difference appears to be that it processes video of the user rather than a single frame. We believe this temporal approach better captures user interaction and plan to explore this in Part 2. However, even Google's model struggled with longer videos and conversations where it assumes everything the user does is correct: 

Video link: [google_ai_live.mov](https://youtu.be/puvYo5_OJCY)


### Part D
### Characterize your own Observant system

Now that you have experimented with one or more of these sense-making systems **characterize their behavior**.
During the lecture, we mentioned questions to help characterize a material:
* What can you use X for?
* What is a good environment for X?
* What is a bad environment for X?
* When will X break?
* When it breaks how will X break?
* What are other properties/behaviors of X?
* How does X feel?

**Include a short video demonstrating the answers to these questions.**

Video Link : [HERE](https://youtu.be/ZU5NM-oH540)


### Part 2.

Following exploration and reflection from Part 1, finish building your interactive system, and demonstrate it in use with a video.

**Include a short video demonstrating the finished result.**

Video Link : [HERE](https://youtube.com/shorts/vKblgSUKpPI?si=JV_WB6N9sYURmRk5)

### AI / Team Contributions

Gemini was only used to develop the **moondream_sign.py** script. The ideation and exploration was done by the whole team and design/documentation (videos) of the system was primarily done by Nikhil Gangaram, Viha Srinivas, and Arya Prasad.