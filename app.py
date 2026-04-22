import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta
import google.generativeai as genai
import requests
import json
import uuid
import base64
import time
import os
import math

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
if 'api_status' not in st.session_state:
    st.session_state.api_status = None

# ==================== Firebase Configuration ====================
FIREBASE_URL = "https://stationary-f85f6-default-rtdb.firebaseio.com"

def save_calculation_to_firebase(calc_data):
    try:
        calc_id = str(uuid.uuid4())
        calc_data['calc_id'] = calc_id
        calc_data['timestamp'] = datetime.now().isoformat()
        
        requests.post(f"{FIREBASE_URL}/public_calculations.json", json=calc_data, timeout=5)
        requests.post(f"{FIREBASE_URL}/admin_calculations.json", json=calc_data, timeout=5)
        return True
    except:
        return False

def get_admin_calculations():
    try:
        response = requests.get(f"{FIREBASE_URL}/admin_calculations.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
        return {}
    except:
        return {}

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

# ==================== UTC Conversion Function ====================

def convert_sri_lanka_to_utc(year, month, day, hour, minute):
    """
    ශ්‍රී ලංකා වේලාව (GMT+5:30) UTC බවට පරිවර්තනය කරයි
    1950-2040 අතර ඕනෑම දිනයක් සඳහා වැඩ කරයි
    """
    # ශ්‍රී ලංකාව GMT+5:30 වේ
    # UTC = Local - 5:30
    
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
                # Leap year check
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
    
    # Julian Day ගණනය කිරීම (1950-2040 සඳහා නිවැරදිව)
    jd = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0)
    
    return jd, (utc_year, utc_month, utc_day, utc_hour, utc_minute)

# ==================== Lagna Calculation Functions ====================

def calculate_lagna_accurately(jd, lat, lon):
    """
    නිවැරදි ලග්නය ගණනය කිරීම
    """
    # Lahiri Ayanamsa පමණක් භාවිතා කරන්න (Sri Lankan system)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # භාව සහ ලග්නය ගණනය කිරීම
    houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
    
    # ලග්නයේ දේශාංශය (ascmc[0])
    lagna_longitude = ascmc[0]
    
    # ලග්න රාශිය (0-11)
    lagna_rashi_index = int(lagna_longitude / 30) % 12
    lagna_name = RA_NAMES[lagna_rashi_index]
    lagna_lord = RA_LORDS[lagna_rashi_index]
    
    # ලග්නයේ නිවැරදි අංශක
    lagna_degree = lagna_longitude % 30
    lagna_minute = (lagna_degree % 1) * 60
    lagna_second = (lagna_minute % 1) * 60
    
    return {
        "longitude": lagna_longitude,
        "rashi_index": lagna_rashi_index,
        "rashi_name": lagna_name,
        "rashi_lord": lagna_lord,
        "degree": int(lagna_degree),
        "minute": int(lagna_minute),
        "second": int(lagna_second),
        "raw_ascmc": ascmc,
        "raw_houses": houses
    }

# ==================== Nakshatra Calculation Functions ====================

def calculate_nakshatra_accurately(moon_longitude):
    """
    නිවැරදි නැකත ගණනය කිරීම
    එක් නැකතක කෝණය = 360/27 = 13.3333333333 අංශක
    """
    nak_angle = 360.0 / 27.0  # 13.333333333333334
    
    # නැකත් අංකය (0-26)
    nak_index = int(moon_longitude / nak_angle) % 27
    
    # නැකතේ ආරම්භක කෝණය
    nak_start = nak_index * nak_angle
    
    # පාදය ගණනය කිරීම (1-4)
    # එක් පාදයක කෝණය = nak_angle / 4 = 3.3333333333
    pada_angle = nak_angle / 4.0
    pada_index = int((moon_longitude - nak_start) / pada_angle) + 1
    
    # නැකතේ අභ්යන්තර කෝණය
    nak_internal_degree = (moon_longitude - nak_start) % nak_angle
    
    return {
        "index": nak_index,
        "name": NAK_NAMES[nak_index],
        "lord": NAK_LORDS[nak_index],
        "gana": NAK_GANA[nak_index],
        "yoni": NAK_YONI[nak_index],
        "linga": NAK_LINGA[nak_index],
        "pada": pada_index,
        "start_degree": nak_start,
        "internal_degree": nak_internal_degree
    }

