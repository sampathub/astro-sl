import streamlit as st
import swisseph as swe
from datetime import datetime
import google.generativeai as genai
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

# ==================== Initialize Swiss Ephemeris ====================
def init_swisseph():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ephe_path = os.path.join(current_dir, "ephe")
        if os.path.exists(ephe_path):
            swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return True
    except:
        return False

EPHE_READY = init_swisseph()

# ==================== Constants ====================
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", 
            "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]

RA_LORDS = ["අඟහරු", "සිකුරු", "බුධ", "සඳු", "රවි", "බුධ",
            "සිකුරු", "අඟහරු", "ගුරු", "සෙනසුරු", "සෙනසුරු", "ගුරු"]

NAK_NAMES = [
    "අශ්විනී", "භරණී", "කෘත්තිකා", "රෝහණී", "මුවසිරිස", "අද",
    "පුනාවස", "පුෂ", "අස්ලිස", "මා", "පුවපල්", "උත්තරපල්",
    "හත", "සිත", "සා", "විසා", "අනුර", "දෙට",
    "මූල", "පුවසල", "උත්තරසල", "සුවණ", "දෙනට", "සියාවස",
    "පුවපුටුප", "උත්තරපුටුප", "රේවතී"
]

NAK_LORDS = [
    "කේතු", "සිකුරු", "රවි", "සඳු", "අඟහරු", "රාහු",
    "ගුරු", "සෙනසුරු", "බුධ", "කේතු", "සිකුරු", "රවි",
    "සඳු", "අඟහරු", "රාහු", "ගුරු", "සෙනසුරු", "බුධ",
    "කේතු", "සිකුරු", "රවි", "සඳු", "අඟහරු", "රාහු",
    "ගුරු", "සෙනසුරු", "බුධ"
]

NAK_GANA = [
    "දේව", "මනුෂ්‍ය", "රාක්ෂස", "මනුෂ්‍ය", "දේව", "මනුෂ්‍ය",
    "දේව", "දේව", "රාක්ෂස", "රාක්ෂස", "මනුෂ්‍ය", "මනුෂ්‍ය",
    "දේව", "රාක්ෂස", "දේව", "රාක්ෂස", "දේව", "රාක්ෂස",
    "රාක්ෂස", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂස", "රාක්ෂස",
    "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව"
]

NAK_YONI = [
    "අශ්වයා", "ඇතා", "බැටළුවා", "සර්පයා", "සර්පයා", "බල්ලා",
    "මීයා", "බැටළුවා", "මීයා", "මීයා", "මීයා", "ගවයා",
    "මීහරක්", "ව්‍යාඝ්‍රයා", "මීහරක්", "ව්‍යාඝ්‍රයා", "මුවා", "මුවා",
    "බල්ලා", "වඳුරා", "මුගටියා", "වඳුරා", "සිංහයා", "අශ්වයා",
    "සිංහයා", "ගවයා", "ඇතා"
]

NAK_LINGA = [
    "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ",
    "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "පුරුෂ", "පුරුෂ",
    "පුරුෂ", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ",
    "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ",
    "ස්ත්‍රී", "පුරුෂ", "පුරුෂ"
]

DISTRICTS = {
    "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "කළුතර": (6.5854, 79.9607),
    "මහනුවර": (7.2906, 80.6337), "මාතලේ": (7.4675, 80.6234), "නුවරඑළිය": (6.9497, 80.7891),
    "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245),
    "යාපනය": (9.6615, 80.0255), "කුරුණෑගල": (7.4863, 80.3647), "අනුරාධපුරය": (8.3114, 80.4037),
    "බදුල්ල": (6.9934, 81.0550), "රත්නපුරය": (6.7056, 80.3847), "කෑගල්ල": (7.2513, 80.3464)
}

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

