import os
from function.image_processing import rotate_image_dir

# Specify the input and output directories
input_dir = r"./image/image_goc"
output_dir = r"./image/image_quay"

# Process each image in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        image_path = os.path.join(input_dir, filename)
        rotate_image_dir(image_path, output_dir)
        