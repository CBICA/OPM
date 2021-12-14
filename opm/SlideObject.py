import zarr
from tifffile import imread


def open_slide(filename):
    store = imread(filename, aszarr=True)
    return SlideObject(store, mode='r')


class SlideObject(zarr.hierarchy.Group):
    def __init__(self, store, mode='r'):
        self.arr = zarr.open(store, mode)
        self.dimensions = self.arr[0].shape[1], self.arr[0].shape[0]

    def read_region(self, location, level, size):
        x, y = location
        end_x, end_y = x + size[0], y + size[1]
        return self.arr[level][y:end_y, x:end_x]

    def get_thumbnail(self, size):
        stride = self.dimensions[0] // size[0], self.dimensions[1] // size[1]
        return self.arr[0][::stride[1], ::stride[0]]





