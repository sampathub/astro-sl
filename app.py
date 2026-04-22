import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
import requests
import json
import uuid
import base64
import os
import math

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== Initialize Swiss Ephemeris ====================
def init_swisseph():
    """Swiss Ephemeris ආරම්භ කිරීම - ephe/ ෆෝල්ඩරය සැකසීම"""
    try:
        # වත්මන් ඩිරෙක්ටරිය ලබා ගැනීම
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ephe_path = os.path.join(current_dir, "ephe")
        
        # ephe path එක පවතීදැයි පරීක්ෂා කිරීම
        if os.path.exists(ephe_path):
            swe.set_ephe_path(ephe_path)
            # Lahiri Ayanamsa පමණක් භාවිතා කරන්න
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            return True, ephe_path
        else:
            # ephe ෆෝල්ඩරය නැතිනම් default එක භාවිතා කරන්න
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            return False, "ephe folder not found"
    except Exception as e:
        return False, str(e)

# Swiss Ephemeris ආරම්භ කිරීම
EPHE_STATUS, EPHE_PATH = init_swisseph()

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
    
    .rashi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin: 15px 0;
    }
    .rashi-cell {
        background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 1px solid #e94560;
    }
    .rashi-cell strong {
        color: #e94560;
        display: block;
        margin-bottom: 5px;
    }
    
    .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; margin-top: 30px; }
    
    @media (max-width: 768px) {
        .detail-card .value { font-size: 14px; }
        .result-card { padding: 15px; }
        .rashi-grid { gap: 5px; }
        .rashi-cell { padding: 5px; font-size: 12px; }
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

# ==================== Firebase Configuration ====================
FIREBASE_URL = "https://stationary-f85f6-default-rtdb.firebaseio.com"

def save_calculation_to_firebase(calc_data):
    try:
        calc_id = str(uuid.uuid4())
        calc_data['calc_id'] = calc_id
        calc_data['timestamp'] = datetime.now().isoformat()
        requests.post(f"{FIREBASE_URL}/calculations.json", json=calc_data, timeout=5)
        return True
    except:
        return False

# ==================== Constants ====================
# රාශි නම් (12 signs)
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", 
            "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]

# රාශි අධිපති ග්‍රහයින්
RA_LORDS = ["අඟහරු", "සිකුරු", "බුධ", "සඳු", "රවි", "බුධ",
            "සිකුරු", "අඟහරු", "ගුරු", "සෙනසුරු", "සෙනසුරු", "ගුරු"]

# නැකත් නම් (27 nakshatras)
NAK_NAMES = [
    "අශ්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද",
    "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්",
    "හත", "සිත", "සා", "විසා", "අනුර", "දෙට",
    "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස",
    "පුවපුටුප", "උත්රපුටුප", "රේවතී"
]

# නැකත් අධිපති ග්‍රහයින්
NAK_LORDS = [
    "කේතු", "සිකුරු", "රවි", "සඳු", "අඟහරු", "රාහු",
    "ගුරු", "සෙනසුරු", "බුධ", "කේතු", "සිකුරු", "රවි",
    "සඳු", "අඟහරු", "රාහු", "ගුරු", "සෙනසුරු", "බුධ",
    "කේතු", "සිකුරු", "රවි", "සඳු", "අඟහරු", "රාහු",
    "ගුරු", "සෙනසුරු", "බුධ"
]

# නැකත් ගණ
NAK_GANA = [
    "දේව", "මනුෂ්ය", "රාක්ෂස", "මනුෂ්ය", "දේව", "රාක්ෂස",
    "දේව", "රාක්ෂස", "රාක්ෂස", "මනුෂ්ය", "මනුෂ්ය", "දේව",
    "රාක්ෂස", "දේව", "රාක්ෂස", "රාක්ෂස", "දේව", "රාක්ෂස",
    "රාක්ෂස", "මනුෂ්ය", "මනුෂ්ය", "දේව", "රාක්ෂස", "රාක්ෂස",
    "මනුෂ්ය", "මනුෂ්ය", "දේව"
]

# නැකත් යෝනිය
NAK_YONI = [
    "අශ්වයා", "මීයා", "ගවයා", "සර්පයා", "සර්පයා", "බල්ලා",
    "බළලා", "සිංහයා", "මීයා", "ඇතා", "බැටළුවා", "මුවා",
    "සුනඛයා", "වඳුරා", "සිංහයා", "ව්‍යාඝ්‍රයා", "මුවා", "ගවයා",
    "ව්‍යාඝ්‍රයා", "මුගටියා", "සුනඛයා", "වඳුරා", "සිංහයා", "මීයා",
    "අශ්වයා", "ඇතා", "අශ්වයා"
]

# නැකත් ජන්ම ලිංගය
NAK_LINGA = [
    "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ",
    "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "පුරුෂ", "පුරුෂ",
    "පුරුෂ", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ",
    "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ",
    "ස්ත්‍රී", "පුරුෂ", "පුරුෂ"
]

# දිස්ත්‍රික්ක සහ ඛණ්ඩාංක
DISTRICTS = {
    "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "කළුතර": (6.5854, 79.9607),
    "මහනුවර": (7.2906, 80.6337), "මාතලේ": (7.4675, 80.6234), "නුවරඑළිය": (6.9497, 80.7891),
    "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245),
    "යාපනය": (9.6615, 80.0255), "කුරුණෑගල": (7.4863, 80.3647), "අනුරාධපුරය": (8.3114, 80.4037),
    "බදුල්ල": (6.9934, 81.0550), "රත්නපුරය": (6.7056, 80.3847), "කෑගල්ල": (7.2513, 80.3464)
}

# ග්‍රහයින්ගේ නම් සහ ID
PLANETS = [
    ("රවි (සූර්ය)", swe.SUN),
    ("සඳු (චන්ද්‍ර)", swe.MOON),
    ("කුජ (අඟහරු)", swe.MARS),
    ("බුධ (බුද්ධ)", swe.MERCURY),
    ("ගුරු (බ්‍රහස්පති)", swe.JUPITER),
    ("සිකුරු (ශුක්‍ර)", swe.VENUS),
    ("ශනි (සෙනසුරු)", swe.SATURN),
    ("රාහු", swe.MEAN_NODE),
    ("කේතු", swe.TRUE_NODE)
]

# ==================== Core Calculation Functions ====================

def convert_sri_lanka_to_utc(year, month, day, hour, minute):
    """
    ශ්‍රී ලංකා වේලාව (GMT+5:30) UTC බවට පරිවර්තනය කරයි
    """
    total_local_minutes = hour * 60 + minute
    total_utc_minutes = total_local_minutes - (5 * 60 + 30)
    
    utc_day = day
    utc_month = month
    utc_year = year
    utc_hour = total_utc_minutes // 60
    utc_minute = total_utc_minutes % 60
    
    if total_utc_minutes < 0:
        total_utc_minutes += 24 * 60
        utc_day = day - 1
        utc_hour = total_utc_minutes // 60
        utc_minute = total_utc_minutes % 60
        
        if utc_day < 1:
            if month == 1:
                utc_month = 12
                utc_year = year - 1
                utc_day = 31
            elif month == 3:
                utc_month = 2
                if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                    utc_day = 29
                else:
                    utc_day = 28
            elif month in [5, 7, 10, 12]:
                utc_month = month - 1
                utc_day = 30
            else:
                utc_month = month - 1
                utc_day = 31
    
    # Julian Day ගණනය කිරීම
    jd = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0, swe.GREG_CAL)
    return jd, (utc_year, utc_month, utc_day, utc_hour, utc_minute)

