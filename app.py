import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import requests
import json

# --- Configuration ---
st.set_page_config(page_title="AstroPro Visual SL", page_icon="☸️", layout="wide")

# --- Multi-API AI Support ---
def get_ai_prediction(summary_data):
    keys = [
        st.secrets.get("GEMINI_API_KEY_1"),
        st.secrets.get("GEMINI_API_KEY_2"),
        st.secrets.get("GEMINI_API_KEY_3")
    ]
    
    prompt = f"ඔබ ප්‍රවීණ ජ්‍යොතිෂවේදියෙකි. මෙම දත්ත මත පදනම්ව ඉතා දීර්ඝ පලාපල විග්‍රහයක් සිංහලෙන් කරන්න: {summary_data}"
    
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue
    return "කණගාටුයි, සියලුම AI සේවාවන් කාර්යබහුලයි."

# --- සාම්ප්‍රදායික කේන්ද්‍ර සටහන ඇඳීමේ Function එක ---
def draw_horoscope_chart(pos_map, lagna_idx):
    img = Image.new('RGB', (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for i in range(5):
        draw.line([(i*100, 0), (i*100, 400)], fill="black", width=2)
        draw.line([(0, i*100), (400, i*100)], fill="black", width=2)
    draw.rectangle([100, 100, 300, 300], fill="#f0f0f0", outline="black")
    
    grid_map = {11:(0,0), 0:(100,0), 1:(200,0), 2:(300,0), 10:(0,100), 3:(300,100),
                9:(0,200), 4:(300,200), 8:(0,300), 7:(100,300), 6:(200,300), 5:(300,300)}
    
    for r_idx, (x, y) in grid_map.items():
        if r_idx == lagna_idx:
            draw.text((x+40, y+10), "L", fill="red")
        planets = pos_map.get(r_idx, [])
        for i, p in enumerate(planets):
            draw.text((x+10, y+30+(i*15)), p, fill="black")
    return img

# --- Data Tables ---
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ දත්ත ඇතුළත් කරන්න")
    name = st.text_input("සම්පූර්ණ නම")
    dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20), min_value=datetime(1900,1,1), max_value=datetime(2100,12,31))
    t_col = st.columns(3)
    h = t_col[0].number_input("පැය", 0, 23, 10)
    m = t_col[1].number_input("විනාඩි", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය", ["කෑගල්ල", "කොළඹ", "ගම්පහ", "මහනුවර", "ගාල්ල"])
    
    if st.button("දත්ත මකන්න"):
        st.rerun()

# --- Main App ---
st.title("☸️ AstroPro SL - Visual Horoscope")

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    if not name:
        st.error("කරුණාකර නම ඇතුළත් කරන්න.")
    else:
        try:
            # 1. Astrology Calculations (AI රහිතව)
            jd = swe.julday(dob.year, dob.month, dob.day, h + m/60.0 - 5.5)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # ලග්නය සහ ග්‍රහයන්
            houses, ascmc = swe.houses_ex(jd, 7.2, 80.3, b'P', swe.FLG_SIDEREAL)
            lagna_idx = int(ascmc[0] / 30)
            
            planets_def = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
            pos_map = {i: [] for i in range(12)}
            moon_lon = 0
            
            for p_name, p_id in planets_def.items():
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                if p_id == 1: moon_lon = res[0]
                r_idx = int(res[0] / 30)
                pos_map[r_idx].append(p_name)
            
            nak_idx = int(moon_lon / (360/27))
            gana = ["දේව", "මනුෂ්‍ය", "රාක්ෂ"][nak_idx % 3]
            yoni = ["අශ්ව", "එළු", "සර්ප", "බැල්ලි", "බළල්", "මූෂික", "මී හරක්", "ව්‍යාඝ්‍ර", "මුව", "මුගටි", "වඳුරු", "සිංහ", "එළදෙන", "අලියා"][nak_idx % 14]
            linga = "පුරුෂ" if (nak_idx % 2 == 0) else "ස්ත්‍රී"
            
            # Results Display
            st.subheader(f"👤 නම: {name}")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(draw_horoscope_chart(pos_map, lagna_idx), caption="සාම්ප්‍රදායික කේන්ද්‍ර සටහන")
            
            with col2:
                st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]} | **නැකත:** {NAK_NAMES[nak_idx]}")
                st.write(f"**ගණය:** {gana} | **යෝනිය:** {yoni} | **ලිංගය:** {linga}")
                st.info(f"උපතේදී මහා දශාව: {DASHA_LORDS[nak_idx % 9]}")

            # Session State එකේ දත්ත තබා ගැනීම (AI එකට යැවීමට)
            summary = f"නම: {name}, ලග්නය: {RA_NAMES[lagna_idx]}, නැකත: {NAK_NAMES[nak_idx]}, ගණය: {gana}, යෝනිය: {yoni}, ලිංගය: {linga}."
            st.session_state['astro_summary'] = summary
            
            # Firebase වෙත දත්ත යැවීම
            f_url = st.secrets.get("FIREBASE_DATABASE_URL")
            if f_url:
                requests.post(f"{f_url}/logs.json", data=json.dumps({"name": name, "lagna": RA_NAMES[lagna_idx], "time": str(datetime.now())}))
                st.toast("දත්ත Firebase වෙත යොමු කළා.")

        except Exception as e:
            st.error(f"Error: {e}")

# AI බොත්තම (ගණනය කිරීම අවසන් වූ පසු පමණක් දිස්වේ)
if 'astro_summary' in st.session_state:
    st.divider()
    if st.button("🤖 AI දීර්ඝ පලාපල විස්තරය ලබාගන්න"):
        with st.spinner("Gemini AI පලාපල විශ්ලේෂණය කරමින්..."):
            prediction = get_ai_prediction(st.session_state['astro_summary'])
            st.markdown(prediction)
