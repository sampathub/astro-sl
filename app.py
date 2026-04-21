import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
import requests
import json
import uuid
import base64
import time
import os

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    .main-header h1 { margin: 0; font-size: 24px; }
    .main-header p { margin: 5px 0 0; font-size: 14px; opacity: 0.9; }
    
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
    .stButton > button:hover { transform: scale(0.98); }
    
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
    .detail-card small { display: block; font-size: 12px; opacity: 0.8; margin-bottom: 5px; }
    .detail-card .value { font-size: 18px; }
    
    .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; margin-top: 30px; }
    
    @media (max-width: 768px) {
        .detail-card .value { font-size: 14px; }
        .result-card { padding: 15px; }
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================
if 'calculation_result' not in st.session_state:
    st.session_state.calculation_result = None
if 'ai_report' not in st.session_state:
    st.session_state.ai_report = None
if 'show_calculation' not in st.session_state:
    st.session_state.show_calculation = False
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False
if 'api_status' not in st.session_state:
    st.session_state.api_status = None

# ==================== Firebase Configuration ====================
FIREBASE_URL = "https://stationary-f85f6-default-rtdb.firebaseio.com"

def save_calculation_to_firebase(calc_data):
    try:
        calc_id = str(uuid.uuid4())
        calc_data['calc_id'] = calc_id
        calc_data['timestamp'] = datetime.now().isoformat()
        
        requests.post(f"{FIREBASE_URL}/public_calculations.json", json=calc_data)
        requests.post(f"{FIREBASE_URL}/admin_calculations.json", json=calc_data)
        return True
    except:
        return False

def get_admin_calculations():
    try:
        response = requests.get(f"{FIREBASE_URL}/admin_calculations.json")
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
        return {}
    except:
        return {}

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
        0: ("දේව ගණ", "අශ්වයා", "පුරුෂ", "කේතු", "උසස් අධ්‍යාපනය, විදේශ සංචාර, සුව කිරීමේ ශක්තිය"),
        1: ("මනුෂ්ය ගණ", "ඇතා", "ස්ත්‍රී", "සිකුරු", "සමෘද්ධිය, සැප සම්පත්, කලා ශක්තිය"),
        2: ("රාක්ෂස ගණ", "එළුවා", "ස්ත්‍රී", "සූර්ය", "ධෛර්යය, නායකත්වය, තේජස"),
        3: ("මනුෂ්ය ගණ", "සර්පයා", "පුරුෂ", "සඳු", "බුද්ධිය, කලා ශක්තිය, මානසික ශක්තිය"),
        4: ("දේව ගණ", "සර්පයා", "පුරුෂ", "අඟහරු", "ශක්තිය, තේජස, ධෛර්යය"),
        5: ("මනුෂ්ය ගණ", "බල්ලා", "පුරුෂ", "රාහු", "අධ්‍යාත්මිකත්වය, ගුප්ත විද්‍යා"),
        6: ("රාක්ෂස ගණ", "බල්ලා", "පුරුෂ", "ගුරු", "ප්‍රඥාව, දැනුම, ධර්මය"),
        7: ("දේව ගණ", "බැටළුවා", "පුරුෂ", "සෙනසුරු", "කර්මය, විනය, ඉවසීම"),
        8: ("රාක්ෂස ගණ", "බළලා", "ස්ත්‍රී", "බුධ", "වාණිජ්‍යය, ව්‍යාපාර, බුද්ධිය"),
        9: ("රාක්ෂස ගණ", "මීයා", "පුරුෂ", "කේතු", "ගුප්ත විද්‍යා, අධ්‍යාත්මය"),
        10: ("මනුෂ්ය ගණ", "මීයා", "පුරුෂ", "සිකුරු", "සෞන්දර්යය, කලාව, සැප සම්පත්"),
        11: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ", "සූර්ය", "සේවය, කැපවීම, අවංකභාවය"),
        12: ("දේව ගණ", "මීයා", "පුරුෂ", "සඳු", "මානසික ශක්තිය, සංවේදීතාව"),
        13: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී", "අඟහරු", "ධෛර්යය, ජයග්‍රහණ, ශක්තිය"),
        14: ("දේව ගණ", "ව්‍යාඝ්‍රයා", "ස්ත්‍රී", "රාහු", "අභිරහස්, ගුප්ත, පරිවර්තනය"),
        15: ("රාක්ෂස ගණ", "ව්‍යාඝ්‍රයා", "පුරුෂ", "ගුරු", "ආධ්‍යාත්මිකත්වය, ප්‍රඥාව"),
        16: ("දේව ගණ", "මුවා", "පුරුෂ", "සෙනසුරු", "ඉවසීම, ස්ථාවරත්වය, විනය"),
        17: ("රාක්ෂස ගණ", "මුවා", "පුරුෂ", "බුධ", "බුද්ධිමත්කම, කථන ශක්තිය"),
        18: ("රාක්ෂස ගණ", "සුනඛයා", "පුරුෂ", "කේතු", "මෝක්ෂය, ගැලවීම, අධ්‍යාත්මය"),
        19: ("මනුෂ්ය ගණ", "වඳුරා", "පුරුෂ", "සිකුරු", "සතුට, විනෝදය, කලාව"),
        20: ("මනුෂ්ය ගණ", "මුගටියා", "පුරුෂ", "සූර්ය", "රහස්, සැඟවුණු දේ, පර්යේෂණ"),
        21: ("දේව ගණ", "වඳුරා", "පුරුෂ", "සඳු", "සශ්‍රීකත්වය, සතුට, මිත්‍රත්වය"),
        22: ("රාක්ෂස ගණ", "සිංහයා", "ස්ත්‍රී", "අඟහරු", "ශක්තිය, බලය, නායකත්වය"),
        23: ("රාක්ෂස ගණ", "අශ්වයා", "පුරුෂ", "රාහු", "වේගය, ගතිකත්වය, අභිලාෂය"),
        24: ("මනුෂ්ය ගණ", "සිංහයා", "පුරුෂ", "ගුරු", "නායකත්වය, අධිකාරිය, ප්‍රඥාව"),
        25: ("මනුෂ්ය ගණ", "ගවයා", "පුරුෂ", "සෙනසුරු", "සේවය, කැපවීම, ස්ථාවරත්වය"),
        26: ("දේව ගණ", "ඇතා", "පුරුෂ", "බුධ", "බුද්ධිය, ප්‍රඥාව, සාර්ථකත්වය")
    }
    return nakshatra_data.get(nak_idx, ("නොදනී", "නොදනී", "නොදනී", "නොදනී", "නොදනී"))

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
    try:
        lat, lon = DISTRICTS[city]
        hour_utc = hour + minute/60 - 5.5
        jd = swe.julday(dob.year, dob.month, dob.day, hour_utc)
        
        ayanamsa_code = get_ayanamsa_system(ayanamsa)
        swe.set_sid_mode(ayanamsa_code)
        
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        lagna_rashi = int(ascmc[0] / 30)
        lagna_name = RA_NAMES[lagna_rashi]
        
        lagna_lords = ["අඟහරු", "සිකුරු", "බුධ", "සඳු", "රවි", "බුධ", "සිකුරු", "අඟහරු", "ගුරු", "සෙනසුරු", "සෙනසුරු", "ගුරු"]
        lagna_lord = lagna_lords[lagna_rashi]
        
        planets_def = [
            ("රවි (සූර්ය)", swe.SUN), 
            ("සඳු (චන්ද්‍ර)", swe.MOON), 
            ("කුජ (අඟහරු)", swe.MARS),
            ("බුධ (බුද්ධ)", swe.MERCURY), 
            ("ගුරු (බ්‍රහස්පති)", swe.JUPITER), 
            ("සිකුරු (ශුක්‍ර)", swe.VENUS),
            ("ශනි (සෙනසුරු)", swe.SATURN), 
            ("රාහු", swe.MEAN_NODE)
        ]
        
        bhava_map = {i: [] for i in range(1, 13)}
        planet_positions = {}
        planet_bhava_details = {}
        moon_lon = 0
        
        for p_name, p_id in planets_def:
            res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
            lon = res[0]
            planet_positions[p_name] = lon
            if p_id == swe.MOON:
                moon_lon = lon
            p_bhava = get_planet_bhava(lon, houses)
            bhava_map[p_bhava].append(p_name)
            planet_bhava_details[p_name] = p_bhava
        
        nak_idx = int(moon_lon / (360.0 / 27)) % 27
        nak_name = NAK_NAMES[nak_idx]
        gana, yoni, linga, nak_lord, nak_features = get_nakshatra_details(nak_idx)
        
        result = {
            "name": name, 
            "gender": gender, 
            "dob": dob.strftime("%Y-%m-%d"),
            "time": f"{hour:02d}:{minute:02d}", 
            "city": city,
            "lagna": lagna_name, 
            "lagna_lord": lagna_lord,
            "nakshathra": nak_name, 
            "nak_lord": nak_lord, 
            "nak_features": nak_features,
            "gana": gana, 
            "yoni": yoni, 
            "linga": linga,
            "ayanamsa": ayanamsa, 
            "bhava_map": bhava_map,
            "planet_bhava_details": planet_bhava_details
        }
        
        return result, None
    except Exception as e:
        return None, str(e)