def get_planet_bhava(planet_lon, cusps):
    """ග්‍රහයා පිහිටි භාවය සොයා ගනී"""
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

def get_nakshatra_from_longitude(lon):
    """දේශාංශය අනුව නැකත සොයා ගනී"""
    nak_angle = 360.0 / 27.0
    nak_index = int(lon / nak_angle) % 27
    nak_start = nak_index * nak_angle
    pada_index = int((lon - nak_start) / (nak_angle / 4)) + 1
    
    return {
        "index": nak_index,
        "name": NAK_NAMES[nak_index],
        "lord": NAK_LORDS[nak_index],
        "gana": NAK_GANA[nak_index],
        "yoni": NAK_YONI[nak_index],
        "linga": NAK_LINGA[nak_index],
        "pada": pada_index
    }

def create_rashi_chart(planet_positions, lagna_rashi_index):
    """රාශි චක්‍රය නිර්මාණය කරයි"""
    rashi_chart = {RA_NAMES[i]: {"index": i, "lord": RA_LORDS[i], "planets": []} for i in range(12)}
    
    for planet_name, data in planet_positions.items():
        rashi_name = data["rashi_name"]
        if rashi_name in rashi_chart:
            rashi_chart[rashi_name]["planets"].append(planet_name)
    
    return rashi_chart

