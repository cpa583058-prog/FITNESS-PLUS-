import base64
import io
import datetime
import json
import os
import hashlib
import streamlit as st
from google import genai
from PIL import Image
from streamlit_oauth import OAuth2Component

# ----------------------------------------------------
# 1. ระบบจัดการข้อมูลผู้ใช้งาน (Local JSON DB) 💾
# ----------------------------------------------------
USER_DB_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    with open(USER_DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ----------------------------------------------------
# 2. Google OAuth Credentials 🔑
# ----------------------------------------------------
CLIENT_ID = "889238823886-3uc77e8sijbgsrmqr7lfdohk3olv501e.apps.googleusercontent.com"
CLIENT_SECRET = "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"

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REFRESH_TOKEN_URL = TOKEN_URL
REVOKE_TOKEN_URL = "https://oauth2.googleapis.com/revoke"

oauth2 = OAuth2Component(
    CLIENT_ID,
    CLIENT_SECRET,
    AUTHORIZE_URL,
    TOKEN_URL,
    REFRESH_TOKEN_URL,
    REVOKE_TOKEN_URL
)

# ----------------------------------------------------
# 3. ตั้งค่าหน้าเว็บและดีไซน์ UI สุดหรู (CSS) 🎨
# ----------------------------------------------------
st.set_page_config(
    page_title="FITNESS PLUS - AI BODY TRACKER",
    page_icon="⚡",
    layout="centered"
)

if "user" not in st.session_state:
    st.session_state.user = None

st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;500;700;800&display=swap" rel="stylesheet">
    <style>
        .stApp {
            background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(10, 10, 10, 0.85)), 
                        url('https://images.unsplash.com/photo-1517838277536-f5f99be501cd?q=80&w=1920&auto=format&fit=crop') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            font-family: 'Kanit', sans-serif !important;
            color: #FFFFFF !important;
        }

        div.stMainBlockContainer {
            background: rgba(18, 18, 18, 0.75) !important;
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            border-radius: 20px !important;
            padding: 40px 30px !important;
            border: 1px solid rgba(255, 184, 0, 0.35) !important;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7), 0 0 20px rgba(255, 184, 0, 0.15) !important;
            margin-top: 40px;
        }

        div[data-testid="stCustomComponentV1"] {
            display: flex !important;
            justify-content: center !important;
            margin-top: 15px !important;
        }

        .fitness-title {
            color: #FFB800 !important;
            font-weight: 800;
            font-size: 2.3rem;
            text-transform: uppercase;
            text-align: center;
            letter-spacing: 1px;
            text-shadow: 0 4px 12px rgba(255, 184, 0, 0.3);
        }

        .fitness-subtitle {
            color: #CCCCCC !important;
            text-align: center;
            font-size: 1rem;
            margin-bottom: 25px;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #FFB800 0%, #E6A100 100%) !important;
            color: #000000 !important;
            font-weight: 800 !important;
            border-radius: 10px !important;
            width: 100%;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 184, 0, 0.4);
        }

        /* ตกแต่ง Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            color: #FFFFFF;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFB800 !important;
            color: #000000 !important;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 4. หน้า Authentication (เข้าสู่ระบบ / ลงทะเบียน) 🔒
# ----------------------------------------------------
if not st.session_state.user:
    st.markdown('<div class="fitness-title">⚡ FITNESS PLUS</div>', unsafe_allow_html=True)
    st.markdown('<div class="fitness-subtitle">ยินดีต้อนรับสู่ระบบวิเคราะห์สุขภาพและรูปร่าง</div>', unsafe_allow_html=True)
    
    tab_login, tab_register, tab_google = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🌐 Google OAuth"])

    # --- TAB 1: เข้าสู่ระบบ ---
    with tab_login:
        st.write("")
        login_user = st.text_input("ชื่อผู้ใช้ / Username", key="login_username")
        login_pass = st.text_input("รหัสผ่าน / Password", type="password", key="login_password")
        
        if st.button("เข้าสู่ระบบ ➔", key="btn_login"):
            users = load_users()
            hashed_input = hash_password(login_pass)
            if login_user in users and users[login_user] == hashed_input:
                st.session_state.user = login_user
                st.success(f"ยินดีต้อนรับคุณ {login_user}!")
                st.rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    # --- TAB 2: สมัครสมาชิก ---
    with tab_register:
        st.write("")
        reg_user = st.text_input("ตั้งชื่อผู้ใช้ / Username", key="reg_username")
        reg_pass = st.text_input("ตั้งรหัสผ่าน / Password", type="password", key="reg_password")
        reg_pass_confirm = st.text_input("ยืนยันรหัสผ่าน / Confirm Password", type="password", key="reg_password_confirm")

        if st.button("ยืนยันการลงทะเบียน ✨", key="btn_register"):
            users = load_users()
            if not reg_user or not reg_pass:
                st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")
            elif reg_user in users:
                st.error("ชื่อผู้ใช้นี้มีในระบบแล้ว กรุณาใช้ชื่ออื่น")
            elif reg_pass != reg_pass_confirm:
                st.error("รหัสผ่านไม่ตรงกัน กรุณาตรวจสอบอีกครั้ง")
            else:
                users[reg_user] = hash_password(reg_pass)
                save_users(users)
                st.success("ลงทะเบียนสำเร็จแล้ว! คุณสามารถเข้าสู่ระบบด้วยรหัสผ่านใหม่ได้ทันที")

    # --- TAB 3: Google Login ---
    with tab_google:
        st.write("")
        st.caption("คลิกปุ่มด้านล่างเพื่อเข้าสู่ระบบด้วยบัญชี Google")
        result = oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com/favicon.ico",
            redirect_uri="http://localhost:8501/",
            scope="openid email profile",
            key="google_auth"
        )

        if result and "token" in result:
            st.session_state.user = "Google User"
            st.rerun()

else:
    # ----------------------------------------------------
    # 5. โค้ดโปรแกรมหลักเมื่อเข้าสู่ระบบสำเร็จ 🏋️‍♂️
    # ----------------------------------------------------
    st.sidebar.write(f"🟢 **เข้าสู่ระบบโดย:** {st.session_state.user}")
    if st.sidebar.button("🚪 ออกจากระบบ"):
        del st.session_state.user
        st.rerun()

    GEMINI_API_KEY = "AQ.Ab8RN6J4R-3ab49IH6JPxOXSBsoNRv3OEExYudcaWNg5ucxKHw"

    if "photo_history" not in st.session_state:
        st.session_state.photo_history = []

    st.markdown('<div class="fitness-title">⚡ FITNESS PLUS & AI ANALYZER</div>', unsafe_allow_html=True)
    st.markdown('<div class="fitness-subtitle">คำนวณ BMI และวิเคราะห์รูปร่างด้วย AI พร้อมเก็บบันทึกภาพ</div>', unsafe_allow_html=True)
    st.write("---")

    mode = st.radio(
        "เลือกฟังก์ชันที่ต้องการใช้งาน:",
        ["📊 คำนวณ BMI & คำแนะนำ", "📸 ถ่ายภาพ / อัปโหลดให้ AI วิเคราะห์", "🖼️ ประวัติรูปภาพที่บันทึกไว้"],
        horizontal=True
    )

    if mode == "📊 คำนวณ BMI & คำแนะนำ":
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("เพศ (GENDER)", ["ชาย", "หญิง"])
                age = st.number_input("อายุ (AGE / ปี)", min_value=1, max_value=120, value=25)
            with col2:
                weight = st.number_input("น้ำหนัก (WEIGHT / กก.)", min_value=1.00, max_value=300.00, value=65.00, step=0.10, format="%.2f")
                height = st.number_input("ส่วนสูง (HEIGHT / ซม.)", min_value=50.00, max_value=250.00, value=170.00, step=0.10, format="%.2f")

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
                category, status_text, status_color = "underweight", "❌ UNDERWEIGHT (ผอมกว่าเกณฑ์มาตรฐาน)", "#FF4B4B"
            elif 18.5 <= bmi <= 22.9:
                category, status_text, status_color = "normal", "✅ NORMAL WEIGHT (สมส่วนตามเกณฑ์มาตรฐาน)", "#FFB800"
            elif 23.0 <= bmi <= 24.9:
                category, status_text, status_color = "overweight", "⚠️ OVERWEIGHT (เริ่มมีน้ำหนักเกิน)", "#FF9F43"
            else:
                category, status_text, status_color = "obese", "🚨 OBESE (สภาวะอ้วน)", "#FF5252"

            st.markdown(
                f"""
                <div style="background-color: rgba(0,0,0,0.5); border-left: 6px solid {status_color}; padding: 20px; border-radius: 8px;">
                    <span style="color: #DDDDDD; font-size: 0.9rem;">ค่า BMI ของคุณคือ</span>
                    <h1 style="color: #FFB800; margin: 0; font-size: 3rem; font-weight: 800;">{bmi:.2f}</h1>
                    <h3 style="color: {status_color}; margin: 5px 0 0 0;">{status_text}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            bmr = (10 * weight) + (6.25 * height) - (5 * age) + (5 if gender == "ชาย" else -161)
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
                target_cal = tdee + 400 if category == "underweight" else (tdee if category == "normal" else tdee - 400)
                st.metric(label="DAILY TARGET", value=f"{target_cal:.0f} kcal")

    elif mode == "📸 ถ่ายภาพ / อัปโหลดให้ AI วิเคราะห์":
        st.subheader("📷 สแกนรูปร่างและไขมันด้วย AI")
        upload_option = st.selectbox("เลือกวิธีส่งรูปภาพ:", ["ถ่ายภาพจากกล้องสด", "อัปโหลดรูปภาพจากเครื่อง"])
        img_data = st.camera_input("กดถ่ายภาพรูปร่างของคุณ") if upload_option == "ถ่ายภาพจากกล้องสด" else st.file_uploader("เลือกไฟล์ภาพรูปร่าง (JPG, PNG)", type=["jpg", "jpeg", "png"])

        if img_data is not None:
            image = Image.open(img_data)
            st.image(image, caption="รูปภาพที่เลือก", use_container_width=True)

            if st.button("🤖 ให้ AI วิเคราะห์รูปร่างภาพนี้"):
                with st.spinner("กำลังส่งภาพให้ AI วิเคราะห์ข้อมูล..."):
                    try:
                        client = genai.Client(http_options={"headers": {"x-goog-api-key": GEMINI_API_KEY}})
                        prompt = "คุณคือเทรนเนอร์ฟิตเนสมืออาชีพ โปรดวิเคราะห์รูปร่างจากภาพนี้..."
                        response = client.models.generate_content(model="gemini-2.5-flash", contents=[image, prompt])

                        st.success("✅ วิเคราะห์เรียบร้อย!")
                        st.markdown("### 📊 ผลวิเคราะห์จาก AI")
                        st.write(response.text)

                        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.photo_history.append({"image": image, "result": response.text, "date": now_str})
                        st.info("💾 บันทึกเรียบร้อย!")
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {e}")

    else:
        st.subheader("🖼️ ประวัติรูปภาพที่ถ่ายบันทึกไว้")
        if len(st.session_state.photo_history) == 0:
            st.warning("ยังไม่มีรูปภาพที่บันทึกไว้")
        else:
            for idx, item in enumerate(reversed(st.session_state.photo_history)):
                with st.expander(f"📸 รูปบันทึกเมื่อ {item['date']}"):
                    col_img, col_info = st.columns([1, 1])
                    with col_img:
                        st.image(item["image"], caption=item["date"], use_container_width=True)
                    with col_info:
                        st.write(item["result"])
