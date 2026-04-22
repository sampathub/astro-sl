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
import pytz

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

# නැකත් අධිපති ග්‍රහයින් (1-27)
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

# නැකත් ජන්ම ලිංගය (පුරුෂ/ස්ත්‍රී)
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

def convert_to_utc(local_datetime, local_hour, local_minute):
    """
    ශ්‍රී ලංකා වේලාව (GMT+5:30) UTC බවට පරිවර්තනය කරයි
    """
    try:
        # ශ්‍රී ලංකා timezone සකසන්න
        sri_lanka_tz = pytz.timezone('Asia/Colombo')
        
        # local datetime object එකක් සාදන්න
        local_dt = datetime(local_datetime.year, local_datetime.month, local_datetime.day, 
                           local_hour, local_minute)
        
        # timezone එක localize කරන්න
        local_dt = sri_lanka_tz.localize(local_dt)
        
        # UTC බවට පරිවර්තනය කරන්න
        utc_dt = local_dt.astimezone(pytz.UTC)
        
        # Julian Day එක ගණනය කරන්න
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, 
                        utc_dt.hour + utc_dt.minute/60.0)
        
        return jd, utc_dt
    except Exception as e:
        # Fallback: manual conversion (GMT+5:30 to UTC)
        utc_hour = local_hour - 5
        utc_minute = local_minute - 30
        if utc_minute < 0:
            utc_minute += 60
            utc_hour -= 1
        if utc_hour < 0:
            utc_hour += 24
            utc_day = local_datetime.day - 1
        else:
            utc_day = local_datetime.day
        
        jd = swe.julday(local_datetime.year, local_datetime.month, utc_day, 
                        utc_hour + utc_minute/60.0)
        return jd, None

def get_planet_bhava(planet_lon, cusps):
    """
    ග්‍රහයා පිහිටි භාවය සොයා ගනී
    """
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        
        # භාවයන් 0-360 අතර වේ
        if start <= end:
            if start <= planet_lon < end:
                return i + 1
        else:
            # 0 ඉක්මවන අවස්ථාව
            if planet_lon >= start or planet_lon < end:
                return i + 1
    return 1

def get_nakshatra_from_longitude(lon):
    """
    දේශාංශය අනුව නැකත සොයා ගනී (0-360)
    එක් නැකතක කෝණය = 360/27 = 13.3333333333 අංශක
    """
    nak_angle = 360.0 / 27.0  # 13.3333333333
    nak_index = int(lon / nak_angle) % 27
    
    # නැකතේ ආරම්භක කෝණය සහ අවසාන කෝණය
    nak_start = nak_index * nak_angle
    nak_end = nak_start + nak_angle
    
    # පාදය ගණනය කිරීම (1-4)
    pada_index = int((lon - nak_start) / (nak_angle / 4)) + 1
    
    return nak_index, pada_index, nak_start, nak_end

def calculate_rashi_chart(planet_longitudes, lagna_rashi):
    """
    රාශි චක්‍රය සකස් කරයි
    """
    # රාශි 12 ක් සඳහා හිස් අරාවක්
    rashi_chart = {i+1: {"sign": RA_NAMES[i], "lord": RA_LORDS[i], "planets": []} 
                   for i in range(12)}
    
    # ලග්නය සැකසීම - ලග්නය 1 වන භාවය වේ
    lagnaa_index = lagna_rashi
    
    # ග්‍රහයින් රාශි වලට යොදන්න
    for planet_name, lon in planet_longitudes.items():
        rashi_index = int(lon / 30) % 12
        rashi_chart[rashi_index + 1]["planets"].append(planet_name)
    
    return rashi_chart

# ==================== Main Calculation Function ====================

