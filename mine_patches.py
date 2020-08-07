import sys
import time
import random
import argparse
from src.patch import *
from src.patch_manager import *
from src.utils import *
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_fill_holes
from PIL import Image
from functools import partial 
Image.MAX_IMAGE_PIXELS = None
from pathlib import Path

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
    final_mask = binary_fill_holes(final_mask)
    final_mask = diate_and_erode(final_mask)
    if show_overlay:
        overlay = slide_thumbnail.copy()
        overlay[~final_mask] = overlay[~final_mask] // 2
        plt.imshow(overlay)
        plt.show()
    return final_mask, real_scale

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input_path',
                        dest='input_path',
                        help="input path for the tissue",
                        required=True)
    parser.add_argument('-tm', '--tissue_mask_path',
                        dest='tissue_mask_path',
                        help="input path for the tissue mask")
    parser.add_argument('-am', '--annotation_mask_path',
                        dest='annotation_mask_path',
                        help="input path for the label mask")
    parser.add_argument('-o', '--output_path',
                        dest='output_path',
                        help="output path for the patches")
    parser.add_argument('-lm', '--landmarks_path',
                        dest='landmarks_path',
                        help="output path for the coordinates"+\
                             "of the patches stored")
    parser.add_argument('-t', '--threads',
                        dest='threads',
                        help="number of threads, by default will use all")
    args = parser.parse_args()
    # Path to openslide supported file (.svs, .tiff, etc.)
    slide_path = os.path.abspath(args.input_path)

    if not os.path.exists(slide_path):
        raise ValueError("Could not find the slide, could you recheck the path?")

    if args.output_path is not None:
        if not os.path.exists(args.output_path):
            print("Output Directory does not exist, we are creating one for you.")
            Path(args.output_path).mkdir(parents=True, exist_ok=True)

    if args.landmarks_path is not None:
        if not os.path.exists(args.landmarks_path):
            print("Landmarks Directory does not exist, we are creating one for you.")
            Path(args.output_path).mkdir(parents=True, exist_ok=True)

    if args.output_path is None and args.landmarks_path is None:
        raise ValueError("Please atleast give output_path or landmarks_path")

    if args.tissue_mask_path is None:
        print("Tissue Mask is was not provided. We are creating one for you.")
    if args.label_mask_path is None:
        print("No label Mask was provided. Using Tissue Mask for extraction.")
    out_dir = os.path.abspath(args.output_path)
    if not out_dir.endswith("/"):
        out_dir += "/"
    # Create new instance of slide manager
    manager = PatchManager(slide_path)

    # Generate an initial validity mask
    valid_mask, scale = generate_initial_mask(slide_path, SHOW_VALID)
    manager.set_valid_mask(valid_mask, scale)
    
    # Create partial gaussian blur validity check.
    # This allows us to create methods that only have one argument (the patch) for validity checking.
    gaussian_blur_check = partial(gaussian_blur, upperlimit=UPPER_LIMIT, lowerlimit=LOWER_LIMIT)
    manager.add_patch_criteria(gaussian_blur_check)

    # Save patches releases saves all patches stored in manager, dumps to specified output file
    manager.save_patches(out_dir, n_patches=1000, n_jobs=NUM_WORKERS)
    print("Total time: {}".format(time.time() - start))
