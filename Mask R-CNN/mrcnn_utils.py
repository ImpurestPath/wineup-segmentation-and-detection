import numpy as np
import skimage.transform
from cv2 import cv2
from distutils.version import LooseVersion


def resize(image, output_shape, order=1, mode='constant', cval=0, clip=True,
           preserve_range=False, anti_aliasing=False, anti_aliasing_sigma=None):
    """A wrapper for Scikit-Image resize().

    Scikit-Image generates warnings on every call to resize() if it doesn't
    receive the right parameters. The right parameters depend on the version
    of skimage. This solves the problem by using different parameters per
    version. And it provides a central place to control resizing defaults.
    """
    if LooseVersion(skimage.__version__) >= LooseVersion("0.14"):
        # New in 0.14: anti_aliasing. Default it to False for backward
        # compatibility with skimage 0.13.
        return skimage.transform.resize(
            image, output_shape,
            order=order, mode=mode, cval=cval, clip=clip,
            preserve_range=preserve_range, anti_aliasing=anti_aliasing,
            anti_aliasing_sigma=anti_aliasing_sigma)
    else:
        return skimage.transform.resize(
            image, output_shape,
            order=order, mode=mode, cval=cval, clip=clip,
            preserve_range=preserve_range)

def generate_segmentation_from_masks(instance_masks, processed_bboxes, height, width):
    """Converts a mask generated by the neural network to a format similar
    to its original shape.
    mask: [height, width] of type float. A small, typically 28x28 mask.
    bbox: [y1, x1, y2, x2]. The box to fit the mask in.

    Returns a binary mask with the same size as the original image.
    """
    threshold = 0.5
    full_mask = np.zeros([processed_bboxes.shape[0], height, width], dtype=np.uint8)
    for i in range(processed_bboxes.shape[0]):
        x1, y1, x2, y2 = processed_bboxes[i].astype("int")
        mask = instance_masks[i]
        mask = resize(mask, (y2, x2))
        mask = np.where(mask >= threshold, 1, 0).astype(np.uint8)

        # Put the mask in the right location.
        full_mask[i, y1:y1+y2, x1:x1+x2] = mask

    return full_mask

def smooth_contours_on_mask(mask):
    height = mask.shape[0]
    width = mask.shape[1]
    contours, _hierarchy = cv2.findContours(mask[:, :, 0].astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)
    smoothened = []

    for cnt in contours:
        epsilon = 0.003*cv2.arcLength(cnt,True)
        smoothened.append(cv2.approxPolyDP(cnt, epsilon, True))
    final_mask = np.zeros((height, width, 3))
    cv2.drawContours(final_mask, smoothened, -1, (1, 1, 1), -1)
    
    return final_mask

def check_background_quality(mask, image):
    layer0 = np.copy(image[:, :, 0])
    layer1 = np.copy(image[:, :, 1])
    layer2 = np.copy(image[:, :, 2])

    layer0[np.where(mask[:, :, 0] > 0)] = 0
    layer1[np.where(mask[:, :, 1] > 0)] = 0
    layer2[np.where(mask[:, :, 2] > 0)] = 0
    max_0 = np.argmax(np.bincount(layer0.flat[np.flatnonzero(layer0)] ))
    max_1 = np.argmax(np.bincount(layer1.flat[np.flatnonzero(layer1)] ))
    max_2 = np.argmax(np.bincount(layer2.flat[np.flatnonzero(layer2)] ))

    if max_0 > 0xE0 and max_1 > 0xE0 and max_2 > 0xE0:
        is_good = True
    else:
        is_good = False

    return is_good

def add_white_background(mask, image):
    mask = cv2.blur(mask, (3, 3))
    background = (mask * -1.0 + 1.0) * 255

    image[:, :, :] = image[:, :, :] * mask + background
    
    return image