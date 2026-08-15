import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from supabase import create_client, Client
import datetime
import io

# --- ⚙️ PAGE CONFIG & STYLING ---
st.set_page_config(
    page_title="Fitness Plus & AI Body Analyzer",
    page_icon="⚡",
    layout="centered"
)

# --- 🗝️ INITIALIZE CLIENTS ---
@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key)

@st.cache_resource
def get_supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"ไม่สามารถเชื่อมต่อ Supabase ได้: {e}")
        return None

ai_client = get_gemini_client()
supabase = get_supabase_client()

# --- 🎨 UI HEADER ---
st.title("⚡ FITNESS PLUS & AI BODY ANALYZER")
st.caption("คำนวณ BMI และวิเคราะห์รูปร่างด้วย AI พร้อมบันทึกประวัติการเปลี่ยนแปลง")

# --- 🔘 MAIN MENU SELECTION ---
app_mode = st.radio(
    "เลือกฟังก์ชันที่ต้องการใช้งาน:",
    [
        "📊 คำนวณ BMI & คำแนะนำ",
        "📸 ถ่ายภาพ / อัปโหลดให้ AI วิเคราะห์",
        "🗂️ ประวัติรูปภาพและการเปรียบเทียบ (Before/After)"
    ]
)

st.divider()

# ==========================================
# 1. 📊 คำนวณ BMI & คำแนะนำ
# ==========================================
if app_mode == "📊 คำนวณ BMI & คำแนะนำ":
    st.header("📊 ประเมินดัชนีมวลกาย (BMI)")
    
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("น้ำหนักตัว (กิโลกรัม):", min_value=1.0, max_value=300.0, value=65.0, step=0.5)
    with col2:
        height_cm = st.number_input("ส่วนสูง (เซนติเมตร):", min_value=50.0, max_value=250.0, value=170.0, step=1.0)

    if st.button("🧮 คำนวณ BMI"):
        height_m = height_cm / 100
        bmi = weight / (height_m ** 2)
        
        st.metric(label="ค่า BMI ของคุณ", value=f"{bmi:.2f}")
        
        if bmi < 18.5:
            st.warning("น้ำหนักน้อยกว่าเกณฑ์ (Underweight)")
        elif 18.5 <= bmi < 23.0:
            st.success("น้ำหนักปกติ เหมาะสม (Normal)")
        elif 23.0 <= bmi < 25.0:
            st.info("น้ำหนักเกินเกณฑ์ / ท้วม (Overweight)")
        elif 25.0 <= bmi < 30.0:
            st.warning("อ้วนระดับ 1 (Obese Class 1)")
        else:
            st.error("อ้วนระดับ 2 / อ้วนมาก (Obese Class 2)")

# ==========================================
# 2. 📸 ถ่ายภาพ / อัปโหลดให้ AI วิเคราะห์
# ==========================================
elif app_mode == "📸 ถ่ายภาพ / อัปโหลดให้ AI วิเคราะห์":
    st.header("📸 สแกนรูปร่างและไขมันด้วย AI")
    
    source_choice = st.selectbox("เลือกวิธีส่งรูปภาพ:", ["ถ่ายภาพจากกล้องสด", "อัปโหลดรูปภาพ"])
    
    img_captured = None
    if source_choice == "ถ่ายภาพจากกล้องสด":
        img_captured = st.camera_input("กดถ่ายภาพรูปร่างของคุณ")
    else:
        img_captured = st.file_uploader("เลือกรูปภาพของคุณ (JPG/PNG)", type=['png', 'jpg', 'jpeg'])

    if img_captured is not None:
        image = Image.open(img_captured)
        st.image(image, caption="รูปภาพที่เลือก", use_container_width=True)
        
        col_btn1, col_btn2 = st.columns(2)
        
        # --- 🤖 ให้ AI วิเคราะห์รูปภาพ ---
        with col_btn1:
            if st.button("🤖 ให้ AI วิเคราะห์รูปร่าง"):
                with st.spinner("Gemini กำลังวิเคราะห์องค์ประกอบร่างกาย..."):
                    try:
                        prompt = """
                        วิเคราะห์รูปภาพรูปร่างนี้เพื่อสุขภาพและฟิตเนส:
                        1. ประเมินมวลกล้ามเนื้อ สัดส่วน และเปอร์เซ็นต์ไขมันในร่างกายโดยประมาณ
                        2. ให้คำแนะนำสั้นๆ เกี่ยวกับการออกกำลังกายที่เหมาะสม
                        3. แนะนำโภชนาการหรือสารอาหารที่ควรเน้น
                        **หมายเหตุ: ระบุตอนท้ายว่านี่คือการประเมินเบื้องต้นจาก AI เท่านั้น ไม่ใช่ผลทางการแพทย์**
                        """
                        response = ai_client.models.generate_content(
                            model="gemini-1.5-flash",
                            contents=[image, prompt]
                        )
                        st.markdown("### 📝 ผลการวิเคราะห์จาก AI")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์: {e}")
                        
        # --- 💾 บันทึกรูปภาพเข้า Supabase Storage ---
        with col_btn2:
            if st.button("💾 บันทึกรูปภาพลงประวัติ"):
                if supabase is None:
                    st.error("ไม่สามารถบันทึกได้ เนื่องจากไม่ได้เชื่อมต่อ Supabase")
                else:
                    with st.spinner("กำลังอัปโหลดรูปภาพลง Supabase..."):
                        try:
                            img_captured.seek(0)
                            img_bytes = img_captured.read()
                            
                            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"progress_{now_str}.jpg"
                            
                            res = supabase.storage.from_("body-progress").upload(
                                path=filename,
                                file=img_bytes,
                                file_options={"content-type": "image/jpeg"}
                            )
                            st.success(f"บันทึกรูปภาพเรียบร้อยในชื่อ: `{filename}`")
                        except Exception as e:
                            st.error(f"การอัปโหลดล้มเหลว: {e} (โปรดตรวจสอบว่าสร้าง Bucket 'body-progress' แล้วหรือยัง)")

