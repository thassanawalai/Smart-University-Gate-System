import easyocr
import cv2
import os  # import ตัวนี้เพิ่ม เพื่อใช้จัดการไฟล์และโฟลเดอร์

# --- ตั้งค่า ---
FOLDER_PATH = 'cropped_plates'  # ชื่อโฟลเดอร์ที่เพื่อนส่งรูปมา
ALLOWED_LIST = 'กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ0123456789'


def main():
    # 1. เช็คว่ามีโฟลเดอร์นี้จริงไหม
    if not os.path.exists(FOLDER_PATH):
        print(f"ไม่พบโฟลเดอร์ {FOLDER_PATH} ! กรุณาสร้างโฟลเดอร์ก่อน")
        os.makedirs(FOLDER_PATH)  # สร้างให้เลยกันเหนียว
        return

    # 2. โหลดโมเดล (ทำครั้งเดียวใช้นานๆ)
    print("Loading Model...")
    reader = easyocr.Reader(['th', 'en'], gpu=False)

    # 3. วนลูปอ่านไฟล์ทั้งหมดในโฟลเดอร์
    print(f"Reading images from {FOLDER_PATH}...")

    # ลิสต์รายชื่อไฟล์ทั้งหมดในโฟลเดอร์
    all_files = os.listdir(FOLDER_PATH)

    found_image = False
    for filename in all_files:
        # เช็คว่าเป็นไฟล์รูปภาพหรือไม่ (jpg, png, jpeg)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            found_image = True
            full_path = os.path.join(FOLDER_PATH, filename)

            # --- เริ่มกระบวนการ OCR ต่อ 1 รูป ---
            img = cv2.imread(full_path)
            if img is None:
                continue

            # อ่านค่า (ใช้ allowlist เพื่อความแม่นยำ)
            results = reader.readtext(img, detail=0, allowlist=ALLOWED_LIST)

            # แปลง List เป็น String เดียว
            text_result = " ".join(results)

            print(f"📄 ไฟล์: {filename} -> 🚗 ทะเบียน: {text_result}")

    if not found_image:
        print("--- ว่างเปล่า ---")
        print(f"ยังไม่มีรูปในโฟลเดอร์ {FOLDER_PATH} ให้เพื่อนเอาไฟล์มาใส่ก่อนนะ")


if __name__ == "__main__":
    main()