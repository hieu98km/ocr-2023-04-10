import cv2
import numpy as np
import os 
from PIL import Image

def rotate_image_x(image_path, output_path, x0=-0.5):
    with Image.open(image_path) as image:
        rotated_image = image.rotate(x0, resample=Image.BICUBIC, expand=True)
        rotated_image.save(output_path)

def rotate_image(image_path, output_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    angle_sum = 0
    count = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x1 != x2:
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            angle_sum += angle
            count += 1
    angle = angle_sum / count

    rows, cols, _ = img.shape
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    rotated = cv2.warpAffine(img, M, (cols, rows))

    cv2.imwrite(output_path, rotated)
    

def rotate_image_dir(image_path, output_dir):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    angle_sum = 0
    count = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x1 != x2:
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            angle_sum += angle
            count += 1
    angle = angle_sum / count

    rows, cols, _ = img.shape
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    rotated = cv2.warpAffine(img, M, (cols, rows))

    # Save the output image
    filename = os.path.basename(image_path)
    output_path = os.path.join(output_dir, filename)
    cv2.imwrite(output_path, rotated)