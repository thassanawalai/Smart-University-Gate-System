import csv
import os

DB_FILE = 'database.csv'


def check_license_plate(plate_text):
    """
    รับทะเบียนรถ -> คืนค่าสถานะ (Status) และเจ้าของ (Owner)
    """
    # ลบช่องว่างออกให้หมดก่อนเช็ค เพื่อความชัวร์
    clean_plate = plate_text.replace(" ", "").strip()

    if not os.path.exists(DB_FILE):
        return "Unknown", "ไม่พบฐานข้อมูล"

    with open(DB_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # เทียบแบบตัดช่องว่างทิ้งทั้งคู่
            db_plate = row['license_plate'].replace(" ", "").strip()

            # ถ้าเจอทะเบียนที่ตรงกัน
            if db_plate == clean_plate:
                # ส่งคืนค่า status และ owner
                return row.get('status', 'Unknown'), row.get('owner', 'Unknown')

    return "Visitor", "ผู้มาติดต่อ (ไม่พบในระบบ)"