# ==================== Main Calculation Function ====================

def perform_calculation(name, gender, dob, hour, minute, city):
    """සම්පූර්ණ ජ්‍යොතිෂ ගණනය කිරීම් සිදු කරයි"""
    try:
        # 1. UTC පරිවර්තනය
        jd, utc_info = convert_sri_lanka_to_utc(dob.year, dob.month, dob.day, hour, minute)
        
        # 2. Lahiri Ayanamsa සැකසීම (ශ්‍රී ලංකා ක්‍රමය)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # 3. ස්ථාන ඛණ්ඩාංක
        lat, lon = DISTRICTS[city]
        
        # 4. ලග්නය සහ භාව ගණනය කිරීම
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        lagna_lon = ascmc[0]
        lagna_rashi = int(lagna_lon / 30) % 12
        lagna_name = RA_NAMES[lagna_rashi]
        lagna_lord = RA_LORDS[lagna_rashi]
        lagna_degree = lagna_lon % 30
        
        # 5. ග්‍රහ පිහිටීම් ගණනය කිරීම
        planet_positions = {}
        planet_bhava_details = {}
        bhava_map = {i+1: [] for i in range(12)}
        moon_lon = 0
        
        for p_name, p_id in PLANETS:
            result, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
            lon_val = result[0]
            
            rashi_idx = int(lon_val / 30) % 12
            rashi_name = RA_NAMES[rashi_idx]
            
            planet_positions[p_name] = {
                "longitude": lon_val,
                "rashi_index": rashi_idx,
                "rashi_name": rashi_name,
                "degree": lon_val % 30
            }
            
            if p_id == swe.MOON:
                moon_lon = lon_val
            
            p_bhava = get_planet_bhava(lon_val, houses)
            planet_bhava_details[p_name] = p_bhava
            bhava_map[p_bhava].append(p_name)
        
        # 6. නැකත ගණනය කිරීම
        nakshatra = get_nakshatra_from_longitude(moon_lon)
        
        # 7. රාශි චක්‍රය
        rashi_chart = create_rashi_chart(planet_positions, lagna_rashi)
        
        result = {
            "name": name,
            "gender": gender,
            "dob": dob.strftime("%Y-%m-%d"),
            "time": f"{hour:02d}:{minute:02d}",
            "city": city,
            "lagna": lagna_name,
            "lagna_lord": lagna_lord,
            "lagna_degree": round(lagna_degree, 2),
            "nakshathra": nakshatra["name"],
            "nak_pada": nakshatra["pada"],
            "nak_lord": nakshatra["lord"],
            "nak_gana": nakshatra["gana"],
            "nak_yoni": nakshatra["yoni"],
            "nak_linga": nakshatra["linga"],
            "planet_positions": planet_positions,
            "planet_bhava_details": planet_bhava_details,
            "bhava_map": bhava_map,
            "rashi_chart": rashi_chart
        }
        
        return result, None
        
    except Exception as e:
        import traceback
        return None, f"දෝෂය: {str(e)}\n{traceback.format_exc()}"

