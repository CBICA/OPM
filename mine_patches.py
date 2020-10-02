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
    
    hsv_mask = HSV_mask(slide_thumbnail)

    final_mask = np.logical_and(hsv_mask, hybrid_mask)
    final_mask = binary_fill_holes(final_mask)
    final_mask = diate_and_erode(final_mask)

    return final_mask, real_scale

def generate_initial_mask_binary(slide_path):
    slide = openslide.open_slide(slide_path)
    slide_dims = slide.dimensions

    # Call thumbnail for effiency, calculate scale relative to whole slide
    slide_thumbnail = np.asarray(slide.get_thumbnail((slide_dims[0]//SCALE, slide_dims[1]//SCALE)))
    real_scale = (slide_dims[0]/slide_thumbnail.shape[1], slide_dims[1]/slide_thumbnail.shape[0])
    return cv2.cvtColor(slide_thumbnail, cv2.COLOR_RGB2GRAY) > 0, real_scale

if __name__ == '__main__':
    start = time.time()
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
                        dest='output_path', default=None,
                        help="output path for the patches")
    parser.add_argument('-ocsv', '--output_csv',
                        dest='output_csv', default=None,
                        help="output path for the csv.")
    parser.add_argument('-icsv', '--input_csv',
                        dest='input_csv', default=None,
                        help="CSV with x,y coordinates of patches to mine.")
    parser.add_argument('-lm', '--landmarks_path',
                        dest='landmarks_path',
                        help="output path for the coordinates"+\
                             "of the patches stored")
    parser.add_argument('-t', '--threads',
                        dest='threads',
                        help="number of threads, by default will use all")
    
    args = parser.parse_args()
    if args.output_path is None:
        do_save_patches = False
        out_dir = ""
    else: 
        if not os.path.exists(args.output_path):
            print("Output Directory does not exist, we are creating one for you.")
            Path(args.output_path).mkdir(parents=True, exist_ok=True)
        
        do_save_patches = True
        out_dir = os.path.abspath(args.output_path)
        if not out_dir.endswith("/"):
            out_dir += "/"
    # Path to openslide supported file (.svs, .tiff, etc.)
    slide_path = os.path.abspath(args.input_path)

    if not os.path.exists(slide_path):
        raise ValueError("Could not find the slide, could you recheck the path?")

    if args.landmarks_path is not None:
        if not os.path.exists(args.landmarks_path):
            print("Landmarks Directory does not exist, we are creating one for you.")
            Path(args.output_path).mkdir(parents=True, exist_ok=True)

    if args.output_path is None and args.landmarks_path is None:
        print("No patch output path found-- not saving.")

    if args.tissue_mask_path is None:
        print("Tissue Mask is was not provided. We are creating one for you.")
    if args.annotation_mask_path is None:
        print("No label Mask was provided. Using Tissue Mask for extraction.")
    # Create new instance of slide manager
    manager = PatchManager(slide_path)

    if args.input_csv is None:
        # Generate an initial validity mask
        mask, scale = generate_initial_mask(args.input_path)
        print("Setting valid mask...")
        plt.imshow(mask)
        plt.show()
        manager.set_valid_mask(mask, scale)
        manager.set_openslide_mask = args.annotation_mask_path
        # Save patches releases saves all patches stored in manager, dumps to specified output file
        manager.save_patches(out_dir, n_patches=1000, output_csv=args.output_csv, n_jobs=NUM_WORKERS, save=do_save_patches)
        print("Total time: {}".format(time.time() - start))
    else:
        manager.save_predefined_patches(out_dir, patch_coord_csv=args.input_csv)

