import pygame
import keyboard
import time
import tkinter as tk
from tkinter import ttk
import threading

# Initialize Pygame and joystick
pygame.init()
pygame.joystick.init()

# Check if a joystick/controller is connected
if pygame.joystick.get_count() == 0:
    print("No gamepad found.")
    exit()

# Initialize the first joystick
gamepad = pygame.joystick.Joystick(0)
gamepad.init()

# Mapping of gamepad axes and buttons
AXIS_RIGHT_STICK_HORIZONTAL = 2
AXIS_RIGHT_STICK_VERTICAL = 3
BUTTON_NAMES = {0: 'A', 1: 'B'}

# Hotkey mappings for buttons
button_hotkeys = {}  # {button_index: hotkey}

# Settings for right stick directions
right_stick_settings = {
    'left': {
        'hotkey': '',
        'max_delay': 1000.0,
        'min_delay': 30.0,
        'deadzone': 0.0
    },
    'right': {
        'hotkey': '',
        'max_delay': 1000.0,
        'min_delay': 30.0,
        'deadzone': 0.0
    },
    'up': {
        'hotkey': '',
        'max_delay': 1000.0,
        'min_delay': 30.0,
        'deadzone': 0.0
    },
    'down': {
        'hotkey': '',
        'max_delay': 1000.0,
        'min_delay': 30.0,
        'deadzone': 0.0
    }
}

# Per-button state tracking
button_states = {}   # {button_index: state_dict}
right_stick_states = {}  # {direction: state_dict}

# Initialize button states for buttons A and B
for i in [0, 1]:
    button_states[i] = {
        'pressed': False,
        'first_press_time': 0,
        'last_keypress_time': 0,
        'initial_delay_passed': False
    }

# Initialize right stick states
RIGHT_STICK_DIRECTIONS = ['left', 'right', 'up', 'down']
for direction in RIGHT_STICK_DIRECTIONS:
    right_stick_states[direction] = {
        'active': False,
        'last_press_time': 0
    }

# Function to get delay based on value and sensitivity settings
def get_delay(value, max_delay, min_delay):
    abs_value = min(1, max(0, abs(value)))
    return max_delay - (abs_value * (max_delay - min_delay))

# Function to send hotkeys from the main thread
def send_hotkey(hotkey):
    root.after(0, lambda: keyboard.send(hotkey))

# Function to run the gamepad input loop
def gamepad_loop():
    try:
        while True:
            pygame.event.pump()
            current_time = time.time() * 1000  # Current time in milliseconds

            # Handle right stick movement
            h_value_right = gamepad.get_axis(AXIS_RIGHT_STICK_HORIZONTAL)
            v_value_right = gamepad.get_axis(AXIS_RIGHT_STICK_VERTICAL)

            # Process right stick directions
            process_stick(h_value_right, v_value_right, right_stick_settings, right_stick_states, current_time, 'Right Stick')

            # Handle buttons A and B
            for i in [0, 1]:
                button = gamepad.get_button(i)
                state = button_states[i]
                hotkey = button_hotkeys.get(i, None)
                name = BUTTON_NAMES.get(i, f"Button {i}")

                if button and not state['pressed']:
                    # Button just pressed
                    state['pressed'] = True
                    state['first_press_time'] = current_time
                    state['last_keypress_time'] = 0
                    state['initial_delay_passed'] = False

                    if hotkey:
                        send_hotkey(hotkey)
                        print(f"Button {name} pressed. Hotkey '{hotkey}' sent.")

                elif not button and state['pressed']:
                    # Button released
                    state['pressed'] = False
                    state['initial_delay_passed'] = False
                    print(f"Button {name} released.")

            time.sleep(0.001)
    except Exception as e:
        print(f"Gamepad loop error: {e}")

def process_stick(h_value, v_value, stick_settings, stick_states, current_time, stick_name):
    # For each direction, check if the stick is moved beyond the deadzone
    for axis_value, axis_direction, positive_direction, negative_direction in [
        (h_value, 'horizontal', 'right', 'left'),
        (v_value, 'vertical', 'down', 'up')
    ]:
        for direction in [positive_direction, negative_direction]:
            settings = stick_settings[direction]
            state = stick_states[direction]
            hotkey = settings['hotkey']
            deadzone = settings['deadzone']
            max_delay = settings['max_delay']
            min_delay = settings['min_delay']

            moved = (axis_value > deadzone if direction == positive_direction else axis_value < -deadzone)
            if moved:
                # Apply deadzone
                adjusted_value = (abs(axis_value) - deadzone) / (1 - deadzone)
                delay = get_delay(adjusted_value, max_delay, min_delay)

                if not state['active'] or (current_time - state['last_press_time']) >= delay:
                    if hotkey:
                        send_hotkey(hotkey)
                        print(f"{stick_name} {direction.capitalize()} pressed. Hotkey '{hotkey}' sent.")
                    state['last_press_time'] = current_time
                    state['active'] = True
            else:
                state['active'] = False

