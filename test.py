import threading
import time
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np

# Define the dimensions of the image
width, height = 400, 400

# Create two sample arrays (you can replace these with your own data)
array_a = np.random.randint(0, 256, size=(width, height, 4), dtype=np.uint8)
array_b = np.random.randint(0, 256, size=(width, height, 4), dtype=np.uint8)

# Create a Tkinter window
root = tk.Tk()
root.title("Display Arrays")

# Create a canvas to display the image
canvas = tk.Canvas(root, width=width, height=height)
canvas.pack()

# Create a PIL image object from the array
image = Image.fromarray(array_a)
photo = ImageTk.PhotoImage(image)

# Create a label to display the image
label = tk.Label(canvas, image=photo)
label.image = photo
label.pack()

# Function to update the image
def update_image():
    global array_a, array_b
    while True:
        # Switch between array_a and array_b every second
        time.sleep(1)
        array_a, array_b = array_b, array_a
        # Create a new PIL image object from the updated array
        image = Image.fromarray(array_a)
        photo = ImageTk.PhotoImage(image)
        # Update the label with the new image
        label.config(image=photo)
        label.image = photo

# Create and start the parallel thread
thread = threading.Thread(target=update_image)
thread.daemon = True
thread.start()

# Run the Tkinter main loop
root.mainloop()