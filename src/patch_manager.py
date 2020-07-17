import os
import concurrent.futures
from tqdm import tqdm
from functools import partial


class PatchManager:
    """Manager for patches for openslide"""

    def __init__(self, filename=None):
        """
        Initialize
        :param filename: path to openslide supported file (str)
        """
        self.patches = set()
        self.path = filename

    def set_slide_path(self, filename):
        """
        Set path for slide
        :param filename: path to openslide supported file (str)
        :return: None
        """
        self.path = filename

    def add_patch(self, patch):
        """
        Add patch to manager
        :param patch: Patch object to add to set of patches
        :return: None
        TODO: test hashing to ensure same patch won't be added
        """
        return self.patches.add(patch)

    def remove_patch(self, patch):
        return self.patches.remove(patch)

    def save_patches(self, output_directory, n_jobs=40):
        os.makedirs(output_directory, exist_ok=True)
        _save_patch_partial = partial(_save_patch, output_directory=output_directory)
        with concurrent.futures.ThreadPoolExecutor(n_jobs) as executor:
            futures = list(
                tqdm(
                    executor.map(_save_patch_partial, self.patches),
                    total=len(self.patches),
                    unit="pchs",
                )
            )
        print("done!")


def _save_patch(patch, output_directory):
    patch.save(out_dir=output_directory)