# ==================== Planet Position Functions ====================

def calculate_planet_positions(jd):
    """
    සියලු ග්‍රහයින්ගේ පිහිටීම් ගණනය කිරීම
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    planet_positions = {}
    
    for planet_name, planet_id in PLANETS:
        try:
            # Siderial ගණනය කිරීම්
            result, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
            longitude = result[0]
            
            # රාශිය ගණනය කිරීම
            rashi_index = int(longitude / 30) % 12
            rashi_name = RA_NAMES[rashi_index]
            degree_in_rashi = longitude % 30
            
            planet_positions[planet_name] = {
                "longitude": longitude,
                "rashi_index": rashi_index,
                "rashi_name": rashi_name,
                "degree": degree_in_rashi,
                "raw_result": result
            }
        except Exception as e:
            planet_positions[planet_name] = {
                "longitude": 0,
                "rashi_index": 0,
                "rashi_name": "නොදනී",
                "degree": 0,
                "error": str(e)
            }
    
    return planet_positions

# ==================== Bhava Calculation Functions ====================

def calculate_bhava_positions(planet_positions, houses):
    """
    ග්‍රහයින් පිහිටි භාව ගණනය කිරීම
    """
    bhava_map = {i+1: [] for i in range(12)}
    planet_bhava_details = {}
    
    for planet_name, planet_data in planet_positions.items():
        planet_lon = planet_data["longitude"]
        
        # ග්‍රහයා පිහිටි භාවය සොයා ගැනීම
        bhava = 1
        for i in range(12):
            start = houses[i]
            end = houses[(i + 1) % 12]
            
            if start <= end:
                if start <= planet_lon < end:
                    bhava = i + 1
                    break
            else:
                if planet_lon >= start or planet_lon < end:
                    bhava = i + 1
                    break
        
        bhava_map[bhava].append(planet_name)
        planet_bhava_details[planet_name] = bhava
    
    return bhava_map, planet_bhava_details

# ==================== Rashi Chart Functions ====================

def create_rashi_chart(planet_positions, lagna_rashi_index):
    """
    රාශි චක්‍රය නිර්මාණය කිරීම
    """
    rashi_chart = {}
    
    for i in range(12):
        rashi_chart[RA_NAMES[i]] = {
            "index": i,
            "lord": RA_LORDS[i],
            "planets": [],
            "is_lagna": (i == lagna_rashi_index)
        }
    
    for planet_name, planet_data in planet_positions.items():
        if "error" not in planet_data:
            rashi_name = planet_data["rashi_name"]
            if rashi_name in rashi_chart:
                rashi_chart[rashi_name]["planets"].append(planet_name)
    
    return rashi_chart

# ==================== Year Range Validation ====================

def is_valid_year_range(year):
    """
    වසර 1950-2040 අතර දැයි පරීක්ෂා කරයි
    """
    return 1950 <= year <= 2040

def get_year_warning(year):
    """
    වසර පරාසය පිළිබඳ අනතුරු ඇඟවීම
    """
    if year < 1950:
        return f"⚠️ {year} වසර 1950 ට පෙර වේ. ගණනය කිරීම් අඩු නිරවද්‍ය විය හැක."
    elif year > 2040:
        return f"⚠️ {year} වසර 2040 ට පසු වේ. ගණනය කිරීම් අඩු නිරවද්‍ය විය හැක."
    return None

# ==================== Main Calculation Function ====================

def perform_calculation(name, gender, dob, hour, minute, city):
    """
    සම්පූර්ණ ජ්‍යොතිෂ ගණනය කිරීම් සිදු කරයි
    1950-2040 අතර ඕනෑම වසරක් සඳහා වැඩ කරයි
    """
    try:
        # වසර පරාසය පරීක්ෂා කිරීම
        year = dob.year
        year_warning = get_year_warning(year)
        
        # 1. UTC පරිවර්තනය
        jd, utc_info = convert_sri_lanka_to_utc(dob.year, dob.month, dob.day, hour, minute)
        
        # 2. ස්ථාන ඛණ්ඩාංක
        lat, lon = DISTRICTS[city]
        
        # 3. ලග්නය ගණනය කිරීම
        lagna_data = calculate_lagna_accurately(jd, lat, lon)
        
        # 4. ග්‍රහ පිහිටීම් ගණනය කිරීම
        planet_positions = calculate_planet_positions(jd)
        
        # 5. චන්ද්‍රයාගේ පිහිටීම ලබා ගැනීම
        moon_longitude = planet_positions["සඳු (චන්ද්‍ර)"]["longitude"]
        
        # 6. නැකත ගණනය කිරීම
        nakshatra_data = calculate_nakshatra_accurately(moon_longitude)
        
        # 7. භාව ගණනය කිරීම
        bhava_map, planet_bhava_details = calculate_bhava_positions(
            planet_positions, 
            lagna_data["raw_houses"]
        )
        
        # 8. රාශි චක්‍රය
        rashi_chart = create_rashi_chart(planet_positions, lagna_data["rashi_index"])
        
        # 9. ප්‍රතිඵල සකස් කිරීම
        result = {
            "name": name,
            "gender": gender,
            "dob": dob.strftime("%Y-%m-%d"),
            "dob_year": dob.year,
            "dob_month": dob.month,
            "dob_day": dob.day,
            "time": f"{hour:02d}:{minute:02d}",
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "julian_day": jd,
            "utc_time": f"{utc_info[3]:02d}:{utc_info[4]:02d} UTC",
            "year_warning": year_warning,
            
            # ලග්න තොරතුරු
            "lagna": lagna_data["rashi_name"],
            "lagna_lord": lagna_data["rashi_lord"],
            "lagna_longitude": round(lagna_data["longitude"], 4),
            "lagna_degree": lagna_data["degree"],
            "lagna_minute": lagna_data["minute"],
            "lagna_second": lagna_data["second"],
            
            # නැකත් තොරතුරු
            "nakshathra": nakshatra_data["name"],
            "nak_index": nakshatra_data["index"] + 1,
            "nak_pada": nakshatra_data["pada"],
            "nak_lord": nakshatra_data["lord"],
            "nak_gana": nakshatra_data["gana"],
            "nak_yoni": nakshatra_data["yoni"],
            "nak_linga": nakshatra_data["linga"],
            
            # ග්‍රහ පිහිටීම්
            "planet_positions": planet_positions,
            "planet_bhava_details": planet_bhava_details,
            "bhava_map": bhava_map,
            "rashi_chart": rashi_chart,
            
            # පරීක්ෂාව සඳහා raw දත්ත
            "debug_houses": lagna_data["raw_houses"].tolist() if hasattr(lagna_data["raw_houses"], 'tolist') else list(lagna_data["raw_houses"]),
            "debug_ascmc": lagna_data["raw_ascmc"].tolist() if hasattr(lagna_data["raw_ascmc"], 'tolist') else list(lagna_data["raw_ascmc"])
        }
        
        return result, None
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return None, f"දෝෂය: {str(e)}\n\n{error_details}"

# ==================== AI Prediction Functions ====================

def get_available_api_keys():
    """Get all available Gemini API keys"""
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
    """Generate AI astrology report using Gemini API"""
    
    api_keys = get_available_api_keys()
    
    if not api_keys:
        return generate_detailed_report_without_ai(calc_data)
    
    salutation = "මහතා" if calc_data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    # ග්‍රහ පිහිටීම් සකස් කිරීම
    planet_list = []
    for planet, data in calc_data.get('planet_positions', {}).items():
        if 'error' not in data:
            bhava = calc_data.get('planet_bhava_details', {}).get(planet, '?')
            planet_list.append(f"   • {planet} - {data['rashi_name']} රාශියේ, {bhava} වන භාවයේ ({data['degree']:.2f}°)")
    planet_text = "\n".join(planet_list)
    
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

🪐 ග්‍රහ පිහිටීම්:
{planet_text}

මෙම දත්ත මත පදනම්ව පහත කරුණු ඇතුළත් සවිස්තරාත්මක පලාපල වාර්තාවක් සිංහලෙන් ලියන්න:

1. උපන් නැකතේ ස්වභාවය, ගුණාංග සහ බලපෑම
2. ලග්නයේ බලපෑම සහ පෞරුෂත්වය
3. අධ්‍යාපනය, බුද්ධි හැකියාව සහ සුදුසු වෘත්තීන්
4. සමාජ සම්බන්ධතා, විවාහ සහ පවුල් ජීවිතය
5. සෞඛ්‍ය තත්ත්වය
6. ඉදිරි කාලය පිළිබඳ අනාවැකි
7. පිළියම්, මන්ත්‍ර සහ උපදෙස්

වාර්තාව ඉතා විස්තරාත්මකව, වෘත්තීයව සහ ශ්‍රී ලාංකීය ජ්‍යොතිෂ සම්ප්‍රදායට අනුකූලව ලියන්න."""

    for api_key in api_keys:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response and response.text:
                st.session_state.api_status = "success"
                return f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ සම්පූර්ණ පලාපල වාර්තාව</h2>
