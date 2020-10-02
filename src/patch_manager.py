import concurrent.futures
import os
from functools import partial
from .patch import Patch
from .config import PATCH_SIZE, SHOW_MINED, SHOW_VALID, READ_TYPE, OVERLAP_FACTOR
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
        self.openslide_mask_path = None

    def set_slide_path(self, filename):
        """
        Set path for slide
        :param filename: path to openslide supported file (str)
        :return: None
        """
        self.path = filename
    
    def set_openslide_mask(self, path):
        self.openslide_mask_path = path
    
    def set_valid_mask(self, mask, scale=(1,1)):
        self.valid_mask = mask
        self.mined_mask = np.zeros_like(mask)
        self.valid_mask_scale = scale
    
    def add_patch(self, patch):
        """
        Add patch to manager
        :param patch: Patch object to add to set of patches
        :return: None
        TODO: test hashing to ensure same patch won't be added
        """
        try:
            if OVERLAP_FACTOR != 1 and self.valid_mask is None:
                print("OVERLAP_FACTOR can only be not one if valid_mask is set.")
                exit(1)
            inverse_overlap_factor = 1-OVERLAP_FACTOR
            valid_start_x = int(round((patch.coordinates[0] - int(round((PATCH_SIZE[0] + 1) * inverse_overlap_factor)))/self.valid_mask_scale[0]))
            valid_start_y = int(round((patch.coordinates[1] - int(round((PATCH_SIZE[1] + 1) * inverse_overlap_factor)))/self.valid_mask_scale[1]))
            if OVERLAP_FACTOR != 1:
                valid_end_x = int(round((patch.coordinates[0] + int(round(PATCH_SIZE[0] * inverse_overlap_factor))) / self.valid_mask_scale[0]))
                valid_end_y = int(round((patch.coordinates[1] + int(round(PATCH_SIZE[1] * inverse_overlap_factor))) / self.valid_mask_scale[1]))
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

        except Exception as e:
            print(e)
            return False

    def add_next_patch(self):
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
            return self.add_patch(patch)

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

                return self.add_patch(patch)
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

    def save_patches(self, output_directory, n_patches, output_csv=None, n_jobs=40, save=True):
        if save:
            os.makedirs(output_directory, exist_ok=True)
        if output_csv is not None:
            print("Creating output csv")
            output = open(output_csv, "w")
            output.write("Patch_X, Patch_Y\n")

        if SHOW_VALID:
            plt.imshow(self.valid_mask)
            plt.show()
        
        _save_patch_partial = partial(_save_patch, output_directory=output_directory, save=save)
        n_completed = 0
        saturated = False
        while n_patches - n_completed > 0 and not saturated:
            could_not_add_flag = False
            for _ in range(n_patches-n_completed):
                if not self.add_next_patch():
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

            with concurrent.futures.ThreadPoolExecutor(n_jobs) as executor:
                futures = list(
                    tqdm(
                        executor.map(_save_patch_partial, self.patches),
                        total=len(self.patches),
                        unit="pchs",
                    )
                )
                self.patches = list()
                np_futures_array = np.array(futures)
                successful_indices = np.argwhere(np_futures_array[:,0] == True)
                unsuccessful_indices = np.argwhere(np_futures_array[:,0] == False)
                successful = np.count_nonzero(np.array(futures) == True)
                print("{}/{} valid patches found in this run.".format(successful, n_patches))
                n_completed += successful
                if output_csv is not None:
                    for index in successful_indices:
                        coords = np_futures_array[:,1][index][0].coordinates
                        output.write("{},{}\n".format(coords[0], coords[1]))

        output.close()
        print("Done!")

    def save_predefined_patches(self, output_directory, patch_coord_csv, n_jobs=40):
        # Todo, port to pandas or something more sophisticated?
        with open(patch_coord_csv, "r") as input_csv:
            for line in input_csv:
                try:
                    x, y = [int(val) for val in line.split(",")]
                    _save_patch_partial = partial(_save_patch, output_directory=output_directory, save=True)
                    patch = Patch(self, (x, y), 0, PATCH_SIZE)
                    self.patches.append(patch)
                except:
                    pass
        with concurrent.futures.ThreadPoolExecutor(n_jobs) as executor:
            futures = list(
                tqdm(
                    executor.map(_save_patch_partial, self.patches),
                    total=len(self.patches),
                    unit="pchs",
                )
            )
            self.patches = list()
            successful = np.count_nonzero(np.array(futures) == True)
            print("{} valid patches found.".format(successful))


def _save_patch(patch, output_directory, save):
    return patch.save(out_dir=output_directory, save=save)
