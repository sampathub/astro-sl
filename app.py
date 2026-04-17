import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import requests
import json
import io

# --- Configuration ---
st.set_page_config(page_title="AstroPro SL v9", page_icon="☸️", layout="wide")

# --- Multi-API AI Support ---
def get_ai_response(prompt):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2"), st.secrets.get("GEMINI_API_KEY_3")]
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            return model.generate_content(prompt).text
        except: continue
    return "AI සේවාව දැනට කාර්යබහුලයි. පසුව උත්සාහ කරන්න."

# --- Chart Drawing Function ---
def draw_sl_chart(pos_map, lagna_idx):
    img = Image.new('RGB', (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for i in range(5):
        draw.line([(i*100, 0), (i*100, 400)], fill="black", width=2)
        draw.line([(0, i*100), (400, i*100)], fill="black", width=2)
    draw.rectangle([100, 100, 300, 300], fill="#f0f0f0", outline="black", width=2)
    
    grid_map = {11:(0,0), 0:(100,0), 1:(200,0), 2:(300,0), 10:(0,100), 3:(300,100),
                9:(0,200), 4:(300,200), 8:(0,300), 7:(100,300), 6:(200,300), 5:(300,300)}
    
    for r_idx, (x, y) in grid_map.items():
        names = pos_map.get(r_idx, [])
        if r_idx == lagna_idx:
            draw.text((x+40, y+10), "L", fill="red")
        y_off = 30
        for n in names:
            draw.text((x+20, y+y_off), n, fill="black")
            y_off += 15
    return img

# --- Data Arrays ---
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("👤 විස්තර ඇතුළත් කරන්න")
    u_name = st.text_input("සම්පූර්ණ නම")
    # මෙහි min_value සහ max_value ඉවත් කර ඇත
    u_dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20))
    t_col = st.columns(3)
    u_h = t_col[0].number_input("පැය", 0, 23, 12)
    u_m = t_col[1].number_input("විනාඩි", 0, 59, 0)
    u_s = t_col[2].number_input("තත්", 0, 59, 0)
    u_city = st.selectbox("උපන් ස්ථානය (දිස්ත්‍රික්කය)", ["කෑගල්ල", "කොළඹ", "ගම්පහ", "මහනුවර", "ගාල්ල", "මාතර"])

# --- Main Logic ---
st.title("☸️ AstroPro SL - Visual & AI Analysis")

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    # නම ඇතුළත් කර ඇත්දැයි පරීක්ෂා කිරීම (Validation)
    if not u_name.strip():
        st.error("කරුණාකර ඉදිරියට යාමට 'නම' ඇතුළත් කරන්න.")
    else:
        try:
            # Astro Calculations
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, u_h + u_m/60.0 - 5.5)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            houses, ascmc = swe.houses_ex(jd, 7.25, 80.34, b'P', swe.FLG_SIDEREAL) 
            lagna_idx = int(ascmc[0] / 30)
            
            planets = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
            pos_map = {i: [] for i in range(12)}
            moon_lon = 0
            
            for n, p_id in planets.items():
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                if p_id == 1: moon_lon = res[0]
                r_idx = int(res[0] / 30)
                pos_map[r_idx].append(n)
                
            nak_idx = int(moon_lon / (360/27))
            d_lord_idx = nak_idx % 9
            
            # පංචාංග තොරතුරු ගණනය (Manual)
            gana = ["දේව", "මනුෂ්‍ය", "රාක්ෂ"][nak_idx % 3]
            yoni = ["අශ්ව", "එළු", "සර්ප", "බැල්ලි", "බළල්", "මූෂික", "මී හරක්", "ව්‍යාඝ්‍ර", "මුව", "මුගටි", "වඳුරු", "සිංහ", "එළදෙන", "අලියා"][nak_idx % 14]
            linga = "පුරුෂ" if nak_idx % 2 == 0 else "ස්ත්‍රී"

            # දත්ත පෙන්වීම
            st.session_state['astro_data'] = {
                "name": u_name, "lagna": RA_NAMES[lagna_idx], "nakatha": NAK_NAMES[nak_idx],
                "gana": gana, "yoni": yoni, "linga": linga, "dasha": DASHA_LORDS[d_lord_idx]
            }
            
            st.header(f"☸️ {u_name} - කේන්ද්‍ර විස්තර")
            c1, c2 = st.columns([1, 1])
            with c1:
                st.image(draw_sl_chart(pos_map, lagna_idx), caption="සාම්ප්‍රදායික කේන්ද්‍ර සටහන")
            with c2:
                st.subheader("📝 ගණනය කළ තොරතුරු")
                st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]}")
                st.write(f"**නැකත:** {NAK_NAMES[nak_idx]}")
                st.write(f"**ගණය:** {gana} | **යෝනිය:** {yoni} | **ලිංගය:** {linga}")
                st.success(f"වර්තමාන මහා දශාව: {DASHA_LORDS[d_lord_idx]}")

            # Firebase සේව් කිරීම (AI එකට පෙර)
            f_url = st.secrets.get("FIREBASE_DATABASE_URL")
            if f_url:
                fb_payload = {
                    "user": u_name, "dob": str(u_dob), "lagna": RA_NAMES[lagna_idx],
                    "nakatha": NAK_NAMES[nak_idx], "timestamp": str(datetime.now())
                }
                requests.post(f"{f_url}/astro_records.json", data=json.dumps(fb_payload))

        except Exception as e:
            st.error(f"ගණනය කිරීමේ දෝෂයකි: {e}")

# AI පලාපල බොත්තම (ගණනය කිරීමෙන් පසු පමණක් දිස්වේ)
if 'astro_data' in st.session_state:
    st.divider()
    if st.button("AI දීර්ඝ පලාපල විස්තරය ලබාගන්න"):
        d = st.session_state['astro_data']
        with st.spinner("Gemini AI පලාපල විශ්ලේෂණය කරමින්..."):
            prompt = f"""
            ලාංකීය ජ්‍යොතිෂ්‍ය ක්‍රමයට අනුව මෙම තොරතුරු මත පදනම්ව දීර්ඝ පලාපල විස්තරයක් සිංහලෙන් ලියන්න.
            නම: {d['name']}, ලග්නය: {d['lagna']}, නැකත: {d['nakatha']}, ගණය: {d['gana']}, යෝනිය: {d['yoni']}, ලිංගය: {d['linga']}.
            චරිතය, අධ්‍යාපනය, රැකියාව, සෞඛ්‍යය සහ අනාගතය ගැන වෙන වෙනම විස්තර කරන්න.
            """
            result = get_ai_response(prompt)
            st.markdown("### 🤖 Gemini AI පලාපල විග්‍රහය")
            st.write(result)
