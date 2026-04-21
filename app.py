import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
import json
import requests
import hashlib
import uuid
from io import BytesIO
import base64
import re

# Try to import reportlab, but provide fallback
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ==================== Firebase Configuration ====================
FIREBASE_URL = "https://stationary-f85f6-default-rtdb.firebaseio.com"

# ==================== Mobile Optimized Configuration ====================
st.set_page_config(
    page_title="AstroPro SL", 
    page_icon="☸️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization
st.markdown("""
    <style>
    /* Main container */
    [data-testid="stAppViewContainer"] { 
        max-width: 100%; 
        margin: 0;
        padding: 0;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom styling */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        padding: 12px;
        border: none;
        margin: 5px 0;
    }
    
    .stButton>button:hover { 
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: scale(0.98);
    }
    
    /* Form inputs */
    .stTextInput > div > div > input, .stSelectbox > div > div, .stDateInput > div > div {
        border-radius: 10px;
        border: 1px solid #ddd;
        padding: 10px;
    }
    
    /* Loading animation */
    .loading-spinner {
        text-align: center;
        padding: 50px;
    }
    
    /* Report styling */
    .report-box { 
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border: 1px solid #e94560;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        color: #f0f0f0;
        font-family: 'Noto Sans Sinhala', 'Iskoola Pota', sans-serif;
        font-size: 14px;
        line-height: 1.6;
    }
    
    .report-box h1, .report-box h2, .report-box h3 {
        color: #e94560;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    .report-box table {
        background-color: #0f3460;
        border-radius: 10px;
        overflow: hidden;
        width: 100%;
        margin: 10px 0;
    }
    
    .report-box th {
        background-color: #e94560;
        color: white;
        padding: 8px;
    }
    
    .report-box td {
        background-color: #16213e;
        color: #f0f0f0;
        padding: 8px;
    }
    
    /* Detail cards */
    .detail-box { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 15px;
        margin: 8px 0;
        text-align: center;
        font-family: 'Noto Sans Sinhala', sans-serif;
        font-size: 14px;
        font-weight: bold;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    
    .detail-box:hover {
        transform: translateY(-3px);
    }
    
    .detail-box b {
        font-size: 12px;
        color: #FFD700;
        display: block;
        margin-bottom: 8px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stInfo {
        border-radius: 10px;
        padding: 12px;
    }
    
    /* Share buttons */
    .share-btn {
        display: inline-block;
        padding: 8px 16px;
        margin: 5px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        text-align: center;
    }
    
    .whatsapp-btn {
        background-color: #25D366;
        color: white;
    }
    
    .email-btn {
        background-color: #EA4335;
        color: white;
    }
    
    /* Admin panel */
    .admin-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
    
    @media (max-width: 768px) {
        .report-box {
            font-size: 12px;
            padding: 15px;
        }
        .detail-box {
            font-size: 12px;
            padding: 10px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ==================== Session State Initialization ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'calculations' not in st.session_state:
    st.session_state.calculations = []
if 'selected_calc' not in st.session_state:
    st.session_state.selected_calc = None
if 'current_calc' not in st.session_state:
    st.session_state.current_calc = None
if 'current_ai_report' not in st.session_state:
    st.session_state.current_ai_report = None

# ==================== Firebase Functions ====================
def firebase_save_data(path, data):
    """Save data to Firebase"""
    try:
        response = requests.put(f"{FIREBASE_URL}/{path}.json", json=data)
        return response.status_code == 200
    except Exception as e:
        return False

def firebase_get_data(path):
    """Get data from Firebase"""
    try:
        response = requests.get(f"{FIREBASE_URL}/{path}.json")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

def firebase_push_data(path, data):
    """Push data to Firebase (generates unique ID)"""
    try:
        response = requests.post(f"{FIREBASE_URL}/{path}.json", json=data)
        if response.status_code == 200:
            return response.json()['name']
        return None
    except Exception as e:
        return None

def save_calculation_to_firebase(user_id, calc_data):
    """Save calculation to user's record"""
    calc_id = str(uuid.uuid4())
    calc_data['calc_id'] = calc_id
    calc_data['timestamp'] = datetime.now().isoformat()
    
    path = f"users/{user_id}/calculations/{calc_id}"
    if firebase_save_data(path, calc_data):
        return calc_id
    return None

def get_user_calculations(user_id):
    """Get all calculations for a user"""
    data = firebase_get_data(f"users/{user_id}/calculations")
    if data:
        return data
    return {}

def register_user(username, password, email, phone=""):
    """Register a new user"""
    users = firebase_get_data("users") or {}
    
    if username in users:
        return False, "Username already exists"
    
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    users[username] = {
        "password": hashed_pw,
        "email": email,
        "phone": phone,
        "created_at": datetime.now().isoformat(),
        "is_admin": False
    }
    
    if firebase_save_data("users", users):
        return True, "Registration successful"
    return False, "Registration failed"

def login_user(username, password):
    """Login user"""
    users = firebase_get_data("users") or {}
    
    if username not in users:
        return False, "User not found"
    
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    if users[username]["password"] == hashed_pw:
        return True, users[username]
    return False, "Wrong password"

# ==================== Ayanamsa Functions ====================
def get_ayanamsa_system(system_name):
    ayanamsa_systems = {
        "Lahiri (Chitrapaksha)": swe.SIDM_LAHIRI,
        "Raman": swe.SIDM_RAMAN,
        "Krishnamurthi": 7,
        "True Chitrapaksha": swe.SIDM_TRUE_CITRA,
        "Suryasiddhanta": 10,
        "Mani-Vakya": 11,
        "Siddhanta": 12
    }
    return ayanamsa_systems.get(system_name, swe.SIDM_LAHIRI)

def get_planet_bhava(planet_lon, cusps):
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start <= end:
            if start <= planet_lon < end:
                return i + 1
        else:
            if planet_lon >= start or planet_lon < end:
                return i + 1
    return 1

def get_nakshatra_details(nak_idx):
    nakshatra_data = {
        0: ("දේව ගණ", "අශ්වයා", "පුරුෂ ලිංග"),
        1: ("මනුෂ්ය ගණ", "ඇතා", "ස්ත්‍රී ලිංග"),
        2: ("රාක්ෂස ගණ", "එළුවා", "ස්ත්‍රී ලිංග"),
        3: ("මනුෂ්ය ගණ", "සර්පයා", "පුරුෂ ලිංග"),
        4: ("දේව ගණ", "සර්පයා", "පුරුෂ ලිංග"),
        5: ("මනුෂ්ය ගණ", "බල්ලා", "පුරුෂ ලිංග"),
        6: ("රාක්ෂස ගණ", "බල්ලා", "පුරුෂ ලිංග"),
        7: ("දේව ගණ", "බැටළුවා", "පුරුෂ ලිංග"),
        8: ("රාක්ෂස ගණ", "බළලා", "ස්ත්‍රී ලිංග"),
        9: ("රාක්ෂස ගණ", "මීයා", "පුරුෂ ලිංග"),
        10: ("මනුෂ්ය ගණ", "මීයා", "පුරුෂ ලිංග"),
        11: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ ලිංග"),
        12: ("දේව ගණ", "මීයා", "පුරුෂ ලිංග"),
        13: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී ලිංග"),
        14: ("දේව ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී ලිංග"),
        15: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "පුරුෂ ලිංග"),
        16: ("දේව ගණ", "මුවා", "පුරුෂ ලිංග"),
        17: ("රාක්ෂස ගණ", "මුවා", "පුරුෂ ලිංග"),
        18: ("රාක්ෂස ගණ", "සුනඛයා", "පුරුෂ ලිංග"),
        19: ("මනුෂ්ය ගණ", "වඳුරා", "පුරුෂ ලිංග"),
        20: ("මනුෂ්ය ගණ", "මුගටියා", "පුරුෂ ලිංග"),
        21: ("දේව ගණ", "වඳුරා", "පුරුෂ ලිංග"),
        22: ("රාක්ෂස ගණ", "සිංහයා", "ස්ත්‍රී ලිංග"),
        23: ("රාක්ෂස ගණ", "අශ්වයා", "පුරුෂ ලිංග"),
        24: ("මනුෂ්ය ගණ", "සිංහයා", "පුරුෂ ලිංග"),
        25: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ ලිංග"),
        26: ("දේව ගණ", "ඇතා", "පුරුෂ ලිංග")
    }
    return nakshatra_data.get(nak_idx, ("නොදනී", "නොදනී", "නොදනී"))

# ==================== Constants ====================
DISTRICTS = {
    "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "කළුතර": (6.5854, 79.9607),
    "මහනුවර": (7.2906, 80.6337), "මාතලේ": (7.4675, 80.6234), "නුවරඑළිය": (6.9497, 80.7891),
    "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245),
    "යාපනය": (9.6615, 80.0255), "කිලිනොච්චිය": (9.3854, 80.3921), "මන්නාරම": (8.9810, 79.9044),
    "වවුනියාව": (8.7542, 80.4982), "මුලතිව්": (9.2671, 80.8143), "මඩකලපුව": (7.7102, 81.6924),
    "අම්පාර": (7.2843, 81.6747), "ත්‍රිකුණාමලය": (8.5711, 81.2335), "කුරුණෑගල": (7.4863, 80.3647),
    "පුත්තලම": (8.0330, 79.8257), "අනුරාධපුරය": (8.3114, 80.4037), "පොළොන්නරුව": (7.9403, 81.0188),
    "බදුල්ල": (6.9934, 81.0550), "මොණරාගල": (6.8719, 81.3512), "රත්නපුරය": (6.7056, 80.3847), "කෑගල්ල": (7.2513, 80.3464)
}

RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

# ==================== AI Prediction Function ====================
def get_ai_prediction(summary_data):
    # Try to get API key from secrets
    try:
        api_key = st.secrets.get("GEMINI_API_KEY_1")
    except:
        api_key = None
    
    if not api_key:
        return generate_fallback_prediction(summary_data)
    
    name = summary_data.get('name', '')
    gender = summary_data.get('gender', '')
    dob = summary_data.get('dob', '')
    time = summary_data.get('time', '')
    city = summary_data.get('city', '')
    lagna = summary_data.get('lagna', '')
    nakshathra = summary_data.get('nakshathra', '')
    gana = summary_data.get('gana', '')
    yoni = summary_data.get('yoni', '')
    linga = summary_data.get('linga', '')
    ayanamsa = summary_data.get('ayanamsa', 'Lahiri')
    bhava_data = summary_data.get('bhava_data', '')
    
    salutation = "මහතා" if gender == "පිරිමි" else "මහත්මිය"
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    prompt = f"""
    ඔබ වෘත්තීය ශ්‍රී ලාංකික ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කරන්න. 
    පහත තොරතුරු අනුව ඉතා නිවැරදි සහ විස්තරාත්මක පලාපල විස්තරයක් සිංහලෙන් ලබා දෙන්න.

    **පරිශීලක තොරතුරු:**
    නම: {name}
    ස්ත්‍රී/පුරුෂ භාවය: {gender}
    උපන් දිනය: {dob}
    උපන් වේලාව: {time}
    උපන් නගරය/දිස්ත්‍රික්කය: {city}

    **ගණනය කරන ලද ජ්‍යොතිෂ දත්ත:**
    - ලග්නය: {lagna}
    - උපන් නැකත: {nakshathra}
    - ගණය: {gana}
    - යෝනිය: {yoni}
    - ලිංගය: {linga}
    - අයනාංශ පද්ධතිය: {ayanamsa}
    - ග්‍රහ පිහිටීම්: {bhava_data}

    කරුණාකර පහත සඳහන් කරුණු ඇතුළත් කරන්න:
    1. නැකතේ ගුණාංග සහ ස්වභාවය
    2. ග්‍රහ පිහිටීම් සහ ඒවායේ බලපෑම
    3. චරිතය සහ පෞරුෂත්වය
    4. අධ්‍යාපනය, වෘත්තිය, සෞඛ්‍යය
    5. ඉදිරි කාලය පිළිබඳ අනාවැකි
    6. පිළියම් සහ උපදෙස්
    """
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return generate_fallback_prediction(summary_data)

def generate_fallback_prediction(data):
    """Generate a basic prediction when AI is unavailable"""
    return f"""
    <div class='report-box'>
    <h2>🌟 {data.get('name', '')} මහත්මිය/මහතාගේ පලාපල වාර්තාව</h2>
    
    <h3>📋 මූලික තොරතුරු</h3>
    <table>
        <tr><th>ගුණාංගය</th><th>විස්තරය</th></tr>
        <tr><td>ලග්නය</td><td>{data.get('lagna', '')}</td></tr>
        <tr><td>නැකත</td><td>{data.get('nakshathra', '')}</td></tr>
        <tr><td>ගණය</td><td>{data.get('gana', '')}</td></tr>
        <tr><td>යෝනිය</td><td>{data.get('yoni', '')}</td></tr>
    </table>
    
    <h3>📖 නැකතේ ගුණාංග</h3>
    <p>ඔබගේ උපන් නැකත වන <strong>{data.get('nakshathra', '')}</strong> ඉතා සුබ නැකතකි. මෙම නැකතේ උපත ලබන අය සාමාන්‍යයෙන් බුද්ධිමත්, කාරුණික සහ සමාජගරුක පුද්ගලයන් වේ.</p>
    
    <h3>💫 චරිත ලක්ෂණ</h3>
    <p>{data.get('lagna', '')} ලග්නය සහ {data.get('nakshathra', '')} නැකතේ උපත ලැබීම නිසා ඔබ සතුව නායකත්ව ගුණාංග, ධෛර්යය සහ අන් අයට උදව් කිරීමේ හැකියාව වැඩි වශයෙන් පවතී.</p>
    
    <h3>🙏 පිළියම්</h3>
    <ul>
        <li>සෑම බ්‍රහස්පතින්දා දිනකම පන්සල් ගොස් පින්කම් කරන්න</li>
        <li>කහ පැහැති මල් පූජා කිරීම සුබයි</li>
        <li>"ඕම් ගුරුවේ නමඃ" මන්ත්‍රය දිනපතා ජප කරන්න</li>
    </ul>
    
    <p><em>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය</em></p>
    </div>
    """

# ==================== PDF Export Function (HTML-based fallback) ====================
def create_html_report(user_data, calc_result, ai_report):
    """Create HTML report (works without reportlab)"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>AstroPro SL - {user_data.get('name', '')} ගේ ජන්ම පත්‍රය</title>
        <style>
            body {{ font-family: 'Noto Sans Sinhala', 'Iskoola Pota', sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #e94560; text-align: center; }}
            h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #667eea; color: white; }}
            .footer {{ text-align: center; margin-top: 40px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <h1>☸️ AstroPro SL - ජන්ම පත්‍ර වාර්තාව</h1>
        
        <h2>📋 පුද්ගලික තොරතුරු</h2>
        <table>
            <tr><th>විස්තරය</th><th>තොරතුරු</th></tr>
            <tr><td>නම</td><td>{user_data.get('name', '')}</td></tr>
            <tr><td>ලිංගය</td><td>{user_data.get('gender', '')}</td></tr>
            <tr><td>උපන් දිනය</td><td>{user_data.get('dob', '')}</td></tr>
            <tr><td>උපන් වේලාව</td><td>{user_data.get('time', '')}</td></tr>
            <tr><td>දිස්ත්‍රික්කය</td><td>{user_data.get('city', '')}</td></tr>
        </table>
        
        <h2>🔮 ජ්‍යොතිෂ ගණනය කිරීම්</h2>
        <table>
            <tr><th>ගුණාංගය</th><th>විස්තරය</th></tr>
            <tr><td>ලග්නය</td><td>{calc_result.get('lagna', '')}</td></tr>
            <tr><td>නැකත</td><td>{calc_result.get('nakshathra', '')}</td></tr>
            <tr><td>ගණය</td><td>{calc_result.get('gana', '')}</td></tr>
            <tr><td>යෝනිය</td><td>{calc_result.get('yoni', '')}</td></tr>
            <tr><td>ලිංගය</td><td>{calc_result.get('linga', '')}</td></tr>
            <tr><td>අයනාංශය</td><td>{calc_result.get('ayanamsa', '')}</td></tr>
        </table>
        
        <h2>📜 පලාපල විස්තරය</h2>
        <div>{ai_report}</div>
        
        <div class="footer">
            <p>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය<br>
            වාර්තාව උත්පාදනය කළ දිනය: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    return html_content

# ==================== WhatsApp Share Function ====================
def create_whatsapp_message(user_data, calc_result):
    """Create WhatsApp share message"""
    message = f"""*AstroPro SL - {user_data.get('name', '')} ගේ ජන්ම පත්‍රය*

📅 *උපන් දිනය:* {user_data.get('dob', '')}
⏰ *උපන් වේලාව:* {user_data.get('time', '')}
📍 *දිස්ත්‍රික්කය:* {user_data.get('city', '')}

*ජ්‍යොතිෂ ගණනය කිරීම්:*
⭐ ලග්නය: {calc_result.get('lagna', '')}
🌙 නැකත: {calc_result.get('nakshathra', '')}
🕉️ ගණය: {calc_result.get('gana', '')}
🦁 යෝනිය: {calc_result.get('yoni', '')}

---
*AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය*
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    return message

# ==================== Calculation Function ====================
def perform_calculation(user_data, ayanamsa_system):
    """Perform astrological calculation"""
    try:
        lat, lon = DISTRICTS[user_data['city']]
        hour_utc = user_data['hour'] + user_data['minute']/60 - 5.5
        jd = swe.julday(
            user_data['dob'].year, 
            user_data['dob'].month, 
            user_data['dob'].day, 
            hour_utc
        )
        
        ayanamsa_code = get_ayanamsa_system(ayanamsa_system)
        swe.set_sid_mode(ayanamsa_code)
        
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        lagna_rashi = int(ascmc[0] / 30)
        lagna_name = RA_NAMES[lagna_rashi]
        
        planets_def = [
            ("රවි", swe.SUN), ("සඳු", swe.MOON), ("කුජ", swe.MARS),
            ("බුධ", swe.MERCURY), ("ගුරු", swe.JUPITER), ("සිකුරු", swe.VENUS),
            ("ශනි", swe.SATURN), ("රාහු", swe.MEAN_NODE)
        ]
        
        bhava_map = {i: [] for i in range(1, 13)}
        moon_lon = 0
        
        for p_name, p_id in planets_def:
            res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
            lon = res[0]
            if p_id == swe.MOON:
                moon_lon = lon
            p_bhava = get_planet_bhava(lon, houses)
            bhava_map[p_bhava].append(p_name)
        
        nak_idx = int(moon_lon / (360.0 / 27)) % 27
        nak_name = NAK_NAMES[nak_idx]
        
        gana, yoni, linga = get_nakshatra_details(nak_idx)
        
        bhava_text = "\n".join([f"{b} වන භාවය: {', '.join(p) if p else '-'}" for b, p in bhava_map.items()])
        
        calculation_result = {
            "lagna": lagna_name,
            "nakshathra": nak_name,
            "gana": gana,
            "yoni": yoni,
            "linga": linga,
            "ayanamsa": ayanamsa_system,
            "bhava_details": bhava_text,
            "bhava_map": bhava_map
        }
        
        return calculation_result
        
    except Exception as e:
        st.error(f"ගණනය කිරීමේ දෝෂයක්: {e}")
        return None

# ==================== Login/Register Page ====================
def login_page():
    st.image("https://cdn-icons-png.flaticon.com/512/2922/2922561.png", width=80)
    st.title("☸️ AstroPro SL")
    st.markdown("### ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය")
    
    tab1, tab2 = st.tabs(["🔐 පිවිසෙන්න", "📝 ලියාපදිංචි වන්න"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("පරිශීලක නම")
            password = st.text_input("මුරපදය", type="password")
            submitted = st.form_submit_button("පිවිසෙන්න")
            
            if submitted:
                if username and password:
                    success, result = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.is_admin = result.get('is_admin', False)
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.warning("කරුණාකර පරිශීලක නම සහ මුරපදය ඇතුළත් කරන්න")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("පරිශීලක නම")
            new_password = st.text_input("මුරපදය", type="password")
            confirm_password = st.text_input("මුරපදය නැවත ඇතුළත් කරන්න", type="password")
            email = st.text_input("විද්‍යුත් තැපෑල")
            phone = st.text_input("දුරකථන අංකය (විකල්ප)")
            
            submitted = st.form_submit_button("ලියාපදිංචි වන්න")
            
            if submitted:
                if not new_username or not new_password:
                    st.warning("පරිශීලක නම සහ මුරපදය අවශ්‍යයි")
                elif new_password != confirm_password:
                    st.warning("මුරපද ගැලපෙන්නේ නැත")
                elif not email:
                    st.warning("විද්‍යුත් තැපෑල අවශ්‍යයි")
                else:
                    success, message = register_user(new_username, new_password, email, phone)
                    if success:
                        st.success(message)
                        st.info("දැන් ඔබට පිවිසිය හැක")
                    else:
                        st.error(message)

# ==================== Admin Panel ====================
def admin_panel():
    st.markdown("## 👑 පරිපාලක පුවරුව")
    
    tab1, tab2 = st.tabs(["📊 පරිශීලකයන්", "📜 සියලු ගණනය කිරීම්"])
    
    with tab1:
        st.subheader("ලියාපදිංචි පරිශීලකයන්")
        users = firebase_get_data("users") or {}
        
        if users:
            user_data = []
            for username, info in users.items():
                user_data.append({
                    "පරිශීලක නම": username,
                    "විද්‍යුත් තැපෑල": info.get('email', ''),
                    "දුරකථන": info.get('phone', ''),
                    "පරිපාලක": "✔️" if info.get('is_admin') else "❌",
                    "ලියාපදිංචි වූ දිනය": info.get('created_at', '')[:10]
                })
            
            st.dataframe(user_data, use_container_width=True)
        else:
            st.info("පරිශීලකයන් නොමැත")
    
    with tab2:
        st.subheader("සියලු පරිශීලක ගණනය කිරීම්")
        users = firebase_get_data("users") or {}
        
        all_calcs = []
        for username, info in users.items():
            calcs = firebase_get_data(f"users/{username}/calculations") or {}
            for calc_id, calc in calcs.items():
                all_calcs.append({
                    "පරිශීලක": username,
                    "නම": calc.get('name', ''),
                    "ලග්නය": calc.get('lagna', ''),
                    "නැකත": calc.get('nakshathra', ''),
                    "දිනය": calc.get('timestamp', '')[:10]
                })
        
        if all_calcs:
            st.dataframe(all_calcs, use_container_width=True)
        else:
            st.info("ගණනය කිරීම් නොමැත")

# ==================== User Dashboard ====================
def user_dashboard():
    st.image("https://cdn-icons-png.flaticon.com/512/2922/2922561.png", width=60)
    st.title("☸️ AstroPro SL")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 👋 ආයුබෝවන්, {st.session_state.current_user}!")
    with col2:
        if st.button("🚪 ඉවත් වන්න"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.is_admin = False
            st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["🔮 නව ගණනය කිරීම", "📜 මගේ වාර්තා", "ℹ️ උපකාරය"])
    
    with tab1:
        st.markdown("### 📝 ඔබගේ තොරතුරු ඇතුළත් කරන්න")
        
        with st.form("calculation_form"):
            name = st.text_input("නම *", placeholder="ඔබගේ සම්පූර්ණ නම")
            gender = st.radio("ලිංගය *", ["පිරිමි", "ගැහැණු"], horizontal=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                dob = st.date_input("උපන් දිනය *", value=datetime(1995, 5, 20))
            with col2:
                hour = st.number_input("පැය (0-23)", 0, 23, 10)
            with col3:
                minute = st.number_input("මිනිත්තු (0-59)", 0, 59, 30)
            
            city = st.selectbox("දිස්ත්‍රික්කය *", list(DISTRICTS.keys()))
            
            ayanamsa = st.selectbox(
                "අයනාංශ පද්ධතිය",
                ["Lahiri (Chitrapaksha)", "Mani-Vakya", "Siddhanta", "Raman", "Krishnamurthi", "Suryasiddhanta"]
            )
            
            submitted = st.form_submit_button("🔮 කේන්දරය බලන්න", use_container_width=True)
            
            if submitted:
                if not name.strip():
                    st.error("කරුණාකර නම ඇතුළත් කරන්න")
                else:
                    with st.spinner("ගණනය කරමින්..."):
                        user_data = {
                            "name": name,
                            "gender": gender,
                            "dob": dob,
                            "hour": hour,
                            "minute": minute,
                            "city": city
                        }
                        
                        calc_result = perform_calculation(user_data, ayanamsa)
                        
                        if calc_result:
                            # Save to Firebase
                            save_data = {
                                "name": name,
                                "gender": gender,
                                "dob": dob.strftime("%Y-%m-%d"),
                                "time": f"{hour:02d}:{minute:02d}",
                                "city": city,
                                "ayanamsa": ayanamsa,
                                **calc_result
                            }
                            
                            calc_id = save_calculation_to_firebase(st.session_state.current_user, save_data)
                            
                            if calc_id:
                                st.success("✅ ගණනය කිරීම් සාර්ථකව සුරකින ලදි!")
                            else:
                                st.warning("ගණනය කිරීම් සිදු කරන ලද නමුත් සුරැකීමට නොහැකි විය")
                            
                            # Display results
                            st.markdown("---")
                            st.markdown("## 📊 ගණනය කිරීමේ ප්‍රතිඵල")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"<div class='detail-box'><b>⭐ ලග්නය</b><br>{calc_result['lagna']}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='detail-box'><b>🕉️ ගණය</b><br>{calc_result['gana']}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='detail-box'><b>⚥ ලිංගය</b><br>{calc_result['linga']}</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"<div class='detail-box'><b>🌙 නැකත</b><br>{calc_result['nakshathra']}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='detail-box'><b>🦁 යෝනිය</b><br>{calc_result['yoni']}</div>", unsafe_allow_html=True)
                            
                            st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
                            col1, col2 = st.columns(2)
                            bhava_items = list(calc_result['bhava_map'].items())
                            mid = len(bhava_items) // 2
                            
                            with col1:
                                for bhava, planets in bhava_items[:mid]:
                                    st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets) if planets else '-'}")
                            with col2:
                                for bhava, planets in bhava_items[mid:]:
                                    st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets) if planets else '-'}")
                            
                            # Store in session for AI
                            st.session_state.current_calc = {
                                "name": name,
                                "gender": gender,
                                "dob": dob.strftime("%Y-%m-%d"),
                                "time": f"{hour:02d}:{minute:02d}",
                                "city": city,
                                "lagna": calc_result['lagna'],
                                "nakshathra": calc_result['nakshathra'],
                                "gana": calc_result['gana'],
                                "yoni": calc_result['yoni'],
                                "linga": calc_result['linga'],
                                "ayanamsa": ayanamsa,
                                "bhava_data": str(calc_result['bhava_map'])
                            }
                            
                            # AI Report button
                            st.markdown("---")
                            if st.button("🤖 AI පලාපල විස්තරය ලබාගන්න", key="calc_ai_btn"):
                                with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... මොහොතක් රැඳී සිටින්න"):
                                    ai_report = get_ai_prediction(st.session_state.current_calc)
                                    st.session_state.current_ai_report = ai_report
                                    st.markdown("### 📜 AI පලාපල වාර්තාව")
                                    st.markdown(ai_report, unsafe_allow_html=True)
                                    
                                    # Share buttons
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        # PDF Download (HTML-based)
                                        html_report = create_html_report(
                                            {"name": name, "gender": gender, "dob": dob.strftime("%Y-%m-%d"), 
                                             "time": f"{hour:02d}:{minute:02d}", "city": city},
                                            calc_result, ai_report
                                        )
                                        b64 = base64.b64encode(html_report.encode()).decode()
                                        href = f'<a href="data:text/html;base64,{b64}" download="astro_report_{name}_{datetime.now().strftime("%Y%m%d")}.html"><button style="background-color:#4CAF50;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">📥 HTML Report බාගන්න</button></a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                    
                                    with col2:
                                        whatsapp_msg = create_whatsapp_message(
                                            {"name": name, "dob": dob.strftime("%Y-%m-%d"), 
                                             "time": f"{hour:02d}:{minute:02d}", "city": city},
                                            calc_result
                                        )
                                        whatsapp_url = f"https://wa.me/?text={requests.utils.quote(whatsapp_msg)}"
                                        st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">📱 WhatsApp එකට Share කරන්න</button></a>', unsafe_allow_html=True)
                                    
                                    with col3:
                                        email_body = f"{whatsapp_msg}\n\n{ai_report[:2000]}"
                                        email_url = f"mailto:?subject=AstroPro SL - {name} ගේ ජන්ම පත්‍රය&body={requests.utils.quote(email_body)}"
                                        st.markdown(f'<a href="{email_url}" target="_blank"><button style="background-color:#EA4335;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">📧 Email එකට Share කරන්න</button></a>', unsafe_allow_html=True)
                        else:
                            st.error("ගණනය කිරීම අසාර්ථක විය. කරුණාකර නැවත උත්සාහ කරන්න")
    
    with tab2:
        st.markdown("### 📜 ඔබගේ සුරැකි වාර්තා")
        
        calculations = get_user_calculations(st.session_state.current_user)
        
        if calculations:
            calc_list = []
            for calc_id, calc in calculations.items():
                calc_list.append({
                    "දිනය": calc.get('timestamp', '')[:10],
                    "නම": calc.get('name', ''),
                    "ලග්නය": calc.get('lagna', ''),
                    "නැකත": calc.get('nakshathra', ''),
                    "calc_id": calc_id
                })
            
            st.dataframe(calc_list, use_container_width=True)
        else:
            st.info("ඔබට තවමත් සුරැකි වාර්තා නොමැත. 'නව ගණනය කිරීම' ටැබයෙන් පළමු ගණනය කිරීම සිදු කරන්න.")
    
    with tab3:
        st.markdown("### ℹ️ උපකාරය සහ උපදෙස්")
        
        st.markdown("""
        #### 📖 භාවිත උපදෙස්
        
        1. **නව ගණනය කිරීම** - ඔබගේ උපන් තොරතුරු ඇතුළත් කර කේන්දරය බලන්න
        2. **AI පලාපල** - ගණනය කිරීමෙන් පසු AI බොත්තම ඔබා විස්තරාත්මක පලාපල වාර්තාවක් ලබාගන්න
        3. **HTML Report** - වාර්තාව HTML ලෙස සුරකින්න
        4. **WhatsApp Share** - වාර්තා WhatsApp මගින් බෙදාගන්න
        
        #### 🙏 පිළියම් පිළිබඳ විස්තර
        
        * **රවි පිළියම්:** ඉරිදා දිනවල තැඹිලි පැහැති මල් පූජා කිරීම
        * **සඳු පිළියම්:** සඳුදා දිනවල සුදු පැහැති ආහාර දන් දීම
        * **කුජ පිළියම්:** අඟහරුවාදා දිනවල කොත්තමල්ලි දන් දීම
        * **බුධ පිළියම්:** බදාදා දිනවල හරිත පැහැති ඇඳුම් ඇඳීම
        * **ගුරු පිළියම්:** බ්‍රහස්පතින්දා කහ පැහැති ආහාර දන් දීම
        * **සිකුරු පිළියම්:** සිකුරාදා සුදු පැහැති මල් පූජා කිරීම
        * **ශනි පිළියම්:** සෙනසුරාදා තල දන් දීම
        
        #### 📞 සම්බන්ධතා
        
        ප්‍රශ්න හෝ යෝජනා සඳහා:
        - විද්‍යුත් තැපෑල: sampathub89@gmail.com
        
        ---
        © 2026 AstroPro SL - සියලුම හිමිකම් ඇවිරිණි
        """)

# ==================== Main App ====================
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.is_admin:
            admin_panel()
        else:
            user_dashboard()

if __name__ == "__main__":
    main()