<p><small>✨ Lahiri Ayanamsa - ශ්‍රී ලාංකීය ජ්‍යොතිෂ ක්‍රමය<br>
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
    return generate_detailed_report_without_ai(calc_data)

def generate_detailed_report_without_ai(calc_data):
    """Generate detailed report without AI"""
    
    salutation = "මහතා" if calc_data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    profession_suggestions = {
        "මේෂ": "හමුදාව, පොලිසිය, ඉංජිනේරු, ශල්ය වෛද්‍ය, ක්‍රීඩා",
        "වෘෂභ": "බැංකු, මූල්ය, කලාව, සංගීතය, ආහාරපාන",
        "මිථුන": "මාධ්‍ය, සන්නිවේදන, ලේඛන, අලෙවිකරණ, ගුරු",
        "කටක": "සත්කාරක, ඉගැන්වීම, බැංකු, දේපළ වෙළඳාම",
        "සිංහ": "දේශපාලනය, කළමනාකරණ, රංගනය, ව්‍යාපාර",
        "කන්‍යා": "ගණකාධිකරණ, වෛද්‍ය, පර්යේෂණ, ලේඛන",
        "තුලා": "නීතිය, රාජ්‍යතාන්ත්‍රික, විනිශ්චය, කලාව",
        "වෘශ්චික": "පර්යේෂණ, රහස් පරීක්ෂණ, මනෝවිද්‍යාව",
        "ධනු": "නීතිය, ඉගැන්වීම, ප්‍රකාශන, සංචාරක",
        "මකර": "ඉංජිනේරු, කළමනාකරණ, දේපළ වෙළඳාම",
        "කුම්භ": "තාක්ෂණය, පර්යේෂණ, ජ්‍යොතිෂය",
        "මීන": "කලාව, සංගීතය, නැටුම්, අධ්‍යාත්මික"
    }
    professions = profession_suggestions.get(calc_data.get('lagna', ''), "විවිධ ක්ෂේත්‍ර")
    
    report = f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ සම්පූර්ණ පලාපල වාර්තාව</h2>
