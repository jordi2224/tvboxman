import numpy as np
import threading
import time
import animations as anim
import keyboard  # python -m pip install keyboard || requiere acceso root en linux
import cv2

from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QDesktopWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, Qt

# Path to the bitmaps folder
BITMAPS_PATH = "bitmaps/"

# Layers names array
LAYER_NAMES = ["background", "static_face", "mouth", "eyes"]
layer_filenames = {"background": "background.png", "static_face": "face.png", "mouth": "mouth.png",
                   "eyes": ["eyes1.png", "eyes2.png"]}
layers = {}

# GUI globals
TARGET_FRAMERATE = 300
update_delay = 1/TARGET_FRAMERATE

working_resolution = None
output_object = None
output_buffer = None
label = None


def state_machine(animation, root):
    """A simple state machine to control the animation
    """
    while True:
        key = keyboard.read_event().name
        match key:
            case 'd':
                animation.current_state = "idle"
            case 'a':
                animation.current_state = "mad"
            case 's':
                animation.current_state = "lol"
            case 'esc':
                root.destroy()  # close the program
                break

    # detectar micro aqui?
class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        # Get the resolution of the screen from the QApplication
        self.screen_resolution = app.desktop().screenGeometry()
        self.screen_resolution = (self.screen_resolution.width(), self.screen_resolution.height())
        
        # animation_resolution = (1080, 720)
        animation_resolution = self.screen_resolution

        self.animation = anim.FrameGenerator(working_resolution=animation_resolution, ressource_path="bitmaps/")


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
        if self.frame_count % 20 == 0:
            # Clear previos line
            print("\rFPS: ", 20 // (time.time() - self.start_time + 1e-6), "                 ", end="")
            self.start_time = time.time()

        self.frame_count += 1
        frame = self.animation.execute_animation()
        # Make the frame the right size
        # If the animation is not the same size as the screen, resize it
        if frame.shape != self.screen_resolution:
            frame = cv2.resize(frame, self.screen_resolution)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
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
