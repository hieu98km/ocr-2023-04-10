import boto3

# Nhận dạng văn bản
def detect_text(image_path, output_path, bucket='bucket-name'):
    # Khởi tạo client Rekognition
    client = boto3.client('rekognition')

    # Mở file ảnh và đọc dữ liệu
    with open(image_path, 'rb') as f:
        image_data = f.read()

    # Gọi API detect_text của Rekognition để phát hiện văn bản trong ảnh
    response = client.detect_text(Image={'Bytes': image_data})

    # Trích xuất nội dung của văn bản
    text = ''
    for item in response['TextDetections']:
        if item['Type'] == 'LINE':
            text += item['DetectedText'] + '\n'

    # Lưu nội dung vào file text
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    return print(f"Đã lưu nội dung văn bản được phát hiện vào tệp tin: {output_path}")
    
