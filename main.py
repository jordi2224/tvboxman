import os
import sys

import imageio.v2 as imageio
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import tkinter as tk

import animations as anim
import keyboard  # python -m pip install keyboard

# Path to the bitmaps folder
BITMAPS_PATH = "bitmaps/"

# Layers names array
LAYER_NAMES = ["background", "static_face", "mouth", "eyes"]
layer_filenames = {"background": "background.png", "static_face": "face.png", "mouth": "mouth.png",
                   "eyes": ["eyes1.png", "eyes2.png"]}
layers = {}

# GUI globals
TARGET_FRAMERATE = 24  # Vamos a ir con este framerate, pero lo bajaria a 12 ?
update_delay = 1 / TARGET_FRAMERATE
working_resolution = None
output_object = None
output_buffer = None
label = None


def state_machine(animation, root):
    """A simple state machine to control the animation
    """
    print("awake")
    while True:
        key = keyboard.read_event().name
        match key:
            case 'a':
                # print('You Pressed the A Key!')
                animation.current_state = "mad"
            case 's':
                # print('You Pressed the S Key!')
                animation.current_state = "idle"
            case 'd':
                # print('You Pressed the D Key!')
                animation.current_state = "lol"
            case 'esc':
                # print('sacabo XD')
                root.destroy()  # close the program
                break

    # detectar micro aqui?


def child_thread(root):
    global output_object
    global output_buffer

    animation = anim.FrameGenerator(working_resolution=working_resolution, ressource_path=BITMAPS_PATH)
    # Start the state machine
    thread = threading.Thread(target=state_machine, args=(animation, root,))  # nos llevamos el root a la maquina de estados
    thread.daemon = True
    thread.start()

    # Tick
    start = time.time()
    while True:
        target_time = time.time() + update_delay

        ### FRAME GENERATION START
        frame = animation.execute_animation()
        output_buffer = ImageTk.PhotoImage(frame)
        output_object.configure(image=output_buffer)
        output_object.image = output_buffer

        ### FRAME GENERATION END

        # Sleep by the remaining time)
        while time.time() < target_time:
            pass


def blink_delay_humanize(open_base=3, close_base=0.1, open_variance=0.5, close_variance=0.05):
    """Generates a random delay time for the blinking of the eyes
    The delay time is generated using a normal distribution with the given parameters

    input: open_base, close_base, open_variance, close_variance
    output: delay times for the eyes [open_delay, close_delay]
    """
    # Generate two random numbers for the open and close delays
    open_delay = np.random.normal(open_base, open_variance)
    close_delay = np.random.normal(close_base, close_variance)
    # Return the delay times
    return [max(0, open_delay), max(0, close_delay)]


def main():
    """Main function
    Intializes the GUI by filling global parameters of the full screen window
    Starts the child thread for updating the image
    Hands over the control to the tkinter main loop
    
    """
    global output_object
    global output_buffer
    global label
    global working_resolution

    # Plot the image using tk
    root = tk.Tk()
    root.title("A pretty face")
    root.attributes("-fullscreen", True)

    # Fill the global working resolution with the full screen resolution
    working_resolution = (root.winfo_screenwidth(), root.winfo_screenheight())

    # Prepare a first image to display
    output_buffer = anim.get_static_first_frame(BITMAPS_PATH, working_resolution)
    img = ImageTk.PhotoImage(output_buffer)

    # Fullscreen output object, shared with the child thread for updating
    output_object = tk.Label(root, image=img)
    output_object.pack(fill="both", expand=True)

    # Start the child thread before the main loop
    thread = threading.Thread(target=child_thread, args=(root,))  # mando al main thread el root
    thread.daemon = True
    thread.start()

    # Hand over the control to the tkinter main loop
    root.mainloop()

    # If the main loop is exited, kill the child thread
    return 0


if __name__ == "__main__":
    main()
