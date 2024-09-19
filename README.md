To use this, make sure python is installed. Python 3.10.11 was used to make this. 
Make sure to click "Add to path" when installing python.

Type "cmd" in your windows search bar and open Command Prompt.

Type pip install pygame and hit Enter.
Wait for finish.
Type pip install keyboard and hit Enter.
Wait for finish.

Close command prompt and double click on the GamepadProgrammerDemo file.
Make sure your gamepad is plugged into your computer.

When the window opens click any field and type the hotkey you want it to control.
Click "Apply"

For stick "Starting Sensitivity", that means how often the hotkey strikes (in miliseconds) when you're barely pushing on the stick.
For stick "Full Sensitivity", that means how often the hotkey strikes (in miliseconds) when you're holding the stick all the way.
The stick hotkey repitition ramps up from Starting to Full as you push the stick farther in the direction you're already pushing.

For example, in Davinci Resolve, if you program Left and Right arrows to the Left and Right stick (for single frame scrubbing), when you barely push the stick, it will go forward/backward one from per second and scrub faster until it's going to the next frame every 30 miliseconds at full stick push.

Button mappings will strike once, delay, and then loop repeat if held, similar to a keyboard.

You can get the full GamepadProgrammer by joing my Patreon at http://patreon.com/sceneofaction

Enjoy!