# Custom Entry widget for capturing hotkeys
class HotkeyEntry:
    def __init__(self, parent, initial_value='', clear_callback=None):
        self.parent = parent
        self.entry = ttk.Entry(parent, width=20)
        self.entry.insert(0, self.format_display(initial_value))
        self.entry.pack(side='left', padx=5)
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.bind('<Key>', self.on_key_press)

        self.previous_value = initial_value
        self.modifiers = set()
        self.capturing = False
        self.hotkey = initial_value  # For internal use

        # Add Clear button
        self.clear_button = ttk.Button(parent, text="Clear", command=self.clear_hotkey)
        self.clear_button.pack(side='left', padx=5)

        self.clear_callback = clear_callback

    def on_focus_in(self, event):
        self.previous_value = self.hotkey
        self.entry.delete(0, tk.END)
        self.capturing = True
        self.modifiers.clear()

    def on_focus_out(self, event):
        if self.capturing:
            # User clicked off without entering a new hotkey
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.format_display(self.previous_value))
            self.hotkey = self.previous_value
            self.capturing = False

    def on_key_press(self, event):
        if not self.capturing:
            return

        # Prevent default behavior
        if event.keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R'):
            self.modifiers.add(event.keysym)
            return 'break'  # Prevent default behavior

        else:
            # Non-modifier key pressed
            modifiers_str = []
            if 'Control_L' in self.modifiers or 'Control_R' in self.modifiers:
                modifiers_str.append('Ctrl')
            if 'Alt_L' in self.modifiers or 'Alt_R' in self.modifiers:
                modifiers_str.append('Alt')
            if 'Shift_L' in self.modifiers or 'Shift_R' in self.modifiers:
                modifiers_str.append('Shift')

            # Handle special keys
            special_keys = {
                'Return': 'Enter',
                'Escape': 'Esc',
                'Space': 'Space',
                'Tab': 'Tab',
                'BackSpace': 'Backspace',
                'Delete': 'Delete',
                'Up': 'Up',
                'Down': 'Down',
                'Left': 'Left',
                'Right': 'Right',
                'Home': 'Home',
                'End': 'End',
                'Page_Up': 'PageUp',
                'Page_Down': 'PageDown',
                'Insert': 'Insert',
                'Caps_Lock': 'CapsLock',
                'Num_Lock': 'NumLock',
                'Scroll_Lock': 'ScrollLock',
                'Print': 'PrintScreen',
                'Pause': 'Pause',
                'Menu': 'Menu',
            }

            key_name = special_keys.get(event.keysym, event.keysym).capitalize()
            display_str = ' + '.join(modifiers_str + [key_name])
            self.entry.delete(0, tk.END)
            self.entry.insert(0, display_str)
            # For internal use, construct the hotkey string
            hotkey_parts = []
            if 'Control_L' in self.modifiers or 'Control_R' in self.modifiers:
                hotkey_parts.append('ctrl')
            if 'Alt_L' in self.modifiers or 'Alt_R' in self.modifiers:
                hotkey_parts.append('alt')
            if 'Shift_L' in self.modifiers or 'Shift_R' in self.modifiers:
                hotkey_parts.append('shift')

            key_name = event.keysym.lower()
            # Map special keys to keyboard module names
            special_keys_lower = {
                'return': 'enter',
                'escape': 'esc',
                'space': 'space',
                'backspace': 'backspace',
                'delete': 'delete',
                'tab': 'tab',
            }
            key_name = special_keys_lower.get(key_name, key_name)

            hotkey_parts.append(key_name)
            self.hotkey = '+'.join(hotkey_parts)
            # Stop capturing
            self.capturing = False
            # Reset modifiers
            self.modifiers.clear()
            print(f'Captured hotkey: {self.hotkey}')
            return 'break'  # Prevent default behavior

    def clear_hotkey(self):
        self.hotkey = ''
        self.entry.delete(0, tk.END)
        if self.clear_callback:
            self.clear_callback()
        print('Hotkey cleared.')

    def get_hotkey(self):
        return self.hotkey

    def set_hotkey(self, hotkey_str):
        # Set the hotkey and update the display
        self.hotkey = hotkey_str
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.format_display(hotkey_str))

    def format_display(self, hotkey_str):
        if hotkey_str:
            parts = hotkey_str.split('+')
            display_parts = []
            for part in parts:
                if part.lower() == 'ctrl':
                    display_parts.append('Ctrl')
                elif part.lower() == 'alt':
                    display_parts.append('Alt')
                elif part.lower() == 'shift':
                    display_parts.append('Shift')
                else:
                    display_parts.append(part.capitalize())
            return ' + '.join(display_parts)
        else:
            return ''

    def pack(self, **kwargs):
        self.entry.pack(**kwargs)

