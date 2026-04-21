import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
import requests
import json
import hashlib
import uuid
from PIL import Image
import base64
import re

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== Firebase Configuration ====================
FIREBASE_URL = "https://stationary-f85f6-default-rtdb.firebaseio.com"

# ==================== Custom CSS ====================
st.markdown("""
<style>
    /* Main container */
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 24px;
    }
    
    .main-header p {
        margin: 5px 0 0;
        font-size: 14px;
        opacity: 0.9;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        padding: 12px;
        border: none;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: scale(0.98);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Result Cards */
    .result-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        border: 1px solid #e94560;
        color: #f0f0f0;
    }
    
    .detail-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin: 8px 0;
        color: white;
        font-weight: bold;
    }
    
    .detail-card small {
        display: block;
        font-size: 12px;
        opacity: 0.8;
        margin-bottom: 5px;
    }
    
    .detail-card .value {
        font-size: 18px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
    }
    
    /* Share Buttons */
    .share-whatsapp {
        background-color: #25D366;
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        margin: 5px;
    }
    
    .share-email {
        background-color: #EA4335;
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        margin: 5px;
    }
    
    /* Login Box */
    .login-box {
        max-width: 400px;
        margin: 50px auto;
        padding: 30px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        font-size: 12px;
        color: #666;
        margin-top: 30px;
    }
    
    @media (max-width: 768px) {
        .detail-card .value {
            font-size: 14px;
        }
        .result-card {
            padding: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'calculation_result' not in st.session_state:
    st.session_state.calculation_result = None
if 'ai_report' not in st.session_state:
    st.session_state.ai_report = None
if 'show_calculation' not in st.session_state:
    st.session_state.show_calculation = False
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False

# ==================== Firebase Functions ====================
def save_calculation_to_firebase(calc_data):
    """Save calculation to Firebase (public - anyone can save)"""
    try:
        calc_id = str(uuid.uuid4())
        calc_data['calc_id'] = calc_id
        calc_data['timestamp'] = datetime.now().isoformat()
        
        # Save to public calculations
        response = requests.post(f"{FIREBASE_URL}/public_calculations.json", json=calc_data)
        
        # Also save to admin's view
        admin_data = {
            **calc_data,
            'user_ip': 'web_user'
        }
        requests.post(f"{FIREBASE_URL}/admin_calculations.json", json=admin_data)
        
        return response.status_code == 200, calc_id
    except Exception as e:
        return False, None

def get_admin_calculations():
    """Get all calculations for admin (only accessible via admin email)"""
    try:
        response = requests.get(f"{FIREBASE_URL}/admin_calculations.json")
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
        return {}
    except:
        return {}

def verify_admin(email):
    """Verify if the email is the admin email"""
    return email == "sampathub89@gmail.com"

# ==================== Astrology Calculation Functions ====================
def get_ayanamsa_system(system_name):
    ayanamsa_systems = {
        "Lahiri (Chitrapaksha)": swe.SIDM_LAHIRI,
        "Raman": swe.SIDM_RAMAN,
        "Krishnamurthi": 7,
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
        0: ("දේව ගණ", "අශ්වයා", "පුරුෂ"),
        1: ("මනුෂ්ය ගණ", "ඇතා", "ස්ත්‍රී"),
        2: ("රාක්ෂස ගණ", "එළුවා", "ස්ත්‍රී"),
        3: ("මනුෂ්ය ගණ", "සර්පයා", "පුරුෂ"),
        4: ("දේව ගණ", "සර්පයා", "පුරුෂ"),
        5: ("මනුෂ්ය ගණ", "බල්ලා", "පුරුෂ"),
        6: ("රාක්ෂස ගණ", "බල්ලා", "පුරුෂ"),
        7: ("දේව ගණ", "බැටළුවා", "පුරුෂ"),
        8: ("රාක්ෂස ගණ", "බළලා", "ස්ත්‍රී"),
        9: ("රාක්ෂස ගණ", "මීයා", "පුරුෂ"),
        10: ("මනුෂ්ය ගණ", "මීයා", "පුරුෂ"),
        11: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ"),
        12: ("දේව ගණ", "මීයා", "පුරුෂ"),
        13: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී"),
        14: ("දේව ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී"),
        15: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "පුරුෂ"),
        16: ("දේව ගණ", "මුවා", "පුරුෂ"),
        17: ("රාක්ෂස ගණ", "මුවා", "පුරුෂ"),
        18: ("රාක්ෂස ගණ", "සුනඛයා", "පුරුෂ"),
        19: ("මනුෂ්ය ගණ", "වඳුරා", "පුරුෂ"),
        20: ("මනුෂ්ය ගණ", "මුගටියා", "පුරුෂ"),
        21: ("දේව ගණ", "වඳුරා", "පුරුෂ"),
        22: ("රාක්ෂස ගණ", "සිංහයා", "ස්ත්‍රී"),
        23: ("රාක්ෂස ගණ", "අශ්වයා", "පුරුෂ"),
        24: ("මනුෂ්ය ගණ", "සිංහයා", "පුරුෂ"),
        25: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ"),
        26: ("දේව ගණ", "ඇතා", "පුරුෂ")
    }
    return nakshatra_data.get(nak_idx, ("නොදනී", "නොදනී", "නොදනී"))

# Constants
DISTRICTS = {
    "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "කළුතර": (6.5854, 79.9607),
    "මහනුවර": (7.2906, 80.6337), "මාතලේ": (7.4675, 80.6234), "නුවරඑළිය": (6.9497, 80.7891),
    "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245),
    "යාපනය": (9.6615, 80.0255), "කුරුණෑගල": (7.4863, 80.3647), "අනුරාධපුරය": (8.3114, 80.4037),
    "බදුල්ල": (6.9934, 81.0550), "රත්නපුරය": (6.7056, 80.3847), "කෑගල්ල": (7.2513, 80.3464)
}

RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

# ==================== Calculation Function ====================
def perform_calculation(name, gender, dob, hour, minute, city, ayanamsa):
    """Perform the astrological calculation"""
    try:
        lat, lon = DISTRICTS[city]
        hour_utc = hour + minute/60 - 5.5
        jd = swe.julday(dob.year, dob.month, dob.day, hour_utc)
        
        ayanamsa_code = get_ayanamsa_system(ayanamsa)
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
        
        result = {
            "name": name,
            "gender": gender,
            "dob": dob.strftime("%Y-%m-%d"),
            "time": f"{hour:02d}:{minute:02d}",
            "city": city,
            "lagna": lagna_name,
            "nakshathra": nak_name,
            "gana": gana,
            "yoni": yoni,
            "linga": linga,
            "ayanamsa": ayanamsa,
            "bhava_map": bhava_map
        }
        
        return result, None
    except Exception as e:
        return None, str(e)

# ==================== AI Prediction Function ====================
def get_ai_prediction(calc_data):
    """Get AI prediction using Gemini"""
    try:
        # Try to get API key from secrets
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except:
            api_key = None
            
        if not api_key:
            return generate_fallback_prediction(calc_data)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        ඔබ වෘත්තීය ශ්‍රී ලාංකික ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කරන්න.
        
        පහත තොරතුරු අනුව පලාපල විස්තරයක් සිංහලෙන් ලබා දෙන්න:
        
        නම: {calc_data.get('name')}
        ලග්නය: {calc_data.get('lagna')}
        නැකත: {calc_data.get('nakshathra')}
        ගණය: {calc_data.get('gana')}
        යෝනිය: {calc_data.get('yoni')}
        
        කරුණාකර පහත සඳහන් කරුණු ඇතුළත් කරන්න:
        1. නැකතේ ගුණාංග
        2. චරිත ලක්ෂණ
        3. අධ්‍යාපනය සහ වෘත්තිය
        4. සෞඛ්‍ය තත්ත්වය
        5. පිළියම් සහ උපදෙස්
        
        වාර්තාව සිංහලෙන් සහ වෘත්තීය ආකාරයෙන් ලියන්න.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return generate_fallback_prediction(calc_data)

def generate_fallback_prediction(data):
    """Fallback prediction when AI is unavailable"""
    return f"""
    <div class="result-card">
    <h3>🌟 {data.get('name', '')} මහත්මිය/මහතාගේ පලාපල වාර්තාව</h3>
    
    <h4>📋 මූලික තොරතුරු</h4>
    <p><strong>ලග්නය:</strong> {data.get('lagna', '')}<br>
    <strong>නැකත:</strong> {data.get('nakshathra', '')}<br>
    <strong>ගණය:</strong> {data.get('gana', '')}<br>
    <strong>යෝනිය:</strong> {data.get('yoni', '')}</p>
    
    <h4>📖 නැකතේ ගුණාංග</h4>
    <p>{data.get('nakshathra', '')} නැකතේ උපත ලබන අය ඉතා බුද්ධිමත්, කාරුණික සහ සමාජගරුක පුද්ගලයන් වේ. 
    ඔබ සතුව නායකත්ව ගුණාංග, ධෛර්යය සහ අන් අයට උදව් කිරීමේ හැකියාව වැඩි වශයෙන් පවතී.</p>
    
    <h4>💫 චරිත ලක්ෂණ</h4>
    <p>{data.get('lagna', '')} ලග්නය නිසා ඔබ ඉතා අවංක, කඩිසර සහ විනයගරුක පුද්ගලයෙකි. 
    ඔබගේ ජීවිතයේ ඉහළ ඉලක්ක තබා ගැනීමට සහ ඒවා සාක්ෂාත් කර ගැනීමට ඇති හැකියාව අගනේය.</p>
    
    <h4>🙏 පිළියම්</h4>
    <ul>
    <li>සෑම බ්‍රහස්පතින්දා දිනකම පන්සල් ගොස් පින්කම් කරන්න</li>
    <li>කහ පැහැති මල් පූජා කිරීම සුබයි</li>
    <li>"ඕම් ගුරුවේ නමඃ" මන්ත්‍රය දිනපතා ජප කරන්න</li>
    <li>දරුවන්ට සහ අවශ්‍යතා ඇති අයට උදව් කිරීමෙන් පින් සිද්ධ වේ</li>
    </ul>
    
    <p><em>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය</em></p>
    </div>
    """

# ==================== WhatsApp Share Function ====================
def get_whatsapp_message(calc_data):
    message = f"""*AstroPro SL - {calc_data.get('name')} ගේ ජන්ම පත්‍රය*

📅 උපන් දිනය: {calc_data.get('dob')}
⏰ උපන් වේලාව: {calc_data.get('time')}
📍 දිස්ත්‍රික්කය: {calc_data.get('city')}

*ජ්‍යොතිෂ ගණනය කිරීම්:*
⭐ ලග්නය: {calc_data.get('lagna')}
🌙 නැකත: {calc_data.get('nakshathra')}
🕉️ ගණය: {calc_data.get('gana')}
🦁 යෝනිය: {calc_data.get('yoni')}

---
*AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය*
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    return message

# ==================== Admin Panel ====================
def admin_panel():
    st.markdown('<div class="main-header"><h1>👑 පරිපාලක පුවරුව</h1><p>Admin Dashboard</p></div>', unsafe_allow_html=True)
    
    # Verify admin email
    admin_email = st.text_input("පරිපාලක විද්‍යුත් තැපෑල ඇතුළත් කරන්න", type="password")
    
    if admin_email:
        if verify_admin(admin_email):
            st.success("✅ සත්‍යාපනය සාර්ථකයි!")
            
            calculations = get_admin_calculations()
            
            if calculations:
                st.subheader(f"📊 සියලු ගණනය කිරීම් ({len(calculations)})")
                
                # Convert to list and reverse for newest first
                calc_list = []
                for calc_id, calc in calculations.items():
                    calc_list.append({"id": calc_id, "data": calc})
                calc_list.reverse()
                
                for item in calc_list[:50]:  # Show last 50
                    calc = item["data"]
                    with st.expander(f"📅 {calc.get('timestamp', '')[:10]} - {calc.get('name', '')} ({calc.get('lagna', '')})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**නම:** {calc.get('name', '')}")
                            st.write(f"**ලිංගය:** {calc.get('gender', '')}")
                            st.write(f"**උපන් දිනය:** {calc.get('dob', '')}")
                            st.write(f"**වේලාව:** {calc.get('time', '')}")
                        with col2:
                            st.write(f"**දිස්ත්‍රික්කය:** {calc.get('city', '')}")
                            st.write(f"**ලග්නය:** {calc.get('lagna', '')}")
                            st.write(f"**නැකත:** {calc.get('nakshathra', '')}")
                            st.write(f"**ගණය:** {calc.get('gana', '')}")
                        
                        st.write("**ග්‍රහ පිහිටීම්:**")
                        bhava = calc.get('bhava_map', {})
                        for b in range(1, 13):
                            planets = bhava.get(b, [])
                            if planets:
                                st.write(f"- {b} වන භාවය: {', '.join(planets)}")
            else:
                st.info("තවමත් ගණනය කිරීම් නොමැත")
        else:
            st.error("වලංගු පරිපාලක විද්‍යුත් තැපෑලක් නොවේ")

# ==================== Main Calculation Form ====================
def calculation_form():
    st.markdown('<div class="main-header"><h1>🔮 AstroPro SL</h1><p>ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය</p></div>', unsafe_allow_html=True)
    
    with st.form("calculation_form"):
        st.markdown("### 📝 ඔබගේ තොරතුරු")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("නම *", placeholder="ඔබගේ සම්පූර්ණ නම")
        with col2:
            gender = st.selectbox("ලිංගය *", ["පිරිමි", "ගැහැණු"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            dob = st.date_input("උපන් දිනය *", value=datetime(1995, 5, 20), min_value=datetime(1940, 1, 1), max_value=datetime(2050, 12, 31))
        with col2:
            hour = st.number_input("පැය (0-23)", 0, 23, 10)
        with col3:
            minute = st.number_input("මිනිත්තු (0-59)", 0, 59, 30)
        
        city = st.selectbox("දිස්ත්‍රික්කය *", list(DISTRICTS.keys()))
        ayanamsa = st.selectbox("අයනාංශ පද්ධතිය", ["Lahiri (Chitrapaksha)", "Raman", "Krishnamurthi"])
        
        submitted = st.form_submit_button("🔮 කේන්දරය ගණනය කරන්න", use_container_width=True)
        
        if submitted:
            if not name.strip():
                st.error("කරුණාකර නම ඇතුළත් කරන්න")
            else:
                with st.spinner("ගණනය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න"):
                    result, error = perform_calculation(name, gender, dob, hour, minute, city, ayanamsa)
                    
                    if result:
                        st.session_state.calculation_result = result
                        st.session_state.show_calculation = True
                        
                        # Save to Firebase
                        success, calc_id = save_calculation_to_firebase(result)
                        if success:
                            st.success("✅ ගණනය කිරීම් සාර්ථකව සුරකින ලදි!")
                        else:
                            st.warning("⚠️ ගණනය කිරීම් සිදු කරන ලද නමුත් සුරැකීමට නොහැකි විය")
                        
                        st.rerun()
                    else:
                        st.error(f"දෝෂයක්: {error}")

# ==================== Display Results ====================
def display_results():
    if st.session_state.calculation_result and st.session_state.show_calculation:
        result = st.session_state.calculation_result
        
        st.markdown("---")
        st.markdown("## 📊 ගණනය කිරීමේ ප්‍රතිඵල")
        
        # Display results in cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="detail-card">
                <small>⭐ ලග්නය</small>
                <div class="value">{result['lagna']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="detail-card">
                <small>🕉️ ගණය</small>
                <div class="value">{result['gana']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="detail-card">
                <small>🌙 නැකත</small>
                <div class="value">{result['nakshathra']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="detail-card">
                <small>🦁 යෝනිය</small>
                <div class="value">{result['yoni']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="detail-card">
                <small>⚥ ජන්ම ලිංගය</small>
                <div class="value">{result['linga']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="detail-card">
                <small>📐 අයනාංශය</small>
                <div class="value">{result['ayanamsa'][:15]}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Planet positions
        st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
        
        bhava_items = list(result['bhava_map'].items())
        mid = len(bhava_items) // 2
        
        col1, col2 = st.columns(2)
        with col1:
            for bhava, planets in bhava_items[:mid]:
                if planets:
                    st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
                else:
                    st.markdown(f"**{bhava} වන භාවය:** -")
        
        with col2:
            for bhava, planets in bhava_items[mid:]:
                if planets:
                    st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
                else:
                    st.markdown(f"**{bhava} වන භාවය:** -")
        
        # AI Report Button
        st.markdown("---")
        if st.button("🤖 AI පලාපල විස්තරය ලබාගන්න", use_container_width=True):
            with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න"):
                ai_report = get_ai_prediction(result)
                st.session_state.ai_report = ai_report
                st.rerun()
        
        # Display AI Report if available
        if st.session_state.ai_report:
            st.markdown("### 📜 AI පලාපල වාර්තාව")
            st.markdown(st.session_state.ai_report, unsafe_allow_html=True)
            
            # Share buttons
            st.markdown("---")
            st.markdown("#### 📤 බෙදාගන්න")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # HTML Report Download
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>AstroPro SL - {result['name']} ගේ වාර්තාව</title>
                <style>body{{font-family:Arial;padding:20px;}} h1{{color:#e94560;}}</style>
                </head>
                <body>
                <h1>AstroPro SL - {result['name']} ගේ ජන්ම පත්‍රය</h1>
                <h2>පුද්ගලික තොරතුරු</h2>
                <p>නම: {result['name']}<br>ලිංගය: {result['gender']}<br>උපන් දිනය: {result['dob']}<br>උපන් වේලාව: {result['time']}<br>දිස්ත්‍රික්කය: {result['city']}</p>
                <h2>ජ්‍යොතිෂ ගණනය කිරීම්</h2>
                <p>ලග්නය: {result['lagna']}<br>නැකත: {result['nakshathra']}<br>ගණය: {result['gana']}<br>යෝනිය: {result['yoni']}</p>
                <h2>පලාපල විස්තරය</h2>
                {st.session_state.ai_report}
                <hr><p>© AstroPro SL - {datetime.now().strftime('%Y-%m-%d')}</p>
                </body>
                </html>
                """
                b64 = base64.b64encode(html_content.encode()).decode()
                href = f'<a href="data:text/html;base64,{b64}" download="astro_report_{result["name"]}_{datetime.now().strftime("%Y%m%d")}.html"><button style="background-color:#4CAF50;color:white;padding:10px;border:none;border-radius:5px;cursor:pointer;width:100%;">📥 Report බාගන්න</button></a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with col2:
                whatsapp_msg = get_whatsapp_message(result)
                whatsapp_url = f"https://wa.me/?text={requests.utils.quote(whatsapp_msg)}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px;border:none;border-radius:5px;cursor:pointer;width:100%;">📱 WhatsApp</button></a>', unsafe_allow_html=True)
            
            with col3:
                email_body = f"{whatsapp_msg}\n\n{st.session_state.ai_report[:2000]}"
                email_url = f"mailto:?subject=AstroPro SL - {result['name']} ගේ වාර්තාව&body={requests.utils.quote(email_body)}"
                st.markdown(f'<a href="{email_url}" target="_blank"><button style="background-color:#EA4335;color:white;padding:10px;border:none;border-radius:5px;cursor:pointer;width:100%;">📧 Email</button></a>', unsafe_allow_html=True)
        
        # New calculation button
        if st.button("🔄 නව ගණනය කිරීමක් සඳහා", use_container_width=True):
            st.session_state.show_calculation = False
            st.session_state.calculation_result = None
            st.session_state.ai_report = None
            st.rerun()

# ==================== Main App ====================
def main():
    # Admin login option in sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("👑 පරිපාලක පුවරුව", use_container_width=True):
            st.session_state.show_admin = not st.session_state.get('show_admin', False)
    
    if st.session_state.get('show_admin', False):
        admin_panel()
    else:
        if not st.session_state.show_calculation:
            calculation_form()
        else:
            display_results()
    
    # Footer
    st.markdown("""
    <div class="footer">
        © 2026 AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය<br>
        <small>වැඩිදුර තොරතුරු සඳහා: sampathub89@gmail.com</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