# ==================== AI Report Functions ====================

def get_available_api_keys():
    """Gemini API keys ලබා ගැනීම"""
    api_keys = []
    try:
        for i in range(1, 4):
            key = st.secrets.get(f"GEMINI_API_KEY_{i}")
            if key and key != "your-gemini-api-key-here" and len(str(key)) > 10:
                api_keys.append(str(key))
    except:
        pass
    
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and env_key not in api_keys:
        api_keys.append(env_key)
    
    return api_keys

def get_ai_astrology_report(calc_data):
    """AI පලාපල වාර්තාව ලබා ගැනීම"""
    api_keys = get_available_api_keys()
    
    if not api_keys:
        return generate_basic_report(calc_data)
    
    salutation = "මහතා" if calc_data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    prompt = f"""ඔබ ශ්‍රී ලංකාවේ ප්‍රමුඛතම වෛදික ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කරන්න.

📊 ජ්‍යොතිෂ දත්ත:
නම: {calc_data.get('name')}
ලිංගය: {calc_data.get('gender')}
උපන් දිනය: {calc_data.get('dob')}
උපන් වේලාව: {calc_data.get('time')}
උපන් ස්ථානය: {calc_data.get('city')}

⭐ ලග්නය: {calc_data.get('lagna')} (අධිපති: {calc_data.get('lagna_lord')})
🌙 නැකත: {calc_data.get('nakshathra')} (පාදය {calc_data.get('nak_pada')}, අධිපති: {calc_data.get('nak_lord')})
🕉️ ගණය: {calc_data.get('nak_gana')}
🦁 යෝනිය: {calc_data.get('nak_yoni')}

මෙම දත්ත මත පදනම්ව:
1. නැකතේ ස්වභාවය
2. ලග්නයේ බලපෑම
3. සුදුසු වෘත්තීන්
4. පිළියම් සහ උපදෙස්

සිංහලෙන් ලියන්න."""

    for api_key in api_keys:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response and response.text:
                return f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ පලාපල වාර්තාව</h2>
<hr>
{response.text}
<hr>
<p style="text-align: center"><em>© AstroPro SL - Lahiri Ayanamsa</em></p>
</div>"""
        except:
            continue
    
    return generate_basic_report(calc_data)

def generate_basic_report(calc_data):
    """මූලික පලාපල වාර්තාව"""
    salutation = "මහතා" if calc_data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    profession_suggestions = {
        "මේෂ": "හමුදාව, පොලිසිය, ඉංජිනේරු, ශල්ය වෛද්‍ය",
        "වෘෂභ": "බැංකු, මූල්ය, කලාව, සංගීතය",
        "මිථුන": "මාධ්‍ය, සන්නිවේදන, ලේඛන, ගුරු",
        "කටක": "සත්කාරක, ඉගැන්වීම, බැංකු",
        "සිංහ": "දේශපාලනය, කළමනාකරණ, රංගනය",
        "කන්‍යා": "ගණකාධිකරණ, වෛද්‍ය, පර්යේෂණ",
        "තුලා": "නීතිය, රාජ්‍යතාන්ත්‍රික, කලාව",
        "වෘශ්චික": "පර්යේෂණ, රහස් පරීක්ෂණ",
        "ධනු": "නීතිය, ඉගැන්වීම, සංචාරක",
        "මකර": "ඉංජිනේරු, කළමනාකරණ",
        "කුම්භ": "තාක්ෂණය, පර්යේෂණ",
        "මීන": "කලාව, සංගීතය, අධ්‍යාත්මික"
    }
    professions = profession_suggestions.get(calc_data.get('lagna', ''), "විවිධ ක්ෂේත්‍ර")
    
    return f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ පලාපල වාර්තාව</h2>
<p><small>✨ Lahiri Ayanamsa - ශ්‍රී ලාංකීය ජ්‍යොතිෂ ක්‍රමය</small></p>
<hr>

<h3>📋 ජ්‍යොතිෂ දත්ත</h3>
<table style="width:100%">
    <tr><th>⭐ ලග්නය</th><td>{calc_data.get('lagna')} ({calc_data.get('lagna_lord')})</td></tr>
    <tr><th>🌙 නැකත</th><td>{calc_data.get('nakshathra')} (පාදය {calc_data.get('nak_pada')}, {calc_data.get('nak_lord')})</td></tr>
    <tr><th>🕉️ ගණය</th><td>{calc_data.get('nak_gana')}</td></tr>
    <tr><th>🦁 යෝනිය</th><td>{calc_data.get('nak_yoni')}</td></tr>
</table>

<h3>💼 සුදුසු වෘත්තීන්</h3>
<p><strong>{professions}</strong></p>

<h3>🙏 පිළියම්</h3>
<ul>
<li>"ඕම් {calc_data.get('nak_lord')}වේ නමඃ" මන්ත්‍රය ජප කිරීම</li>
<li>සෑම බ්‍රහස්පතින්දා පන්සල් යාම</li>
</ul>

<hr>
<p style="text-align: center">© AstroPro SL - ආයුබෝවන්!</p>
</div>"""

