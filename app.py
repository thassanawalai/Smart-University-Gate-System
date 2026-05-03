import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import os
import threading
import shutil
import detect
import my_ocr
import database_manager


class LicensePlateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ระบบตรวจจับป้ายทะเบียน (EasyOCR + Roboflow)")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")

        # ตัวแปรเก็บ path รูป
        self.current_image_path = None

        # --- ส่วนหัวโปรแกรม ---
        header = tk.Frame(root, bg="#3498db", height=60)
        header.pack(fill="x")
        lbl_title = tk.Label(header, text="License Plate Recognition System",
                             font=("Arial", 20, "bold"), bg="#3498db", fg="white")
        lbl_title.pack(pady=10)

        # --- พื้นที่หลักแบ่งซ้ายขวา ---
        main_frame = tk.Frame(root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # === ฝั่งซ้าย: โหมดการทำงาน (Tabs) ===
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(side="left", fill="both", expand=True, padx=5)

        # -- Tab 1: โหมดรูปภาพ --
        tab_image = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab_image, text="📂 โหมดอัปโหลดรูปภาพ")

        self.lbl_image = tk.Label(tab_image, text="กรุณาเลือกรูปภาพ", bg="#eeeeee")
        self.lbl_image.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(tab_image, bg="white")
        btn_frame.pack(fill="x", pady=5)

        btn_select = tk.Button(btn_frame, text="📂 เลือกรูปภาพ", command=self.select_image,
                               bg="#2ecc71", fg="white", font=("Arial", 12), width=15)
        btn_select.pack(side="left", padx=10)

        btn_process = tk.Button(btn_frame, text="🔍 ตรวจสอบทะเบียน", command=self.process_image,
                                bg="#e74c3c", fg="white", font=("Arial", 12), width=15)
        btn_process.pack(side="right", padx=10)
        
        # -- Tab 2: โหมดเปิดกล้อง (WebRTC) --
        tab_camera = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab_camera, text="📷 โหมดเปิดกล้อง (WebRTC)")
        
        tk.Label(tab_camera, text="ระบบจะเปิดหน้าต่างกล้องใหม่ขึ้นมาสแกนอัตโนมัติ", 
                 font=("Arial", 12), bg="white").pack(pady=40)
                 
        btn_start_cam = tk.Button(tab_camera, text="🟢 เริ่มสแกนจากกล้อง", command=self.start_camera,
                                bg="#34495e", fg="white", font=("Arial", 14, "bold"))
        btn_start_cam.pack(pady=10)
        
        self.lbl_cam_status = tk.Label(tab_camera, text="สถานะ: รอการทำงาน", fg="gray", bg="white", font=("Arial", 10))
        self.lbl_cam_status.pack(pady=10)

        # === ฝั่งขวา: ตารางผลลัพธ์ ===
        right_frame = tk.Frame(main_frame, bg="white", bd=2, relief="groove", width=350)
        right_frame.pack(side="right", fill="y", padx=5)

        tk.Label(right_frame, text="📊 ผลการตรวจสอบ", font=("Arial", 14, "bold"), bg="white").pack(pady=10)

        # สร้างตาราง (Treeview)
        cols = ("Plate", "Owner", "Status")
        self.tree = ttk.Treeview(right_frame, columns=cols, show="headings", height=15)
        self.tree.heading("Plate", text="ทะเบียน")
        self.tree.heading("Owner", text="เจ้าของ")
        self.tree.heading("Status", text="สถานะ")

        self.tree.column("Plate", width=100)
        self.tree.column("Owner", width=150)
        self.tree.column("Status", width=100)
        self.tree.pack(padx=5, pady=5, fill="both", expand=True)

        # ส่วนแสดงรูปที่ตัดมา (Crop Display)
        self.lbl_crop = tk.Label(right_frame, text="ภาพป้ายทะเบียน", bg="#ddd", height=8)
        self.lbl_crop.pack(fill="x", padx=10, pady=10)

        # ผูก event คลิกที่ตาราง
        self.tree.bind("<<TreeviewSelect>>", self.on_table_click)

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.png;*.jpeg")])
        if file_path:
            self.current_image_path = file_path
            self.show_image(file_path)
            # ล้างตารางเก่า
            for item in self.tree.get_children():
                self.tree.delete(item)

    def show_image(self, path):
        # โหลดรูปมาแสดงใน GUI
        img = Image.open(path)
        img.thumbnail((500, 500))  # ย่อรูปรักษาอัตราส่วน
        self.photo = ImageTk.PhotoImage(img)
        self.lbl_image.config(image=self.photo, text="")

    def process_image(self):
        if not self.current_image_path:
            messagebox.showwarning("เตือน", "กรุณาเลือกรูปภาพก่อนครับ")
            return

        # เปลี่ยนเมาส์เป็นรูปโหลด เพื่อบอกว่าเริ่มประมวลผลแล้ว
        self.root.config(cursor="wait")
        
        # เริ่ม Thread ใหม่เพื่อแยกการทำงานที่ใช้เวลานานออกไป ไม่ให้ UI ค้าง
        target_path = self.current_image_path
        thread = threading.Thread(target=self.run_process_task, args=(target_path,))
        thread.start()

    def run_process_task(self, image_path):
        """ ฟังก์ชันนี้จะทำงานอยู่เบื้องหลัง (Background Thread) """
        # ใช้ Workflow ตัวใหม่แทนการเรียก detect_and_crop
        result = detect.detect_new_workflow_image(image_path)
        
        if not result:
            self.root.after(0, self.finish_process_task, False, [], "เกิดข้อผิดพลาดในการเชื่อมต่อ Workflow")
            return
            
        plates = detect.extract_plate_texts(result)
        if not plates:
            self.root.after(0, self.finish_process_task, False, [], "ไม่พบข้อความทะเบียนในรูปภาพ")
            return

        # เตรียมข้อมูลส่งกลับไป Main Thread
        final_data = []
        for plate_text in plates:
            # เช็ค Database
            status, owner = database_manager.check_license_plate(plate_text)
            final_data.append((plate_text, owner, status, image_path))
            
        # ส่งผลลัพธ์กลับไปให้ Main Thread เพื่ออัปเดต UI
        self.root.after(0, self.finish_process_task, True, final_data, "")

    def finish_process_task(self, success, result_data, error_msg):
        """ ฟังก์ชันนี้จะถูกเรียกกลับมาทำงานใน Main Thread (อัปเดต UI ได้อย่างปลอดภัย) """
        self.root.config(cursor="")
        
        if not success:
            messagebox.showerror("Error", error_msg)
            return
            
        # แสดงผลลงตาราง
        for data in result_data:
            plate_text, owner, status, file_path = data
            # ใส่ข้อมูลลงตาราง (เก็บ file_path ไว้ใน tag เพื่อดึงมาโชว์รูปทีหลัง)
            self.tree.insert("", "end", values=(plate_text, owner, status), tags=(file_path,))

        messagebox.showinfo("เสร็จสิ้น", f"ตรวจสอบเสร็จสิ้น พบ {len(result_data)} ป้าย")

    def on_table_click(self, event):
        # เมื่อคลิกที่บรรทัดไหน ให้เอารูปป้ายทะเบียนนั้นมาโชว์ข้างล่าง
        selected_item = self.tree.selection()
        if not selected_item: return

        item = self.tree.item(selected_item)
        file_path = item['tags'][0]  # ดึง path รูปที่เราแอบแปะไว้

        if os.path.exists(file_path):
            img = Image.open(file_path)
            img.thumbnail((300, 200))  # ย่อรูปแบบรักษาอัตราส่วนแทนการบีบภาพ
            self.crop_photo = ImageTk.PhotoImage(img)
            self.lbl_crop.config(image=self.crop_photo, text="")
            
    def start_camera(self):
        self.lbl_cam_status.config(text="สถานะ: กำลังสแกนจากกล้อง... (กรุณาดูหน้าต่างใหม่ที่เด้งขึ้นมา)", fg="green")
        thread = threading.Thread(target=self.run_camera_task)
        thread.daemon = True
        thread.start()
        
    def run_camera_task(self):
        def on_plate(data):
            # เมื่อกล้องสแกนเจอข้อมูล จะดึงข้อความทะเบียนมาเช็คและใส่ตาราง
            plates = detect.extract_plate_texts(data)
            for plate_text in plates:
                if plate_text:
                    self.root.after(0, self.add_plate_to_table, plate_text)
                    
        detect.start_webrtc_camera(on_plate)
        self.root.after(0, lambda: self.lbl_cam_status.config(text="สถานะ: หยุดการทำงาน", fg="gray"))

    def add_plate_to_table(self, plate_text):
        # เช็คก่อนว่าทะเบียนนี้โชว์ในตารางแล้วหรือยัง (ป้องกันแสดงซ้ำรัวๆ)
        for child in self.tree.get_children():
            if self.tree.item(child)["values"][0] == plate_text: return
        status, owner = database_manager.check_license_plate(plate_text)
        self.tree.insert("", "end", values=(plate_text, owner, status), tags=("",))


if __name__ == "__main__":
    root = tk.Tk()
    app = LicensePlateApp(root)
    root.mainloop()