# Create the main window
root = tk.Tk()
root.title("Gamepad Mapping Settings")

# Create frames for right stick mappings
ttk.Label(root, text="Right Stick Mappings:").pack(pady=10)
right_stick_frame = ttk.Frame(root)
right_stick_frame.pack(padx=5, pady=5)

right_stick_entries = {}

for direction in RIGHT_STICK_DIRECTIONS:
    frame = ttk.Frame(right_stick_frame)
    frame.pack(fill='x', pady=5)

    label = ttk.Label(frame, text=direction.capitalize() + ":")
    label.pack(side='left')

    # Hotkey Entry
    hotkey_entry = HotkeyEntry(frame)
    hotkey_entry.set_hotkey(right_stick_settings[direction]['hotkey'])

    # Max Delay Slider
    ttk.Label(frame, text="Starting Sensitivity:").pack(side='left', padx=(10, 0))
    max_delay_var = tk.DoubleVar(value=right_stick_settings[direction]['max_delay'])
    max_delay_slider = ttk.Scale(frame, from_=1.0, to=1000.0, orient="horizontal", length=100, variable=max_delay_var)
    max_delay_slider.pack(side='left')

    # Max Delay Entry
    max_delay_entry = ttk.Entry(frame, width=12)
    max_delay_entry.insert(0, f"{max_delay_var.get():.2f}")
    max_delay_entry.pack(side='left')

    # Update the Entry when the slider moves
    def update_max_delay_entry(val, entry=max_delay_entry):
        entry.delete(0, tk.END)
        entry.insert(0, f"{float(val):.2f}")

    max_delay_slider.config(command=update_max_delay_entry)

    # Bind the Entry to handle Enter key
    def on_max_delay_entry(event, var=max_delay_var, entry=max_delay_entry):
        try:
            val = float(entry.get())
            if val < 1.0:
                val = 1.0
            elif val > 1000.0:
                val = 1000.0
            var.set(val)
        except ValueError:
            pass  # Invalid input; ignore
    max_delay_entry.bind('<Return>', on_max_delay_entry)
    max_delay_entry.bind('<FocusOut>', on_max_delay_entry)
    max_delay_entry.bind('<Tab>', on_max_delay_entry)

    # Min Delay Slider
    ttk.Label(frame, text="Full Sensitivity:").pack(side='left', padx=(10, 0))
    min_delay_var = tk.DoubleVar(value=right_stick_settings[direction]['min_delay'])
    min_delay_slider = ttk.Scale(frame, from_=1.0, to=1000.0, orient="horizontal", length=100, variable=min_delay_var)
    min_delay_slider.pack(side='left')

    # Min Delay Entry
    min_delay_entry = ttk.Entry(frame, width=12)
    min_delay_entry.insert(0, f"{min_delay_var.get():.2f}")
    min_delay_entry.pack(side='left')

    # Update the Entry when the slider moves
    def update_min_delay_entry(val, entry=min_delay_entry):
        entry.delete(0, tk.END)
        entry.insert(0, f"{float(val):.2f}")

    min_delay_slider.config(command=update_min_delay_entry)

    # Bind the Entry to handle Enter key
    def on_min_delay_entry(event, var=min_delay_var, entry=min_delay_entry):
        try:
            val = float(entry.get())
            if val < 1.0:
                val = 1.0
            elif val > 1000.0:
                val = 1000.0
            var.set(val)
        except ValueError:
            pass  # Invalid input; ignore
    min_delay_entry.bind('<Return>', on_min_delay_entry)
    min_delay_entry.bind('<FocusOut>', on_min_delay_entry)
    min_delay_entry.bind('<Tab>', on_min_delay_entry)

    # Deadzone Slider
    ttk.Label(frame, text="Deadzone:").pack(side='left', padx=(10, 0))
    deadzone_var = tk.DoubleVar(value=right_stick_settings[direction]['deadzone'])
    deadzone_slider = ttk.Scale(frame, from_=0.0, to=0.5, orient="horizontal", length=100, variable=deadzone_var)
    deadzone_slider.pack(side='left')

    # Deadzone Entry
    deadzone_entry = ttk.Entry(frame, width=12)
    deadzone_entry.insert(0, f"{deadzone_var.get():.2f}")
    deadzone_entry.pack(side='left')

    # Update the Entry when the slider moves
    def update_deadzone_entry(val, entry=deadzone_entry):
        entry.delete(0, tk.END)
        entry.insert(0, f"{float(val):.2f}")

    deadzone_slider.config(command=update_deadzone_entry)

    # Bind the Entry to handle Enter key
    def on_deadzone_entry(event, var=deadzone_var, entry=deadzone_entry):
        try:
            val = float(entry.get())
            if val < 0.0:
                val = 0.0
            elif val > 0.5:
                val = 0.5
            var.set(val)
        except ValueError:
            pass  # Invalid input; ignore
    deadzone_entry.bind('<Return>', on_deadzone_entry)
    deadzone_entry.bind('<FocusOut>', on_deadzone_entry)
    deadzone_entry.bind('<Tab>', on_deadzone_entry)

    right_stick_entries[direction] = {
        'hotkey': hotkey_entry,
        'max_delay': max_delay_var,
        'min_delay': min_delay_var,
        'deadzone': deadzone_var,
        'max_delay_entry': max_delay_entry,
        'min_delay_entry': min_delay_entry,
        'deadzone_entry': deadzone_entry
    }

