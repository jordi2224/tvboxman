import imageio.v2 as imageio
from PIL import Image



# Animation config, to be moved to a config file
BACKGROUND_FILE = "background.png" # Background image, shared by all animations
LAYERS = ["face", "mouth", "eyes", "flair"] # Layers to be added, shared by all animations
"""
This should be something like:
face: blush, hair, nose, anything not moving
mouth: mouth, may change based on voice or something
eyes: eyes, change automatically based on time to simulate blinking
flair: anything that is not part of the face, like special effects
Animations should have layers matching the names in this list
"""

# IDLE ANIMATION
IDLE = {"face": "idle_face.png", "mouth": "idle_mouth.png", "eyes": ["idle_eyes.png", "idle_blink.png"], "flair": None}
MAD = {"face": "idle_face.png", "mouth": "mad_mouth.png", "eyes": "mad_eyes.png", "flair": None}
LOL = {"face": "idle_face.png", "mouth": ["lol_mouth.png", "idle_mouth.png"], "eyes": "lol_eyes.png", "flair": None}

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
            final_image = Image.alpha_composite(final_image, layer.resize(working_resolution))
        else:
            final_image = Image.alpha_composite(final_image, Image.fromarray(layer).resize(working_resolution))

    return final_image


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
                sub_array.append(Image.open(ressource_path + sub).resize(working_resolution))
            layer_images[layer] = sub_array
        else:
            layer_images[layer] = Image.open(ressource_path + filename).resize(working_resolution)
    return layer_images

class FrameGenerator:
    """A class to generate frames based on multiple posible animations
        Hold state accross frames as a sort of memory for the animations
        
    """
    def __init__(self, working_resolution, ressource_path):
        self.current_state = "idle"
        self.current_frame = 0
        self.current_frame_time = 0
        self.current_animation = None
        self.animations = {"idle": self.idle_animation, "mad": self.mad_animation, "lol": self.lol_animation}

        self.working_resolution = working_resolution
        self.background = Image.open(ressource_path + BACKGROUND_FILE).resize(working_resolution)


        # Idle animation initialization
        self.idle_layers = load_layer_images(ressource_path, IDLE, working_resolution)
        self.idle_eyes_state = 0 # 0 is open, 1 is closed
        self.next_change = 0 # Time to change the eyes state
        self.blink_delay = 100
        self.blink_duration = 5
        self.idle_animation_buffer = None

        # Mad animation initialization
        self.mad_animation_buffer = None
        self.mad_layers = load_layer_images(ressource_path, MAD, working_resolution)

        # Lol animation initialization
        self.lol_layers = load_layer_images(ressource_path, LOL, working_resolution)
        self.lol_mouth_state = 0 #open mouth
        self.next_mouth_change = self.current_frame #Time to change the mouth state
        self.laugh_delay = 5
        self.laugh_duration = 4
        self.lol_animation_buffer = None
        

    def execute_animation(self):
        """Execute the current animation
        """
        output = self.animations[self.current_state]()
        self.current_frame += 1

        return output

    def idle_animation(self):
        """Idle animation
        """
        if self.idle_animation_buffer is None:
            # Generate the first frame by assuming the eyes are open
            layer_arrays = [self.background, self.idle_layers["face"], self.idle_layers["mouth"], self.idle_layers["eyes"][0]]
            self.idle_animation_buffer = generate_image(layer_arrays, self.working_resolution)
        else:
            # Do we need to change the eyes state?
            if self.current_frame >= self.next_change:
                
                # Change the eyes state
                if self.idle_eyes_state == 0:
                    self.idle_eyes_state = 1
                    self.next_change = self.current_frame + self.blink_duration
                else:
                    self.idle_eyes_state = 0
                    self.next_change = self.current_frame + self.blink_delay

                # Generate the new frame
                layer_arrays = [self.background, self.idle_layers["face"], self.idle_layers["mouth"], self.idle_layers["eyes"][self.idle_eyes_state]]
                self.idle_animation_buffer = generate_image(layer_arrays, self.working_resolution)

        return self.idle_animation_buffer
            


    def mad_animation(self):
        """Mad animation
        """
        if self.mad_animation_buffer is None:
            layer_arrays = [self.background, self.mad_layers["face"], self.mad_layers["mouth"], self.mad_layers["eyes"]]
            self.mad_animation_buffer = generate_image(layer_arrays, self.working_resolution)
        return self.mad_animation_buffer

    def lol_animation(self):
        """Lol animation
        """
        if self.lol_animation_buffer is None:
            layer_arrays = [self.background, self.lol_layers["face"], self.lol_layers["mouth"][0], self.lol_layers["eyes"]]
            self.lol_animation_buffer = generate_image(layer_arrays, self.working_resolution)
        else:
            # Do we need to change the mouth state?
            if self.current_frame >= self.next_mouth_change:

                # Change the mouth state
                if self.lol_mouth_state== 0:
                    self.lol_mouth_state= 1
                    self.next_mouth_change = self.current_frame + self.laugh_duration
                else:
                    self.lol_mouth_state= 0
                    self.next_mouth_change = self.current_frame + self.laugh_delay

                # Generate the new frame
                layer_arrays = [self.background, self.lol_layers["face"], self.lol_layers["mouth"][self.lol_mouth_state],self.lol_layers["eyes"]]
                self.lol_animation_buffer = generate_image(layer_arrays, self.working_resolution)

        return self.lol_animation_buffer