def perform_calculation(name, gender, dob, hour, minute, city):
    """
    සම්පූර්ණ ජ්‍යොතිෂ ගණනය කිරීම් සිදු කරයි
    ශ්‍රී ලංකාවේ භාවිතා වන Lahiri Ayanamsa පමණක් භාවිතා කරයි
    UTC වලට පරිවර්තනය කර ගණනය කරයි
    """
    try:
        # 1. UTC බවට පරිවර්තනය කර Julian Day ලබා ගන්න
        jd, utc_dt = convert_to_utc(dob, hour, minute)
        
        # 2. Lahiri Ayanamsa පමණක් භාවිතා කරන්න (Sri Lankan system)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # 3. දිස්ත්‍රික්කයේ ඛණ්ඩාංක ලබා ගන්න
        lat, lon = DISTRICTS[city]
        
        # 4. භාව සහ ලග්නය ගණනය කිරීම
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        # 5. ලග්න රාශිය (ascmc[0] = Lagna longitude)
        lagna_lon = ascmc[0]
        lagna_rashi = int(lagna_lon / 30) % 12
        lagna_name = RA_NAMES[lagna_rashi]
        lagna_lord = RA_LORDS[lagna_rashi]
        
        # 6. සියලු ග්‍රහයින්ගේ පිහිටීම් ගණනය කිරීම
        planet_longitudes = {}
        planet_bhava_details = {}
        bhava_map = {i+1: [] for i in range(12)}
        
        moon_lon = 0
        
        for p_name, p_id in PLANETS:
            # Siderial ගණනය කිරීම් සඳහා FLG_SIDEREAL භාවිතා කරන්න
            res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
            lon = res[0]
            planet_longitudes[p_name] = lon
            
            if p_id == swe.MOON:
                moon_lon = lon
            
            # ග්‍රහයා පිහිටි භාවය
            p_bhava = get_planet_bhava(lon, houses)
            planet_bhava_details[p_name] = p_bhava
            bhava_map[p_bhava].append(p_name)
        
        # 7. නැකත ගණනය කිරීම (චන්ද්‍රයාගේ පිහිටීම අනුව)
        nak_index, pada_index, nak_start, nak_end = get_nakshatra_from_longitude(moon_lon)
        nak_name = NAK_NAMES[nak_index]
        nak_lord = NAK_LORDS[nak_index]
        nak_gana = NAK_GANA[nak_index]
        nak_yoni = NAK_YONI[nak_index]
        nak_linga = NAK_LINGA[nak_index]
        
        # 8. රාශි චක්‍රය ගණනය කිරීම
        rashi_chart = calculate_rashi_chart(planet_longitudes, lagna_rashi)
        
        # 9. ප්‍රතිඵල සකස් කිරීම
        result = {
            "name": name,
            "gender": gender,
            "dob": dob.strftime("%Y-%m-%d"),
            "time": f"{hour:02d}:{minute:02d}",
            "time_utc": utc_dt.strftime("%Y-%m-%d %H:%M:%S") if utc_dt else "Calculated",
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "julian_day": jd,
            "lagna": lagna_name,
            "lagna_lord": lagna_lord,
            "lagna_lon": round(lagna_lon, 2),
            "nakshathra": nak_name,
            "nak_index": nak_index + 1,
            "nak_pada": pada_index,
            "nak_lord": nak_lord,
            "nak_gana": nak_gana,
            "nak_yoni": nak_yoni,
            "nak_linga": nak_linga,
            "planet_longitudes": planet_longitudes,
            "planet_bhava_details": planet_bhava_details,
            "bhava_map": bhava_map,
            "rashi_chart": rashi_chart,
            "houses": houses.tolist() if hasattr(houses, 'tolist') else list(houses),
            "ascmc": ascmc.tolist() if hasattr(ascmc, 'tolist') else list(ascmc)
        }
        
        return result, None
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return None, f"දෝෂය: {str(e)}\n{error_details}"

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
    
    # Prepare planet positions
    planet_list = []
    for planet, bhava in calc_data.get('planet_bhava_details', {}).items():
        lon = calc_data.get('planet_longitudes', {}).get(planet, 0)
        rashi = RA_NAMES[int(lon / 30) % 12]
        planet_list.append(f"   • {planet} - {rashi} රාශියේ, {bhava} වන භාවයේ")
    planet_text = "\n".join(planet_list)
    
    prompt = f"""ඔබ ශ්‍රී ලංකාවේ ප්‍රමුඛතම වෛදික ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කරන්න. පහත දක්වා ඇති නිවැරදිව ගණනය කරන ලද ජ්‍යොතිෂ දත්ත මත පදනම්ව ඉතා සවිස්තරාත්මක, වෘත්තීය පලාපල වාර්තාවක් සිංහලෙන් සකස් කරන්න.

═══════════════════════════════════════
📊 ගණනය කරන ලද ජ්‍යොතිෂ දත්ත
═══════════════════════════════════════

👤 පුද්ගලික තොරතුරු:
   • නම: {calc_data.get('name')}
   • ලිංගය: {calc_data.get('gender')}
   • උපන් දිනය: {calc_data.get('dob')}
   • උපන් වේලාව: {calc_data.get('time')} (ශ්‍රී ලංකාව)
   • උපන් ස්ථානය: {calc_data.get('city')}

⭐ ලග්න තොරතුරු:
   • ලග්නය: {calc_data.get('lagna')}
   • ලග්නාධිපති ග්‍රහයා: {calc_data.get('lagna_lord')}

🌙 නැකත් තොරතුරු:
   • උපන් නැකත: {calc_data.get('nakshathra')} (පාදය {calc_data.get('nak_pada')})
   • නැකත් අධිපති ග්‍රහයා: {calc_data.get('nak_lord')}
   • ගණය: {calc_data.get('nak_gana')}
   • යෝනිය: {calc_data.get('nak_yoni')}
   • ජන්ම ලිංගය: {calc_data.get('nak_linga')}

🪐 ග්‍රහ පිහිටීම්:
{planet_text}

═══════════════════════════════════════

මෙම දත්ත මත පදනම්ව පහත සඳහන් කරුණු ඇතුළත් සම්පූර්ණ පලාපල වාර්තාවක් ලියන්න:

1. උපන් නැකතේ ස්වභාවය, ගුණාංග සහ එහි බලපෑම
2. ලග්නයේ බලපෑම සහ පෞරුෂත්වය
3. අධ්‍යාපනය, බුද්ධි හැකියාව සහ සුදුසු වෘත්තීන්
4. සමාජ සම්බන්ධතා, විවාහ සහ පවුල් ජීවිතය
5. සෞඛ්‍ය තත්ත්වය සහ විශේෂ සැලකිල්ල
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
<p><small>✨ වෛදික ජ්‍යොතිෂය මත පදනම් වූ ගණනය කිරීම් (Lahiri Ayanamsa)<br>
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
    
    # Profession suggestions based on lagna
    profession_suggestions = {
        "මේෂ": "හමුදාව, පොලිසිය, ඉංජිනේරු, ශල්ය වෛද්‍ය, ක්‍රීඩා, ව්‍යාපාර",
        "වෘෂභ": "බැංකු, මූල්ය, කලාව, සංගීතය, ආහාරපාන කර්මාන්තය",
        "මිථුන": "මාධ්‍ය, සන්නිවේදන, ලේඛන, අලෙවිකරණ, ගුරු වෘත්තිය",
        "කටක": "සත්කාරක, ඉගැන්වීම, බැංකු, දේපළ වෙළඳාම, සෞඛ්‍ය",
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
    
    report = f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ සම්පූර්ණ පලාපල වාර්තාව</h2>
<p><small>✨ වෛදික ජ්‍යොතිෂය මත පදනම් වූ ගණනය කිරීම් (Lahiri Ayanamsa)<br>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
<hr>

<h3>📋 1. ගණනය කරන ලද ජ්‍යොතිෂ දත්ත</h3>
<table style="width:100%; border-collapse:collapse;">
    <tr><th style="background:#e94560; padding:10px; text-align:left;">ගුණාංගය</th><th style="background:#e94560; padding:10px; text-align:left;">විස්තරය</th></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>⭐ ලග්නය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('lagna')} (අධිපති: {calc_data.get('lagna_lord')})</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🌙 උපන් නැකත</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('nakshathra')} (පාදය {calc_data.get('nak_pada')})<br>අධිපති: {calc_data.get('nak_lord')}</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🕉️ ගණය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('nak_gana')}</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🦁 යෝනිය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('nak_yoni')}</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>⚥ ජන්ම ලිංගය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{calc_data.get('nak_linga')}</td></tr>
    <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>📐 අයනාංශය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">Lahiri (Chitrapaksha) - ශ්‍රී ලාංකීය ක්‍රමය</td></tr>
</table>

<h3>🪐 2. ග්‍රහ පිහිටීම් සාරාංශය</h3>
<ul>
"""
    for planet, bhava in calc_data.get('planet_bhava_details', {}).items():
        lon = calc_data.get('planet_longitudes', {}).get(planet, 0)
        rashi = RA_NAMES[int(lon / 30) % 12]
        report += f"<li><strong>{planet}:</strong> {rashi} රාශියේ - {bhava} වන භාවයේ</li>"
    
    report += f"""
</ul>

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
<p><strong>{calc_data.get('nakshathra')} නැකත</strong> - {calc_data.get('nak_gana')} ගණය, {calc_data.get('nak_yoni')} යෝනිය</p>
<p>{calc_data.get('nakshathra')} නැකතේ උපත ලබන අය ඉතා බුද්ධිමත්, කාරුණික, අවංක සහ ප්‍රතිපත්තිගරුක පුද්ගලයන් වේ. මෙම නැකතේ අධිපතිත්වය දරන්නේ <strong>{calc_data.get('nak_lord')}</strong> ග්‍රහයා වන අතර, {calc_data.get('nak_gana')} ගණය සහ {calc_data.get('nak_yoni')} යෝනිය නිසා සමාජයේ ගෞරවයට පාත්‍ර වේ.</p>

<h3>💫 5. ලග්නයේ බලපෑම</h3>
<p><strong>{calc_data.get('lagna')} ලග්නය</strong> සහ <strong>{calc_data.get('lagna_lord')}</strong> ලග්නාධිපතිත්වය යටතේ උපත ලැබීම නිසා, ඔබ සතුව අතිවිශිෂ්ට නායකත්ව ගුණාංග, ධෛර්යය, ස්ථිරභාවය සහ අධිෂ්ඨාන ශක්තියක් පවතී.</p>

<h3>💼 6. සුදුසු වෘත්තීන්</h3>
<p>ඔබගේ ලග්නය {calc_data.get('lagna')} සහ නැකත {calc_data.get('nakshathra')} මත පදනම්ව පහත ක්ෂේත්‍ර සුදුසු වේ:</p>
<p><strong>{professions}</strong></p>

<h3>🙏 7. පිළියම් සහ උපදෙස්</h3>
<ul>
<li>සෑම <strong>බ්‍රහස්පතින්දා</strong> දිනකම පන්සල් ගොස් බුද්ධ පූජා පැවැත්වීම</li>
<li><strong>"ඕම් {calc_data.get('nak_lord')}වේ නමඃ"</strong> මන්ත්‍රය දිනපතා ජප කිරීම</li>
<li>කහ පැහැති මල් පූජා කිරීම සුබයි</li>
<li>දරුවන්ට සහ අවශ්‍යතා ඇති අයට උදව් කිරීමෙන් පින් සිද්ධ වේ</li>
</ul>

<hr>
<p style="text-align: center"><em>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය (Lahiri Ayanamsa)<br>
🔮 සත්‍යය සහ ධර්මය ජය වේවා!<br>
🌺 ආයුබෝවන්! සැම දෙයක්ම සුභ සිද්ධ වේවා!</em></p>
</div>"""
    
    return report

