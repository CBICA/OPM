import concurrent.futures
import os
from functools import partial
from .patch import Patch
from .config import PATCH_SIZE, SHOW_MINED, READ_TYPE
import numpy as np
import openslide
from tqdm import tqdm
import matplotlib.pyplot as plt

class PatchManager:
    """Manager for patches for openslide"""

    def __init__(self, filename):
        """
        Initialize
        :param filename: path to openslide supported file (str)
        """
        self.patches = list()
        self.path = filename
        self.slide_dims = openslide.open_slide(self.path).dimensions
        self.valid_mask = None
        self.mined_mask = None
        self.valid_mask_scale = (0, 0)
        self.valid_patch_checks = []

    def set_slide_path(self, filename):
        """
        Set path for slide
        :param filename: path to openslide supported file (str)
        :return: None
        """
        self.path = filename

    def set_valid_mask(self, mask, scale=(1,1)):
        self.valid_mask = mask
        self.mined_mask = np.zeros_like(mask)
        self.valid_mask_scale = scale

    def add_patch(self, patch, allow_overlap=False):
        """
        Add patch to manager
        :param patch: Patch object to add to set of patches
        :return: None
        TODO: test hashing to ensure same patch won't be added
        """
        try:
            if not allow_overlap and self.valid_mask is None:
                print("allow_overlap can only true if valid_mask is set.")
                exit(1)

            valid_start_x = int(round((patch.coordinates[0] - PATCH_SIZE[0] + 1)/self.valid_mask_scale[0]))
            valid_start_y = int(round((patch.coordinates[1] - PATCH_SIZE[1] + 1)/self.valid_mask_scale[1]))
            if not allow_overlap:
                valid_end_x = int(round((patch.coordinates[0] + PATCH_SIZE[0]) / self.valid_mask_scale[0]))
                valid_end_y = int(round((patch.coordinates[1] + PATCH_SIZE[1]) / self.valid_mask_scale[1]))
                self.valid_mask[
                    self.min_bound_check(valid_start_x):self.width_bound_check(valid_end_x),
                    self.min_bound_check(valid_start_y):self.height_bound_check(valid_end_y)
                ] = False
            else:
                self.valid_mask[valid_start_x, valid_start_y] = False # Change only the starting index to prevent calling the same patch

            mined_start_x = int(round((patch.coordinates[0]) / self.valid_mask_scale[0]))
            mined_start_y = int(round((patch.coordinates[1]) / self.valid_mask_scale[1]))
            mined_end_x = int(round((patch.coordinates[0] + PATCH_SIZE[0]) / self.valid_mask_scale[0]))
            mined_end_y = int(round((patch.coordinates[1] + PATCH_SIZE[1]) / self.valid_mask_scale[1]))

            self.mined_mask[
            self.min_bound_check(mined_start_x):self.width_bound_check(mined_end_x),
            self.min_bound_check(mined_start_y):self.width_bound_check(mined_end_y)
            ] = True

            self.patches.append(patch)
            return True

        except:
            return False

    def add_next_patch(self, allow_overlap=False):
        """
        Add patch to manager
        :param patch: Patch object to add to set of patches
        :return: None
        TODO: test hashing to ensure same patch won't be added
        """
        if self.valid_mask is None:
            # Find indices on filled mask, then multiply by real scale to get actual coordinates
            x_value = np.random.choice(self.slide_dims[0], 1)
            y_value = np.random.choice(self.slide_dims[1], 1)
            coordinates = np.array([x_value, y_value])
            patch = Patch(self, coordinates, 0, PATCH_SIZE)
            return self.add_patch(patch, allow_overlap)

        else:
            # Find indices on filled mask, then multiply by real scale to get actual coordinates
            try:
                indices = np.argwhere(self.valid_mask)
                # (X/Y get reversed because openslide and np use reversed height/width indexing)
                x_values = np.round(indices[:, 0] * self.valid_mask_scale[0]).astype(int)
                y_values = np.round(indices[:, 1] * self.valid_mask_scale[1]).astype(int)
                num_indices = len(indices.ravel()) // 2
                print("%i indices left " % num_indices, end="\r")
                if READ_TYPE == 'random':
                    choice = np.random.choice(num_indices, 1)
                elif READ_TYPE == 'sequential':
                    choice = 0
                else:
                    print("Unrecognized read type %s" % READ_TYPE)
                    exit(1)
                coordinates = np.array([x_values[choice], y_values[choice]]).ravel()
                patch = Patch(self, coordinates, 0, PATCH_SIZE)

                return self.add_patch(patch, allow_overlap)
            except:
                return False


    def remove_patch(self, patch):
        return self.patches.remove(patch)

    def min_bound_check(self, num):
        return max(num, 0)

    def height_bound_check(self, num):
        return min(num, self.slide_dims[0])

    def width_bound_check(self, num):
        return min(num, self.slide_dims[1])

    def add_patch_criteria(self, patch_validity_check):
        self.valid_patch_checks.append(patch_validity_check)

    def save_patches(self, output_directory, n_patches, allow_overlap=False, n_jobs=40):
        os.makedirs(output_directory, exist_ok=True)
        _save_patch_partial = partial(_save_patch, output_directory=output_directory)
        n_completed = 0
        original_valid_mask =self.valid_mask.copy()
        saturated = False
        while n_patches - n_completed > 0 and not saturated:
            could_not_add_flag = False
            for _ in range(n_patches-n_completed):
                if not self.add_next_patch(allow_overlap=allow_overlap):
                    could_not_add_flag = True
                    print("\nCould not add new patch, breaking.")
                    break
            if not could_not_add_flag:
                print("") # Fixes spacing in case it breaks. Inelegant but I'll fix later

            if len(self.patches) != n_patches - n_completed:
                print("Slide has reached saturation: No more non-overlapping patches to be found.\n"
                              "Change SHOW_MINED in config.py to True to see patch locations.\n"
                              "Alternatively, change READ_TYPE to 'sequential' for greater mining effiency.")
                saturated = True

            if SHOW_MINED:
                slide = openslide.open_slide(self.path)
                slide_thumbnail = np.asarray(slide.get_thumbnail((self.slide_dims[0] // int(self.valid_mask_scale[0]),
                    self.slide_dims[1]//int(self.valid_mask_scale[1]))))
                overlay = slide_thumbnail.copy()

                overlay[~self.mined_mask] = overlay[~self.mined_mask] // 2
                plt.imshow(overlay)
                plt.show()
                plt.imshow(original_valid_mask)
                plt.show()

            with concurrent.futures.ThreadPoolExecutor(n_jobs) as executor:
                futures = list(
                    tqdm(
                        executor.map(_save_patch_partial, self.patches),
                        total=len(self.patches),
                        unit="pchs",
                    )
                )
                self.patches = list()
                successful = np.count_nonzero(np.array(futures))
                print("{}/{} valid patches found in this run.".format(successful, n_patches))
                n_completed += successful

        print("Done!")


def _save_patch(patch, output_directory):
    return patch.save(out_dir=output_directory)