<p><small>✨ Lahiri Ayanamsa - ශ්‍රී ලාංකීය ජ්‍යොතිෂ ක්‍රමය<br>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
<hr>

<h3>📋 1. ජ්‍යොතිෂ දත්ත</h3>
<table style="width:100%; border-collapse:collapse;">
    <tr><th style="background:#e94560; padding:10px; text-align:left;">ගුණාංගය</th><th style="background:#e94560; padding:10px; text-align:left;">විස්තරය</th></tr>
    <tr><td style="padding:8px;"><strong>⭐ ලග්නය</strong></td><td style="padding:8px;">{calc_data.get('lagna')} (අධිපති: {calc_data.get('lagna_lord')})<br><small>{calc_data.get('lagna_degree', 0)}° {calc_data.get('lagna_minute', 0)}′</small></td></tr>
    <tr><td style="padding:8px;"><strong>🌙 නැකත</strong></td><td style="padding:8px;">{calc_data.get('nakshathra')} (පාදය {calc_data.get('nak_pada')})<br>අධිපති: {calc_data.get('nak_lord')}</td></tr>
    <tr><td style="padding:8px;"><strong>🕉️ ගණය</strong></td><td style="padding:8px;">{calc_data.get('nak_gana')}</td></tr>
    <tr><td style="padding:8px;"><strong>🦁 යෝනිය</strong></td><td style="padding:8px;">{calc_data.get('nak_yoni')}</td></tr>
    <tr><td style="padding:8px;"><strong>⚥ ජන්ම ලිංගය</strong></td><td style="padding:8px;">{calc_data.get('nak_linga')}</td></tr>
</table>

