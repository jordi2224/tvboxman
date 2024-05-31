import sys
import numpy as np
import threading
import time
import animations as anim
import keyboard  # python -m pip install keyboard || requiere acceso root en linux
from PIL import Image

from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QDesktopWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, Qt

import pyaudio
import queue

import signal

# Path to the bitmaps folder
BITMAPS_PATH = "bitmaps/"

# Layers names array
LAYER_NAMES = ["background", "static_face", "mouth", "eyes"]
layer_filenames = {"background": "background.png", "static_face": "face.png", "mouth": "mouth.png",
                   "eyes": ["eyes1.png", "eyes2.png"]}
layers = {}

# GUI globals
PRINT_FPS_DEBUG = False
TARGET_FRAMERATE = 240
update_delay = 1/TARGET_FRAMERATE

# Force screen resolution
FORCE_SCREEN_RESOLUTION = True
FORCED_SCREEN_RESOLUTION = (700, 500)

# Animation downscale factor
DO_DOWNSCALE = False
downscale_factor = 2

output_object = None
output_buffer = None
label = None

# State machine
DO_AUDIO = False
stop_main_process_flag = False
audio_power = None

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal_timer = QTimer()
signal_timer.start(200)
signal_timer.timeout.connect(lambda: None)

def get_power(stream, N):
    global audio_power
    # print("Recording")
    samples = stream.read(N)
    samples = np.frombuffer(samples, dtype=np.int16).astype(np.float32)
    audio_power = 10 * np.log10(np.sum(samples**2))

# Create a queue to hold the key press events
key_queue = queue.Queue()

def read_key():
    while True:
        # Read the key press event and put it in the queue
        key_queue.put(keyboard.read_event().name)

# Start the read_key function in a separate thread
threading.Thread(target=read_key, daemon=True).start()


def state_machine(animation):
    global stop_main_process_flag, audio_power
    """A simple state machine to control the animation
    """

    # Currently not working on linux and crashes the thread
    if DO_AUDIO:
        # Local python audio setup
        p = pyaudio.PyAudio()
        Fs = 44100
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=Fs,
                        input=True,
                        frames_per_buffer=1024)
        power_recording_time = 0.1
        power_recording_samples = int(power_recording_time * Fs)

        # Start the recording thread
        recording_thread = threading.Thread(target=get_power, args=(stream, power_recording_samples))
        recording_thread.start()

    while True:
        # Check if a key press event is in the queue
        if not key_queue.empty():
            key = key_queue.get()
            if key == 'd':
                animation.current_state = "idle"
            elif key =='a':
                animation.current_state = "mad"
            elif key == 's':
                animation.current_state = "laugh"
            elif key == 'esc':
                stop_main_process_flag = True
                break

        if DO_AUDIO and audio_power is not None:
            if audio_power >= 89: #detectar que estoy hablando, cambiar valor al micro que usaremos
                animation.talking = True
                print("Audio power: ", audio_power)
            else:
                animation.talking = False
            audio_power = None
            # launch a new recording thread
            recording_thread = threading.Thread(target=get_power, args=(stream, power_recording_samples))
            recording_thread.start()


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if FORCE_SCREEN_RESOLUTION:
            self.screen_resolution = FORCED_SCREEN_RESOLUTION
        else:
            # Get the resolution of the screen from the QApplication
            self.screen_resolution = app.desktop().screenGeometry()
            self.screen_resolution = (self.screen_resolution.width(), self.screen_resolution.height())

        print("Screen resolution: ", self.screen_resolution)
        
        #Checl if we need to downscale the resolution
        if DO_DOWNSCALE:
            animation_resolution = (self.screen_resolution[0]//downscale_factor, self.screen_resolution[1]//downscale_factor)
        else:
            # Use the screen resolution as the animation resolution
            animation_resolution = self.screen_resolution

        self.animation = anim.FrameGenerator(working_resolution=animation_resolution, ressource_path="bitmaps/")


        self.frame_count = 0
        self.start_time = time.time()
        self.update_image()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(int(update_delay * 1000))


        # Launch the state machine
        self.thread = threading.Thread(target=state_machine, args=(self.animation,))
        self.thread.daemon = True
        self.thread.start()


    def update_image(self):
        if stop_main_process_flag:
            print("Exiting by user request...")
            sys.exit(0)

        if self.frame_count % 20 == 0 and PRINT_FPS_DEBUG:
            # Clear previos line
            print("\rFPS: ", 20 // (time.time() - self.start_time + 1e-6), "                 ", end="")
            self.start_time = time.time()


        self.frame_count += 1
        frame = self.animation.execute_animation()
        frame = frame.astype(np.uint8)
        image = Image.fromarray(frame)
        image = image.convert("RGB")

        # Make the frame the right size
        # If the animation is not the same size as the screen, resize it
        if image.size != self.screen_resolution:
            image = image.resize(self.screen_resolution)

        # Convert the image to a QImage
        qImg = QImage(image.tobytes(), image.size[0], image.size[1], QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qImg))


    def move_to_screen(self, screen_number):
        screen = QDesktopWidget().screenGeometry(screen_number)
        self.move(screen.left(), screen.top())
        print("Screen resolution: ", self.screen_resolution)
        self.resize(self.screen_resolution[0], self.screen_resolution[1])
        #self.showNormal()
        self.showFullScreen()

if __name__ == "__main__":
    #main()
    app = QApplication([])
    window = MainWindow()
    window.move_to_screen(0)

    app.exec_()