# Create frames for button mappings
ttk.Label(root, text="Button Mappings:").pack(pady=10)
buttons_frame = ttk.Frame(root)
buttons_frame.pack(padx=5, pady=5)

button_entries = {}
for i in [0, 1]:
    name = BUTTON_NAMES.get(i, f"Button {i}")
    frame = ttk.Frame(buttons_frame)
    frame.pack(fill='x', pady=2)
    label = ttk.Label(frame, text=name + ":")
    label.pack(side='left')

    # Hotkey Entry
    hotkey_entry = HotkeyEntry(frame)
    hotkey_entry.set_hotkey(button_hotkeys.get(i, ''))

    button_entries[i] = {
        'hotkey': hotkey_entry
    }

# Function to apply new settings
def apply_settings():
    # Update hotkey mappings
    for i, entries in button_entries.items():
        hotkey_entry = entries['hotkey']
        hotkey = hotkey_entry.get_hotkey()
        if hotkey.strip() == '':
            button_hotkeys.pop(i, None)
        else:
            button_hotkeys[i] = hotkey.strip()

        name = BUTTON_NAMES.get(i, f"Button {i}")
        print(f"Applied settings for {name} - Hotkey: {hotkey}")

    for direction, entries in right_stick_entries.items():
        hotkey_entry = entries['hotkey']
        hotkey = hotkey_entry.get_hotkey()
        if hotkey.strip() == '':
            right_stick_settings[direction]['hotkey'] = ''
        else:
            right_stick_settings[direction]['hotkey'] = hotkey.strip()

        max_delay = float(entries['max_delay'].get())
        min_delay = float(entries['min_delay'].get())
        deadzone = float(entries['deadzone'].get())

        right_stick_settings[direction]['max_delay'] = max_delay
        right_stick_settings[direction]['min_delay'] = min_delay
        right_stick_settings[direction]['deadzone'] = deadzone

        print(f"Applied settings for Right Stick {direction.capitalize()} - Hotkey: {hotkey}, Max Delay: {max_delay}ms, Min Delay: {min_delay}ms, Deadzone: {deadzone}")

# Create and pack the buttons
ttk.Button(root, text="Apply", command=apply_settings).pack(pady=10)
ttk.Button(root, text="Exit", command=root.quit).pack(pady=5)

# Start the gamepad input thread
gamepad_thread = threading.Thread(target=gamepad_loop, daemon=True)
gamepad_thread.start()

# Start the Tkinter event loop
root.mainloop()

# Cleanup
pygame.quit()
