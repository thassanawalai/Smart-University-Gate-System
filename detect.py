import cv2
import os
from roboflow import Roboflow
from inference_sdk import InferenceHTTPClient
from inference_sdk.webrtc import WebcamSource, StreamConfig, VideoMetadata

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

# ====================================================
# NEW WORKFLOW (Inference SDK) สำหรับโหมดใหม่
# ====================================================

def detect_new_workflow_image(image_path):
    """โหมดที่ 1: ตรวจจับจากรูปภาพ (อ้างอิงจาก Roboflow.py)"""
    client = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=API_KEY)
    try:
        result = client.run_workflow(
            workspace_name="thassanawalai",
            workflow_id="license-plate-text-reader-1777740758005",
            images={"image": image_path},
            use_cache=True
        )
        return result
    except Exception as e:
        print(f"Workflow Image Error: {e}")
        return None

def start_webrtc_camera(on_plate_callback):
    """โหมดที่ 2: เปิดกล้องสด (อ้างอิงจาก Roboflow2.py)"""
    client = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=API_KEY)
    source = WebcamSource(resolution=(1280, 720))
    config = StreamConfig(
        stream_output=["annotated_image"],
        data_output=["plate_text", "plate_predictions"],
        processing_timeout=3600,
        requested_plan="webrtc-gpu-medium",
        requested_region="us"
    )
    
    session = client.webrtc.stream(
        source=source, workflow="license-plate-text-reader-1777740758005",
        workspace="thassanawalai", image_input="image", config=config
    )

    @session.on_frame
    def show_frame(frame, metadata):
        cv2.imshow("Live Plate Scanner (Press 'q' to stop)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            session.close()

    @session.on_data
    def on_data(data: dict, metadata: VideoMetadata):
        # เมื่อพบข้อมูลให้ส่งเข้า Callback ทันที
        on_plate_callback(data)

    print("Starting WebRTC Camera...")
    session.run()
    cv2.destroyAllWindows()

def extract_plate_texts(result):
    """ดึงข้อความทะเบียนจากผลลัพธ์ของ Workflow อย่างปลอดภัย"""
    plates = []
    if not result: return plates
    
    data = result[0] if isinstance(result, list) and result else (result if not isinstance(result, list) else {})
        
    if "plate_text" in data:
        pt = data["plate_text"]
        if isinstance(pt, str): plates.append(pt)
        elif isinstance(pt, list): plates.extend([str(x) for x in pt])
        
    if not plates and "plate_predictions" in data:
        preds = data["plate_predictions"]
        if isinstance(preds, list):
            for p in preds:
                if isinstance(p, dict):
                    if "class_name" in p: plates.append(p["class_name"])
                    elif "class" in p: plates.append(p["class"])
                    elif "text" in p: plates.append(p["text"])
                    
    # ทำความสะอาดข้อมูล: ตัดช่องว่างและคืนค่าเฉพาะที่ไม่ซ้ำกัน
    return list(set([str(p).replace(" ", "").strip() for p in plates if p]))