# ==================== UTC Conversion ====================
def convert_to_utc(year, month, day, hour, minute):
    total_local = hour * 60 + minute
    total_utc = total_local - (5 * 60 + 30)
    
    utc_day, utc_month, utc_year = day, month, year
    utc_hour = total_utc // 60
    utc_minute = total_utc % 60
    
    if total_utc < 0:
        total_utc += 24 * 60
        utc_day -= 1
        utc_hour = total_utc // 60
        utc_minute = total_utc % 60
        
        if utc_day < 1:
            if month == 1:
                utc_month, utc_year = 12, year - 1
                utc_day = 31
            elif month == 3:
                utc_month = 2
                leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
                utc_day = 29 if leap else 28
            elif month in [5, 7, 10, 12]:
                utc_month = month - 1
                utc_day = 30
            else:
                utc_month = month - 1
                utc_day = 31
    
    jd = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0, swe.GREG_CAL)
    return jd

def get_bhava(planet_lon, cusps):
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

def get_nakshatra(moon_lon):
    nak_angle = 360.0 / 27.0
    nak_idx = int(moon_lon / nak_angle) % 27
    nak_start = nak_idx * nak_angle
    pada = int((moon_lon - nak_start) / (nak_angle / 4)) + 1
    
    return {
        "index": nak_idx,
        "name": NAK_NAMES[nak_idx],
        "lord": NAK_LORDS[nak_idx],
        "gana": NAK_GANA[nak_idx],
        "yoni": NAK_YONI[nak_idx],
        "linga": NAK_LINGA[nak_idx],
        "pada": pada
    }

# ==================== Main Calculation ====================
def calculate_astrology(name, gender, dob, hour, minute, city):
    try:
        jd = convert_to_utc(dob.year, dob.month, dob.day, hour, minute)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        lat, lon = DISTRICTS[city]
        
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        
        lagna_lon = ascmc[0]
        lagna_rashi = int(lagna_lon / 30) % 12
        lagna_name = RA_NAMES[lagna_rashi]
        lagna_lord = RA_LORDS[lagna_rashi]
        
        planet_positions = {}
        planet_bhava = {}
        bhava_map = {i+1: [] for i in range(12)}
        moon_lon = 0
        
        for p_name, p_id in PLANETS:
            res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
            lon_val = res[0]
            
            rashi_idx = int(lon_val / 30) % 12
            planet_positions[p_name] = {
                "lon": lon_val,
                "rashi": RA_NAMES[rashi_idx],
                "degree": lon_val % 30
            }
            
            if p_id == swe.MOON:
                moon_lon = lon_val
            
            bhava = get_bhava(lon_val, houses)
            planet_bhava[p_name] = bhava
            bhava_map[bhava].append(p_name)
        
        nakshatra = get_nakshatra(moon_lon)
        
        return {
            "name": name,
            "gender": gender,
            "dob": dob.strftime("%Y-%m-%d"),
            "time": f"{hour:02d}:{minute:02d}",
            "city": city,
            "lagna": lagna_name,
            "lagna_lord": lagna_lord,
            "lagna_degree": round(lagna_lon % 30, 2),
            "nakshathra": nakshatra["name"],
            "nak_pada": nakshatra["pada"],
            "nak_lord": nakshatra["lord"],
            "nak_gana": nakshatra["gana"],
            "nak_yoni": nakshatra["yoni"],
            "nak_linga": nakshatra["linga"],
            "planet_positions": planet_positions,
            "planet_bhava": planet_bhava,
            "bhava_map": bhava_map
        }, None
        
    except Exception as e:
        return None, f"දෝෂය: {str(e)}"

# ==================== API Key Setup ====================
def setup_api_key():
    """API Key එක setup කිරීම"""
    api_key = None
    
    # Try to get from secrets
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if api_key and api_key != "your-gemini-api-key-here":
            return api_key
    except:
        pass
    
    # Try environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    return None

