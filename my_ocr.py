import easyocr
import cv2
import os

# --- ตั้งค่า ---
FOLDER_PATH = 'cropped_plates'
ALLOWED_LIST = 'กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ0123456789'

# โหลดโมเดลไว้เป็น Global Variable เพื่อไม่ให้ต้องโหลดใหม่ทุกครั้ง
reader = None

def read_plates_in_folder():
    """
    อ่านรูปทั้งหมดในโฟลเดอร์ แล้วส่งคืนค่าเป็น List ของข้อมูล
    Ex: [{'text': '1กข1234', 'file': 'plate_0.jpg'}, ...]
    """
    detected_data = []

    if not os.path.exists(FOLDER_PATH):
        return []

    global reader
    if reader is None:
        print("Loading OCR Model...")
        reader = easyocr.Reader(['th', 'en'], gpu=False)

    print(f"Reading images from {FOLDER_PATH}...")
    all_files = os.listdir(FOLDER_PATH)
    all_files.sort() # เรียงลำดับไฟล์

    for filename in all_files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            full_path = os.path.join(FOLDER_PATH, filename)

            img = cv2.imread(full_path)
            if img is None: continue

            # --- ส่วน OCR เดิมของคุณ ---
            results = reader.readtext(img, detail=0, allowlist=ALLOWED_LIST)
            text_result = "".join(results).replace(" ", "")

            if text_result:
                print(f"อ่านได้: {text_result} (จากไฟล์ {filename})")
                # เก็บข้อมูลทั้งข้อความและชื่อไฟล์ เพื่อส่งให้ UI
                detected_data.append({
                    'text': text_result,
                    'file': full_path
                })

    return detected_data