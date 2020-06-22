import time
import random
from patch import *
from patch_manager import *

# Change patch size
PATCH_SIZE = (256, 256)

def generate_coordinates(slide_path, num_patches):
    """
    Helper method to generate random coordinates within a slide
    :param slide_path: Path to slide (str)
    :param num_patches: Number of patches you want to generate
    :return: list of n (x,y) coordinates
    """
    slide = openslide.open_slide(slide_path)
    slide_dimensions = slide.dimensions
    x_max = slide_dimensions[0] - PATCH_SIZE[0]
    y_max = slide_dimensions[1] - PATCH_SIZE[1]

    x_values = []
    y_values = []
    for i in range(num_patches):
        x_values.append(random.randint(0, x_max))
    for i in range(num_patches):
        y_values.append(random.randint(0, y_max))

    return list(zip(x_values, y_values))

if __name__ == "__main__":
    start = time.time()
    # Path to openslide supported file (.svs, .tiff, etc.)
    slide_path = "../images/example_slide.svs"
    # Create new instance of slide manager
    manager = PatchManager()
    # Set path of slide to string of slide path (can be done when initializing PatchManager(fname))
    manager.set_slide_path(slide_path)

    # Randomly generate n coordinates
    coordinates = generate_coordinates(slide_path, num_patches=500)
    for coordinate in coordinates:
        # Add patches to manager (need to pass it a Patch object as arg)
        manager.add_patch(Patch(slide_path, coordinate, 0, PATCH_SIZE))

    # Save patches releases saves all patches stored in manager, dumps to specified output file
    manager.save_patches("../output/", n_jobs=100)
    print("Total time: {}".format(time.time() - start))