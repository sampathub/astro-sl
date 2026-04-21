import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
import requests
import json
import uuid
import base64
import time

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
if 'ai_loading' not in st.session_state:
    st.session_state.ai_loading = False

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
        
        # Lagna lord
        lagna_lords = ["අඟහරු", "සිකුරු", "බුධ", "සඳු", "රවි", "බුධ", "සිකුරු", "අඟහරු", "ගුරු", "සෙනසුරු", "සෙනසුරු", "ගුරු"]
        lagna_lord = lagna_lords[lagna_rashi]
        
        planets_def = [
            ("රවි", swe.SUN), ("සඳු", swe.MOON), ("කුජ", swe.MARS),
            ("බුධ", swe.MERCURY), ("ගුරු", swe.JUPITER), ("සිකුරු", swe.VENUS),
            ("ශනි", swe.SATURN), ("රාහු", swe.MEAN_NODE)
        ]
        
        bhava_map = {i: [] for i in range(1, 13)}
        planet_positions = {}
        moon_lon = 0
        
        for p_name, p_id in planets_def:
            res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
            lon = res[0]
            planet_positions[p_name] = lon
            if p_id == swe.MOON:
                moon_lon = lon
            p_bhava = get_planet_bhava(lon, houses)
            bhava_map[p_bhava].append(p_name)
        
        nak_idx = int(moon_lon / (360.0 / 27)) % 27
        nak_name = NAK_NAMES[nak_idx]
        gana, yoni, linga, nak_lord, nak_features = get_nakshatra_details(nak_idx)
        
        result = {
            "name": name, "gender": gender, "dob": dob.strftime("%Y-%m-%d"),
            "time": f"{hour:02d}:{minute:02d}", "city": city,
            "lagna": lagna_name, "lagna_lord": lagna_lord,
            "nakshathra": nak_name, "nak_lord": nak_lord, "nak_features": nak_features,
            "gana": gana, "yoni": yoni, "linga": linga,
            "ayanamsa": ayanamsa, "bhava_map": bhava_map,
            "planet_positions": planet_positions
        }
        
        return result, None
    except Exception as e:
        return None, str(e)

