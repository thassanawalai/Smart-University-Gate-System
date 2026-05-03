import streamlit as st
from PIL import Image
import os
import shutil
import detect
import my_ocr
import database_manager

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบตรวจจับป้ายทะเบียน", layout="wide")

st.title("🚗 ระบบตรวจจับป้ายทะเบียน (Web App)")
st.write("อัปโหลดรูปภาพรถเพื่อตรวจสอบป้ายทะเบียนและเช็คสิทธิ์การเข้า-ออก")

def process_and_display(img_path):
    """ฟังก์ชันกลางสำหรับส่งภาพเข้า Workflow และแสดงผลลัพธ์"""
    with st.spinner("กำลังประมวลผลด้วย AI Workflow..."):
        result = detect.detect_new_workflow_image(img_path)
        
        if not result:
            st.error("⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อ AI Workflow")
            return
            
        plates = detect.extract_plate_texts(result)
        
        if not plates:
            st.warning("⚠️ ไม่พบป้ายทะเบียนในภาพ")
            return
            
        st.subheader("📊 ผลการตรวจสอบ")
        for plate_text in plates:
            status, owner = database_manager.check_license_plate(plate_text)
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(img_path, caption="ภาพที่ใช้ตรวจจับ")
            with col2:
                st.write(f"**ทะเบียน:** {plate_text}")
                st.write(f"**เจ้าของ:** {owner}")
                if status == "Allowed":
                    st.success(f"**สถานะ:** {status} (อนุญาตให้ผ่าน)")
                elif status == "Blacklist":
                    st.error(f"**สถานะ:** {status} (ห้ามเข้า)")
                else:
                    st.warning(f"**สถานะ:** {status} (ผู้มาติดต่อ)")

tab1, tab2 = st.tabs(["📂 โหมดอัปโหลดรูปภาพ", "📷 โหมดถ่ายรูปจากกล้อง"])

with tab1:
    uploaded_file = st.file_uploader("📂 เลือกรูปภาพ", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        st.image(Image.open(uploaded_file), caption="รูปภาพที่เลือก", width=500)
        if st.button("🔍 ตรวจสอบทะเบียน (ภาพ)"):
            temp_path = "temp_upload.jpg"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            process_and_display(temp_path)

with tab2:
    camera_file = st.camera_input("📷 ถ่ายรูปป้ายทะเบียน")
    if camera_file is not None:
        temp_path = "temp_camera.jpg"
        with open(temp_path, "wb") as f:
            f.write(camera_file.getbuffer())
        process_and_display(temp_path)