# ==================== Display Functions ====================

def display_rashi_chart(rashi_chart, lagna_name):
    """රාශි චක්‍රය ප්‍රදර්ශනය කරයි"""
    st.subheader(f"🕉️ රාශි චක්‍රය (ලග්නය: {lagna_name})")
    
    rashi_order = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා",
                   "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
    
    if lagna_name in rashi_order:
        lagna_idx = rashi_order.index(lagna_name)
        rotated_rashi = rashi_order[lagna_idx:] + rashi_order[:lagna_idx]
    else:
        rotated_rashi = rashi_order
    
    planet_symbols = {"රවි": "☀️", "සඳු": "🌙", "කුජ": "♂️", "බුධ": "☿",
                      "ගුරු": "♃", "සිකුරු": "♀️", "ශනි": "♄", "රාහු": "☊", "කේතු": "☋"}
    
    for row in range(3):
        cols = st.columns(4)
        for col in range(4):
            idx = row * 4 + col
            if idx < 12:
                rashi = rotated_rashi[idx]
                planets = rashi_chart.get(rashi, {}).get("planets", [])
                symbols = [planet_symbols.get(p.split(' (')[0], "●") for p in planets[:3]]
                display = " ".join(symbols) if symbols else "-"
                
                with cols[col]:
                    st.markdown(f'<div class="rashi-cell"><strong>{rashi}</strong><br><small>{display}</small></div>', unsafe_allow_html=True)

