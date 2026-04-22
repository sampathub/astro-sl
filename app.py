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
# රාශි නම්
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", 
            "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]

# රාශි අධිපති
RA_LORDS = ["අඟහරු", "සිකුරු", "බුධ", "සඳු", "රවි", "බුධ",
            "සිකුරු", "අඟහරු", "ගුරු", "සෙනසුරු", "සෙනසුරු", "ගුරු"]

# ==================== නැකත් දත්ත (ඔබගේ වගුව අනුව) ====================
# නැකත් නම් (27)
NAK_NAMES = [
    "අශ්විනී", "භරණී", "කෘත්තිකා", "රෝහණී", "මුවසිරිස", "අද",
    "පුනාවස", "පුෂ", "අස්ලිස", "මා", "පුවපල්", "උත්තරපල්",
    "හත", "සිත", "සා", "විසා", "අනුර", "දෙට",
    "මූල", "පුවසල", "උත්තරසල", "සුවණ", "දෙනට", "සියාවස",
    "පුවපුටුප", "උත්තරපුටුප", "රේවතී"
]

# නැකත් අධිපති ග්‍රහයින්
NAK_LORDS = [
    "කේතු", "සිකුරු", "රවි", "සඳු", "අඟහරු", "රාහු",
    "ගුරු", "සෙනසුරු", "බුධ", "කේතු", "සිකුරු", "රවි",
    "සඳු", "අඟහරු", "රාහු", "ගුරු", "සෙනසුරු", "බුධ",
    "කේතු", "සිකුරු", "රවි", "සඳු", "අඟහරු", "රාහු",
    "ගුරු", "සෙනසුරු", "බුධ"
]

# නැකත් ගණය (Gana) - ඔබගේ වගුව අනුව
NAK_GANA = [
    "දේව",      # 1. අශ්විනී
    "මනුෂ්‍ය",   # 2. භරණී
    "රාක්ෂස",   # 3. කෘත්තිකා
    "මනුෂ්‍ය",   # 4. රෝහණී
    "දේව",      # 5. මුවසිරිස
    "මනුෂ්‍ය",   # 6. අද
    "දේව",      # 7. පුනාවස
    "දේව",      # 8. පුෂ
    "රාක්ෂස",   # 9. අස්ලිස
    "රාක්ෂස",   # 10. මා
    "මනුෂ්‍ය",   # 11. පුවපල්
    "මනුෂ්‍ය",   # 12. උත්තරපල්
    "දේව",      # 13. හත
    "රාක්ෂස",   # 14. සිත
    "දේව",      # 15. සා
    "රාක්ෂස",   # 16. විසා
    "දේව",      # 17. අනුර
    "රාක්ෂස",   # 18. දෙට
    "රාක්ෂස",   # 19. මූල
    "මනුෂ්‍ය",   # 20. පුවසල
    "මනුෂ්‍ය",   # 21. උත්තරසල
    "දේව",      # 22. සුවණ
    "රාක්ෂස",   # 23. දෙනට
    "රාක්ෂස",   # 24. සියාවස
    "මනුෂ්‍ය",   # 25. පුවපුටුප
    "මනුෂ්‍ය",   # 26. උත්තරපුටුප
    "දේව"       # 27. රේවතී
]

# නැකත් යෝනිය (Yoni) - ඔබගේ වගුව අනුව
NAK_YONI = [
    "අශ්වයා",      # 1. අශ්විනී - අශ්ව
    "ඇතා",         # 2. භරණී - ගජ (ඇත්)
    "බැටළුවා",     # 3. කෘත්තිකා - බැටළු
    "සර්පයා",       # 4. රෝහණී - සර්ප
    "සර්පයා",       # 5. මුවසිරිස - සර්ප
    "බල්ලා",        # 6. අද - සුනඛ (බල්ලා)
    "මීයා",         # 7. පුනාවස - මූෂික (මීයා)
    "බැටළුවා",     # 8. පුෂ - බැටළු
    "මීයා",         # 9. අස්ලිස - මූෂික (මීයා)
    "මීයා",         # 10. මා - මූෂික (මීයා)
    "මීයා",         # 11. පුවපල් - මූෂික (මීයා)
    "ගවයා",         # 12. උත්තරපල් - ගව
    "මීහරක්",       # 13. හත - මහිෂ (මීහරක්)
    "ව්‍යාඝ්‍රයා",   # 14. සිත - ව්‍යාඝ්‍ර (වියා)
    "මීහරක්",       # 15. සා - මහිෂ (මීහරක්)
    "ව්‍යාඝ්‍රයා",   # 16. විසා - ව්‍යාඝ්‍ර (වියා)
    "මුවා",         # 17. අනුර - මෘග (මුවා)
    "මුවා",         # 18. දෙට - මෘග (මුවා)
    "බල්ලා",        # 19. මූල - සුනඛ (බල්ලා)
    "වඳුරා",        # 20. පුවසල - වඳුරු
    "මුගටියා",      # 21. උත්තරසල - නකුල (මුගටියා)
    "වඳුරා",        # 22. සුවණ - වඳුරු
    "සිංහයා",       # 23. දෙනට - සිංහ
    "අශ්වයා",       # 24. සියාවස - අශ්ව
    "සිංහයා",       # 25. පුවපුටුප - සිංහ
    "ගවයා",         # 26. උත්තරපුටුප - ගව
    "ඇතා"           # 27. රේවතී - ගජ (ඇත්)
]

