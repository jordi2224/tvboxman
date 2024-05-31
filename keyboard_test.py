import keyboard
import time

# Continuously check for key press events and display them
while True:
    if keyboard.is_pressed('d'):
        print("d")
    if keyboard.is_pressed('a'):
        print("a")
    if keyboard.is_pressed('s'):
        print("s")
    if keyboard.is_pressed('esc'):
        print("esc")
        break
    print("No key pressed")
    time.sleep(0.1)