# ==================== Display Rashi Chart ====================

def display_rashi_chart(rashi_chart, lagna_name):
    """
    රාශි චක්‍රය ග්‍රිඩ් එකක් ලෙස ප්‍රදර්ශනය කරයි
    """
    st.subheader(f"🕉️ රාශි චක්‍රය (ලග්නය: {lagna_name})")
    
    # රාශි චක්‍රය පෙළගැස්ම (North Indian style grid)
    # 4x3 grid එකක්
    rashi_order = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා",
                   "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
    
    # ලග්නය 1 වන ස්ථානයේ තැබීමට භ්‍රමණය කරන්න
    lagna_index = rashi_order.index(lagna_name)
    rotated_rashi = rashi_order[lagna_index:] + rashi_order[:lagna_index]
    
    # Grid එක display කිරීම
    cols = st.columns(4)
    for i, rashi in enumerate(rotated_rashi):
        col_idx = i % 4
        row_idx = i // 4
        
        if col_idx == 0 and i > 0:
            cols = st.columns(4)
        
        planets_in_rashi = []
        for planet, rashi_data in rashi_chart.items():
            if rashi_data["sign"] == rashi and rashi_data["planets"]:
                planets_in_rashi.extend(rashi_data["planets"])
        
        planet_symbols = {
            "රවි (සූර්ය)": "☀️",
            "සඳු (චන්ද්‍ර)": "🌙",
            "කුජ (අඟහරු)": "♂️",
            "බුධ (බුද්ධ)": "☿",
            "ගුරු (බ්‍රහස්පති)": "♃",
            "සිකුරු (ශුක්‍ර)": "♀️",
            "ශනි (සෙනසුරු)": "♄",
            "රාහු": "☊",
            "කේතු": "☋"
        }
        
        planet_display = " ".join([planet_symbols.get(p.split(' (')[0], "●") for p in planets_in_rashi[:3]])
        
        with cols[col_idx]:
            st.markdown(f"""
            <div class="rashi-cell">
                <strong>{rashi}</strong><br>
                <small>{planet_display if planet_display else "-"}</small>
            </div>
            """, unsafe_allow_html=True)

