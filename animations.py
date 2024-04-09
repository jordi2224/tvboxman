from PIL import Image
from abc import ABC, abstractmethod
import numpy as np

RENDER_EVERY_FRAME = False

# Animation config, to be moved to a config file
BACKGROUND_FILE = ("vox_fondo_base.png")  # Background image, shared by all animations
LAYERS = ["face", "mouth", "eyes", "flair"]  # Layers to be added, shared by all animations
"""
This should be something like:
face: blush, hair, nose, anything not moving
mouth: mouth, may change based on voice or something
eyes: eyes, change automatically based on time to simulate blinking
flair: anything that is not part of the face, like special effects
Animations should have layers matching the names in this list
"""

# Animation layers declare
IDLE = {"face": "idle_face.png",
        "mouth": ["idle/boca_default_1.png", "idle/boca_default_2.png", "idle/boca_default_3.png"],
        "eyes": ["idle/ojos_default.png", "idle/ojos_cerrados.png"],
        "flair": None}

MAD = {"face": "idle_face.png",
       "mouth": "mad_mouth.png",
       "eyes": "mad_eyes.png",
       "flair": None}

LAUGH = {"face": "idle_face.png",
         "mouth": ["laugh/boca_risa_1.png", "laugh/boca_risa_2.png"],
         "eyes": "laugh/ojos_risa.png",
         "flair": None}


# TALK = {"face": "idle_face.png", "mouth": ["lol_mouth.png", "idle_mouth.png"], "eyes": "lol_eyes.png", "flair": None}


def generate_image(layers: list, working_resolution: tuple):
    """Gets a layers list and generates the final image
    Simply alpha composites the layers on top of each other in the order they are given
    Resizes the layers to the working resolution

    input: layers dictionary
    output: final image
    
    """
    final_image = Image.new("RGBA", working_resolution, (0, 0, 0, 0))
    for layer in layers:
        # If it is already a PIL image, no need to convert it
        if isinstance(layer, Image.Image):
            final_image = Image.alpha_composite(final_image, layer)
        elif isinstance(layer, list):
            # If it's a list, loop through its elements and convert each one to a PIL image
            for sub_layer in layer:
                final_image = Image.alpha_composite(final_image, Image.fromarray(sub_layer))
        else:
            final_image = Image.alpha_composite(final_image, Image.fromarray(layer))


    return np.array(final_image)


def get_static_first_frame(ressource_path, working_resolution):
    """Get the first frame of a static animation
    This should be used when first instantiating the window to have something to display
    Automatically creates an open eye frame of the idle animation
    """
    layer_arrays = []
    layer_arrays.append(Image.open(ressource_path + BACKGROUND_FILE).resize(working_resolution))
    for layer in LAYERS:
        filename = IDLE[layer]
        # If its a list, get the first element
        if isinstance(filename, list):
            filename = filename[0]
        if filename is None:
            continue
        # Create a PIL image from the file and resize it
        img = Image.open(ressource_path + filename)
        layer_arrays.append(img.resize(working_resolution))

    return generate_image(layer_arrays, working_resolution)


def load_layer_images(ressource_path, layer_dict, working_resolution):
    """Helper function to load and resize images for each layer"""
    layer_images = {}
    for layer, filename in layer_dict.items():
        if filename is None:
            continue
        if isinstance(filename, list):
            sub_array = []
            for sub in filename:
                # Convert the image into a numpy array
                sub_array.append(np.array(Image.open(ressource_path + sub).resize(working_resolution)))
            layer_images[layer] = sub_array
        else:
            layer_images[layer] = np.array(Image.open(ressource_path + filename).resize(working_resolution))
    return layer_images


class Animation(ABC):
    def __init__(self, working_resolution, ressource_path):
        self.working_resolution = working_resolution
        self.background = np.array(Image.open(ressource_path + BACKGROUND_FILE).resize(working_resolution))
        self.animation_buffer = None
        self.current_frame = 0
        self.talking = False

    @abstractmethod
    def execute_animation(self, talking):
        pass


