import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

# --- Mobile Optimized Configuration ---
st.set_page_config(page_title="AstroPro SL", page_icon="☸️", layout="centered")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { max-width: 800px; margin: auto; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #4CAF50; color: white; }
    .stButton>button:hover { background-color: #45a049; }
    img { width: 100%; height: auto; }
    .report-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0; }
    
    .detail-box { 
        background-color: #e8f4f8; 
        padding: 10px; 
        border-radius: 8px; 
        margin: 5px 0; 
        text-align: center;
        font-family: 'Iskoola Pota', 'Noto Sans Sinhala', 'Arial', sans-serif; 
        font-size: 16px;           
        font-weight: bold;         
        color: #1a237e;            
        letter-spacing: 1px;       
        line-height: 1.5;          
    }
    
    .detail-box b {
        font-size: 18px;           
        color: #0d47a1;            
        display: block;            
        margin-bottom: 5px;        
    }
</style>
""", unsafe_allow_html=True)

# --- Helper: Planet to Bhava Calculation ---
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

# --- Optimized Gana, Yoni, Linga Calculation (Standardized) ---
def get_nakshatra_details(nak_idx):
    # 27 Nakshatras: [Gana, Yoni, Linga] - Standardized Table
    nak_data = {
        0: ("දේව", "අශ්වයා", "පුරුෂ"), 1: ("මනුෂ්‍ය", "ඇතා", "ස්ත්‍රී"), 2: ("රාක්ෂස", "එළුවා", "ස්ත්‍රී"),
        3: ("මනුෂ්‍ය", "සර්පයා", "පුරුෂ"), 4: ("දේව", "සර්පයා", "ස්ත්‍රී"), 5: ("මනුෂ්‍ය", "බල්ලා", "පුරුෂ"),
        6: ("රාක්ෂස", "බළලා", "ස්ත්‍රී"), 7: ("මනුෂ්‍ය", "එළුවා", "ස්ත්‍රී"), 8: ("රාක්ෂස", "බළලා", "ස්ත්‍රී"),
        9: ("දේව", "මීයා", "පුරුෂ"), 10: ("මනුෂ්‍ය", "මීයා", "පුරුෂ"), 11: ("මනුෂ්‍ය", "ගවයා", "ස්ත්‍රී"),
        12: ("රාක්ෂස", "මී හරකා", "ස්ත්‍රී"), 13: ("දේව", "කොටියා", "පුරුෂ"), 14: ("මනුෂ්‍ය", "මී හරකා", "ස්ත්‍රී"),
        15: ("රාක්ෂස", "කොටියා", "පුරුෂ"), 16: ("දේව", "මුවා", "ස්ත්‍රී"), 17: ("මනුෂ්‍ය", "මුවා", "ස්ත්‍රී"),
        18: ("රාක්ෂස", "බල්ලා", "පුරුෂ"), 19: ("දේව", "වඳුරා", "පුරුෂ"), 20: ("මනුෂ්‍ය", "මුගටියා", "පුරුෂ"),
        21: ("රාක්ෂස", "වඳුරා", "ස්ත්‍රී"), 22: ("දේව", "සිංහයා", "ස්ත්‍රී"), 23: ("මනුෂ්‍ය", "අශ්වයා", "පුරුෂ"),
        24: ("රාක්ෂස", "සිංහයා", "පුරුෂ"), 25: ("මනුෂ්‍ය", "ගවයා", "ස්ත්‍රී"), 26: ("දේව", "ඇතා", "ස්ත්‍රී")
    }
    return nak_data.get(nak_idx, ("නොදනී", "නොදනී", "නොදනී"))

# --- Send Email ---
def send_calculation_to_email(user_data, calculation_result, recipient_email="sampathub89@gmail.com"):
    try:
        sender_email = st.secrets.get("EMAIL_SENDER", "astroprosl@gmail.com")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "")
        
        if not sender_password:
            save_to_local_file(user_data, calculation_result)
            return True, "ගණනය කිරීම් සාර්ථකව ගොනුවක සුරකින ලදි"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"AstroPro SL - {user_data['name']} ගේ ජන්ම පත්‍රය"
        
        body = f"""
        🌟 AstroPro SL - ජන්ම පත්‍ර වාර්තාව 🌟
        👤 පරිශීලක නම: {user_data['name']}
        📅 උපන් දිනය: {user_data['dob']}
        ⏰ උපන් වේලාව: {user_data['time']}
        ⭐ ලග්නය: {calculation_result['lagna']}
        🌙 නැකත: {calculation_result['nakshathra']}
        🕉️ ගණය: {calculation_result['gana']}
        🦁 යෝනිය: {calculation_result['yoni']}
        ⚥ ලිංගය: {calculation_result['linga']}
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return True, "වාර්තාව සාර්ථකව sampathub89@gmail.com වෙත යවන ලදි"
    except Exception as e:
        save_to_local_file(user_data, calculation_result)
        return True, f"ගණනය කිරීම් ගොනුවක සුරකින ලදි"

def save_to_local_file(user_data, calculation_result):
    try:
        filename = f"astro_calculations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {"user": user_data, "calculation": calculation_result, "timestamp": datetime.now().isoformat()}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

# --- AI Prediction ---
def get_ai_prediction(summary_data):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2")]
    prompt = f"""
    ඔබ ප්‍රවීණ ශ්‍රී ලාංකීය ජ්‍යොතිෂවේදියෙකි. {summary_data['name']} ගේ ජන්ම පත්‍ර දත්ත මත පදනම්ව පලාපල විස්තරයක් සිංහලෙන් ලියන්න.
    දත්ත: ලග්නය: {summary_data['lagna']}, නැකත: {summary_data['nakshathra']}, ගණය: {summary_data['gana']}, යෝනිය: {summary_data['yoni']}, ලිංගය: {summary_data['linga']}
    """
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return "කණගාටුයි, AI සේවාව තාවකාලිකව කාර්යබහුලයි."

# --- UI & Logic ---
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

with st.sidebar:
    st.header("👤 පරිශීලක තොරතුරු")
    u_name = st.text_input("නම")
    u_gender = st.radio("ලිංගය", ["පිරිමි", "ගැහැණු"], horizontal=True)
    u_dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20))
    c1, c2 = st.columns(2)
    u_h = c1.number_input("පැය", 0, 23, 10)
    u_m = c2.number_input("මිනිත්තු", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

if st.button("🔮 කේන්දරය බලන්න"):
    try:
        lat, lon = DISTRICTS[u_city]
        jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, (u_h + u_m/60) - 5.5)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        # Lagna
        lagna_name = RA_NAMES[int(ascmc[0] / 30)]
        
        # Moon/Nakshatra
        res, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        moon_lon = res[0]
        # Robust Nakshatra calculation using floor to avoid float boundary errors
        nak_idx = int((moon_lon / (360.0 / 27.0)) % 27)
        nak_name = NAK_NAMES[nak_idx]
        gana, yoni, linga = get_nakshatra_details(nak_idx)
        
        # Planets
        bhava_map = {i: [] for i in range(1, 13)}
        planets_def = [("රවි", swe.SUN), ("සඳු", swe.MOON), ("කුජ", swe.MARS), ("බුධ", swe.MERCURY), 
                       ("ගුරු", swe.JUPITER), ("සිකුරු", swe.VENUS), ("ශනි", swe.SATURN), ("රාහු", swe.MEAN_NODE)]
        for p_name, p_id in planets_def:
            res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
            p_bhava = get_planet_bhava(res[0], houses)
            bhava_map[p_bhava].append(p_name)
            
        st.success(f"{u_name} ජන්ම පත්‍රය")
        
        # Store for AI
        st.session_state.astro_data = {"name": u_name, "gender": u_gender, "lagna": lagna_name, 
                                       "nakshathra": nak_name, "gana": gana, "yoni": yoni, 
                                       "linga": linga, "bhava_data": str(bhava_map)}
        st.session_state.calculation_done = True
        
        # UI Display
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='detail-box'><b>⭐ ලග්නය</b><br>{lagna_name}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='detail-box'><b>🕉️ ගණය</b><br>{gana}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='detail-box'><b>⚥ ලිංගය</b><br>{linga}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='detail-box'><b>🌙 නැකත</b><br>{nak_name}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='detail-box'><b>🦁 යෝනිය</b><br>{yoni}</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.get('calculation_done'):
    if st.button("🔮 AI පලාපල විස්තරය ලබාගන්න"):
        with st.spinner("AI විශ්ලේෂණය කරමින්..."):
            st.markdown(f"<div class='report-box'>{get_ai_prediction(st.session_state.astro_data)}</div>", unsafe_allow_html=True)