# ==================== AI Prediction with Gemini API ====================
def get_available_api_keys():
    """Get all available Gemini API keys from different sources"""
    api_keys = []
    
    # Try to get from streamlit secrets
    try:
        for i in range(1, 4):
            key = st.secrets.get(f"GEMINI_API_KEY_{i}")
            if key and key != "your-gemini-api-key-here" and len(key) > 10:
                api_keys.append(key)
    except:
        pass
    
    # Try environment variables
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and env_key not in api_keys:
        api_keys.append(env_key)
    
    # If no keys found, show instructions
    if not api_keys:
        st.session_state.api_status = "no_keys"
    
    return api_keys

def get_ai_astrology_report(calc_data):
    """Send calculated data to Gemini API and get professional astrology report"""
    
    api_keys = get_available_api_keys()
    
    if not api_keys:
        return generate_detailed_report_without_ai(calc_data, "API key not configured")
    
    salutation = "මහතා" if calc_data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    # Prepare planet positions text
    planet_list = []
    for planet, bhava in calc_data.get('planet_bhava_details', {}).items():
        planet_list.append(f"   • {planet} - {bhava} වන භාවයේ")
    planet_text = "\n".join(planet_list)
    
    # Format bhava details
    bhava_list = []
    for bhava, planets in calc_data.get('bhava_map', {}).items():
        if planets:
            bhava_list.append(f"   • {bhava} වන භාවය: {', '.join(planets)}")
        else:
            bhava_list.append(f"   • {bhava} වන භාවය: කිසිදු ග්‍රහයෙක් නැත")
    bhava_text = "\n".join(bhava_list)
    
    prompt = f"""ඔබ ශ්‍රී ලංකාවේ ප්‍රමුඛතම වෛදික ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කරන්න. පහත දක්වා ඇති නිවැරදිව ගණනය කරන ලද ජ්‍යොතිෂ දත්ත මත පදනම්ව ඉතා සවිස්තරාත්මක, වෘත්තීය පලාපල වාර්තාවක් සිංහලෙන් සකස් කරන්න.

═══════════════════════════════════════
📊 ගණනය කරන ලද ජ්‍යොතිෂ දත්ත
═══════════════════════════════════════

👤 පුද්ගලික තොරතුරු:
   • නම: {calc_data.get('name')}
   • ලිංගය: {calc_data.get('gender')}
   • උපන් දිනය: {calc_data.get('dob')}
   • උපන් වේලාව: {calc_data.get('time')}
   • උපන් ස්ථානය: {calc_data.get('city')}

⭐ ලග්න තොරතුරු:
   • ලග්නය: {calc_data.get('lagna')}
   • ලග්නාධිපති ග්‍රහයා: {calc_data.get('lagna_lord')}

🌙 නැකත් තොරතුරු:
   • උපන් නැකත: {calc_data.get('nakshathra')}
   • නැකත් අධිපති ග්‍රහයා: {calc_data.get('nak_lord')}
   • නැකතේ විශේෂ ලක්ෂණ: {calc_data.get('nak_features')}
   • ගණය: {calc_data.get('gana')}
   • යෝනිය: {calc_data.get('yoni')}
   • ජන්ම ලිංගය: {calc_data.get('linga')}

🪐 ග්‍රහ පිහිටීම් (භාව අනුව):
{planet_text}

🏠 භාව වල ග්‍රහ පිහිටීම් සාරාංශය:
{bhava_text}

═══════════════════════════════════════

මෙම දත්ත මත පදනම්ව පහත සඳහන් කරුණු ඇතුළත් සම්පූර්ණ පලාපල වාර්තාවක් සිංහලෙන් ලියන්න:

1. උපන් නැකතේ ස්වභාවය සහ ගුණාංග
2. ලග්නයේ බලපෑම සහ පෞරුෂත්වය
3. අධ්‍යාපනය, බුද්ධි හැකියාව සහ වෘත්තිය
4. සමාජ සම්බන්ධතා, විවාහ සහ පවුල් ජීවිතය
5. සෞඛ්‍ය තත්ත්වය
6. ඉදිරි කාලය පිළිබඳ අනාවැකි
7. පිළියම්, මන්ත්‍ර සහ උපදෙස්

වාර්තාව ඉතා විස්තරාත්මකව, වෘත්තීයව සහ ශ්‍රී ලාංකීය ජ්‍යොතිෂ සම්ප්‍රදායට අනුකූලව ලියන්න."""

    # Try each API key
    for i, api_key in enumerate(api_keys):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response and response.text:
                st.session_state.api_status = "success"
                return f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ සම්පූර්ණ පලාපල වාර්තාව</h2>