class IdleAnimation(Animation):
    def __init__(self, working_resolution, ressource_path):
        super().__init__(working_resolution, ressource_path)
        # Idle animation initialization
        self.layers = load_layer_images(ressource_path, IDLE, working_resolution)
        self.eyes_state = 0  # 0 is open, 1 is closed
        self.open_duration = 15
        self.next_change = self.open_duration  # Time to change the eyes state
        self.blink_duration = 5
        self.animation_buffer = None
        self.mouth_state = 0
        self.mouth_duration = 3
        self.mouth_delay = 3
        self.next_mouth_change = self.mouth_duration

    def execute_animation(self, talking):
        """Idle animation
        """
        if self.animation_buffer is None or RENDER_EVERY_FRAME:
            # Generate the first frame by assuming the eyes are open
            layer_arrays = [self.background, self.layers["face"], self.layers["mouth"],
                            self.layers["eyes"][self.eyes_state]]
            self.animation_buffer = generate_image(layer_arrays, self.working_resolution)
        else:
            # Generate a frame with the current eyes state
            # Do we need to change the eyes state?
            if self.current_frame >= self.next_change:
                self.eyes_state = (self.eyes_state + 1) % len(IDLE["eyes"])
                if self.eyes_state == 0:
                    self.next_change = self.current_frame + self.open_duration
                else:
                    self.next_change = self.current_frame + self.blink_duration
                # Create the new frame
                layer_arrays = [self.background, self.layers["face"], self.layers["mouth"][self.mouth_state],
                                self.layers["eyes"][self.eyes_state]]
                self.animation_buffer = generate_image(layer_arrays, self.working_resolution)

                self.current_frame += 1
                return self.animation_buffer

            #Guarrada, esto podría ser una clase para ahorrar lineas ?
            if talking and self.current_frame >= self.next_mouth_change:
                # Change the mouth state
                self.mouth_state = (self.mouth_state + 1) % len(IDLE["mouth"])
                if self.mouth_state == 0:
                    self.next_mouth_change = self.current_frame + self.mouth_delay
                else:
                    self.next_mouth_change = self.current_frame + self.mouth_delay
                # Generate the new frame
                layer_arrays = [self.background, self.layers["face"], self.layers["mouth"][self.mouth_state],
                                self.layers["eyes"]]
                self.animation_buffer = generate_image(layer_arrays, self.working_resolution)
            if not talking:
                self.mouth_state = 0
                layer_arrays = [self.background, self.layers["face"], self.layers["mouth"][self.mouth_state],
                                self.layers["eyes"]]
                self.animation_buffer = generate_image(layer_arrays, self.working_resolution)

        self.current_frame += 1
        return self.animation_buffer


class MadAnimation(Animation):
    def __init__(self, working_resolution, ressource_path):
        super().__init__(working_resolution, ressource_path)
        # Mad animation initialization
        self.layers = load_layer_images(ressource_path, MAD, working_resolution)
        self.animation_buffer = None

    def execute_animation(self, talking):
        """Mad animation
        """
        if self.animation_buffer is None or RENDER_EVERY_FRAME:
            layer_arrays = [self.background, self.layers["face"], self.layers["mouth"], self.layers["eyes"]]
            self.animation_buffer = generate_image(layer_arrays, self.working_resolution)

        self.current_frame += 1
        return self.animation_buffer


class LaughAnimation(Animation):

    def __init__(self, working_resolution, ressource_path):
        super().__init__(working_resolution, ressource_path)
        # Laugh animation initialization
        self.layers = load_layer_images(ressource_path, LAUGH, working_resolution)
        self.state = 0
        self.mouth_duration = 2
        self.mouth_delay = 2
        self.next_mouth_change = self.mouth_duration
        self.animation_buffer = None

    def execute_animation(self, talking):
        if self.animation_buffer is None or RENDER_EVERY_FRAME:
            layer_arrays = [self.background, self.layers["face"], self.layers["mouth"][0], self.layers["eyes"]]
            self.animation_buffer = generate_image(layer_arrays, self.working_resolution)
        else:
            # Do we need to change the mouth state?
            if talking and self.current_frame >= self.next_mouth_change:
                # Change the mouth state
                self.state = 1 - self.state
                if self.state == 0:
                    self.next_mouth_change = self.current_frame + self.mouth_delay
                else:
                    self.next_mouth_change = self.current_frame + self.mouth_delay
                # Generate the new frame
                layer_arrays = [self.background, self.layers["face"], self.layers["mouth"][self.state],
                                self.layers["eyes"]]
                self.animation_buffer = generate_image(layer_arrays, self.working_resolution)
            if not talking:
                self.state = 0
                layer_arrays = [self.background, self.layers["face"], self.layers["mouth"][self.state],
                                self.layers["eyes"]]
                self.animation_buffer = generate_image(layer_arrays, self.working_resolution)

        self.current_frame += 1
        return self.animation_buffer

class FrameGenerator:
    """A class to generate frames based on multiple posible animations
        Hold state accross frames as a sort of memory for the animations
        
    """

    def __init__(self, working_resolution, ressource_path):
        self.current_state = "idle"
        self.current_frame = 0
        self.current_frame_time = 0
        self.current_animation = None
        self.talking = False
        self.working_resolution = working_resolution

        # Idle animation initialization
        self.idle = IdleAnimation(working_resolution, ressource_path)

        # Mad animation initialization
        self.mad = MadAnimation(working_resolution, ressource_path)

        # Laugh animation initialization
        self.laugh = LaughAnimation(working_resolution, ressource_path)

        # Dict to hold the animations
        self.animations = {"idle": self.idle, "mad": self.mad, "laugh": self.laugh}

    def execute_animation(self):
        """Execute the current animation
        """
        output = self.animations[self.current_state].execute_animation(self.talking)
        self.current_frame += 1

        return output
