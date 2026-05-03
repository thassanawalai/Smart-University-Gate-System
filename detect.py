import cv2
import os
from roboflow import Roboflow

# --- ตั้งค่า API (ใช้ Key ของคุณเอง) ---
API_KEY = "DkIoL2AV2ihaoXDF6XT2"
PROJECT_ID = "ilovemycar-dojig"
VERSION = 2


def detect_and_crop(image_path, output_folder='cropped_plates'):
    # สร้างโฟลเดอร์ถ้ายังไม่มี
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. เชื่อมต่อ Roboflow
    try:
        rf = Roboflow(api_key=API_KEY)
        project = rf.workspace().project(PROJECT_ID)
        model = project.version(VERSION).model
    except Exception as e:
        print(f"Error connecting to Roboflow: {e}")
        return False

    # 2. อ่านภาพ
    img = cv2.imread(image_path)
    if img is None:
        return False

    # 3. ส่งให้ AI ตรวจจับ
    print("🤖 กำลังสแกนหาป้ายทะเบียน...")
    try:
        predictions = model.predict(image_path, confidence=40, overlap=30).json()['predictions']
    except:
        return False

    if not predictions:
        print("⚠️ ไม่พบป้ายทะเบียนในภาพ")
        return False

    # 4. ตัดภาพ (Crop) ตามตำแหน่งที่เจอ
    count = 0
    img_h, img_w = img.shape[:2]
    for pred in predictions:
        x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']

        # แปลงพิกัด
        x1 = max(0, int(x - w / 2))
        y1 = max(0, int(y - h / 2))
        x2 = min(img_w, int(x + w / 2))
        y2 = min(img_h, int(y + h / 2))

        # ตัดภาพ
        crop_img = img[y1:y2, x1:x2]

        # บันทึกไฟล์ (ตั้งชื่อเป็น plate_0.jpg, plate_1.jpg ...)
        save_path = os.path.join(output_folder, f"plate_{count}.jpg")
        cv2.imwrite(save_path, crop_img)
        count += 1

    return True