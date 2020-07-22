import sys
import time
import random
from src.patch import *
from src.patch_manager import *
from src.utils import *
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_fill_holes
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def generate_initial_mask(slide_path, show_overlay=False):
    """
    Helper method to generate random coordinates within a slide
    :param slide_path: Path to slide (str)
    :param num_patches: Number of patches you want to generate
    :return: list of n (x,y) coordinates
    """
    # Open slide and get properties
    slide = openslide.open_slide(slide_path)
    slide_dims = slide.dimensions

    # Call thumbnail for effiency, calculate scale relative to whole slide
    slide_thumbnail = np.asarray(slide.get_thumbnail((slide_dims[0]//SCALE, slide_dims[1]//SCALE)))
    real_scale = (slide_dims[0]/slide_thumbnail.shape[1], slide_dims[1]/slide_thumbnail.shape[0])
    # Mask out whitespace
    thumb_whitespace_mask = whitespace_mask(slide_thumbnail)
    thumb_whitespace_mask = binary_fill_holes(thumb_whitespace_mask)
    thumb_whitespace_mask = diate_and_erode(thumb_whitespace_mask)
    # Remove pixels above G/B color difference threshold
    thumb_pen_mask = pen_mask(slide_thumbnail)
    hybrid_mask = np.logical_and(thumb_whitespace_mask, thumb_pen_mask)
    # Get all values with low saturation (gray) or value (darkness), remove
    hsv_mask = HSV_mask(slide_thumbnail)
    final_mask = np.logical_and(hybrid_mask, hsv_mask)
    if show_overlay:
        overlay = slide_thumbnail.copy()
        overlay[~final_mask] = overlay[~final_mask] // 2
        plt.imshow(overlay)
        plt.show()

    return final_mask, real_scale


if __name__ == "__main__":
    start = time.time()
    # Path to openslide supported file (.svs, .tiff, etc.)
    slide_path = sys.argv[1]
    out_dir = sys.argv[2]
    if not out_dir.endswith("/"):
        out_dir += "/"
    # Create new instance of slide manager
    manager = PatchManager(slide_path)

    # Randomly generate n coordinates
    valid_mask, scale = generate_initial_mask(slide_path, SHOW_VALID)
    manager.set_valid_mask(valid_mask, scale)
    # Save patches releases saves all patches stored in manager, dumps to specified output file
    manager.save_patches(out_dir, n_patches=1000, allow_overlap=False, n_jobs=NUM_WORKERS)
    print("Total time: {}".format(time.time() - start))