# ==================== AI Prediction with Multiple API Keys ====================
def get_ai_prediction_with_fallback(calc_data):
    """Try multiple Gemini API keys with fallback"""
    
    # Get all API keys from secrets
    api_keys = []
    try:
        for i in range(1, 4):  # Try keys 1, 2, 3
            key = st.secrets.get(f"GEMINI_API_KEY_{i}")
            if key and key != "your-gemini-api-key-here":
                api_keys.append(key)
    except:
        pass
    
    # Create detailed prompt for Sinhala astrology report
    prompt = f"""ඔබ ශ්‍රී ලංකාවේ ප්‍රමුඛතම ජ්‍යොතිෂවේදියෙකු ලෙස ක්‍රියා කරන්න. පහත තොරතුරු අනුව ඉතා නිවැරදි, සවිස්තරාත්මක සහ වෘත්තීය පලාපල වාර්තාවක් සිංහලෙන් සකස් කරන්න.

## පුද්ගලික තොරතුරු
- නම: {calc_data.get('name')}
- ලිංගය: {calc_data.get('gender')}
- උපන් දිනය: {calc_data.get('dob')}
- උපන් වේලාව: {calc_data.get('time')}
- උපන් ස්ථානය: {calc_data.get('city')}

## ජ්‍යොතිෂ ගණනය කිරීම්
- ලග්නය: {calc_data.get('lagna')}
- ලග්නාධිපති: {calc_data.get('lagna_lord')}
- උපන් නැකත: {calc_data.get('nakshathra')}
- නැකත් අධිපති: {calc_data.get('nak_lord')}
- නැකතේ විශේෂ ලක්ෂණ: {calc_data.get('nak_features')}
- ගණය: {calc_data.get('gana')}
- යෝනිය: {calc_data.get('yoni')}

කරුණාකර පහත සඳහන් කරුණු ඉතා විස්තරාත්මකව, පේළි ගණන 30-40 අතර සිංහලෙන් ලියන්න. එක් එක් කොටසට අවම වශයෙන් පේළි 3-4 බැගින් ලියන්න:

### 1. නැකතේ ස්වභාවය සහ ගුණාංග
{calc_data.get('nakshathra')} නැකතේ සාමාන්‍ය ලක්ෂණ, මෙම නැකතේ උපත ලබන අයගේ චරිත ස්වභාවය, නැකත් අධිපති ග්‍රහයාගේ බලපෑම පිළිබඳ විස්තර කරන්න.

### 2. ලග්නයේ බලපෑම
{calc_data.get('lagna')} ලග්නයේ ප්‍රධාන ලක්ෂණ, ලග්නාධිපති {calc_data.get('lagna_lord')} ග්‍රහයාගේ බලපෑම, ලග්නය සහ නැකත එක්වීමෙන් සිදුවන විශේෂ බලපෑම් විස්තර කරන්න.

### 3. චරිතය සහ පෞරුෂත්වය
ප්‍රධාන චරිත ලක්ෂණ (හොඳ සහ නරක), සමාජ සම්බන්ධතා, පවුල් ජීවිතය පිළිබඳ විස්තර කරන්න.

### 4. අධ්‍යාපනය සහ බුද්ධි හැකියාව
අධ්‍යාපන ක්ෂේත්‍රයේ දක්ෂතා, විශේෂ දක්ෂතා සහ කුසලතා, ඉගෙනුම් ක්‍රමය පිළිබඳ විස්තර කරන්න.

### 5. වෘත්තිය සහ රැකියාව
සුදුසුම රැකියා ක්ෂේත්‍ර, වෘත්තීය දියුණුව සඳහා සුබ කාල, ව්‍යාපාරික අවස්ථා පිළිබඳ විස්තර කරන්න.

### 6. සෞඛ්‍ය තත්ත්වය
සාමාන්‍ය සෞඛ්‍ය තත්ත්වය, අවධානය යොමු කළ යුතු රෝග, සෞඛ්‍ය සම්බන්ධ උපදෙස් දෙන්න.

### 7. විවාහ සහ සම්බන්ධතා
විවාහ ජීවිතය, සහකරු/සහකාරියගේ ලක්ෂණ, ප්‍රේම සම්බන්ධතා පිළිබඳ විස්තර කරන්න.

### 8. ඉදිරි කාලය පිළිබඳ අනාවැකි
ලබන වසර 5 සඳහා ප්‍රධාන සිදුවීම්, සුබ කාල පරිච්ඡේද, අවධානය යොමු කළ යුතු කාල පිළිබඳ අනාවැකි දෙන්න.

### 9. පිළියම් සහ උපදෙස්
ග්‍රහ දෝෂ සඳහා පිළියම්, දෛනික චර්යාව සඳහා යෝජනා, මන්ත්‍ර සහ ජප මාලා, දාන ශීලාදිය, ආගමික වතාවත් පිළිබඳ උපදෙස් දෙන්න.

වාර්තාව ඉතා වෘත්තීය, සවිස්තරාත්මක, ශ්‍රී ලාංකීය ජ්‍යොතිෂ සම්ප්‍රදායට අනුකූල සහ ධනාත්මක විය යුතුය. සුදුසු තැන්වලදී ශුභාශීර්වාද එක් කරන්න."""

    # Try each API key
    for i, api_key in enumerate(api_keys):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            time.sleep(1)
            continue
    
    # If all keys fail, return detailed fallback report
    return generate_detailed_sinhala_report(calc_data)

