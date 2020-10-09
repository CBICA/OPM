import sys
import warnings
import openslide
import numpy as np
from PIL import Image
from pathlib import Path
from skimage.io import imsave
from src.config import SCALE
from src.utils import tissue_mask
Image.MAX_IMAGE_PIXELS = None

warnings.simplefilter('ignore')


def display_overlay(img, img_mask):
    overlay = img.copy()
    overlay[~img_mask] = (overlay[~img_mask] // 1.5).astype(np.uint8)
    return overlay


def generate_initial_mask(slide_path):
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
    return slide_thumbnail, tissue_mask(slide_thumbnail)


if __name__ == "__main__":
    slide_path = sys.argv[1]
    overlay_output_path = sys.argv[1].split(".")[0] + "_overlay.jpg"
    mask_output_path = sys.argv[1].split(".")[0] + "_mask.png"
    print("Generating masks...")
    image, mask = generate_initial_mask(slide_path)
    print("Saving...")
    print("\t" + mask_output_path)
    imsave(mask_output_path, mask.astype(np.uint8) * 255)
    print("\t" + overlay_output_path)
    imsave(overlay_output_path, display_overlay(image, mask))
    print("Done!")