# ==================== AI Report Generation ====================
def get_ai_report(calc_data):
    """AI වාර්තාව ලබා ගැනීම"""
    
    api_key = setup_api_key()
    
    if not api_key:
        return """
        <div class="result-card">
        <h2>⚠️ API Key එකක් සකසා නැත</h2>
        <p>කරුණාකර පහත ආකාරයට API Key එකක් සකසන්න:</p>
        <ol>
            <li>Google AI Studio වෙත ගොස් <a href="https://aistudio.google.com/" target="_blank">https://aistudio.google.com/</a></li>
            <li>Get API Key බොත්තම ඔබන්න</li>
            <li>API Key එක පිටපත් කරන්න</li>
            <li>Streamlit Cloud හි Secrets තුළ GEMINI_API_KEY ලෙස එකතු කරන්න</li>
        </ol>
        <p><strong>Local testing සඳහා:</strong><br>
        terminal එකේ: <code>export GEMINI_API_KEY="your-api-key-here"</code><br>
        හෝ <code>.env</code> ගොනුවක් සාදන්න</p>
        <hr>
        <p style="text-align:center">© AstroPro SL</p>
        </div>
        """
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use gemini-1.5-flash (more stable)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        salutation = "මහතා" if calc_data.get('gender') == "පිරිමි" else "මහත්මිය"
        
        # Simple prompt (shorter for better success)
        prompt = f"""ඔබ ශ්‍රී ලංකාවේ ප්‍රසිද්ධ වෛදික ජ්‍යොතිෂවේදියෙකි. පහත දත්ත මත පදනම්ව පලාපල වාර්තාවක් ලියන්න.

නම: {calc_data.get('name')}
ලිංගය: {calc_data.get('gender')}
උපන් දිනය: {calc_data.get('dob')}
උපන් වේලාව: {calc_data.get('time')}
ස්ථානය: {calc_data.get('city')}

ලග්නය: {calc_data.get('lagna')} (අධිපති: {calc_data.get('lagna_lord')})
නැකත: {calc_data.get('nakshathra')} (පාදය {calc_data.get('nak_pada')}, අධිපති: {calc_data.get('nak_lord')})
ගණය: {calc_data.get('nak_gana')}
යෝනිය: {calc_data.get('nak_yoni')}

පහත කරුණු ඇතුළත් කරන්න:
1. නැකතේ ස්වභාවය
2. ලග්නයේ බලපෑම
3. සුදුසු වෘත්තීන්
4. පිළියම් සහ උපදෙස්

සිංහලෙන් ලියන්න."""

        with st.spinner("🤖 AI විශ්ලේෂණය කරමින්... (තත්පර 10-15)"):
            response = model.generate_content(prompt)
        
        if response and response.text:
            return f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ පලාපල වාර්තාව</h2>
<p><small>✨ වෛදික ජ්‍යොතිෂය (Lahiri Ayanamsa)<br>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
🤖 Gemini 1.5 Flash මගින්</small></p>
<hr>
{response.text}
<hr>
<p style="text-align:center">© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය</p>
</div>"""
        else:
            return generate_fallback_report(calc_data, "AI ප්‍රතිචාරයක් ලැබුණේ නැත")
            
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg:
            return generate_fallback_report(calc_data, "API Key එක වලංගු නැත")
        elif "quota" in error_msg:
            return generate_fallback_report(calc_data, "API Quota ඉක්මවා ඇත")
        elif "model" in error_msg:
            return generate_fallback_report(calc_data, "Model එකට ප්‍රවේශයක් නැත")
        else:
            return generate_fallback_report(calc_data, f"දෝෂය: {error_msg[:100]}")

# ==================== Fallback Report ====================
def generate_fallback_report(calc_data, reason=""):
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
    
    warning = f'<p style="color:#ffaa00;">⚠️ {reason}</p>' if reason else ''
    
    return f"""<div class="result-card">