def generate_detailed_sinhala_report(data):
    """Generate detailed Sinhala astrology report without AI"""
    
    salutation = "මහතා" if data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    report = f"""
    <div class="result-card">
    <h2>🌟 {data.get('name', '')} {salutation} ගේ සවිස්තර පලාපල වාර්තාව</h2>
    <p><small>ශ්‍රී ලාංකීය වෛදික ජ්‍යොතිෂ සම්ප්‍රදාය අනුව සකස් කරන ලදී</small></p>
    
    <h3>📋 1. මූලික ජ්‍යොතිෂ තොරතුරු</h3>
    <table style="width:100%; border-collapse:collapse;">
        <tr><th style="background:#e94560; padding:10px; text-align:left;">ගුණාංගය</th><th style="background:#e94560; padding:10px; text-align:left;">විස්තරය</th></tr>
        <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>⭐ ලග්නය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{data.get('lagna', '')} </td></tr>
        <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>👑 ලග්නාධිපති</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{data.get('lagna_lord', '')}</td></tr>
        <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🌙 උපන් නැකත</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{data.get('nakshathra', '')}</td></tr>
        <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🪐 නැකත් අධිපති</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{data.get('nak_lord', '')}</td></tr>
        <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🕉️ ගණය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{data.get('gana', '')}</td></tr>
        <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>🦁 යෝනිය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{data.get('yoni', '')}</td></tr>
        <tr><td style="padding:8px; border-bottom:1px solid #333;"><strong>⚥ ජන්ම ලිංගය</strong></td><td style="padding:8px; border-bottom:1px solid #333;">{data.get('linga', '')}</td></tr>
    </table>
    
    <h3>📖 2. නැකතේ ස්වභාවය සහ ගුණාංග</h3>
    <p><strong>{data.get('nakshathra', '')} නැකත</strong> - {data.get('nak_features', '')}</p>
    <p>මෙම නැකතේ අධිපතිත්වය දරන්නේ <strong>{data.get('nak_lord', '')}</strong> ග්‍රහයා වන අතර, මෙම නැකතේ උපත ලබන පුද්ගලයන් සාමාන්‍යයෙන් ඉතා බුද්ධිමත්, කාරුණික, අවංක සහ ප්‍රතිපත්තිගරුක පුද්ගලයන් වේ. අන් අයට උදව් කිරීමට ඇති කැමැත්ත සහ ස්වභාවික නායකත්ව ගුණාංග නිසා සමාජයේ ගෞරවයට පාත්‍ර වේ. මෙම නැකතේ උපත ලබන අය තුළ අධ්‍යාත්මික නැඹුරුවක් ද දැකිය හැකි අතර, ඔවුන් සැමවිටම සත්‍යය සහ ධර්මය උසස් කොට සලකයි.</p>
    
    <h3>🪐 3. ලග්නයේ බලපෑම</h3>
    <p><strong>{data.get('lagna', '')} ලග්නය</strong> සහ <strong>{data.get('lagna_lord', '')}</strong> ලග්නාධිපතිත්වය යටතේ උපත ලැබීම නිසා, ඔබ සතුව ඇත්තේ අතිවිශිෂ්ට නායකත්ව ගුණාංග, ධෛර්යය, ස්ථිරභාවය සහ අධිෂ්ඨාන ශක්තියයි. {data.get('lagna', '')} ලග්නය නිසා ඔබ ඉතා අවංක, කඩිසර සහ විනයගරුක පුද්ගලයෙකි. ඔබගේ ජීවිතයේ ඉහළ ඉලක්ක තබා ගැනීමට සහ ඒවා සාක්ෂාත් කර ගැනීමට ඇති හැකියාව අගනේය.</p>
    
    <h3>💫 4. චරිතය සහ පෞරුෂත්වය</h3>
    <p><strong>ප්‍රධාන ලක්ෂණ:</strong> අවංකභාවය, කඩිසරකම, විනයගරුක බව, අන් අයට ගරු කිරීම, ඉවසීම, ස්ථාවරත්වය</p>
    <p><strong>සමාජ සම්බන්ධතා:</strong> මිත්‍රශීලී ස්වභාවය නිසා පුළුල් මිතුරු කවයක් ඇත. සමාජයේ ක්‍රියාකාරීව සහභාගී වීමට කැමැත්තක් දක්වයි.</p>
    <p><strong>පවුල් ජීවිතය:</strong> පවුලේ අය කෙරෙහි ඇති බැඳීම සහ ආදරය අගනේය. පවුලේ සාමාජිකයන්ගේ සුවදුක් සඳහා සැමවිටම ක්‍රියා කරයි.</p>
    
    <h3>📚 5. අධ්‍යාපනය සහ බුද්ධි හැකියාව</h3>
    <p>ඔබ සතුව ඇති තියුණු බුද්ධිය සහ විශ්ලේෂණාත්මක චින්තනය නිසා අධ්‍යාපන කටයුතුවලදී විශිෂ්ට ප්‍රතිඵල අත්කර ගනු ඇත. විශේෂයෙන් ගණිතය, විද්‍යාව, පරිගණක තාක්ෂණය, නීතිය, වෛද්‍ය විද්‍යාව, ඉංජිනේරු විද්‍යාව, කළමනාකරණය වැනි ක්ෂේත්‍රවල දක්ෂතා පෙන්වයි. ඉගෙනුම් කටයුතු සඳහා ඇති කැපවීම සහ කඩිසරකම නිසා උසස් අධ්‍යාපනයක් සාමාන්‍යයෙන් හිමි වේ.</p>
    
    <h3>💼 6. වෘත්තිය සහ රැකියාව</h3>
    <p><strong>සුදුසු රැකියා ක්ෂේත්‍ර:</strong> ඉංජිනේරු, වෛද්‍ය, නීතිඥ, කළමනාකරණ, පරිපාලන සේවා, අධ්‍යාපනය, පර්යේෂණ, තාක්ෂණය, මූල්ය, බැංකු, රාජ්‍ය සේවය</p>
    <p><strong>වෘත්තීය දියුණුව:</strong> වයස අවුරුදු 25-32 අතර කාලය තුළ වෘත්තීය දියුණුවක් අපේක්ෂා කළ හැකිය. වයස අවුරුදු 35-42 අතර කාලය තුළ ස්ථාවරත්වයක් සහ පිළිගැනීමක් හිමි වේ.</p>
    
    <h3>🏥 7. සෞඛ්‍ය තත්ත්වය</h3>
    <p>සාමාන්‍යයෙන් හොඳ සෞඛ්‍ය තත්ත්වයක් පවතී. කෙසේ වෙතත්, ආහාර ගැනීමේදී විමසිල්ලෙන් කටයුතු කළ යුතුය. නිතිපතා ව්‍යායාම කිරීම, යෝගාවලිය, ප්‍රාණායාම මගින් සෞඛ්‍යය වඩාත් හොඳින් පවත්වා ගත හැක. ආමාශ ආබාධ, හිසරදය, ආතතිය වැනි ගැටලු ඇති විය හැකි බැවින් ඒ පිළිබඳ අවධානයෙන් සිටීම වැදගත්.</p>
    
    <h3>💑 8. විවාහ සහ සම්බන්ධතා</h3>
    <p>විවාහ ජීවිතය සාමාන්‍යයෙන් සාමකාමී වේ. අන්යෝන්ය අවබෝධය, ගෞරවය සහ විශ්වාසය මත පදනම් වූ සම්බන්ධතාවයක් ගොඩනගා ගැනීමට හැකි වේ. විවාහය සඳහා සුබ කාල වයස අවුරුදු 26-30 අතර වේ. සහකරු/සහකාරිය බුද්ධිමත්, අවංක, කාරුණික සහ ස්ථාවර පුද්ගලයෙකු වනු ඇත.</p>
    
    <h3>🔮 9. ඉදිරි කාලය පිළිබඳ අනාවැකි</h3>
    <p>• <strong>ලබන වසර 1-2:</strong> අධ්‍යාපනය හා වෘත්තිය සඳහා සුබ කාලයකි. නව අවස්ථා සහ ජයග්‍රහණ අත්කර ගැනීමට හැකි වේ.<br>
    • <strong>ලබන වසර 3-5:</strong> ආර්ථික දියුණුවක් සහ ස්ථාවරත්වයක් අපේක්ෂා කළ හැක. දේපළ වාහන සම්බන්ධ සුබ අවස්ථා හිමි වේ.<br>
    • <strong>විදේශ ගමන්:</strong> විදේශ සංචාර සඳහා ඇති අවස්ථා හිමිවේ. විදේශ රැකියා සඳහා ද අවස්ථා තිබේ.</p>
    
    <h3>🙏 10. පිළියම් සහ උපදෙස්</h3>
    <p><strong>ග්‍රහ දෝෂ සඳහා පිළියම්:</strong></p>
    <ul>
        <li>සෑම <strong>බ්‍රහස්පතින්දා</strong> දිනකම පන්සල් ගොස් බුද්ධ පූජා පැවැත්වීම</li>
        <li><strong>කහ පැහැති මල්</strong> සහ ආහාර දන් දීම සුබයි</li>
        <li><strong>"ඕම් ගුරුවේ නමඃ"</strong> මන්ත්‍රය දිනපතා 108 වතාවක් ජප කිරීම</li>
        <li>සෑම <strong>පුර අටවක</strong> දිනකම උපවාසයක් රැකීම</li>
        <li>දරුවන්ට, ගුරුවරුන්ට සහ අවශ්‍යතා ඇති අයට උදව් කිරීමෙන් පින් සිද්ධ වේ</li>
        <li>සෑම දිනකම උදෑසන හිරු දෙවියන්ට වතුර පූජා කිරීම</li>
    </ul>
    
    <p><strong>දෛනික චර්යාව සඳහා යෝජනා:</strong></p>
    <ul>
        <li>උදෑසන 5.00-6.00 අතර කාලයේ නැගිටීම</li>
        <li>දිනපතා යෝගා සහ භාවනාව පුරුදු කිරීම</li>
        <li>සරල, සෞඛ්‍ය සම්පන්න ආහාර ගැනීම</li>
        <li>රාත්‍රී 10.00 ට පෙර නින්දට යාම</li>
    </ul>
    
    <hr>
    <p style="text-align: center;"><em>© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂ පද්ධතිය<br>
    ආයුබෝවන්! සැම දෙයක්ම සුභ සිද්ධ වේවා!</em></p>
    </div>
    """
    
    return report

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
    
    admin_email = st.text_input("පරිපාලක විද්‍යුත් තැපෑල ඇතුළත් කරන්න", type="password")
    
    if admin_email == "sampathub89@gmail.com":
        st.success("✅ සත්‍යාපනය සාර්ථකයි!")
        
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
                        st.write(f"**යෝනිය:** {calc.get('yoni', '')}")
        else:
            st.info("තවමත් ගණනය කිරීම් නොමැත")
    elif admin_email:
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
                        st.session_state.ai_report = None  # Reset AI report
                        
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
            st.session_state.ai_loading = True
            with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... කරුණාකර මොහොතක් රැඳී සිටින්න (තත්පර 10-15)"):
                ai_report = get_ai_prediction_with_fallback(result)
                st.session_state.ai_report = ai_report
                st.session_state.ai_loading = False
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
                <p>ලග්නය: {result['lagna']}<br>නැකත: {result['nakshathra']}<br>ගණය: {result['gana']}<br>යෝනිය: {result['yoni']}</p>
                <h2>පලාපල විස්තරය</h2>
                {st.session_state.ai_report}
                </div>
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
        <small>වැඩිදුර තොරතුරු සඳහා: sampathub89@gmail.com</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