<h3>🪐 2. ග්‍රහ පිහිටීම්</h3>
<ul>
"""
    for planet, data in calc_data.get('planet_positions', {}).items():
        if 'error' not in data:
            bhava = calc_data.get('planet_bhava_details', {}).get(planet, '?')
            report += f"<li><strong>{planet}:</strong> {data['rashi_name']} රාශියේ - {bhava} වන භාවයේ ({data['degree']:.2f}°)</li>"
    
    report += f"""
</ul>

<h3>💼 3. සුදුසු වෘත්තීන්</h3>
<p><strong>{professions}</strong></p>

<h3>🙏 4. පිළියම් සහ උපදෙස්</h3>
<ul>
<li><strong>"ඕම් {calc_data.get('nak_lord')}වේ නමඃ"</strong> මන්ත්‍රය දිනපතා ජප කිරීම</li>
<li>සෑම බ්‍රහස්පතින්දා පන්සල් ගොස් බුද්ධ පූජා පැවැත්වීම</li>
<li>කහ පැහැති මල් පූජා කිරීම සුබයි</li>
<li>දරුවන්ට සහ අවශ්‍යතා ඇති අයට උදව් කිරීම</li>
</ul>

<hr>
<p style="text-align: center"><em>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය<br>
🔮 Lahiri Ayanamsa - UTC පරිවර්තනය<br>
🌺 ආයුබෝවන්! සැම දෙයක්ම සුභ සිද්ධ වේවා!</em></p>
</div>"""
    
    return report

# ==================== Display Functions ====================

def display_rashi_chart(rashi_chart, lagna_name):
    """රාශි චක්‍රය ප්‍රදර්ශනය කරයි"""
    st.subheader(f"🕉️ රාශි චක්‍රය (ලග්නය: {lagna_name})")
    
    # North Indian style grid - ලග්නය 1 වන ස්ථානයේ
    rashi_order = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා",
                   "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
    
    # ලග්නය 1 වන ස්ථානයට ගෙන ඒම
    if lagna_name in rashi_order:
        lagna_idx = rashi_order.index(lagna_name)
        rotated_rashi = rashi_order[lagna_idx:] + rashi_order[:lagna_idx]
    else:
        rotated_rashi = rashi_order
    
    planet_symbols = {
        "රවි": "☀️", "සඳු": "🌙", "කුජ": "♂️", "බුධ": "☿",
        "ගුරු": "♃", "සිකුරු": "♀️", "ශනි": "♄", "රාහු": "☊", "කේතු": "☋"
    }
    
    # Grid එක display කිරීම
    for row in range(3):
        cols = st.columns(4)
        for col in range(4):
            idx = row * 4 + col
            if idx < 12:
                rashi = rotated_rashi[idx]
                planets_in_rashi = rashi_chart.get(rashi, {}).get("planets", [])
                
                planet_display = []
                for p in planets_in_rashi:
                    short_name = p.split(' (')[0]
                    planet_display.append(planet_symbols.get(short_name, "●"))
                
                display_text = " ".join(planet_display[:3]) if planet_display else "-"
                
                with cols[col]:
                    st.markdown(f"""
                    <div class="rashi-cell">
                        <strong>{rashi}</strong><br>
                        <small>{display_text}</small>
                    </div>
                    """, unsafe_allow_html=True)

def display_nakshatra_details(calc_data):
    """නැකත් විස්තර ප්‍රදර්ශනය කරයි"""
    st.subheader("🌙 නැකත් විස්තර")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="detail-card">
            <small>🌟 නැකත</small>
            <div class="value">{calc_data.get('nakshathra')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="detail-card">
            <small>🕉️ ගණය</small>
            <div class="value">{calc_data.get('nak_gana')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="detail-card">
            <small>👑 නැකත් අධිපති</small>
            <div class="value">{calc_data.get('nak_lord')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="detail-card">
            <small>🔢 පාදය</small>
            <div class="value">{calc_data.get('nak_pada')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="detail-card">
            <small>🦁 යෝනිය</small>
            <div class="value">{calc_data.get('nak_yoni')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="detail-card">
            <small>⚥ ජන්ම ලිංගය</small>
            <div class="value">{calc_data.get('nak_linga')}</div>
        </div>
        """, unsafe_allow_html=True)

