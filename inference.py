import cv2
import json
import numpy as np
import os
import time
import glob

from model import efficientdet
from utils import preprocess_image, postprocess_boxes
from utils.draw_boxes import draw_boxes

def get_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-model_path", type=str, required=True)
    parser.add_argument("-image_dir", type=str, required=True)
    parser.add_argument("-output_image_dir", type=str, required=True)

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'

    phi = 1
    weighted_bifpn = True
    model_path = args.model_path
    image_sizes = (512, 640, 768, 896, 1024, 1280, 1408)
    image_size = image_sizes[phi]
    # coco classes
    classes = {value['id'] - 1: value['name'] for value in json.load(open('coco_90.json', 'r')).values()}
    num_classes = 90
    score_threshold = 0.3
    colors = [np.random.randint(0, 256, 3).tolist() for _ in range(num_classes)]
    _, model = efficientdet(phi=phi,
                            weighted_bifpn=weighted_bifpn,
                            num_classes=num_classes,
                            score_threshold=score_threshold)
    model.load_weights(model_path, by_name=True)

    for image_path in glob.glob(args.image_dir):
        image = cv2.imread(image_path)
        src_image = image.copy()
        # BGR -> RGB
        image = image[:, :, ::-1]
        h, w = image.shape[:2]

        image, scale = preprocess_image(image, image_size=image_size)
        # run network
        start = time.time()
        boxes, scores, labels = model.predict_on_batch([np.expand_dims(image, axis=0)])
        boxes, scores, labels = np.squeeze(boxes), np.squeeze(scores), np.squeeze(labels)
        print(time.time() - start)
        boxes = postprocess_boxes(boxes=boxes, scale=scale, height=h, width=w)

        # select indices which have a score above the threshold
        indices = np.where(scores[:] > score_threshold)[0]

        # select those detections
        boxes = boxes[indices]
        labels = labels[indices]

        draw_boxes(src_image, boxes, scores, labels, colors, classes)

        # cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        # cv2.imshow('image', src_image)
        # cv2.waitKey(0)
        cv2.imwrite(args.output_image_dir+image_path, src_image)


if __name__ == '__main__':
    main()
