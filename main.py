import os
import imageio.v2 as imageio
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import tkinter as tk
import animations as anim
import cProfile
import cv2

from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QDesktopWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, Qt

# Path to the bitmaps folder
BITMAPS_PATH = "bitmaps/"

# Layers names array
LAYER_NAMES = ["background", "static_face", "mouth", "eyes"]
layer_filenames = {"background": "background.png", "static_face": "face.png", "mouth": "mouth.png", "eyes": ["eyes1.png", "eyes2.png"]}
layers = {}

# GUI globals
TARGET_FRAMERATE = 300
update_delay = 1/TARGET_FRAMERATE
working_resolution = None
output_object = None
output_buffer = None
label = None


def state_machine(animation):
    """A simple state machine to control the animation
    """
    while True:
        # Every 10 seconds, change the state from IDLE to MAD or vice versa
        if animation.current_state == "idle":
            animation.current_state = "mad"
            time.sleep(3)
        else:
            animation.current_state = "idle"
            time.sleep(7)


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Get the resolution of the screen from the QApplication
        screen_resolution = app.desktop().screenGeometry()
        screen_resolution = (screen_resolution.width(), screen_resolution.height())

        self.animation = anim.FrameGenerator(working_resolution=screen_resolution, ressource_path="bitmaps/")

        self.frame_count = 0
        self.start_time = time.time()
        self.update_image()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1000 // 300)  # Update at 300 FPS


        # Launch the state machine
        self.thread = threading.Thread(target=state_machine, args=(self.animation,))
        self.thread.daemon = True
        self.thread.start()


    def update_image(self):
        if self.frame_count % 30 == 0:
            print("FPS: ", self.frame_count / (time.time() - self.start_time + 1e-6))

        self.frame_count += 1
        frame = self.animation.execute_animation()
        frame = frame.convert("RGB")
        #frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        frame = np.array(frame)

        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qImg))


    def move_to_screen(self, screen_number):
        screen = QDesktopWidget().screenGeometry(screen_number)
        self.move(screen.left(), screen.top())
        self.showFullScreen()

if __name__ == "__main__":
    #main()
    app = QApplication([])
    window = MainWindow()
    window.move_to_screen(0)

    app.exec_()