def display_nakshatra_details(calc_data):
    """
    නැකතේ සම්පූර්ණ විස්තර ප්‍රදර්ශනය කරයි
    """
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
            <small>🦁 යෝනිය</small>
            <div class="value">{calc_data.get('nak_yoni')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="detail-card">
            <small>🔢 පාදය</small>
            <div class="value">{calc_data.get('nak_pada')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="detail-card">
            <small>⚥ ජන්ම ලිංගය</small>
            <div class="value">{calc_data.get('nak_linga')}</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== Admin Panel ====================

def admin_panel():
    st.markdown('<div class="main-header"><h1>👑 පරිපාලක පුවරුව</h1><p>Admin Dashboard</p></div>', unsafe_allow_html=True)
    
    admin_email = st.text_input("පරිපාලක විද්‍යුත් තැපෑල ඇතුළත් කරන්න", type="password")
    
    if admin_email == "sampathub89@gmail.com":
        st.success("✅ සත්‍යාපනය සාර්ථකයි!")
        
        st.subheader("🔑 API තත්ත්වය")
        api_keys = get_available_api_keys()
        if api_keys:
            st.success(f"✅ Gemini API යතුරු {len(api_keys)}ක් හමු විය")
        else:
            st.warning("⚠️ Gemini API යතුරක් හමු නොවීය")
            st.info("API Key එකක් සැකසීමට: https://aistudio.google.com/app/apikey වෙත ගොස් API key එකක් ලබා ගන්න")
        
        calculations = get_admin_calculations()
        
        if calculations:
            st.subheader(f"📊 සියලු ගණනය කිරීම් ({len(calculations)})")
            
            calc_list = []
            for calc_id, calc in calculations.items():
                calc_list.append({"id": calc_id, "data": calc})
            calc_list.reverse()
            
            for item in calc_list[:50]:
                calc = item["data"]
                with st.expander(f"📅 {calc.get('timestamp', '')[:10]} - {calc.get('name', '')} ({calc.get('lagna', '')})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**නම:** {calc.get('name', '')}")
                        st.write(f"**ලිංගය:** {calc.get('gender', '')}")
                        st.write(f"**උපන් දිනය:** {calc.get('dob', '')}")
                    with col2:
                        st.write(f"**ලග්නය:** {calc.get('lagna', '')}")
                        st.write(f"**නැකත:** {calc.get('nakshathra', '')}")
                        st.write(f"**යෝනිය:** {calc.get('nak_yoni', '')}")
        else:
            st.info("තවමත් ගණනය කිරීම් නොමැත")
    elif admin_email:
        st.error("වලංගු පරිපාලක විද්‍යුත් තැපෑලක් නොවේ")

# ==================== Main Calculation Form ====================

def calculation_form():
    st.markdown('<div class="main-header"><h1>🔮 AstroPro SL</h1><p>ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය (Lahiri Ayanamsa)</p></div>', unsafe_allow_html=True)
    
    st.info("📌 මෙම පද්ධතිය ශ්‍රී ලංකාවේ භාවිතා වන **Lahiri Ayanamsa** පමණක් භාවිතා කරයි. සියලු ගණනය කිරීම් UTC වලට පරිවර්තනය කර සිදු කෙරේ.")
    
    if not get_available_api_keys():
        st.info("💡 සම්පූර්ණ AI පලාපල වාර්තා සඳහා API key එකක් සැකසීමට පරිපාලක අමතන්න")
    
    with st.form("calculation_form"):
        st.markdown("### 📝 ඔබගේ තොරතුරු")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("නම *", placeholder="ඔබගේ සම්පූර්ණ නම")
        with col2:
            gender = st.selectbox("ලිංගය *", ["පිරිමි", "ගැහැණු"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            dob = st.date_input("උපන් දිනය *", value=datetime(1995, 5, 20), 
                               min_value=datetime(1940, 1, 1), max_value=datetime(2050, 12, 31))
        with col2:
            hour = st.number_input("පැය (0-23)", 0, 23, 10)
        with col3:
            minute = st.number_input("මිනිත්තු (0-59)", 0, 59, 30)
        
        city = st.selectbox("දිස්ත්‍රික්කය *", list(DISTRICTS.keys()))
        
        st.caption(f"⏰ ශ්‍රී ලංකා වේලාව (GMT+5:30) UTC වලට පරිවර්තනය කර ගණනය කෙරේ")
        
        submitted = st.form_submit_button("🔮 කේන්දරය ගණනය කරන්න", use_container_width=True)
        
        if submitted:
            if not name.strip():
                st.error("කරුණාකර නම ඇතුළත් කරන්න")
            else:
                with st.spinner("🔄 ගණනය කරමින්... UTC වලට පරිවර්තනය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න"):
                    result, error = perform_calculation(name, gender, dob, hour, minute, city)
                    
                    if result:
                        st.session_state.calculation_result = result
                        st.session_state.show_calculation = True
                        st.session_state.ai_report = None
                        
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
        
        # Basic details in cards
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
                <small>{result['nak_lord']} අධිපති</small>
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
        
        # Display Rashi Chart
        display_rashi_chart(result.get('rashi_chart', {}), result.get('lagna', ''))
        
        # Display Nakshatra Details
        display_nakshatra_details(result)
        
        # Planet positions by Bhava
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
        
        # Planet longitudes table
        with st.expander("🔭 ග්‍රහයින්ගේ සම්පූර්ණ දේශාංශ"):
            for planet, lon in result.get('planet_longitudes', {}).items():
                rashi = RA_NAMES[int(lon / 30) % 12]
                degree = lon % 30
                st.write(f"**{planet}:** {rashi} රාශියේ {degree:.2f}°")
        
        # AI Report Button
        st.markdown("---")
        if st.button("🤖 AI පලාපල විස්තරය ලබාගන්න", use_container_width=True):
            with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න (තත්පර 15-20)"):
                ai_report = get_ai_astrology_report(result)
                st.session_state.ai_report = ai_report
                st.rerun()
        
        # Display AI Report if available
        if st.session_state.ai_report:
            st.markdown(st.session_state.ai_report, unsafe_allow_html=True)
            
            # Share buttons
            st.markdown("---")
            st.markdown("#### 📤 බෙදාගන්න")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>AstroPro SL - {result['name']} ගේ වාර්තාව</title>
                <style>body{{font-family:Arial;padding:20px;}} h1{{color:#e94560;}} .report{{background:#1a1a2e;color:white;padding:20px;border-radius:15px;}}</style>
                </head>
                <body>
                <h1>AstroPro SL - {result['name']} ගේ ජන්ම පත්‍රය</h1>
                <div class="report">
                <h2>පුද්ගලික තොරතුරු</h2>
                <p>නම: {result['name']}<br>ලිංගය: {result['gender']}<br>උපන් දිනය: {result['dob']}<br>උපන් වේලාව: {result['time']}<br>දිස්ත්‍රික්කය: {result['city']}</p>
                <h2>ජ්‍යොතිෂ ගණනය කිරීම්</h2>
                <p>ලග්නය: {result['lagna']}<br>නැකත: {result['nakshathra']}<br>ගණය: {result['nak_gana']}<br>යෝනිය: {result['nak_yoni']}</p>
                <h2>පලාපල විස්තරය</h2>
                {st.session_state.ai_report}
                </div>
                <hr><p>© AstroPro SL - {datetime.now().strftime('%Y-%m-%d')}<br>Lahiri Ayanamsa - ශ්‍රී ලාංකීය ජ්‍යොතිෂ ක්‍රමය</p>
                </body>
                </html>
                """
                b64 = base64.b64encode(html_content.encode()).decode()
                href = f'<a href="data:text/html;base64,{b64}" download="astro_report_{result["name"]}_{datetime.now().strftime("%Y%m%d")}.html"><button style="background-color:#4CAF50;color:white;padding:10px;border:none;border-radius:5px;cursor:pointer;width:100%;">📥 Report බාගන්න</button></a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with col2:
                whatsapp_msg = f"""*AstroPro SL - {result['name']} ගේ ජන්ම පත්‍රය*

📅 උපන් දිනය: {result['dob']}
⏰ උපන් වේලාව: {result['time']}
📍 දිස්ත්‍රික්කය: {result['city']}

*ජ්‍යොතිෂ ගණනය කිරීම්:*
⭐ ලග්නය: {result['lagna']}
🌙 නැකත: {result['nakshathra']}
🕉️ ගණය: {result['nak_gana']}
🦁 යෝනිය: {result['nak_yoni']}

---
*AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය (Lahiri Ayanamsa)*"""
                whatsapp_url = f"https://wa.me/?text={requests.utils.quote(whatsapp_msg)}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px;border:none;border-radius:5px;cursor:pointer;width:100%;">📱 WhatsApp</button></a>', unsafe_allow_html=True)
            
            with col3:
                email_body = f"{whatsapp_msg}\n\n{st.session_state.ai_report[:2000]}"
                email_url = f"mailto:?subject=AstroPro SL - {result['name']} ගේ වාර්තාව&body={requests.utils.quote(email_body)}"
                st.markdown(f'<a href="{email_url}" target="_blank"><button style="background-color:#EA4335;color:white;padding:10px;border:none;border-radius:5px;cursor:pointer;width:100%;">📧 Email</button></a>', unsafe_allow_html=True)
        
        if st.button("🔄 නව ගණනය කිරීමක් සඳහා", use_container_width=True):
            st.session_state.show_calculation = False
            st.session_state.calculation_result = None
            st.session_state.ai_report = None
            st.rerun()

# ==================== Main App ====================

def main():
    with st.sidebar:
        st.markdown("---")
        if st.button("👑 පරිපාලක පුවරුව", use_container_width=True):
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
        © 2026 AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය<br>
        <small>📐 Lahiri Ayanamsa (Chitrapaksha) - ශ්‍රී ලංකාවේ භාවිතා වන ක්‍රමය<br>
        ⏰ සියලු ගණනය කිරීම් UTC වලට පරිවර්තනය කර සිදු කෙරේ<br>
        📧 වැඩිදුර තොරතුරු සඳහා: sampathub89@gmail.com</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
