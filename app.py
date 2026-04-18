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
    
    /* අකුරු පෙනුම වෙනස් කිරීමට මෙතනින් පටන් ගන්න */
    .detail-box { 
        background-color: #e8f4f8; 
        padding: 10px; 
        border-radius: 8px; 
        margin: 5px 0; 
        text-align: center;
        
        /* අකුරු වෙනස් කිරීම් */
        font-family: 'Iskoola Pota', 'Noto Sans Sinhala', 'Arial', sans-serif;  /* සිංහල ෆොන්ට් එක */
        font-size: 16px;           /* අකුරු ප්‍රමාණය (වැඩි කරන්න 20px, 24px) */
        font-weight: bold;         /* තද අකුරු */
        color: #1a237e;            /* අකුරු පාට (නිල් පැහැයට) */
        letter-spacing: 1px;       /* අකුරු අතර පරතරය */
        line-height: 1.5;          /* පේළි අතර පරතරය */
    }
    
    /* විශේෂයෙන් b tag එක (bold) වෙනස් කිරීමට */
    .detail-box b {
        font-size: 18px;           /* සිරස්තල අකුරු ප්‍රමාණය */
        color: #0d47a1;            /* සිරස්තල පාට */
        display: block;            /* නව පේළියක */
        margin-bottom: 5px;        /* පහළ පරතරය */
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

# --- Gana, Yoni, Linga Calculation (Corrected Yoni Mapping) ---
def get_nakshatra_details(nak_idx):
    # Nakshatra details: (Gana, Yoni, Linga) - Traditional Vedic Mapping
    nakshatra_data = {
        0: ("දේව ගණ", "අශ්වයා", "පුරුෂ ලිංග"),
        1: ("මනුෂ්ය ගණ", "ඇතා", "ස්ත්‍රී ලිංග"),
        2: ("රාක්ෂස ගණ", "එළුවා", "ස්ත්‍රී ලිංග"),
        3: ("මනුෂ්ය ගණ", "සර්පයා", "පුරුෂ ලිංග"),
        4: ("දේව ගණ", "සර්පයා", "ස්ත්‍රී ලිංග"),
        5: ("මනුෂ්ය ගණ", "බල්ලා", "පුරුෂ ලිංග"),
        6: ("රාක්ෂස ගණ", "බළලා", "ස්ත්‍රී ලිංග"),
        7: ("මනුෂ්ය ගණ", "එළුවා", "ස්ත්‍රී ලිංග"),
        8: ("රාක්ෂස ගණ", "බළලා", "ස්ත්‍රී ලිංග"),
        9: ("දේව ගණ", "මීයා", "පුරුෂ ලිංග"),
        10: ("මනුෂ්ය ගණ", "මීයා", "පුරුෂ ලිංග"),
        11: ("මනුෂ්ය ගණ", "ගවයා", "ස්ත්‍රී ලිංග"),
        12: ("රාක්ෂස ගණ", "මී හරකා", "ස්ත්‍රී ලිංග"),
        13: ("දේව ගණ", "කොටියා", "පුරුෂ ලිංග"),
        14: ("මනුෂ්ය ගණ", "මී හරකා", "ස්ත්‍රී ලිංග"),
        15: ("රාක්ෂස ගණ", "කොටියා", "පුරුෂ ලිංග"),
        16: ("දේව ගණ", "මුවා", "ස්ත්‍රී ලිංග"),
        17: ("මනුෂ්ය ගණ", "මුවා", "ස්ත්‍රී ලිංග"),
        18: ("රාක්ෂස ගණ", "බල්ලා", "පුරුෂ ලිංග"),
        19: ("දේව ගණ", "වඳුරා", "පුරුෂ ලිංග"),
        20: ("මනුෂ්ය ගණ", "මුගටියා", "පුරුෂ ලිංග"),
        21: ("රාක්ෂස ගණ", "වඳුරා", "ස්ත්‍රී ලිංග"),
        22: ("දේව ගණ", "සිංහයා", "ස්ත්‍රී ලිංග"),
        23: ("මනුෂ්ය ගණ", "අශ්වයා", "පුරුෂ ලිංග"),
        24: ("රාක්ෂස ගණ", "සිංහයා", "පුරුෂ ලිංග"),
        25: ("මනුෂ්ය ගණ", "ගවයා", "ස්ත්‍රී ලිංග"),
        26: ("දේව ගණ", "ඇතා", "ස්ත්‍රී ලිංග")
    }
    return nakshatra_data.get(nak_idx, ("නොදනී", "නොදනී", "නොදනී"))

# --- Send Email Function (Save to FreeBSD Server) ---
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
        
        salutation = "මහතාගේ" if user_data['gender'] == "පිරිමි" else "මහත්මියගේ"
        
        body = f"""
        🌟 AstroPro SL - ජන්ම පත්‍ර වාර්තාව 🌟
        
        👤 පරිශීලක නම: {user_data['name']}
        🚻 ලිංගය: {user_data['gender']}
        📅 උපන් දිනය: {user_data['dob']}
        ⏰ උපන් වේලාව: {user_data['time']}
        📍 දිස්ත්‍රික්කය: {user_data['city']}
        
        ========================================
        📊 ගණනය කිරීම් ප්‍රතිඵල
        ========================================
        
        ⭐ ලග්නය: {calculation_result['lagna']}
        🌙 නැකත: {calculation_result['nakshathra']}
        🕉️ ගණය: {calculation_result['gana']}
        🦁 යෝනිය: {calculation_result['yoni']}
        ⚥ ලිංගය: {calculation_result['linga']}
        
        🏠 ග්‍රහ පිහිටීම් (භාව අනුව):
        {calculation_result['bhava_details']}
        
        ========================================
        © AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය
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
        data = {
            "user": user_data,
            "calculation": calculation_result,
            "timestamp": datetime.now().isoformat()
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        with open("astro_calculations_log.json", 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')
            
    except Exception as e:
        st.error(f"ගොනුව සුරැකීමේ දෝෂයක්: {e}")

# --- AI Prediction using Gemini ---
def get_ai_prediction(summary_data):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2")]
    
    salutation = "මහතා" if summary_data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    prompt = f"""
    ඔබ ප්‍රවීණ ශ්‍රී ලාංකීය ජ්‍යොතිෂවේදියෙකි. {summary_data['name']} {salutation} ගේ පහත දත්ත මත පදනම්ව චරිතය, අධ්‍යාපනය, රැකියාව, සෞඛ්‍යය සහ විවාහය ගැන සවිස්තරාත්මක පලාපල විස්තරයක් සිංහලෙන් ලියන්න.
    
    දත්ත:
    - ලග්නය: {summary_data['lagna']}
    - නැකත: {summary_data['nakshathra']}
    - ගණය: {summary_data['gana']}
    - යෝනිය: {summary_data['yoni']}
    - ලිංගය: {summary_data['linga']}
    - ග්‍රහ පිහිටීම්: {summary_data['bhava_data']}
    """
    for key in keys:
        if not key:
            continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue
    return "කණගාටුයි, AI සේවාව තාවකාලිකව කාර්යබහුලයි. කරුණාකර පසුව නැවත උත්සාහ කරන්න."

# --- Data ---
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

# --- Initialize Session State ---
if 'form_validated' not in st.session_state:
    st.session_state.form_validated = False
if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False
if 'astro_data' not in st.session_state:
    st.session_state.astro_data = None

# --- UI Sidebar ---
with st.sidebar:
    st.header("👤 පරිශීලක තොරතුරු")
    
    u_name = st.text_input("නම *", placeholder="ඔබගේ නම ඇතුළත් කරන්න")
    
    u_gender = st.radio("ලිංගය *", ["පිරිමි", "ගැහැණු"], horizontal=True)
    
    u_dob = st.date_input(
        "උපන් දිනය *",
        value=datetime(1995, 5, 20),
        min_value=datetime(1940, 1, 1),
        max_value=datetime(2050, 12, 31)
    )
    
    c1, c2 = st.columns(2)
    u_h = c1.number_input("පැය (0-23) *", 0, 23, 10)
    u_m = c2.number_input("මිනිත්තු (0-59) *", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය *", list(DISTRICTS.keys()))
    
    st.markdown("<span class='required'>* අවශ්‍ය ක්ෂේත්‍ර</span>", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("📅 1940 සිට 2050 දක්වා උපන් අය සඳහා සහාය දක්වයි")

# --- Validation Function ---
def is_form_complete():
    if not u_name.strip():
        return False, "කරුණාකර නම ඇතුළත් කරන්න."
    if u_dob.year < 1940 or u_dob.year > 2050:
        return False, "උපන් දිනය 1940-2050 අතර විය යුතුය."
    return True, ""

# --- Main Calculation Button ---
if st.button("🔮 කේන්දරය බලන්න"):
    is_valid, error_msg = is_form_complete()
    
    if not is_valid:
        st.error(error_msg)
        st.session_state.form_validated = False
        st.session_state.calculation_done = False
    else:
        st.session_state.form_validated = True
        
        try:
            lat, lon = DISTRICTS[u_city]
            hour_utc = u_h + u_m/60 - 5.5
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, hour_utc)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
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
                "bhava_details": bhava_text,
                "bhava_map": bhava_map
            }
            
            user_data = {
                "name": u_name,
                "gender": u_gender,
                "dob": u_dob.strftime("%Y-%m-%d"),
                "time": f"{u_h:02d}:{u_m:02d}",
                "city": u_city
            }
            
            success, message = send_calculation_to_email(user_data, calculation_result)
            
            st.session_state.astro_data = {
                "name": u_name,
                "gender": u_gender,
                "lagna": lagna_name,
                "nakshathra": nak_name,
                "gana": gana,
                "yoni": yoni,
                "linga": linga,
                "bhava_data": str(bhava_map),
                "dob": u_dob.strftime("%Y-%m-%d"),
                "city": u_city,
                "time": f"{u_h:02d}:{u_m:02d}"
            }
            
            st.session_state.calculation_done = True
            
            salutation_display = "මහතාගේ" if u_gender == "පිරිමි" else "මහත්මියගේ"
            st.success(f"✨ {u_name} {salutation_display} ජන්ම පත්‍රය ✨")
            st.info(f"📧 {message}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='detail-box'><b>⭐ ලග්නය</b><br>{lagna_name}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detail-box'><b>🕉️ ගණය</b><br>{gana}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detail-box'><b>⚥ ලිංගය</b><br>{linga}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='detail-box'><b>🌙 නැකත</b><br>{nak_name}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detail-box'><b>🦁 යෝනිය</b><br>{yoni}</div>", unsafe_allow_html=True)
            
            st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
            
            col_a, col_b = st.columns(2)
            bhava_items = list(bhava_map.items())
            mid = len(bhava_items) // 2
            
            with col_a:
                for bhava, planets in bhava_items[:mid]:
                    if planets:
                        st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
                    else:
                        st.markdown(f"**{bhava} වන භාවය:** -")
            
            with col_b:
                for bhava, planets in bhava_items[mid:]:
                    if planets:
                        st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
                    else:
                        st.markdown(f"**{bhava} වන භාවය:** -")
            
            st.info("📌 වැඩිදුර විස්තර (AI පලාපල) සඳහා පහත බොත්තම ඔබන්න.")
            
        except Exception as e:
            st.error(f"දෝෂයක් ඇති විය: {e}")
            st.session_state.calculation_done = False

# --- AI Prediction Section ---
if st.session_state.calculation_done and st.session_state.astro_data:
    st.markdown("---")
    if st.button("🔮 AI පලාපල විස්තරය ලබාගන්න", key="ai_btn"):
        with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න"):
            ai_response = get_ai_prediction(st.session_state.astro_data)
            st.markdown("### 📜 AI පලාපල වාර්තාව")
            st.markdown(f"<div class='report-box'>{ai_response}</div>", unsafe_allow_html=True)
    
    st.caption("© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය")
