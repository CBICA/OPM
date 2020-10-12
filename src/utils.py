import cv2
import numpy as np
from skimage.filters.rank import maximum, minimum
from skimage.filters import threshold_otsu, median, gaussian
from skimage.morphology.selem import rectangle, disk
from skimage.morphology import remove_small_objects, remove_small_holes
from skimage.util import img_as_ubyte
from skimage.color.colorconv import rgb2hsv
from .config import *
from numpy.fft import fft2, fftshift, ifft2
import matplotlib.pyplot as plt

# RGB Masking (pen) constants
RGB_RED_CHANNEL = 0
RGB_GREEN_CHANNEL = 1
RGB_BLUE_CHANNEL = 2
MIN_COLOR_DIFFERENCE = 40

# HSV Masking
HSV_HUE_CHANNEL = 0
HSV_SAT_CHANNEL = 1
HSV_VAL_CHANNEL = 2
MIN_SAT = 20 / 255
MIN_VAL = 30 / 255

# LAB Masking
LAB_L_CHANNEL = 0
LAB_A_CHANNEL = 1
LAB_B_CHANNEL = 2
LAB_L_THRESHOLD = 0.80


def display_overlay(image, mask):
    overlay = image.copy()
    overlay[~mask] = (overlay[~mask] // 1.5).astype(np.uint8)
    plt.imshow(overlay)
    plt.show()


def hue_range_mask(image, min_hue, max_hue, sat_min=0.05):
    hsv_image = rgb2hsv(image)
    h_channel = gaussian(hsv_image[:, :, HSV_HUE_CHANNEL])
    above_min = h_channel > min_hue
    below_max = h_channel < max_hue

    s_channel = gaussian(hsv_image[:, :, HSV_SAT_CHANNEL])
    above_sat = s_channel > sat_min
    return np.logical_and(np.logical_and(above_min, below_max), above_sat)

def tissue_mask(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    high_pass_saturation = high_pass_isolation_filter(hsv_image[:, :, 1])
    high_pass_value = high_pass_isolation_filter(hsv_image[:, :, 2])
    sat_val_mask = np.abs(high_pass_saturation + high_pass_value)

    cropped = border_crop(sat_val_mask, fx=0.025, fy=0.025)
    plt.imshow(cropped)
    plt.show()
    thresholded_sat_val_mask = cropped >= threshold_otsu(cropped)
    filled = remove_small_holes(thresholded_sat_val_mask, PEN_SIZE_THRESHOLD)
    pruned = remove_small_objects(filled, PEN_SIZE_THRESHOLD)
    pen_markings = basic_pen_mask(image)
    final_mask = pruned.copy()
    final_mask[pen_markings] = False
    return final_mask


def tissue_mask_2(image):
    hue_mask = hue_range_mask(image, 0.8, 0.95)
    final_mask = remove_small_holes(hue_mask)
    return final_mask


def high_pass_isolation_filter(image):
    transformed = fftshift(fft2(image))
    l_x, l_y = transformed.shape[0], transformed.shape[1]
    X, Y = np.ogrid[:l_x, :l_y]
    outer_disk_mask = (X - l_x / 2) ** 2 + (Y - l_y / 2) ** 2 > (l_x / 2) ** 1.5
    transformed[~outer_disk_mask] = 0
    reconstructed = ifft2(transformed)
    return median(np.abs(reconstructed))


def border_crop(mask, fx=None, fy=None):
    bring_in_height = int(np.round(mask.shape[0] * fy))
    bring_in_width = int(np.round(mask.shape[1] * fx))

    cropping_mask = np.ones(mask.shape, dtype=bool)
    cropping_mask[
        bring_in_height : mask.shape[0] - bring_in_height,
        bring_in_width : mask.shape[1] - bring_in_width
    ] = False

    mask[cropping_mask] = 0
    return mask



def dilate_and_erode(mask):
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


def basic_pen_mask(image):
    """
    Mask based on RGB color channel differences. Will return true where the pixels are significantly more green
    or blue than the other channels.
    TODO: Convert to OD, threshold based on green and blue densities
    TODO: Add watershedding of pen
    :param image: RGB numpy image
    :return: image mask, True pixels are pen
    """
    green_mask = np.bitwise_and(
        image[:, :, RGB_GREEN_CHANNEL] > image[:, :, RGB_GREEN_CHANNEL],
        image[:, :, RGB_GREEN_CHANNEL] - image[:, :, RGB_GREEN_CHANNEL] > MIN_COLOR_DIFFERENCE)

    blue_mask = np.bitwise_and(
        image[:, :, RGB_BLUE_CHANNEL] > image[:, :, RGB_GREEN_CHANNEL],
        image[:, :, RGB_BLUE_CHANNEL] - image[:, :, RGB_GREEN_CHANNEL] > MIN_COLOR_DIFFERENCE)

    masked_pen = np.bitwise_or(green_mask, blue_mask)
    new_mask_image = remove_small_objects(masked_pen, PEN_SIZE_THRESHOLD)

    return maximum(np.where(new_mask_image, 1, 0), disk(PEN_MASK_EXPANSION)).astype(bool)


def basic_hsv_mask(image):
    """
    Mask based on low saturation and value (gray-black colors)
    :param image: RGB numpy image
    :return: image mask, True pixels are gray-black.
    """
    hsv_image = rgb2hsv(image)
    return np.bitwise_or(hsv_image[:, :, HSV_SAT_CHANNEL] <= MIN_SAT,
                         hsv_image[:, :, HSV_VAL_CHANNEL] <= MIN_VAL)

def hybrid_mask(image):
    return ~np.bitwise_or(basic_hsv_mask(image), basic_pen_mask(image))

def trim_mask(image, mask, background_value=0, mask_func=hybrid_mask):
    """
    Set the values of single-channel image to 0 if outside of whitespace.
    :param image: RGB numpy image
    :param mask: Mask to be trimmed
    :param background_value: Value to set in mask.
    :param mask_func: Func which takes `image` as a parameter. Returns a binary mask, `True` will be background.
    :return: `mask` with excess trimmed off
    """
    mask_copy = mask.copy()
    masked_image = mask_func(image)
    mask_copy[masked_image] = background_value
    return mask_copy


def patch_size_check(img, patch_height, patch_width):
    if img.size[0] != patch_height or img.size[1] != patch_width:
        return False
    else:
        return True


def alpha_channel_check(img, alpha_thresh=0):
    img = np.asarray(img)
    alpha_channel = img[:, :, 3]

    if np.any(alpha_channel != 255):
        return False
    else:
        return True


def difference_of_gauss_check(img, upperlimit, lowerlimit):
    try:
        patch_size = img.size
        img = np.asarray(img)
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

        # If homogeneity
        if upperlimit > ssd_blur_non > lowerlimit - 1:
            return True
        else:
            return False
    except:
        return False

