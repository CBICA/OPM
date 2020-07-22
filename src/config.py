# TODO: Refactor to YAML

config = {
    'visualization' : {
        'show_mined' : False,
        'show_valid' : False
    },
    'misc' : {
        'white_color' : 255,
        'scale' : 8
    }

}


# Visualization and debugging
SHOW_MINED = True
SHOW_VALID = False

# Overlap option
ALLOW_OVERLAP = False
READ_TYPE = 'random' # Change to 'sequential' for increased effiency

# Misc
WHITE_COLOR = 255
SCALE = 8
PATCH_SIZE = (256, 256)
NUM_WORKERS = 100

# Gaussian Filtering
UPPPER_LIMIT = 290000
LOWER_LIMIT = 1500
GAUSSIAN_KERNEL_SIZE = 65
GAUSSIAN_KERNEL_SIGMA = 16

# RGB Masking
PEN_SIZE_THRESHOLD = 200
MINIMUM_COLOR_DIFFERENCE = 30
BGR_RED_CHANNEL = 2
BGR_GREEN_CHANNEL = 1
BGR_BLUE_CHANNEL = 0
PEN_MASK_EXPANSION = 7

# HSV Masking
HSV_MASK_S_THRESHOLD = 15
HSV_MASK_V_THRESHOLD = 90