<h2>🌟 {calc_data.get('name')} {salutation} ගේ පලාපල වාර්තාව</h2>
{warning}
<hr>
<h3>📋 {calc_data.get('nakshathra')} නැකත</h3>
<p>{calc_data.get('nak_gana')} ගණය, {calc_data.get('nak_yoni')} යෝනිය. අධිපති: {calc_data.get('nak_lord')}</p>
<h3>⭐ {calc_data.get('lagna')} ලග්නය</h3>
<p>අධිපති: {calc_data.get('lagna_lord')}</p>
<h3>💼 සුදුසු වෘත්තීන්</h3>
<p><strong>{professions}</strong></p>
<h3>🙏 පිළියම්</h3>
<p>"ඕම් {calc_data.get('nak_lord')}වේ නමඃ" මන්ත්‍රය ජප කරන්න.</p>
<hr>
<p style="text-align:center">© AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය</p>
</div>"""

# ==================== Display Results ====================
def display_results():
    if not st.session_state.calculation_result:
        return
    
    r = st.session_state.calculation_result
    
    st.markdown("---")
    st.markdown("## 📊 ගණනය කිරීමේ ප්‍රතිඵල")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="detail-card"><small>⭐ ලග්නය</small><div class="value">{r["lagna"]}</div><small>{r["lagna_lord"]}</small></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="detail-card"><small>🌙 නැකත</small><div class="value">{r["nakshathra"]}</div><small>පාදය {r["nak_pada"]}</small></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="detail-card"><small>🕉️ ගණය</small><div class="value">{r["nak_gana"]}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="detail-card"><small>🦁 යෝනිය</small><div class="value">{r["nak_yoni"]}</div></div>', unsafe_allow_html=True)
    
    st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
    bhava_items = list(r["bhava_map"].items())
    col1, col2 = st.columns(2)
    for i, (bhava, planets) in enumerate(bhava_items):
        with col1 if i < 6 else col2:
            if planets:
                st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
            else:
                st.markdown(f"**{bhava} වන භාවය:** -")
    
    st.markdown("---")
    
    if st.button("🤖 AI පලාපල විස්තරය ලබාගන්න", use_container_width=True):
        ai_report = get_ai_report(r)
        st.session_state.ai_report = ai_report
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
    st.markdown('<div class="main-header"><h1>🔮 AstroPro SL</h1><p>ශ්‍රී ලාංකීය ජ්‍යොතිෂය (Lahiri Ayanamsa)</p></div>', unsafe_allow_html=True)
    
    if EPHE_READY:
        st.success("✅ Swiss Ephemeris සක්‍රියයි")
    else:
        st.warning("⚠️ Swiss Ephemeris සැකසීමේ ගැටළුවක්")
    
    # Check API status
    api_key = setup_api_key()
    if api_key:
        st.success("✅ Gemini API Key සකසා ඇත")
    else:
        st.warning("⚠️ Gemini API Key සකසා නැත - AI වාර්තාව ලබාගත නොහැක")
    
    st.info("📌 **Lahiri Ayanamsa** - ශ්‍රී ලංකා ජ්‍යොතිෂ ක්‍රමය\n\n⏰ UTC පරිවර්තනය | 📅 1950-2040")
    
    with st.form("astro_form"):
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
        
        if st.form_submit_button("🔮 කේන්දරය ගණනය කරන්න", use_container_width=True):
            if not name.strip():
                st.error("කරුණාකර නම ඇතුළත් කරන්න")
            else:
                with st.spinner("🔄 ගණනය කරමින්... (Lahiri Ayanamsa + UTC)"):
                    result, error = calculate_astrology(name, gender, dob, hour, minute, city)
                    if result:
                        st.session_state.calculation_result = result
                        st.session_state.show_calculation = True
                        st.success("✅ ගණනය කිරීම් සාර්ථකයි!")
                        st.rerun()
                    else:
                        st.error(f"දෝෂය: {error}")

# ==================== Main ====================
def main():
    if not st.session_state.show_calculation:
        calculation_form()
    else:
        display_results()
    
    st.markdown("""
    <div class="footer">
        © 2026 AstroPro SL - ශ්‍රී ලාංකීය ජ්‍යොතිෂය<br>
        <small>📐 Lahiri Ayanamsa | ⏰ UTC | 📅 1950-2040</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