# ==========================================
# 3. 🗂️ ประวัติรูปภาพและการเปรียบเทียบ
# ==========================================
elif app_mode == "🗂️ ประวัติรูปภาพและการเปรียบเทียบ (Before/After)":
    st.header("🗂️ ประวัติและเปรียบเทียบการเปลี่ยนแปลง (Before / After)")
    
    if supabase is None:
        st.warning("กรุณาตั้งค่า Supabase URL และ Key ใน Secrets ก่อนเปิดใช้งานฟังก์ชันนี้")
    else:
        try:
            file_list = supabase.storage.from_("body-progress").list()
            valid_files = [f['name'] for f in file_list if f['name'].endswith(('.jpg', '.jpeg', '.png'))]
            
            if len(valid_files) == 0:
                st.info("ยังไม่มีรูปภาพที่ถูกบันทึกในระบบ")
            elif len(valid_files) < 2:
                st.warning(f"พบบันทึกเพียง {len(valid_files)} รูป (ต้องมีอย่างน้อย 2 รูปเพื่อทำการเปรียบเทียบ Before/After)")
                url = supabase.storage.from_("body-progress").get_public_url(valid_files[0])
                st.image(url, caption=valid_files[0], use_container_width=True)
            else:
                col_b, col_a = st.columns(2)
                
                with col_b:
                    st.subheader("📷 ก่อน (Before)")
                    before_file = st.selectbox("เลือกระบุรูปภาพแรก (Before):", valid_files, index=0)
                    url_before = supabase.storage.from_("body-progress").get_public_url(before_file)
                    st.image(url_before, use_container_width=True)
                    
                with col_a:
                    st.subheader("📸 หลัง (After)")
                    after_file = st.selectbox("เลือกรูปภาพปัจจุบัน (After):", valid_files, index=len(valid_files)-1)
                    url_after = supabase.storage.from_("body-progress").get_public_url(after_file)
                    st.image(url_after, use_container_width=True)
                
                st.divider()
                
                # --- 🤖 เปรียบเทียบสองรูปด้วย Gemini ---
                if st.button("🤖 ให้ AI วิเคราะห์เปรียบเทียบการเปลี่ยนแปลง"):
                    with st.spinner("Gemini กำลังประมวลผลเปรียบเทียบรูปภาพทั้งสอง..."):
                        try:
                            img_b_bytes = supabase.storage.from_("body-progress").download(before_file)
                            img_a_bytes = supabase.storage.from_("body-progress").download(after_file)
                            
                            img_before = Image.open(io.BytesIO(img_b_bytes))
                            img_after = Image.open(io.BytesIO(img_a_bytes))
                            
                            prompt = """
                            โปรดเปรียบเทียบรูปภาพรูปร่างก่อน (Before) และหลัง (After) ของผู้ใช้:
                            1. สังเกตการเปลี่ยนแปลงของสัดส่วน ปริมาณไขมัน และมวลกล้ามเนื้อ
                            2. สรุปความก้าวหน้าที่เกิดขึ้นอย่างเป็นรูปธรรม
                            3. ให้คำแนะนำขั้นตอนต่อไปในการออกกำลังกายและควบคุมอาหาร
                            **คำเตือน: นี่คือการประเมินจาก AI ไม่ใช่ผลตรวจทางการแพทย์**
                            """
                            
                            response = ai_client.models.generate_content(
                                model="gemini-1.5-flash",
                                contents=[img_before, img_after, prompt]
                            )
                            st.markdown("### 📊 ผลการเปรียบเทียบโดย AI")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลหรือเปรียบเทียบรูปภาพ: {e}")
                            
        except Exception as e:
            st.error(f"ไม่สามารถเชื่อมต่อดึงข้อมูลภาพได้: {e}")
