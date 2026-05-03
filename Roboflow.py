# 1. Import the library
import os
from inference_sdk import InferenceHTTPClient

# 2. Connect to your workflow
client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="DkIoL2AV2ihaoXDF6XT2"
)

# กำหนด path ของภาพที่ต้องการทดสอบ (เปลี่ยน YOUR_IMAGE.jpg เป็นชื่อไฟล์ของคุณ)
image_path = "YOUR_IMAGE.jpg" 

if os.path.exists(image_path):
    # 3. Run your workflow on an image
    result = client.run_workflow(
        workspace_name="thassanawalai",
        workflow_id="license-plate-text-reader-1777740758005",
        images={
            "image": image_path
        },
        use_cache=True # Speeds up repeated requests
    )
    # 4. Get your results
    print(result)
else:
    print(f"Error: ไม่พบไฟล์ภาพ '{image_path}' โปรดเตรียมไฟล์ภาพไว้ก่อนรันโปรแกรมครับ")