def display_debug_info(result):
    """දෝෂ පරීක්ෂාව සඳහා සවිස්තරාත්මක තොරතුරු ප්‍රදර්ශනය කරයි"""
    with st.expander("🔧 තාක්ෂණික තොරතුරු (Debug Info)"):
        if result.get('year_warning'):
            st.warning(result['year_warning'])
        
        st.write("### 📅 දිනය සහ වේලාව")
        st.write(f"- ශ්‍රී ලංකා වේලාව: {result.get('time', '')}")
        st.write(f"- UTC වේලාව: {result.get('utc_time', '')}")
        st.write(f"- ජූලියන් දිනය: {result.get('julian_day', 0):.6f}")
        
        st.write("### ⭐ ලග්න ගණනය කිරීම්")
        st.write(f"- ලග්න දේශාංශය: {result.get('lagna_longitude', 0)}°")
        st.write(f"- ලග්න අංශක: {result.get('lagna_degree', 0)}° {result.get('lagna_minute', 0)}′ {result.get('lagna_second', 0)}″")
        st.write(f"- ලග්න රාශිය: {result.get('lagna', '')} (අධිපති: {result.get('lagna_lord', '')})")
        
        st.write("### 🪐 ග්‍රහ දේශාංශ")
        for planet, data in result.get('planet_positions', {}).items():
            if 'error' not in data:
                st.write(f"- {planet}: {data['longitude']:.4f}° ({data['rashi_name']} රාශියේ {data['degree']:.2f}°)")

# ==================== Admin Panel ====================

def admin_panel():
    st.markdown('<div class="main-header"><h1>👑 පරිපාලක පුවරුව</h1><p>Admin Dashboard</p></div>', unsafe_allow_html=True)
    
    admin_email = st.text_input("පරිපාලක විද්‍යුත් තැපෑල", type="password")
    
    if admin_email == "sampathub89@gmail.com":
        st.success("✅ සත්‍යාපනය සාර්ථකයි!")
        
        st.subheader("🔑 API තත්ත්වය")
        api_keys = get_available_api_keys()
        if api_keys:
            st.success(f"✅ Gemini API යතුරු {len(api_keys)}ක් හමු විය")
        else:
            st.warning("⚠️ Gemini API යතුරක් හමු නොවීය")
        
        calculations = get_admin_calculations()
        if calculations:
            st.subheader(f"📊 ගණනය කිරීම් ({len(calculations)})")
            for calc_id, calc in list(calculations.items())[-10:]:
                with st.expander(f"📅 {calc.get('timestamp', '')[:10]} - {calc.get('name', '')}"):
                    st.write(f"ලග්නය: {calc.get('lagna')}, නැකත: {calc.get('nakshathra')}")
    elif admin_email:
        st.error("වලංගු පරිපාලක ඊමේල් එකක් නොවේ")

# ==================== Main Form ====================