# නැකත් ජන්ම ලිංගය
NAK_LINGA = [
    "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ",
    "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "පුරුෂ", "පුරුෂ",
    "පුරුෂ", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ",
    "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ",
    "ස්ත්‍රී", "පුරුෂ", "පුරුෂ"
]

# දිස්ත්‍රික්ක
DISTRICTS = {
    "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "කළුතර": (6.5854, 79.9607),
    "මහනුවර": (7.2906, 80.6337), "මාතලේ": (7.4675, 80.6234), "නුවරඑළිය": (6.9497, 80.7891),
    "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245),
    "යාපනය": (9.6615, 80.0255), "කුරුණෑගල": (7.4863, 80.3647), "අනුරාධපුරය": (8.3114, 80.4037),
    "බදුල්ල": (6.9934, 81.0550), "රත්නපුරය": (6.7056, 80.3847), "කෑගල්ල": (7.2513, 80.3464)
}

# ග්‍රහයින්
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

# ==================== Planet in Bhava ====================
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

# ==================== Nakshatra Calculation ====================
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
        
        # Rashi chart
        rashi_chart = {rashi: [] for rashi in RA_NAMES}
        for p_name, data in planet_positions.items():
            rashi_name = data["rashi"]
            if rashi_name in rashi_chart:
                rashi_chart[rashi_name].append(p_name)
        
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
            "bhava_map": bhava_map,
            "rashi_chart": rashi_chart
        }, None
        
    except Exception as e:
        return None, f"දෝෂය: {str(e)}"