def display_results():
    """ප්‍රතිඵල ප්‍රදර්ශනය කරයි"""
    if not st.session_state.calculation_result:
        return
    
    result = st.session_state.calculation_result
    
    st.markdown("---")
    st.markdown("## 📊 ගණනය කිරීමේ ප්‍රතිඵල")
    
    # ප්‍රධාන කාඩ්පත්
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="detail-card"><small>⭐ ලග්නය</small><div class="value">{result["lagna"]}</div><small>{result["lagna_lord"]}</small></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="detail-card"><small>🌙 නැකත</small><div class="value">{result["nakshathra"]}</div><small>පාදය {result["nak_pada"]}</small></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="detail-card"><small>🕉️ ගණය</small><div class="value">{result["nak_gana"]}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="detail-card"><small>🦁 යෝනිය</small><div class="value">{result["nak_yoni"]}</div></div>', unsafe_allow_html=True)
    
    # රාශි චක්‍රය
    display_rashi_chart(result.get("rashi_chart", {}), result.get("lagna", ""))
    
    # භාව පිහිටීම්
    st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
    bhava_items = list(result.get("bhava_map", {}).items())
    col1, col2 = st.columns(2)
    for i, (bhava, planets) in enumerate(bhava_items):
        with col1 if i < 6 else col2:
            if planets:
                st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
            else:
                st.markdown(f"**{bhava} වන භාවය:** -")
    
    # AI Report
    if st.button("🤖 AI පලාපල විස්තරය", use_container_width=True):
        with st.spinner("AI විශ්ලේෂණය කරමින්..."):
            st.session_state.ai_report = get_ai_astrology_report(result)
            st.rerun()
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report, unsafe_allow_html=True)
    
    if st.button("🔄 නව ගණනය කිරීමක්", use_container_width=True):
        st.session_state.show_calculation = False
        st.session_state.calculation_result = None
        st.session_state.ai_report = None
        st.rerun()

# ==================== Main Form ====================

def calculation_form():
    """ප්‍රධාන ආදාන පෝරමය"""
    st.markdown('<div class="main-header"><h1>🔮 AstroPro SL</h1><p>ශ්‍රී ලාංකීය ජ්‍යොතිෂය (Lahiri Ayanamsa)</p></div>', unsafe_allow_html=True)
    
    # Swiss Ephemeris තත්ත්වය පෙන්වීම
    if EPHE_STATUS:
        st.success(f"✅ Swiss Ephemeris සක්‍රියයි - ephe files හමු විය")
    else:
        st.warning(f"⚠️ Swiss Ephemeris ephe files හමු නොවීය - ගණනය කිරීම් අඩු නිරවද්‍ය විය හැක")
    
    with st.form("calculation_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("නම *", placeholder="ඔබගේ සම්පූර්ණ නම")
        with col2:
            gender = st.selectbox("ලිංගය *", ["පිරිමි", "ගැහැණු"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            dob = st.date_input("උපන් දිනය *", value=datetime(1995, 5, 20),
                               min_value=datetime(1950, 1, 1), max_value=datetime(2040, 12, 31))
        with col2:
            hour = st.number_input("පැය (0-23)", 0, 23, 10)
        with col3:
            minute = st.number_input("මිනිත්තු (0-59)", 0, 59, 30)
        
        city = st.selectbox("දිස්ත්‍රික්කය *", list(DISTRICTS.keys()))
        
        submitted = st.form_submit_button("🔮 කේන්දරය ගණනය කරන්න", use_container_width=True)
        
        if submitted:
            if not name.strip():
                st.error("කරුණාකර නම ඇතුළත් කරන්න")
            else:
                with st.spinner("🔄 ගණනය කරමින්... (Lahiri Ayanamsa + UTC)"):
                    result, error = perform_calculation(name, gender, dob, hour, minute, city)
                    if result:
                        st.session_state.calculation_result = result
                        st.session_state.show_calculation = True
                        save_calculation_to_firebase(result)
                        st.success("✅ ගණනය කිරීම් සාර්ථකයි!")
                        st.rerun()
                    else:
                        st.error(f"දෝෂය: {error}")

# ==================== Main ====================

def main():
    with st.sidebar:
        st.markdown("### 📅 වසර පරාසය")
        st.info("1950 - 2040")
        st.markdown("---")
        if st.button("🏠 මුල් පිටුව", use_container_width=True):
            st.session_state.show_calculation = False
            st.session_state.calculation_result = None
            st.session_state.ai_report = None
            st.rerun()
    
    if not st.session_state.show_calculation:
        calculation_form()
    else:
        display_results()
    
    st.markdown("""
    <div class="footer">
        © 2026 AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය<br>
        <small>📐 Lahiri Ayanamsa | ⏰ UTC පරිවර්තනය | 📅 1950-2040</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
