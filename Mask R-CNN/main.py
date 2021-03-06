from PIL import Image
import numpy as np
import mrcnn
import argparse
import os
from cv2 import cv2

if __name__ == "__main__":

    # Argument parsing, multiple arguments allowed
    parser = argparse.ArgumentParser(description="Segment bottle images")
    parser.add_argument('--paths', metavar='path', default="./paths.list",
                        help="File, containing paths to images")
    parser.add_argument('--dest', metavar='path', default="./results",
                        help='Destination folder to srore your results')
    args = parser.parse_args()

    # Make sure that file paths exist
    if not os.path.isfile(args.paths):
        raise Exception(("File with paths to images doesn't exist by path '{0}'").format(args.paths))
    # Read image paths
    fl = open(args.paths, 'r')
    image_path = fl.readlines()
    for i in range(len(image_path)):
        image_path[i] = image_path[i].rstrip()
    fl.close()
    
    # Make sure that destination directory is valid
    if not os.path.isdir(args.dest):
        if not os.path.isdir('./results'):
            os.mkdir("./results")
        args.dest = './results'
    
    # Build the output paths
    output_image_path = [os.path.join(args.dest, os.path.split(s)[-1]) for s in image_path]

    # Start backend and process incoming images
    mask, images = [], []
    backend = mrcnn.SegmentationBackend()
    for i in range(len(image_path)):
        result = backend.run(image_path[i])
        mask.append(result[0])
        images.append(result[1])
    del backend

    # Save all processed images
    for i in range(len(image_path)):
        Image.fromarray(images[i].astype(np.uint8)).save(output_image_path[i])
    
    # Show the result
    #cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    #cv2.resizeWindow("Image", 800, 600)
    #cv2.imshow("Image", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
