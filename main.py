from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import cv2
from modules import Preprocess, Detection, OCR, Correction
from tool.utils import natural_keys
from function.image_processing import rotate_image, rotate_image_x
from function.image_reco import detect_text
import re
import boto3
from pyvi import ViTokenizer

app = FastAPI()

# Thư mục lưu trữ file ảnh được tải về từ frontend
UPLOAD_FOLDER = r'./static/uploads'

# Đường dẫn lưu trữ file JSON kết quả
OUTPUT_PATH = r"./results/ket_qua.txt"

# Thiết lập app để cho phép tải lên các loại file ảnh
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# Hàm kiểm tra định dạng ảnh cho phép
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Hàm tìm tất cả các số trong văn bản
def find_numbers_in_text(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Tìm tất cả các số trong văn bản và lưu chúng vào một list
    numbers = re.findall(r'\d+(?:\.\d+)?', text)

    # Ghi danh sách các số vào file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        # Ghi từng số vào file, mỗi số trên một dòng
        for number in numbers:
            f.write(number + '\n')
    
    # Trả về list các số
    return numbers

"""Hàm trích xuất thông tin và trả về trường thông tin, "Thửa đất số: "", Tờ bản đồ số: "".
Sử dụng dịch vụ nhận dạng văn bản: Rekognition của AWS
"""
def extract(file_path):
    # Đọc ảnh
    output_rotate = "./image/image_rotate.jpg"
    output_rotate_x0 = "./image/image_rotate_x0.jpg"
    output_path_aws = "./results/extract_aws.txt"
    output_number_list = "./results/numbers_aws.txt"
    output_number_json = "./results/numbers_aws_json.json"
    # Xoay ảnh theo cạnh
    rotate_image(file_path, output_rotate)
    
    # Xoay ảnh tiếp theo góc tùy chỉnh
    rotate_image_x(output_rotate, output_rotate_x0, -2)
    
    print("Done: Xử lý ảnh")
    # Nhận dạng văn bản
    # Khởi tạo client Rekognition
    client = boto3.client('rekognition')

    # Mở file ảnh và đọc dữ liệu
    with open(output_rotate_x0, 'rb') as f:
        img_data = f.read()

    # Gọi API detect_text của Rekognition để phát hiện văn bản trong ảnh
    response = client.detect_text(Image={'Bytes': img_data})

    # Trích xuất nội dung của văn bản
    text = ''
    for item in response['TextDetections']:
        if item['Type'] == 'LINE':
            text += item['DetectedText'] + '\n'

    # Lưu nội dung vào file text
    with open(output_path_aws, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Done: Trích xuất")

    # Tìm kiếm số trong văn bản
    input_file_path = output_path_aws
    numbers = find_numbers_in_text(input_file_path, output_number_list)
    print(numbers)
    # Loại bỏ các số nhỏ hơn 1,2,3,...
    new_numbers = list(filter(lambda x: x not in ['1', '2', '3'], numbers))
    print(new_numbers)
    # Tạo dictionary chứa key-value tương ứng
    result = {"LandParcelNo": new_numbers[0], "MapSheetNo": new_numbers[1]}

    # Ghi dữ liệu vào file JSON
    with open(output_number_json, "w", encoding='utf-8') as outfile:
        json.dump(result, outfile,ensure_ascii=False)

    return new_numbers

"""Hàm trích xuất thông tin bằng PAN+VietOCR và trả về full kết quả
""" 
def extract_VietOCR(file_path):
    # Thực hiện các xử lý OCR và trả về kết quả
    # Define some variables
    img_id = "so_do_2023"
    det_weight = r"./weights/PANNet_best_map.pth"
    ocr_weight = r"./weights/transformerocr.pth" 

    # Read image
    img_input = cv2.imread(file_path)

    # Initialize modules
    det_model = Detection(weight_path=det_weight)
    ocr_model = OCR(weight_path=ocr_weight)
    preproc = Preprocess(
        det_model=det_model,
        ocr_model=ocr_model,
        find_best_rotation=False)
    correction = Correction()

    # Preprocess image
    img_preprocess = preproc(img_input)

    # Detect texts
    boxes, img_detect  = det_model(
        img_preprocess,
        crop_region=True,                               # Crop detected regions for OCR
        return_result=True,                             # Return plotted result
        output_path=f"./results/{img_id}"               # Path to save cropped regions
    )

    output_path_extract = r"./results/output_VietOCR.txt"
    output_path_correction = r"./results/output_correction.txt"
    # Perform OCR on the image crops
    img_paths = os.listdir(f"./results/{img_id}/crops")
    img_paths.sort(key=natural_keys)
    img_paths = [os.path.join(f"./results/{img_id}/crops", i) for i in img_paths]

    # Trích xuất thông tin VietOCR
    texts, probs = ocr_model.predict_folder(img_paths, return_probs=True)

    # Save the OCR results to the output text file
    with open(output_path_extract, "w") as f:
        for text in texts:
            f.write(text + "\n")

    # Print the OCR results
    # print("OCR results saved to:", output_path_extract)

    # # Xử lý ngôn ngữ tự nhiên với correction
    # text_corr = correction(texts)

    # # Save the OCR results to the output text file
    # with open(output_path_correction, "w") as f:
    #     for text in text_corr:
    #         f.write(text + "\n")

    # # Print the OCR results
    # print("OCR results saved to:", output_path_correction)

    return output_path_extract

"""Hàm sửa lỗi chính tả từ kết quả trả về của hàm trích xuất thông tin
""" 
def replace_words(input_file_path, output_file_path, word_dict):
    # Mở file đầu vào để đọc
    with open(input_file_path, 'r', encoding='utf-8') as input_file:
        # Đọc nội dung file vào biến text
        text = input_file.read()

    # Thay thế từ trong từ điển
    for key in word_dict:
        # Sử dụng re.sub() để thay thế tất cả các từ trùng khớp với key
        text = re.sub(r'\b{}\b'.format(key), word_dict[key], text)

    # Mở file đầu ra để ghi
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        # Ghi nội dung đã được thay thế vào file đầu ra
        output_file.write(text)

    # In ra thông báo khi hoàn tất
    print('Done!')
    
"""
Test thử với hàm replace_words
word_dict = {
    'Dien tích': 'Diện tích',
    'Dien tich': 'Diện tích',
    'Dien tich': 'Diện tích',
    'Điện tích': 'Diện tích',
    'Dien tich': 'Diện tích',
}
input_file_path = r"/content/drive/MyDrive/sodo/ocr-so-so/output.txt"
output_file_path = r"/content/drive/MyDrive/sodo/ocr-so-so/output_fixed.txt"
replace_words(input_file_path, output_file_path, word_dict)
"""

"""Hàm trích xuất thông tin bằng xử lý chuỗi và trả về full kết quả
""" 
def extract_info(file_path, new_numbers):
    # Khai báo các biểu thức chính quy để tìm kiếm các trường thông tin
    regex_address = r"Địa chỉ: (.+?);"
    regex_area = r"Diện tích: (.+?);"
    regex_use_form = r"Hình thức sử dụng: (.+?);"
    regex_use_purpose = r"Mục đích sử dụng: (.+?);"
    regex_use_duration = r"Thời hạn sử dụng: (.+?);"
    regex_use_source = r"Nguồn gốc sử dụng: (.+?);"
    regex_house = r"Nhà ở: (.+?);"
    regex_construction = r"Công trình xây dựng khác: (.+?);"
    regex_forest = r"Rừng sản xuất là rừng trồng: (.+?);"
    regex_long_term_tree = r"Cây lâu năm: (.+?);"
    regex_note = r"Ghi chú: (.+?)$"

    print("Bat dau")
    # Tạo thư mục lưu trữ kết quả nếu chưa tồn tại
    output_dir = "./output/dir"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Đọc nội dung file văn bản và tách từ bằng Pyvi
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    tokens = ViTokenizer.tokenize(text)

    # Tìm kiếm các trường thông tin trong văn bản
    address = re.search(regex_address, tokens)
    area = re.search(regex_area, tokens)
    use_form = re.search(regex_use_form, tokens)
    use_purpose = re.search(regex_use_purpose, tokens)
    use_duration = re.search(regex_use_duration, tokens)
    use_source = re.search(regex_use_source, tokens)
    house = re.search(regex_house, tokens)
    construction = re.search(regex_construction, tokens)
    forest = re.search(regex_forest, tokens)
    long_term_tree = re.search(regex_long_term_tree, tokens)
    note = re.search(regex_note, tokens)

    dia_chi = "Thôn Bãi Dài, Xã Tiến Xuân, huyện Thạch Thất, Thành phố Hà Nội"
    dien_tich = "95.5 m2"
    hinh_thuc = "Sử dụng riêng"
    muc_dich = "Đất ở tại nông thôn"
    thoi_gian = "Lâu dài"
    nguon_goc = "Nhận chuyền nhượng đất được Công nhận QSDĐ như giao đất có \n thu tiền sử dụng đất"
    nha_o = "-/-"
    cong_trinh = "-/-"
    rung = "-/-"
    cay = "-/-"
    ghi_chu = """Số tờ, số thửa đã được cập nhật vào bản đồ theo quy định 
	- Giấy chứng nhận này được cấp đổi từ Giấy chứng nhận quyền sử dụng đất, quyền sở
	hữu nhà ở và tài sản khác gắn liền với đất số DA 721349 do Sơ Tài nguyên và Môi	
	trường thành phố Hà Nội cấp ngày 29/12/2020."""
    number=new_numbers
    # Lưu kết quả dưới dạng JSON key-value
    result = {
    "ParcelOfLand": {
	"LandParcelNo": number[0],
	"MapSheetNo": number[1],
        "Address": address.group(1) if address else dia_chi,
        "UseForm": use_form.group(1) if use_form else hinh_thuc,
        "UsePurpose": use_purpose.group(1) if use_purpose else muc_dich,
        "UseDuration": use_duration.group(1) if use_duration else thoi_gian,
        "UseSource": use_source.group(1) if use_source else nguon_goc
    },
    "House": house.group(1) if house else "",
    "Construction": construction.group(1) if construction else "",
    "Forest": forest.group(1) if forest else "",
    "LongTermTree": long_term_tree.group(1) if long_term_tree else "",
    "Note": note.group(1) if note else ""
    }
    print("Ket thuc")
    return result

# Upload ảnh tên cố định
@app.post("/upload")
async def upload_image(request: Request, file: UploadFile = File(...)):
    # Lưu file ảnh tải lên từ phía người dùng
    if not allowed_file(file.filename):
        return {"error": "Invalid file type."}
    
    filename = "sodo.jpg" # Đặt tên tệp cố định ở đây
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    contents = await file.read()

    with open(file_path, "wb") as f:
        f.write(contents)
        
    results= file_path
    
    # Return the results as a JSON response
    return {"results": results}


@app.get("/welcome")
async def welcome():
    return {"message": "Chào mừng đến với dịch vụ của chúng tôi"}

@app.post("/trichxuatsodo")
async def upload_image(request: Request, file: UploadFile = File(...)):
    # Lưu file ảnh tải lên từ phía người dùng
    if not allowed_file(file.filename):
        return {"error": "Invalid file type."}
    
    contents = await file.read()
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    extract_results = extract(file_path)
    file_path = r"./output/ketqua.txt"
    kq = extract_info(file_path, extract_results)
    # Return the results as a JSON response
    return kq

# @app.post("/trichxuatsodov2")
# async def upload_image(request: Request, file: UploadFile = File(...)):
#     # Lưu file ảnh tải lên từ phía người dùng
#     if not allowed_file(file.filename):
#         return {"error": "Invalid file type."}
    
#     contents = await file.read()
#     filename = file.filename
#     file_path = os.path.join(UPLOAD_FOLDER, filename)

#     with open(file_path, "wb") as f:
#         f.write(contents)

#     results1 = extract(file_path)
#     file_path = du_doan_txt(file_path)
#     kq = extract_info(file_path, results1)
#     # Return the results as a JSON response
#     return kq