# ==================== Display Rashi Chart ====================
def display_rashi_chart(rashi_chart, lagna_name):
    st.subheader(f"🕉️ රාශි චක්‍රය (ලග්නය: {lagna_name})")
    
    rashi_order = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා",
                   "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
    
    if lagna_name in rashi_order:
        idx = rashi_order.index(lagna_name)
        rotated = rashi_order[idx:] + rashi_order[:idx]
    else:
        rotated = rashi_order
    
    symbols = {"රවි": "☀️", "සඳු": "🌙", "කුජ": "♂️", "බුධ": "☿",
               "ගුරු": "♃", "සිකුරු": "♀️", "ශනි": "♄", "රාහු": "☊", "කේතු": "☋"}
    
    st.markdown('<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0;">', unsafe_allow_html=True)
    
    for i, rashi in enumerate(rotated):
        planets = rashi_chart.get(rashi, [])
        if planets is None:
            planets = []
        
        planet_symbols = []
        for p in planets[:3]:
            if p and isinstance(p, str):
                short = p.split(' (')[0]
                planet_symbols.append(symbols.get(short, "●"))
        
        display = " ".join(planet_symbols) if planet_symbols else "—"
        is_lagna = (i == 0)
        bg = "#e94560" if is_lagna else "#0f3460"
        border = "2px solid #ffd700" if is_lagna else "1px solid #e94560"
        text_color = "#ffd700" if is_lagna else "#e94560"
        
        st.markdown(f'''
        <div style="background:{bg}; border-radius:10px; padding:10px; text-align:center; border:{border};">
            <strong style="color:{text_color}; display:block; margin-bottom:5px;">{rashi}</strong>
            <small style="color:#f0f0f0;">{display}</small>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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
    
    display_rashi_chart(r["rashi_chart"], r["lagna"])
    
    st.subheader("🏠 ග්‍රහ පිහිටීම් (භාව අනුව)")
    bhava_items = list(r["bhava_map"].items())
    col1, col2 = st.columns(2)
    for i, (bhava, planets) in enumerate(bhava_items):
        with col1 if i < 6 else col2:
            if planets and len(planets) > 0:
                st.markdown(f"**{bhava} වන භාවය:** {', '.join(planets)}")
            else:
                st.markdown(f"**{bhava} වන භාවය:** -")
    
    with st.expander("🔭 ග්‍රහයින්ගේ සම්පූර්ණ දේශාංශ"):
        for planet, data in r["planet_positions"].items():
            st.write(f"**{planet}:** {data['rashi']} රාශියේ {data['degree']:.2f}°")
    
    if st.button("🤖 AI පලාපල විස්තරය", use_container_width=True):
        with st.spinner("AI විශ්ලේෂණය කරමින්..."):
            st.session_state.ai_report = generate_ai_report(r)
            st.rerun()
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report, unsafe_allow_html=True)
    
    if st.button("🔄 නව ගණනය කිරීමක්", use_container_width=True):
        st.session_state.show_calculation = False
        st.session_state.calculation_result = None
        st.session_state.ai_report = None
        st.rerun()

# ==================== AI Report ====================
def get_api_keys():
    keys = []
    try:
        for i in range(1, 4):
            key = st.secrets.get(f"GEMINI_API_KEY_{i}")
            if key and len(str(key)) > 10:
                keys.append(str(key))
    except:
        pass
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        keys.append(env_key)
    return keys

def generate_ai_report(data):
    keys = get_api_keys()
    salutation = "මහතා" if data.get('gender') == "පිරිමි" else "මහත්මිය"
    
    prompt = f"""ඔබ ශ්‍රී ලංකාවේ ප්‍රමුඛ ජ්‍යොතිෂවේදියෙකි.

දත්ත:
නම: {data['name']}
ලිංගය: {data['gender']}
උපන් දිනය: {data['dob']}
උපන් වේලාව: {data['time']}
ස්ථානය: {data['city']}
ලග්නය: {data['lagna']} ({data['lagna_lord']})
නැකත: {data['nakshathra']} (පාදය {data['nak_pada']}, අධිපති: {data['nak_lord']})
ගණය: {data['nak_gana']}
යෝනිය: {data['nak_yoni']}

පහත සඳහන් කරුණු ඇතුළත් පලාපල වාර්තාවක් සිංහලෙන් ලියන්න:
1. නැකතේ ස්වභාවය
2. ලග්නයේ බලපෑම
3. සුදුසු වෘත්තීන්
4. පිළියම් සහ උපදෙස්"""

    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response and response.text:
                return f"""<div class="result-card">
<h2>🌟 {data['name']} {salutation} ගේ පලාපල වාර්තාව</h2>
<hr>
{response.text}
<hr>
<p style="text-align:center">© AstroPro SL - Lahiri Ayanamsa</p>
</div>"""
        except:
            continue
    
    return f"""<div class="result-card">
<h2>🌟 {data['name']} {salutation} ගේ පලාපල වාර්තාව</h2>
<hr>
<h3>📋 {data['nakshathra']} නැකත</h3>
<p>{data['nak_gana']} ගණය, {data['nak_yoni']} යෝනිය. අධිපති: {data['nak_lord']}</p>
<h3>⭐ {data['lagna']} ලග්නය</h3>
<p>අධිපති: {data['lagna_lord']}</p>
<h3>🙏 පිළියම්</h3>
<p>"ඕම් {data['nak_lord']}වේ නමඃ" මන්ත්‍රය ජප කරන්න.</p>
<hr>
<p style="text-align:center">© AstroPro SL</p>
</div>"""

# ==================== Main Form ====================
def calculation_form():
    st.markdown('<div class="main-header"><h1>🔮 AstroPro SL</h1><p>ශ්‍රී ලාංකීය ජ්‍යොතිෂය (Lahiri Ayanamsa)</p></div>', unsafe_allow_html=True)
    
    if EPHE_READY:
        st.success("✅ Swiss Ephemeris සක්‍රියයි")
    else:
        st.warning("⚠️ Swiss Ephemeris සැකසීමේ ගැටළුවක්")
    
    with st.form("astro_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("නම *")
        with col2:
            gender = st.selectbox("ලිංගය", ["පිරිමි", "ගැහැණු"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20),
                               min_value=datetime(1950, 1, 1), max_value=datetime(2040, 12, 31))
        with col2:
            hour = st.number_input("පැය (0-23)", 0, 23, 10)
        with col3:
            minute = st.number_input("මිනිත්තු (0-59)", 0, 59, 30)
        
        city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
        
        if st.form_submit_button("🔮 කේන්දරය ගණනය කරන්න", use_container_width=True):
            if not name.strip():
                st.error("නම ඇතුළත් කරන්න")
            else:
                with st.spinner("ගණනය කරමින්..."):
                    result, error = calculate_astrology(name, gender, dob, hour, minute, city)
                    if result:
                        st.session_state.calculation_result = result
                        st.session_state.show_calculation = True
                        st.success("✅ සාර්ථකයි!")
                        st.rerun()
                    else:
                        st.error(error)

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
