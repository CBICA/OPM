import sys
import time
import random
from patch import *
from patch_manager import *
import cv2
import numpy as np
from skimage.morphology.selem import rectangle
from skimage.filters.rank import maximum, minimum


# Change patch size
SCALE = 20
PATCH_SIZE = (256, 256)
WHITE_COLOR = 255
NUM_WORKERS = 100
def tissue_mask(Image, Threshold=0.8):
    """
    Get a binary mask where true denotes 'not white'
    :param I: Image to create mask from.
    :param thresh: Threshold of L in I_LAB colorspace. All values above this threshold are masked out.
    :return: Binary mask of I.
    """
    # Luminance from black (0) to white (100)
    # a from green (−) to red (+)
    # b from blue (−) to yellow (+)

    LuminanceChannelNumber = 0

    LabColorSpaceImage          = cv2.cvtColor(Image, cv2.COLOR_RGB2LAB)
    Luminance                   = LabColorSpaceImage[:, :, LuminanceChannelNumber]

    NormalizedLuminance         = Luminance/WHITE_COLOR
    LuminanceMask               = NormalizedLuminance < Threshold
    return LuminanceMask

def diate_and_erode(mask):
    """
    Take binary mask, dilated it by the patch size, then erode by the patch size.
    
    """
    dtype = mask.dtype
    if dtype == bool:
        mask = mask.astype(np.uint8)
    selem = rectangle(PATCH_SIZE[0]//SCALE, PATCH_SIZE[1]//SCALE)
    dilated = maximum(mask, selem)
    eroded = minimum(dilated, selem)
    return eroded != 0


def generate_coordinates(slide_path, num_patches):
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
    
    # Find mask of thumbnail
    thumb_mask = tissue_mask(slide_thumbnail)
    
    # Expand mask by PATCH_SIZE/2, then contract it. This insures that regions with lots of whitespace (i.e. adipose, etc.) are 'filled' and have
    # the same chance of getting called as filled tissue.
    # Feel free to use whatever masking you want.
    final_mask = diate_and_erode(thumb_mask)
    
    # Find indices on filled mask, then multiply by real scale to get actual coordinates
    indices = np.argwhere(final_mask)
    # (X/Y get reversed because openslide and np use reversed height/width indexing)
    x_values = np.round(indices[:,1] * real_scale[1]).astype(int)
    y_values = np.round(indices[:,0] * real_scale[0]).astype(int)
    
    # Randomly select num_patches indices from all tissue indices
    index = np.random.choice(x_values.shape[0], num_patches, replace=False)

    return list(zip(x_values[index], y_values[index]))


if __name__ == "__main__":
    start = time.time()
    # Path to openslide supported file (.svs, .tiff, etc.)
    slide_path = sys.argv[1]
    out_dir = sys.argv[2]
    if not out_dir.endswith("/"):
        outdir += "/"
    # Create new instance of slide manager
    manager = PatchManager()
    # Set path of slide to string of slide path (can be done when initializing PatchManager(fname))
    manager.set_slide_path(slide_path)

    # Randomly generate n coordinates
    coordinates = generate_coordinates(slide_path, num_patches=1000)
    for coordinate in coordinates:
        # Add patches to manager (need to pass it a Patch object as arg)
        manager.add_patch(Patch(slide_path, coordinate, 0, PATCH_SIZE))

    # Save patches releases saves all patches stored in manager, dumps to specified output file
    manager.save_patches(out_dir, n_jobs=NUM_WORKERS)
    print("Total time: {}".format(time.time() - start))
