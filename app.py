import streamlit as st
import swisseph as swe
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
import json
import google.generativeai as genai

# --- Mobile Optimized Configuration ---
st.set_page_config(page_title="AstroPro SL", page_icon="☸️", layout="centered")

st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { max-width: 800px; margin: auto; }
        .stButton>button { width: 100%; border-radius: 5px; }
        img { width: 100%; height: auto; }
    </style>
""", unsafe_allow_html=True)

# --- Logic: Planet Bhava Calculation ---
def get_planet_bhava(planet_lon, cusps):
    """ග්‍රහයාගේ අංශකය අනුව භාවය (1-12) තීරණය කිරීම"""
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start <= end:
            if start <= planet_lon < end: return i + 1
        else: # Boundary crossing 360
            if planet_lon >= start or planet_lon < end: return i + 1
    return 1

# --- AI Prediction ---
def get_ai_prediction(summary_data):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2")]
    prompt = f"""
    ඔබ ප්‍රවීණ ශ්‍රී ලාංකීය ජ්‍යොතිෂවේදියෙකි. පහත දත්ත මත පදනම්ව චරිතය, අධ්‍යාපනය, රැකියාව, සෞඛ්‍යය සහ විවාහය ගැන දීර්ඝ පලාපල විස්තරයක් සිංහලෙන් ලියන්න. 
    දත්ත: {summary_data}
    """
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash') # Updated to a stable model
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return "කණගාටුයි, AI සේවාව තාවකාලිකව කාර්යබහුලයි."

# --- Data ---
DISTRICTS = {"කොළඹ": (6.9271, 79.8612), "මහනුවර": (7.2906, 80.6337), "ගාල්ල": (6.0535, 80.2210), "කෑගල්ල": (7.2513, 80.3464)} # තවත් එකතු කරන්න
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

# --- UI Sidebar ---
with st.sidebar:
    st.header("👤 පරිශීලක තොරතුරු")
    u_name = st.text_input("නම")
    u_dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20))
    c1, c2 = st.columns(2)
    u_h = c1.number_input("පැය", 0, 23, 10)
    u_m = c2.number_input("මිනිත්තු", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

# --- Logic Implementation ---
if st.button("කේන්දරය බලන්න"):
    if not u_name: st.warning("නම ඇතුළත් කරන්න.")
    else:
        try:
            lat, lon = DISTRICTS[u_city]
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, (u_h + u_m/60) - 5.5)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # භාව සන්ධි ගණනය
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            lagna_bhava = get_planet_bhava(ascmc[0], houses) # ලග්නය භාවයකට අනුරූපව
            
            # ග්‍රහ පිහිටීම් (භාව අනුව)
            planets_def = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
            bhava_map = {i: [] for i in range(1, 13)}
            moon_lon = 0
            
            for p_name, p_id in planets_def.items():
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                if p_id == 1: moon_lon = res[0]
                p_bhava = get_planet_bhava(res[0], houses)
                bhava_map[p_bhava].append(p_name)
            
            nak_idx = int(moon_lon / (360/27))
            
            # Display Results
            st.success(f"{u_name} මහතාගේ/මියගේ ජන්ම පත්‍රය")
            
            st.write(f"**ලග්නය:** {RA_NAMES[int(ascmc[0]/30)]}")
            st.write(f"**නැකත:** {NAK_NAMES[nak_idx]}")
            
            # භාව අනුව ග්‍රහ පිහිටීම් වගුව
            st.subheader("ග්‍රහ පිහිටීම් (භාව අනුව)")
            for b in range(1, 13):
                if bhava_map[b]:
                    st.write(f"**{b} වන භාවය:** {', '.join(bhava_map[b])}")
            
            st.session_state['astro_data'] = {"name": u_name, "nak": NAK_NAMES[nak_idx], "bhava_data": str(bhava_map)}

        except Exception as e:
            st.error(f"දෝෂයක් ඇති විය: {e}")

# --- AI Prediction ---
if 'astro_data' in st.session_state:
    if st.button("🔮 පලාපල විස්තරය ලබාගන්න"):
        with st.spinner("AI විශ්ලේෂණය කරමින්..."):
            ai_res = get_ai_prediction(st.session_state['astro_data'])
            st.markdown("### 🤖 පලාපල වාර්තාව")
            st.write(ai_res)