def calculation_form():
    st.markdown('<div class="main-header"><h1>🔮 AstroPro SL</h1><p>ශ්‍රී ලාංකීය ජ්‍යොතිෂය (Lahiri Ayanamsa)</p></div>', unsafe_allow_html=True)
    
    st.info("📌 **Lahiri Ayanamsa** භාවිතා කරයි - ශ්‍රී ලංකා ජ්‍යොතිෂ ක්‍රමය\n\n"
            "⏰ UTC පරිවර්තනය ස්වයංක්‍රීයව සිදු කෙරේ\n\n"
            "📅 **1950 සිට 2040 දක්වා** වසර සඳහා නිවැරදි ගණනය කිරීම්")
    
    with st.form("calculation_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("නම *", placeholder="ඔබගේ සම්පූර්ණ නම")
        with col2:
            gender = st.selectbox("ලිංගය *", ["පිරිමි", "ගැහැණු"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            dob = st.date_input(
                "උපන් දිනය *", 
                value=datetime(1995, 5, 20),
                min_value=datetime(1950, 1, 1),
                max_value=datetime(2040, 12, 31)
            )
        with col2:
            hour = st.number_input("පැය (0-23)", 0, 23, 10)
        with col3:
            minute = st.number_input("මිනිත්තු (0-59)", 0, 59, 30)
        
        city = st.selectbox("දිස්ත්‍රික්කය *", list(DISTRICTS.keys()))
        
        # වසර පරාසය පෙන්වීම
        year = dob.year
        if year < 1950:
            st.warning(f"⚠️ {year} වසර 1950 ට පෙර වේ. ගණනය කිරීම් අඩු නිරවද්‍ය විය හැක.")
        elif year > 2040:
            st.warning(f"⚠️ {year} වසර 2040 ට පසු වේ. ගණනය කිරීම් අඩු නිරවද්‍ය විය හැක.")
        else:
            st.success(f"✅ {year} වසර සඳහා නිවැරදි ගණනය කිරීම් සිදු කෙරේ.")
        
        submitted = st.form_submit_button("🔮 කේන්දරය ගණනය කරන්න", use_container_width=True)
        
        if submitted:
            if not name.strip():
                st.error("කරුණාකර නම ඇතුළත් කරන්න")
            else:
                with st.spinner("🔄 ගණනය කරමින්... UTC පරිවර්තනය + Lahiri Ayanamsa"):
                    result, error = perform_calculation(name, gender, dob, hour, minute, city)
                    if result:
                        st.session_state.calculation_result = result
                        st.session_state.show_calculation = True
                        save_calculation_to_firebase(result)
                        st.success("✅ ගණනය කිරීම් සාර්ථකයි!")
                        st.rerun()
                    else:
                        st.error(f"දෝෂයක්: {error}")

# ==================== Display Results ====================

def display_results():
    if st.session_state.calculation_result and st.session_state.show_calculation:
        result = st.session_state.calculation_result
        
        st.markdown("---")
        st.markdown("## 📊 ගණනය කිරීමේ ප්‍රතිඵල")
        
        # වසර අනතුරු ඇඟවීම
        if result.get('year_warning'):
            st.warning(result['year_warning'])
        
        # ප්‍රධාන ප්‍රතිඵල කාඩ්පත්
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="detail-card">
                <small>⭐ ලග්නය</small>
                <div class="value">{result['lagna']}</div>
                <small>{result['lagna_lord']} අධිපති</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="detail-card">
                <small>🌙 නැකත</small>
                <div class="value">{result['nakshathra']}</div>
                <small>පාදය {result['nak_pada']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="detail-card">
                <small>🕉️ ගණය</small>
                <div class="value">{result['nak_gana']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="detail-card">
                <small>🦁 යෝනිය</small>
                <div class="value">{result['nak_yoni']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # රාශි චක්‍රය
        display_rashi_chart(result.get('rashi_chart', {}), result.get('lagna', ''))
        
        # නැකත් විස්තර
        display_nakshatra_details(result)
        
        # භාව පිහිටීම්
        st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
        
        bhava_items = list(result.get('bhava_map', {}).items())
        col1, col2 = st.columns(2)
        for i, (bhava, planets) in enumerate(bhava_items):
            with col1 if i < 6 else col2:
                if planets:
                    st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
                else:
                    st.markdown(f"**{bhava} වන භාවය:** -")
        
        # Debug information (collapsed)
        display_debug_info(result)
        
        # AI Report Button
        st.markdown("---")
        if st.button("🤖 AI පලාපල විස්තරය ලබාගන්න", use_container_width=True):
            with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න"):
                ai_report = get_ai_astrology_report(result)
                st.session_state.ai_report = ai_report
                st.rerun()
        
        if st.session_state.ai_report:
            st.markdown(st.session_state.ai_report, unsafe_allow_html=True)
        
        if st.button("🔄 නව ගණනය කිරීමක් සඳහා", use_container_width=True):
            st.session_state.show_calculation = False
            st.session_state.calculation_result = None
            st.session_state.ai_report = None
            st.rerun()

# ==================== Main ====================

def main():
    with st.sidebar:
        st.markdown("### 📅 වසර පරාසය")
        st.info("1950 - 2040")
        
        st.markdown("---")
        if st.button("👑 පරිපාලක", use_container_width=True):
            st.session_state.show_admin = not st.session_state.get('show_admin', False)
        if st.button("🏠 මුල් පිටුව", use_container_width=True):
            st.session_state.show_admin = False
            st.session_state.show_calculation = False
            st.session_state.calculation_result = None
            st.session_state.ai_report = None
            st.rerun()
    
    if st.session_state.get('show_admin', False):
        admin_panel()
    else:
        if not st.session_state.show_calculation:
            calculation_form()
        else:
            display_results()
    
    st.markdown("""
    <div class="footer">
        © 2026 AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය<br>
        <small>📐 Lahiri Ayanamsa (Chitrapaksha) | ⏰ UTC පරිවර්තනය<br>
        📅 1950 - 2040 වසර සඳහා නිවැරදි ගණනය කිරීම්<br>
        📧 sampathub89@gmail.com</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
