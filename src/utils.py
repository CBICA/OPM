import cv2
import numpy as np
from skimage.filters.rank import maximum, minimum
from skimage.morphology.selem import rectangle, disk
from skimage.morphology import remove_small_objects, label
from skimage.util import img_as_ubyte
from .config import *

def diate_and_erode(mask):
    """
    Take binary mask, dilated it by the patch size, then erode by the patch size.

    """
    dtype = mask.dtype
    if dtype == bool:
        mask = img_as_ubyte(mask).astype(np.uint8)
    selem = rectangle(PATCH_SIZE[0] // SCALE, PATCH_SIZE[1] // SCALE)
    dilated = maximum(mask, selem)
    eroded = minimum(dilated, selem)
    return eroded != 0


def whitespace_mask(Image, Threshold=0.8):
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

    LabColorSpaceImage = cv2.cvtColor(Image, cv2.COLOR_RGB2LAB)
    Luminance = LabColorSpaceImage[:, :, LuminanceChannelNumber]

    NormalizedLuminance = Luminance / WHITE_COLOR
    LuminanceMask = NormalizedLuminance < Threshold
    return LuminanceMask

def pen_mask(Img):
    Img = Img.astype(np.uint8)
    blue_mask = np.logical_and(Img[:,:,1] < Img[:,:,2],
                               Img[:,:,2] - Img[:,:,1] > MINIMUM_COLOR_DIFFERENCE)
    green_mask = np.logical_and(Img[:,:,0] < Img[:,:,1],
                               Img[:,:,1] - Img[:,:,0] > MINIMUM_COLOR_DIFFERENCE)
    mask_with_noise = np.logical_or(blue_mask, green_mask)
    NewMaskImage = remove_small_objects(mask_with_noise, PEN_SIZE_THRESHOLD)
    expanded_mask = maximum(np.where(NewMaskImage, 1, 0), disk(PEN_MASK_EXPANSION))
    return ~(expanded_mask == 1)

def HSV_mask(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    return ~np.logical_or(hsv_image[:,:,2] < HSV_MASK_V_THRESHOLD, hsv_image[:,:,1] < HSV_MASK_S_THRESHOLD)

def gaussian_blur(img, patch_size, upperlimit, lowerlimit):
    try:
        img = np.asarray(img)
        if img.shape[0] < patch_size[0] or img.shape[1] < patch_size[1]:
            return False
        else:
            # Transform to grayscale
            non = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_non = cv2.GaussianBlur(non, (63, 63), 2)
            last_blur_non = np.zeros_like(non)
            # Go through 20 iterations of a gaussian blur
            for i in range(20):
                blur_non = cv2.GaussianBlur(blur_non, (63, 63), 2)
                last_blur_non = cv2.GaussianBlur(blur_non, (63, 63), 2)
            # Find difference of gaussians
            ssd_blur_non = np.sum((last_blur_non - blur_non) ** 2)
            import matplotlib.pyplot as plt
            # If homogeneity
            if upperlimit > ssd_blur_non > lowerlimit - 1:
                return True
            else:
                return False
    except:
        return False

