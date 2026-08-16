import streamlit as st
import sqlite3
import hashlib
import google.generativeai as genai
from PIL import Image

# ---------------------------------------------------------
# 1. Page Config & API Key Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="NUTRITION & BODY AI DASHBOARD",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto"
)

GEMINI_API_KEY = "AQ.Ab8RN6L8XwG8tPbyxWzHdFThhTszmc0SNAAUJX6y3_EO6kKuAw"
genai.configure(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------
# 2. Database & Auth Management (SQLite)
# ---------------------------------------------------------
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, make_hashes(password)))
    conn.commit()
    conn.close()

def check_username_exists(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT username FROM userstable WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    return data is not None

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

init_db()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# ---------------------------------------------------------
# 3. Custom Premium UX/UI CSS
# ---------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Kanit', 'Plus Jakarta Sans', sans-serif;
        box-sizing: border-box;
    }

    html, body {
        overflow-x: hidden;
    }

    /* Main App Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(245, 158, 11, 0.12) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.12) 0%, transparent 40%),
                    radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.08) 0%, transparent 60%),
                    #0b0f19;
        background-attachment: fixed;
        color: #f1f5f9;
        min-height: 100vh;
    }

    #MainMenu, footer, header { visibility: hidden; }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }

    /* Header Container */
    .hero-header {
        background: rgba(18, 24, 38, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 32px 24px;
        text-align: center;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 30%;
        right: 30%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #F59E0B, #10B981, transparent);
    }

    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.3);
        color: #FBBF24;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 999px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero-title {
        background: linear-gradient(135deg, #FFFFFF 20%, #FBBF24 60%, #F59E0B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }

    .hero-sub {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        margin-top: 10px;
    }

    /* Container Styling */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(18, 24, 38, 0.65) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4) !important;
        padding: 24px !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(245, 158, 11, 0.25) !important;
        box-shadow: 0 20px 45px rgba(245, 158, 11, 0.1) !important;
    }

    /* Section Headings */
    .card-heading {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #FBBF24 !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Inputs & Selects */
    label, label p, [data-testid="stWidgetLabel"] p {
        color: #CBD5E1 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div, 
    input {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #F8FAFC !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        transition: all 0.2s ease !important;
    }

    div[data-baseweb="select"] > div:hover, 
    div[data-baseweb="input"] > div:hover {
        border-color: #F59E0B !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #FFFFFF !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 12px 28px !important;
        border-radius: 14px !important;
        border: none !important;
        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.35) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(245, 158, 11, 0.5) !important;
        background: linear-gradient(135deg, #FBBF24 0%, #D97706 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Tabs Styling - Ultra Clean Pill Frame & Font Clarity */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: rgba(15, 23, 42, 0.85) !important;
        padding: 6px !important;
        border-radius: 999px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        display: inline-flex !important;
        align-items: center !important;
        margin-bottom: 16px !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"],
    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
        height: 0 !important;
        visibility: hidden !important;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 999px !important;
        color: #E2E8F0 !important;
        font-size: 0.98rem !important;
        font-weight: 600 !important;
        padding: 8px 22px !important;
        transition: all 0.25s ease !important;
        border: none !important;
        outline: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 40px !important;
    }

    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span {
        color: inherit !important;
        font-size: 0.98rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        display: flex !important;
        align-items: center !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 999px !important;
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.4) !important;
    }

    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }

    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 18px 14px;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(245, 158, 11, 0.4);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #F59E0B, #10B981);
    }

    .metric-label {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-value {
        color: #F8FAFC;
        font-size: 1.9rem;
        font-weight: 800;
        margin-top: 6px;
        background: linear-gradient(180deg, #FFFFFF 0%, #CBD5E1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-unit {
        font-size: 0.85rem;
        color: #F59E0B;
        font-weight: 600;
        margin-left: 2px;
    }

    /* Advice & Status Boxes */
    .advice-card {
        border-radius: 16px;
        padding: 22px;
        margin-top: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        line-height: 1.7;
    }

    .advice-underweight {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.05) 100%);
        border-left: 5px solid #F59E0B;
    }

    .advice-normal {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.05) 100%);
        border-left: 5px solid #10B981;
    }

    .advice-overweight {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(220, 38, 38, 0.05) 100%);
        border-left: 5px solid #EF4444;
    }

    .advice-header {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .advice-underweight .advice-header { color: #FBBF24; }
    .advice-normal .advice-header { color: #34D399; }
    .advice-overweight .advice-header { color: #F87171; }

    .advice-body {
        color: #E2E8F0;
        font-size: 0.95rem;
    }

    .food-chip-group {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }

    .food-chip {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #F1F5F9;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(11, 15, 25, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .sidebar-user {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 20px;
        text-align: center;
    }

    .sidebar-avatar {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #F59E0B, #10B981);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0 auto 10px auto;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
    }

    /* Radio buttons */
    div[role="radiogroup"] {
        gap: 12px;
    }
    
    div[role="radiogroup"] label {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 8px 16px !important;
        transition: all 0.2s ease;
    }
    
    div[role="radiogroup"] label:hover {
        border-color: #F59E0B;
    }

    /* AI Analysis Response Card */
    .ai-response-box {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        line-height: 1.8;
        color: #F1F5F9;
    }

    @media (max-width: 768px) {
        .hero-header {
            padding: 22px 16px;
            border-radius: 18px;
            margin-bottom: 18px;
        }

        .hero-title {
            font-size: 1.9rem;
            line-height: 1.15;
        }

        .hero-sub {
            font-size: 0.92rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 16px !important;
            border-radius: 16px !important;
        }

        .metric-grid {
            grid-template-columns: 1fr;
        }

        .metric-value {
            font-size: 1.5rem;
        }

        .stButton > button {
            width: 100% !important;
            padding: 12px 18px !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            border-radius: 999px !important;
        }

        .stTabs [data-baseweb="tab"] {
            width: 100%;
            padding: 10px 8px;
            font-size: 0.9rem;
            border-radius: 999px !important;
        }
    }

    @media (max-width: 480px) {
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }

        .badge-pill {
            font-size: 0.72rem;
            letter-spacing: 0.5px;
        }

        .card-heading {
            font-size: 1.1rem !important;
        }

        .food-chip {
            font-size: 0.75rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. Auth Screen
# ---------------------------------------------------------
def show_auth_page():
    st.markdown("""
        <div class="hero-header">
            <div class="badge-pill">FITNESS & NUTRITION AI</div>
            <h1 class="hero-title">HEALTH DASHBOARD</h1>
            <div class="hero-sub">กรุณากรอกข้อมูลเพื่อเข้าสู่ระบบ หรือ สมัครสมาชิกใหม่</div>
        </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        tab_login, tab_register = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิกใหม่"])

        with tab_login:
            st.markdown('<div class="card-heading">เข้าสู่ระบบใช้งาน</div>', unsafe_allow_html=True)
            login_user_input = st.text_input("ชื่อผู้ใช้งาน (Username)", key="login_user", placeholder="กรอกชื่อผู้ใช้...")
            login_pass_input = st.text_input("รหัสผ่าน (Password)", type="password", key="login_pass", placeholder="กรอกรหัสผ่าน...")

            if st.button("เข้าสู่ระบบ", key="btn_login"):
                if login_user_input and login_pass_input:
                    result = login_user(login_user_input, login_pass_input)
                    if result:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = login_user_input
                        st.rerun()
                    else:
                        st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                else:
                    st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

        with tab_register:
            st.markdown('<div class="card-heading">สมัครสมาชิกใหม่</div>', unsafe_allow_html=True)
            reg_user = st.text_input("ตั้งชื่อผู้ใช้งาน (Username)", key="reg_user", placeholder="ตั้งชื่อผู้ใช้งาน...")
            reg_pass = st.text_input("ตั้งรหัสผ่าน (Password)", type="password", key="reg_pass", placeholder="ตั้งรหัสผ่าน...")
            reg_pass_confirm = st.text_input("ยืนยันรหัสผ่าน (Confirm Password)", type="password", key="reg_pass_confirm", placeholder="ยืนยันรหัสผ่านอีกครั้ง...")

            if st.button("บันทึกการลงทะเบียน", key="btn_register"):
                if reg_user and reg_pass and reg_pass_confirm:
                    if reg_pass != reg_pass_confirm:
                        st.error("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
                    elif check_username_exists(reg_user):
                        st.warning("ชื่อผู้ใช้นี้ถูกใช้งานแล้ว กรุณาใช้ชื่ออื่น")
                    else:
                        add_userdata(reg_user, reg_pass)
                        st.success("สมัครสมาชิกสำเร็จเรียบร้อย! คุณสามารถเข้าสู่ระบบได้ทันที")
                else:
                    st.warning("กรุณากรอกข้อมูลลงทะเบียนให้ครบถ้วน")

# ---------------------------------------------------------
# 5. Main Dashboard Screen
# ---------------------------------------------------------
def show_main_dashboard():
    user_initial = st.session_state['username'][0].upper() if st.session_state['username'] else "U"
    
    with st.sidebar:
        st.markdown(f"""
            <div class="sidebar-user">
                <div class="sidebar-avatar">{user_initial}</div>
                <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">ผู้ใช้งานปัจจุบัน</div>
                <div style="color: #F8FAFC; font-size: 1.1rem; font-weight: 700; margin-top: 2px;">{st.session_state['username']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("ออกจากระบบ"):
            st.session_state["authenticated"] = False
            st.session_state["username"] = ""
            st.rerun()

    st.markdown("""
        <div class="hero-header">
            <div class="badge-pill">INTELLIGENT HEALTH ENGINE</div>
            <h1 class="hero-title">NUTRITION & BODY DASHBOARD</h1>
            <div class="hero-sub">คำนวณพลังงาน BMI / BMR / TDEE และวิเคราะห์รูปร่างด้วย AI มืออาชีพ</div>
        </div>
    """, unsafe_allow_html=True)

    tab_calc, tab_ai = st.tabs(["คำนวณ BMI / BMR / TDEE", "สแกนรูปร่างด้วย AI"])

    # --- TAB 1: คำนวณ BMR/TDEE ---
    with tab_calc:
        with st.container(border=True):
            st.markdown('<div class="card-heading">ข้อมูลส่วนบุคคลเพื่อคำนวณ</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("เพศสภาพ", ["ชาย", "หญิง"])
                age = st.number_input("อายุ (ปี)", min_value=10, max_value=100, value=25)
            with col2:
                weight = st.number_input("น้ำหนัก (กก.)", min_value=30.0, max_value=200.0, value=65.0, step=0.5)
                height = st.number_input("ส่วนสูง (ซม.)", min_value=100.0, max_value=230.0, value=170.0, step=0.5)

            act_factors = {
                "นั่งทำงานอยู่กับที่ / ไม่ได้ออกกำลังกาย": 1.2,
                "ออกกำลังกายเบาๆ (1-3 วัน/สัปดาห์)": 1.375,
                "ออกกำลังกายปานกลาง (3-5 วัน/สัปดาห์)": 1.55,
                "ออกกำลังกายหนัก (6-7 วัน/สัปดาห์)": 1.725
            }
            activity = st.selectbox("ระดับกิจกรรมประจำวัน", list(act_factors.keys()))

            calculate_btn = st.button("คำนวณผลลัพธ์และจัดเมนูอาหาร")

        if calculate_btn:
            height_m = height / 100
            bmi = weight / (height_m ** 2)

            if gender == "ชาย":
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
            else:
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

            tdee = bmr * act_factors[activity]

            st.write("")
            with st.container(border=True):
                st.markdown('<div class="card-heading">สรุปผลลัพธ์ดัชนีร่างกายของคุณ</div>', unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="metric-grid">
                        <div class="metric-card">
                            <div class="metric-label">BMI</div>
                            <div class="metric-value">{bmi:.1f}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">BMR</div>
                            <div class="metric-value">{bmr:,.0f} <span class="metric-unit">kcal</span></div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">TDEE</div>
                            <div class="metric-value">{tdee:,.0f} <span class="metric-unit">kcal</span></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if bmi < 18.5:
                    target_cal = tdee + 400
                    st.markdown(f"""
                        <div class="advice-card advice-underweight">
                            <div class="advice-header">สถานะ: น้ำหนักน้อยกว่าเกณฑ์มาตรฐาน (BMI < 18.5)</div>
                            <div class="advice-body">
                                พลังงานที่แนะนำต่อวันสำหรับการเพิ่มน้ำหนักอย่างมีคุณภาพ: <b style="color:#FBBF24;">{target_cal:,.0f} kcal / วัน</b>
                                <hr style="border-top: 1px solid rgba(245, 158, 11, 0.2); margin: 12px 0;">
                                <b>แนวทางโภชนาการและสารอาหารแนะนำ:</b>
                                <div class="food-chip-group">
                                    <span class="food-chip">🥩 อกไก่ & ปลาแซลมอน</span>
                                    <span class="food-chip">🥚 ไข่ต้ม (2-3 ฟอง/วัน)</span>
                                    <span class="food-chip">🍚 ข้าวกล้อง & มันนึ่ง</span>
                                    <span class="food-chip">🥜 อัลมอนด์ & อะโวคาโด</span>
                                    <span class="food-chip">🥤 เวย์โปรตีน / นมถั่วเหลือง</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                elif 18.5 <= bmi <= 22.9:
                    st.markdown(f"""
                        <div class="advice-card advice-normal">
                            <div class="advice-header">สถานะ: น้ำหนักอยู่ในเกณฑ์สมส่วน (BMI 18.5 - 22.9)</div>
                            <div class="advice-body">
                                พลังงานที่แนะนำต่อวันสำหรับการรักษาสมดุลร่างกาย: <b style="color:#34D399;">{tdee:,.0f} kcal / วัน</b>
                                <hr style="border-top: 1px solid rgba(16, 185, 129, 0.2); margin: 12px 0;">
                                <b>แนวทางโภชนาการและสารอาหารแนะนำ:</b>
                                <div class="food-chip-group">
                                    <span class="food-chip">🥗 สัดส่วนจานสุขภาพ 2:1:1</span>
                                    <span class="food-chip">🍗 อกไก่ลอกหนัง & ปลาเนื้อขาว</span>
                                    <span class="food-chip">🌾 ข้าวไรซ์เบอร์รี & ขนมปังโฮลวีต</span>
                                    <span class="food-chip">🍏 ผลไม้หวานน้อย (แอปเปิลเขียว, ฝรั่ง)</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                else:
                    target_cal = tdee - 500
                    st.markdown(f"""
                        <div class="advice-card advice-overweight">
                            <div class="advice-header">สถานะ: น้ำหนักเกินเกณฑ์มาตรฐาน (BMI ≥ 23.0)</div>
                            <div class="advice-body">
                                พลังงานที่แนะนำต่อวันสำหรับการลดไขมันอย่างปลอดภัย: <b style="color:#F87171;">{target_cal:,.0f} kcal / วัน</b>
                                <hr style="border-top: 1px solid rgba(239, 68, 68, 0.2); margin: 12px 0;">
                                <b>แนวทางโภชนาการและสารอาหารแนะนำ:</b>
                                <div class="food-chip-group">
                                    <span class="food-chip">🥦 ผักบรอกโคลี & กะหล่ำปลี (เน้นอิ่มนาน)</span>
                                    <span class="food-chip">🍳 อกไก่ต้ม & ไข่ขาว</span>
                                    <span class="food-chip">🍠 ข้าวโอ๊ต & มันหวาน GI ต่ำ</span>
                                    <span class="food-chip">🚫 งดเครื่องดื่มน้ำตาล & ของทอด</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    # --- TAB 2: วิเคราะห์รูปร่างด้วย AI ---
    with tab_ai:
        with st.container(border=True):
            st.markdown('<div class="card-heading">สแกนและวิเคราะห์รูปร่างด้วย AI</div>', unsafe_allow_html=True)
            
            cam_mode = st.radio("เลือกช่องทางรับภาพ:", ["เปิดกล้องถ่ายภาพ", "อัปโหลดไฟล์รูปภาพ"])
            
            img_file = None
            if cam_mode == "เปิดกล้องถ่ายภาพ":
                img_file = st.camera_input("ถ่ายรูปหน้าตรงให้เห็นช่วงลำตัวหรือทั้งตัว")
            else:
                img_file = st.file_uploader("อัปโหลดภาพถ่ายรูปร่างของคุณ", type=["jpg", "jpeg", "png"])

            if img_file:
                image = Image.open(img_file)
                st.image(image, caption="ภาพถ่ายของคุณ", use_container_width=True)

                if st.button("ให้ AI วิเคราะห์รูปร่างและคำแนะนำ"):
                    with st.spinner("AI กำลังประมวลผลและวิเคราะห์โครงสร้างร่างกายของคุณ..."):
                        try:
                            prompt = """
                            คุณคือโค้ชฟิตเนสและนักโภชนาการมืออาชีพ โปรดวิเคราะห์ภาพถ่ายรูปร่างนี้:
                            1. ประเมินโครงสร้างรูปร่างคร่าวๆ (เช่น Ectomorph, Mesomorph, Endomorph)
                            2. วิเคราะห์จุดเด่นและจุดที่สามารถพัฒนาเพิ่มได้ (เช่น ไหล่, อก, หน้าท้อง, ต้นขา)
                            3. แนะนำแนวทางการออกกำลังกายที่เหมาะสม
                            4. แนะนำโภชนาการเพื่อสร้างหรือกระชับสัดส่วน
                            (ตอบเป็นภาษาไทยอย่างเป็นกันเอง สุภาพ และให้กำลังใจ จัดรูปแบบอ่านง่าย สวยงาม มีหัวข้อชัดเจน)
                            """

                            # ค้นหาโมเดลที่มีในระบบแบบอัตโนมัติ
                            available_models = []
                            try:
                                for m in genai.list_models():
                                    if 'generateContent' in m.supported_generation_methods:
                                        name = m.name.replace('models/', '')
                                        available_models.append(name)
                            except Exception:
                                pass

                            candidate_models = ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash-exp']
                            
                            if available_models:
                                flash_models = [m for m in available_models if 'flash' in m]
                                other_models = [m for m in available_models if m not in flash_models]
                                candidate_models = flash_models + other_models + candidate_models

                            seen = set()
                            target_models = [x for x in candidate_models if not (x in seen or seen.add(x))]

                            response = None
                            used_model = ""
                            last_err = None

                            for model_name in target_models:
                                try:
                                    model = genai.GenerativeModel(model_name)
                                    res = model.generate_content([prompt, image])
                                    if res and res.text:
                                        response = res
                                        used_model = model_name
                                        break
                                except Exception as err:
                                    last_err = err
                                    continue

                            if response:
                                st.markdown(f'<div class="card-heading">ผลการวิเคราะห์จาก AI ({used_model})</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="ai-response-box">{response.text}</div>', unsafe_allow_html=True)
                            else:
                                st.error(f"เกิดข้อผิดพลาดในการเรียกใช้ AI: {last_err}")
                                if available_models:
                                    st.info(f"รายชื่อโมเดลที่รองรับในระบบของคุณ: {', '.join(available_models)}")
                                else:
                                    st.warning("กรุณาตรวจสอบ API Key ของคุณในบรรทัดที่ 16 ของ phum.py (API Key จาก Google AI Studio มักจะขึ้นต้นด้วย 'AIzaSy...')")

                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ภาพ: {e}")

# ---------------------------------------------------------
# 6. Main Routing
# ---------------------------------------------------------
if not st.session_state["authenticated"]:
    show_auth_page()
else:
    show_main_dashboard()