<p><small>✨ වෛදික ජ්‍යොතිෂය මත පදනම් වූ ගණනය කිරීම් සහ AI විශ්ලේෂණය<br>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
<hr>
{response.text}
<hr>
<p style="text-align: center"><em>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය<br>
🔮 සත්‍යය සහ ධර්මය ජය වේවා!</em></p>
</div>"""
        except Exception as e:
            continue
    
    st.session_state.api_status = "failed"
    return generate_detailed_report_without_ai(calc_data, "API keys failed")

def generate_detailed_report_without_ai(calc_data, reason=""):
    """Generate detailed report without AI - based on calculated data only"""
    
    salutation = "මහතා" if calc_data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    # Prepare planet positions text
    planet_list = []
    for planet, bhava in calc_data.get('planet_bhava_details', {}).items():
        planet_list.append(f"   • {planet} - {bhava} වන භාවයේ")
    planet_text = "\n".join(planet_list)
    
    # Determine good professions based on lagna
    profession_suggestions = {
        "මේෂ": "හමුදාව, පොලිසිය, ඉංජිනේරු, ශල්ය වෛද්‍ය, ක්‍රීඩා",
        "වෘෂභ": "බැංකු, මූල්ය, කලාව, සංගීතය, ආහාරපාන කර්මාන්තය",
        "මිථුන": "මාධ්‍ය, සන්නිවේදන, ලේඛන, අලෙවිකරණ, ගුරු වෘත්තිය",
        "කටක": "සත්කාරක, ඉගැන්වීම, බැංකු, දේපළ වෙළඳාම",
        "සිංහ": "දේශපාලනය, කළමනාකරණ, රංගනය, ව්‍යාපාරික නායකත්වය",
        "කන්‍යා": "ගණකාධිකරණ, වෛද්‍ය, පර්යේෂණ, ලේඛන, සංඛ්‍යාන",
        "තුලා": "නීතිය, රාජ්‍යතාන්ත්‍රික, විනිශ්චය, කලාව, විලාසිතා",
        "වෘශ්චික": "පර්යේෂණ, රහස් පරීක්ෂණ, මනෝවිද්‍යාව, ශල්ය වෛද්‍ය",
        "ධනු": "නීතිය, ඉගැන්වීම, ප්‍රකාශන, විදේශ සේවා, සංචාරක",
        "මකර": "ඉංජිනේරු, කළමනාකරණ, දේපළ වෙළඳාම, කෘෂිකර්ම",
        "කුම්භ": "තාක්ෂණය, පර්යේෂණ, ජ්‍යොතිෂය, සමාජ සේවා",
        "මීන": "කලාව, සංගීතය, නැටුම්, අධ්‍යාත්මික, සාගර කටයුතු"
    }
    professions = profession_suggestions.get(calc_data.get('lagna', ''), "විවිධ ක්ෂේත්‍ර")
    
    # Remedies based on nakshatra lord
    remedy_suggestions = {
        "රවි": "ඉරිදා දිනවල තැඹිලි පැහැති මල් පූජා කිරීම",
        "සඳු": "සඳුදා දිනවල සුදු පැහැති ආහාර දන් දීම",
        "කුජ": "අඟහරුවාදා දිනවල කොත්තමල්ලි දන් දීම",
        "බුධ": "බදාදා දිනවල හරිත පැහැති ඇඳුම් ඇඳීම",
        "ගුරු": "බ්‍රහස්පතින්දා කහ පැහැති ආහාර දන් දීම",
        "සිකුරු": "සිකුරාදා සුදු පැහැති මල් පූජා කිරීම",
        "ශනි": "සෙනසුරාදා තල දන් දීම",
        "රාහු": "නිල් පැහැති මල් පූජා කිරීම",
        "කේතු": "රාත්‍රී කාලයේ දීප පූජා"
    }
    remedy = remedy_suggestions.get(calc_data.get('nak_lord', ''), "සතර වරම් දෙවිවරුන්ට පූජා පැවැත්වීම")
    
    report = f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ සම්පූර්ණ පලාපල වාර්තාව</h2>
<p><small>✨ වෛදික ජ්‍යොතිෂය මත පදනම් වූ ගණනය කිරීම්<br>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>

{"⚠️ " + reason if reason else ""}

<hr>

<h3>📋 1. ගණනය කරන ලද ජ්‍යොතිෂ දත්ත</h3>
<table style="width:100%; border-collapse:collapse;">
    <tr><th style="background:#e94560; padding:10px; text-align:left;">ගුණාංගය</th><th style="background:#e94560; padding:10px; text-align:left;">විස්තරය</th></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>⭐ ලග්නය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('lagna')} (අධිපති: {calc_data.get('lagna_lord')})</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🌙 උපන් නැකත</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('nakshathra')} (අධිපති: {calc_data.get('nak_lord')})</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🕉️ ගණය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('gana')}</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🦁 යෝනිය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('yoni')}</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>⚥ ජන්ම ලිංගය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('linga')}</td></tr>
</table>

<h3>🪐 2. ග්‍රහ පිහිටීම් (භාව අනුව)</h3>
<pre style="background:#0f3460; padding:15px; border-radius:10px; overflow-x:auto;">
{planet_text}
</pre>

<h3>🏠 3. භාව වල ග්‍රහ පිහිටීම්</h3>
<ul>
"""
    for bhava, planets in calc_data.get('bhava_map', {}).items():
        if planets:
            report += f"<li><strong>{bhava} වන භාවය:</strong> {', '.join(planets)}</li>"
        else:
            report += f"<li><strong>{bhava} වන භාවය:</strong> කිසිදු ග්‍රහයෙක් නැත</li>"
    
    report += f"""
</ul>

<h3>📖 4. නැකතේ ස්වභාවය</h3>
<p><strong>{calc_data.get('nakshathra')} නැකත</strong> - {calc_data.get('nak_features')}</p>
<p>{calc_data.get('nakshathra')} නැකතේ උපත ලබන අය ඉතා බුද්ධිමත්, කාරුණික, අවංක සහ ප්‍රතිපත්තිගරුක පුද්ගලයන් වේ. මෙම නැකතේ අධිපතිත්වය දරන්නේ <strong>{calc_data.get('nak_lord')}</strong> ග්‍රහයා වන අතර, {calc_data.get('gana')} සහ {calc_data.get('yoni')} යන ගුණාංග නිසා සමාජයේ ගෞරවයට පාත්‍ර වේ.</p>

<h3>💫 5. ලග්නයේ බලපෑම</h3>
<p><strong>{calc_data.get('lagna')} ලග්නය</strong> සහ <strong>{calc_data.get('lagna_lord')}</strong> ලග්නාධිපතිත්වය යටතේ උපත ලැබීම නිසා, ඔබ සතුව අතිවිශිෂ්ට නායකත්ව ගුණාංග, ධෛර්යය, ස්ථිරභාවය සහ අධිෂ්ඨාන ශක්තියක් පවතී.</p>

<h3>💼 6. සුදුසු වෘත්තීන්</h3>
<p>ඔබගේ ලග්නය {calc_data.get('lagna')} සහ නැකත {calc_data.get('nakshathra')} මත පදනම්ව පහත ක්ෂේත්‍ර සුදුසු වේ:</p>
<p><strong>{professions}</strong></p>

<h3>🙏 7. පිළියම් සහ උපදෙස්</h3>
<ul>
<li>{remedy}</li>
<li>සෑම <strong>බ්‍රහස්පතින්දා</strong> දිනකම පන්සල් ගොස් බුද්ධ පූජා පැවැත්වීම</li>
<li><strong>"ඕම් {calc_data.get('nak_lord')}වේ නමඃ"</strong> මන්ත්‍රය දිනපතා ජප කිරීම</li>
<li>කහ පැහැති මල් පූජා කිරීම සුබයි</li>
<li>දරුවන්ට සහ අවශ්‍යතා ඇති අයට උදව් කිරීමෙන් පින් සිද්ධ වේ</li>
</ul>

<hr>
<p style="text-align: center"><em>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය<br>
🔮 සත්‍යය සහ ධර්මය ජය වේවා!<br>
🌺 ආයුබෝවන්! සැම දෙයක්ම සුභ සිද්ධ වේවා!</em></p>
</div>"""
    
    return report

# ==================== Admin Panel ====================
def admin_panel():
    st.markdown('<div class="main-header"><h1>👑 පරිපාලක පුවරුව</h1><p>Admin Dashboard</p></div>', unsafe_allow_html=True)
    
    admin_email = st.text_input("පරිපාලක විද්‍යුත් තැපෑල ඇතුළත් කරන්න", type="password")
    
    if admin_email == "sampathub89@gmail.com":
        st.success("✅ සත්‍යාපනය සාර්ථකයි!")
        
        # Show API status
        st.subheader("🔑 API තත්ත්වය")
        api_keys = get_available_api_keys()
        if api_keys:
            st.success(f"✅ Gemini API යතුරු {len(api_keys)}ක් හමු විය")
        else:
            st.warning("⚠️ Gemini API යතුරක් හමු නොවීය. AI පලාපල සඳහා API key එකක් සැකසීමට පහත උපදෙස් අනුගමනය කරන්න.")
            st.info("""
            **API Key එකක් සැකසීමට:**
            1. https://aistudio.google.com/app/apikey වෙත ගොස් API key එකක් ලබා ගන්න
            2. `.streamlit/secrets.toml` ගොනුව සාදන්න:
