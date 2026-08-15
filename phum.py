import base64
import io
import datetime
import streamlit as st
from google import genai
from PIL import Image

# ----------------------------------------------------
# 1. ใส่ GEMINI API KEY ของจริง (ขึ้นต้นด้วย AIzaSy...) 🔑
# ----------------------------------------------------
GEMINI_API_KEY = "AQ.Ab8RN6K3NJ415Ql2EREFoWqIfy7EicyIzUZtRjiSH9lnu_XBfQ"  # 👈 นำคีย์ AIzaSy... ของคุณมาใส่ตรงนี้ครับ

# ----------------------------------------------------
# 2. ตั้งค่าระบบบันทึกประวัติรูปภาพ (Session State)
# ----------------------------------------------------
if "photo_history" not in st.session_state:
    st.session_state.photo_history = []

# ----------------------------------------------------
# 3. ตั้งค่าหน้าตาของเว็บและ CSS (ธีม Dark & Yellow)
# ----------------------------------------------------
st.set_page_config(
    page_title="ออกกำลังกายนะไอ้นาย - AI BODY TRACKER",
    page_icon="⚡",
    layout="centered"
)

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;500;700;800&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"] {
            font-family: 'Kanit', sans-serif !important;
            color: #FFFFFF !important;
        }
        .stApp {
            background-color: #121212 !important;
        }
        div.stMainBlockContainer {
            background-color: rgba(26, 26, 26, 0.95) !important;
            border-radius: 16px;
            padding: 30px !important;
            border: 1px solid rgba(255, 184, 0, 0.3);
            margin-top: 20px;
        }
        .fitness-title {
            color: #FFB800 !important;
            font-weight: 800;
            font-size: 2.2rem;
            text-transform: uppercase;
            text-align: center;
        }
        .fitness-subtitle {
            color: #CCCCCC !important;
            text-align: center;
            font-size: 1rem;
            margin-bottom: 20px;
        }
        div.stButton > button {
            background: linear-gradient(135deg, #FFB800 0%, #E6A100 100%) !important;
            color: #000000 !important;
            font-weight: 800 !important;
            border-radius: 8px !important;
            width: 100%;
        }
        .rec-box {
            background-color: #1E1E1E;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 18px;
            margin-top: 15px;
        }
        .rec-title {
            color: #FFB800;
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 10px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="fitness-title">⚡ FITNESS PLUS & AI BODY ANALYZER</div>', unsafe_allow_html=True)
st.markdown('<div class="fitness-subtitle">คำนวณ BMI และวิเคราะห์รูปร่างด้วย AI พร้อมคำแนะนำครบถ้วน</div>', unsafe_allow_html=True)
st.write("---")

# ----------------------------------------------------
# 4. เมนูเลือกโหมดการทำงาน
# ----------------------------------------------------
mode = st.radio(
    "เลือกฟังก์ชันที่ต้องการใช้งาน:",
    ["📊 คำนวณ BMI & คำแนะนำ", "📸 ถ่ายภาพ / อัปโหลดให้ AI วิเคราะห์", "🖼️ ประวัติรูปภาพที่บันทึกไว้"],
    horizontal=True
)

# ----------------------------------------------------
# โหมดที่ 1: คำนวณ BMI & คำแนะนำอาหาร/ออกกำลังกาย
# ----------------------------------------------------
if mode == "📊 คำนวณ BMI & คำแนะนำ":
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("เพศ (GENDER)", ["ชาย", "หญิง"])
            age = st.number_input("อายุ (AGE / ปี)", min_value=1, max_value=120, value=25)
        with col2:
            weight = st.number_input(
                "น้ำหนัก (WEIGHT / กก.)",
                min_value=1.00,
                max_value=300.00,
                value=65.00,
                step=0.10,
                format="%.2f"
            )
            height = st.number_input(
                "ส่วนสูง (HEIGHT / ซม.)",
                min_value=50.00,
                max_value=250.00,
                value=170.00,
                step=0.10,
                format="%.2f"
            )

        activity = st.selectbox(
            "ระดับกิจกรรมประจำวัน (ACTIVITY LEVEL)",
            [
                "นั่งทำงานอยู่กับที่ (ไม่ออกกำลังกายเลย)",
                "ออกกำลังกายเล็กน้อย (1-3 วัน/สัปดาห์)",
                "ออกกำลังกายปานกลาง (3-5 วัน/สัปดาห์)",
                "ออกกำลังกายหนัก (6-7 วัน/สัปดาห์)",
            ],
        )

    if st.button("CALCULATE RESULT ➔"):
        height_m = height / 100
        bmi = weight / (height_m**2)

        st.markdown("---")
        st.subheader("📊 RESULTS & EVALUATION")

        if bmi < 18.5:
            category = "underweight"
            status_text = "❌ UNDERWEIGHT (ผอมกว่าเกณฑ์มาตรฐาน)"
            status_color = "#FF4B4B"
        elif 18.5 <= bmi <= 22.9:
            category = "normal"
            status_text = "✅ NORMAL WEIGHT (สมส่วนตามเกณฑ์มาตรฐาน)"
            status_color = "#FFB800"
        elif 23.0 <= bmi <= 24.9:
            category = "overweight"
            status_text = "⚠️ OVERWEIGHT (เริ่มมีน้ำหนักเกิน)"
            status_color = "#FF9F43"
        else:
            category = "obese"
            status_text = "🚨 OBESE (สภาวะอ้วน)"
            status_color = "#FF5252"

        st.markdown(
            f"""
            <div style="background-color: #222; border-left: 6px solid {status_color}; padding: 20px; border-radius: 8px;">
                <span style="color: #DDDDDD; font-size: 0.9rem;">ค่า BMI ของคุณคือ</span>
                <h1 style="color: #FFB800; margin: 0; font-size: 3rem; font-weight: 800;">{bmi:.2f}</h1>
                <h3 style="color: {status_color}; margin: 5px 0 0 0;">{status_text}</h3>
            </div>
        """,
            unsafe_allow_html=True,
        )

        if gender == "ชาย":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        act_factors = {
            "นั่งทำงานอยู่กับที่ (ไม่ออกกำลังกายเลย)": 1.2,
            "ออกกำลังกายเล็กน้อย (1-3 วัน/สัปดาห์)": 1.375,
            "ออกกำลังกายปานกลาง (3-5 วัน/สัปดาห์)": 1.55,
            "ออกกำลังกายหนัก (6-7 วัน/สัปดาห์)": 1.725,
        }

        tdee = bmr * act_factors[activity]

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric(label="BMR (อัตราเผาผลาญขั้นต่ำ)", value=f"{bmr:.0f} kcal")
        with col_b:
            if category == "underweight":
                target_cal = tdee + 400
                target_label = "DAILY TARGET (เป้าหมายเพิ่มน้ำหนัก)"
            elif category == "normal":
                target_cal = tdee
                target_label = "DAILY TARGET (เป้าหมายรักษาสภาพ)"
            else:
                target_cal = tdee - 400
                target_label = "DAILY TARGET (เป้าหมายลดไขมัน)"
            st.metric(label=target_label, value=f"{target_cal:.0f} kcal")

        # ----------------------------------------------------
        # 💡 ส่วนที่เพิ่มเข้ามาใหม่: คำแนะนำอาหารและการออกกำลังกาย
        # ----------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("💡 NUTRITION & EXERCISE RECOMMENDATIONS")

        col_nut, col_ex = st.columns(2)

        with col_nut:
            st.markdown('<div class="rec-box"><div class="rec-title">🥗 คำแนะนำด้านอาหาร (Nutrition)</div>', unsafe_allow_html=True)
            
            # คำนวณสัดส่วนสารอาหารคร่าวๆ (Macronutrients)
            protein_g = weight * (2.0 if category == "underweight" or category == "normal" else 1.6)
            
            if category == "underweight":
                st.write(f"• **เป้าหมาย:** เพิ่มมวลกล้ามเนื้อและน้ำหนักตัว")
                st.write(f"• **โปรตีนที่ควรได้รับ:** ~{protein_g:.0f} กรัม/วัน (อกไก่, ไข่ต้ม, เวย์โปรตีน)")
                st.write("• เน้นทานอาหารที่มีสารอาหารสูง แป้งเชิงซ้อน เช่น ข้าวกล้อง ขนมปังโฮลวีต")
                st.write("• แบ่งทานวันละ 4-5 มื้อเล็ก เพื่อเพิ่มปริมาณแคลอรีโดยไม่อึดอัด")
            elif category == "normal":
                st.write(f"• **เป้าหมาย:** รักษามวลกล้ามเนื้อและควบคุมเปอร์เซ็นต์ไขมัน")
                st.write(f"• **โปรตีนที่ควรได้รับ:** ~{protein_g:.0f} กรัม/วัน")
                st.write("• เน้นรับประทานอาหารครบ 5 หมู่ในสัดส่วนที่เหมาะสม")
                st.write("• เลี่ยงของหวาน น้ำชง และอาหารแปรรูป คุมโซเดียมให้อยู่ในเกณฑ์พอดี")
            else:
                st.write(f"• **เป้าหมาย:** ลดไขมันสะสม (Caloric Deficit)")
                st.write(f"• **โปรตีนที่ควรได้รับ:** ~{protein_g:.0f} กรัม/วัน (รักษาเนื้อกล้ามเนื้อ)")
                st.write("• ลดการบริโภคคาร์โบไฮเดรตเชิงเดี่ยว (น้ำตาล, ข้าวขาว, น้ำชง)")
                st.write("• เพิ่มผักใบเขียวในทุกมื้อเพื่อให้รู้สึกอิ่มนาน และดื่มน้ำ 2.5-3 ลิตร/วัน")
            
            st.markdown('</div>', unsafe_allow_html=True)

        with col_ex:
            st.markdown('<div class="rec-box"><div class="rec-title">🏋️‍♂️ คำแนะนำการออกกำลังกาย (Exercise)</div>', unsafe_allow_html=True)
            
            if category == "underweight":
                st.write("• **เวทเทรนนิ่ง (Hypertrophy):** 3-4 วัน/สัปดาห์ (เน้นท่า Compound เช่น Squat, Bench Press)")
                st.write("• **คาร์ดิโอ:** 1-2 วัน/สัปดาห์ ครั้งละ 15-20 นาที พอประมาณ")
                st.write("• **พักผ่อน:** นอนหลับให้ครบ 7-8 ชม. เพื่อการซ่อมแซมกล้ามเนื้อ")
            elif category == "normal":
                st.write("• **เวทเทรนนิ่ง:** 3-4 วัน/สัปดาห์ (เพื่อกระชับสัดส่วนสร้างมวลกล้ามเนื้อ)")
                st.write("• **คาร์ดิโอ (Zone 2):** 2-3 วัน/สัปดาห์ ครั้งละ 30-45 นาที (วิ่งเหยาะๆ, ปั่นจักรยาน)")
                st.write("• เน้นความสม่ำเสมอในการออกกำลังกายอย่างต่อเนื่อง")
            else:
                st.write("• **เวทเทรนนิ่ง:** 3-4 วัน/สัปดาห์ (สร้างกล้ามเนื้อช่วยเร่งการเผาผลาญ BMR)")
                st.write("• **คาร์ดิโอเผาผลาญไขมัน:** 4-5 วัน/สัปดาห์ ครั้งละ 40-60 นาที (เดินชัน, เดินเร็ว)")
                st.write("• หากน้ำหนักตัวมาก ควรเลี่ยงการวิ่งเพื่อถนอมข้อเข่า")

            st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# โหมดที่ 2: ถ่ายภาพ/อัปโหลดภาพ + ให้ AI วิเคราะห์
# ----------------------------------------------------
elif mode == "📸 ถ่ายภาพ / อัปโหลดให้ AI วิเคราะห์":
    st.subheader("📷 สแกนรูปร่างและไขมันด้วย AI")

    upload_option = st.selectbox(
        "เลือกวิธีส่งรูปภาพ:", ["ถ่ายภาพจากกล้องสด", "อัปโหลดรูปภาพจากเครื่อง"]
    )

    img_data = None
    if upload_option == "ถ่ายภาพจากกล้องสด":
        img_data = st.camera_input("กดถ่ายภาพรูปร่างของคุณ")
    else:
        img_data = st.file_uploader(
            "เลือกไฟล์ภาพรูปร่าง (JPG, PNG)", type=["jpg", "jpeg", "png"]
        )

    if img_data is not None:
        image = Image.open(img_data)
        st.image(image, caption="รูปภาพที่เลือก", use_container_width=True)

        if st.button("🤖 ให้ AI วิเคราะห์รูปร่างภาพนี้"):
            with st.spinner("กำลังส่งภาพให้ AI วิเคราะห์ข้อมูล..."):
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)

                    prompt = """
                    คุณคือเทรนเนอร์ฟิตเนสมืออาชีพ โปรดวิเคราะห์รูปร่างจากภาพนี้แบบตรงไปตรงมาและให้กำลังใจ:
                    1. ประเมินสภาวะรูปร่างโดยรวม (ผอม / สมส่วน / มีไขมันสะสม / อ้วน)
                    2. ประเมินเปอร์เซ็นต์ไขมันคร่าวๆ (Body Fat Percentage)
                    3. ให้คำแนะนำ 3 ข้อที่ควรเริ่มทำทันที (อาหารและการออกกำลังกาย)
                    """

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[image, prompt]
                    )

                    ai_result = response.text

                    st.success("✅ วิเคราะห์เรียบร้อย!")
                    st.markdown("### 📊 ผลวิเคราะห์จาก AI")
                    st.write(ai_result)

                    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.photo_history.append({
                        "image": image,
                        "result": ai_result,
                        "date": now_str
                    })
                    st.info("💾 บันทึกรูปและผลวิเคราะห์เข้าสู่ประวัติเรียบร้อยแล้ว!")

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ AI: {e}")

# ----------------------------------------------------
# โหมดที่ 3: เปิดดูประวัติรูปภาพที่ถ่ายไว้
# ----------------------------------------------------
else:
    st.subheader("🖼️ ประวัติรูปภาพที่ถ่ายบันทึกไว้")

    if len(st.session_state.photo_history) == 0:
        st.warning("ยังไม่มีรูปภาพที่บันทึกไว้ ลองถ่ายรูปหรืออัปโหลดในโหมดที่ 2 ดูนะครับ!")
    else:
        for idx, item in enumerate(reversed(st.session_state.photo_history)):
            with st.expander(f"📸 รูปบันทึกเมื่อ {item['date']}"):
                col_img, col_info = st.columns([1, 1])
                with col_img:
                    st.image(item["image"], caption=item["date"], use_container_width=True)
                with col_info:
                    st.markdown("**ผลวิเคราะห์ของรูปนี้:**")
                    st.write(item["result"])   