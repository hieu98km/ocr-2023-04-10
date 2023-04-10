import os
import re
import json
from pyvi import ViTokenizer

def extract_info(file_path):
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

    # Lưu kết quả dưới dạng JSON key-value
    result = {
        "Địa chỉ": address.group(1) if address else "",
        "Diện tích": area.group(1) if area else "",
        "Hình thức sử dụng": use_form.group(1) if use_form else "",
        "Mục đích sử dụng": use_purpose.group(1) if use_purpose else "",
        "Thời hạn sử dụng": use_duration.group(1) if use_duration else "",
        "Nguồn gốc sử dụng": use_source.group(1) if use_source else "",
        "Nhà ở": house.group(1) if house else "",
        "Công trình xây dựng khác": construction.group(1) if construction else "",
        "Rừng sản xuất là rừng trồng": forest.group(1) if forest else "",
        "Cây lâu năm": long_term_tree.group(1) if long_term_tree else "",
        "Ghi chú": note.group(1) if note else ""
    }
    print("Ket thuc")
    return result

file_path = r"./results/output.txt"
extract = extract_info(file_path)
print(extract)