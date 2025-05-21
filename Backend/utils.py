import numpy as np
import math


def convert_to_top_left_v1(x_center, y_center, width, height):
    left = int(x_center - width / 2)
    top = int(y_center - height / 2)
    right = left + int(width)
    bottom = top + int(height)

    return left, top, width, height, right, bottom


def are_boxes_overlapping(bbox1, bbox2):
    left1, top1, right1, bottom1 = bbox1
    left2, top2, right2, bottom2 = bbox2

    if left1 >= right2 or right1 <= left2 or top1 >= bottom2 or bottom1 <= top2:
        return False, 0
    else:
        overlap_area = calculate_overlap_area(bbox1, bbox2)
        return True, overlap_area


def calculate_overlap_area(bbox1, bbox2):
    left1, top1, right1, bottom1 = bbox1
    left2, top2, right2, bottom2 = bbox2

    x_overlap = max(0, min(right1, right2) - max(left1, left2))
    y_overlap = max(0, min(bottom1, bottom2) - max(top1, top2))

    return x_overlap * y_overlap


def calculate_centroid_distance(centroid1, centroid2):
    diff_x = centroid2[0] - centroid1[0]
    diff_y = centroid2[1] - centroid1[1]

    distance = math.sqrt(diff_x ** 2 + diff_y ** 2)
    return distance


def calculate_centroid(bbox):
    x_min, y_min, x_max, y_max = bbox
    centroid_x = (x_min + x_max) / 2
    centroid_y = (y_min + y_max) / 2

    return centroid_x, centroid_y


def euclidean_distance(bbox1, bbox2):
    center1 = [(bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2]
    center2 = [(bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2]
    return np.linalg.norm(np.array(center1) - np.array(center2))


def is_present(target_bbox, bboxes_list):
    best_distance = float('inf')
    best_match = None
    print(f"target_bbox: {target_bbox}")
    print(f" ===>>> bboxes_list: {bboxes_list} <<<=== ")
    for bbox in bboxes_list:
        distance = euclidean_distance(bbox, target_bbox)
        print(f" ===>>> distance: {distance} <<<=== ")
        if distance < 5.0:
            best_distance = distance
            best_match = bbox
            return True
    return False