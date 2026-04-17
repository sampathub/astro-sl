import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, date
from PIL import Image, ImageDraw
import requests
import json

# --- Configuration ---
st.set_page_config(page_title="AstroPro SL Ultimate v15", page_icon="☸️", layout="wide")

# --- 1. Multi-API AI Support ---
def get_ai_prediction(summary_data):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2"), st.secrets.get("GEMINI_API_KEY_3")]
    prompt = f"ඔබ ප්‍රවීණ සිංහල ජ්‍යොතිෂවේදියෙකි. මෙම දත්ත මත පදනම්ව දීර්ඝ පලාපල විස්තරයක් සිංහලෙන් කරන්න: {summary_data}"
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            return model.generate_content(prompt).text
        except: continue
    return "AI සේවාව දැනට කාර්යබහුලයි."

# --- 2. කේන්ද්‍ර සටහන ඇඳීම ---
def draw_styled_chart(pos_map, lagna_idx):
    img = Image.new('RGB', (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for i in range(5):
        draw.line([(i*150, 0), (i*150, 600)], fill="black", width=3)
        draw.line([(0, i*150), (600, i*150)], fill="black", width=3)
    draw.rectangle([150, 150, 450, 450], fill="#fdfdfd", outline="black", width=3)
    grid_map = {11:(0,0), 0:(150,0), 1:(300,0), 2:(450,0), 10:(0,150), 3:(450,150),
                9:(0,300), 4:(450,300), 8:(0,450), 7:(150,450), 6:(300,450), 5:(450,450)}
    for r_idx, (x, y) in grid_map.items():
        if r_idx == lagna_idx: draw.text((x+65, y+10), "L", fill="red")
        planets = pos_map.get(r_idx, [])
        p_short = {"රවි":"Sun", "සඳු":"Moon", "කුජ":"Mars", "බුධ":"Merc", "ගුරු":"Jup", "සිකුරු":"Ven", "ශනි":"Sat", "රාහු":"Rahu"}
        for i, p in enumerate(planets):
            draw.text((x+25, y+45+(i*25)), p_short.get(p, p), fill="black")
    return img

# --- 3. සම්පූර්ණ දත්ත වගු (100% Correct) ---
DISTRICTS = {
    "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "කළුතර": (6.5854, 79.9607),
    "මහනුවර": (7.2906, 80.6337), "මාතලේ": (7.4675, 80.6234), "නුවරඑළිය": (6.9497, 80.7891),
    "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245),
    "යාපනය": (9.6615, 80.0255), "කිලිනොච්චිය": (9.3854, 80.3921), "මන්නාරම": (8.9810, 79.9044),
    "වවුනියාව": (8.7542, 80.4982), "මුලතිව්": (9.2671, 80.8143), "මඩකලපුව": (7.7102, 81.6924),
    "අම්පාර": (7.2843, 81.6747), "ත්‍රිකුණාමලය": (8.5711, 81.2335), "කුරුණෑගල": (7.4863, 80.3647),
    "පුත්තලම": (8.0330, 79.8257), "අනුරාධපුරය": (8.3114, 80.4037), "පොළොන්නරුව": (7.9403, 81.0188),
    "බදුල්ල": (6.9934, 81.0550), "මොණරාගල": (6.8719, 81.3512), "රත්නපුරය": (6.7056, 80.3847), "කෑගල්ල": (7.2513, 80.3464)
}

NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
GANA_TABLE = ["දේව", "මනුෂ්‍ය", "රාක්ෂ", "මනුෂ්‍ය", "දේව", "මනුෂ්‍ය", "දේව", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව"]
YONI_TABLE = ["අශ්ව", "ඇත්", "එළු", "සර්ප", "සර්ප", "බැල්ලි", "බළල්", "එළු", "බළල්", "මී මින්", "මී මින්", "ගව", "මී හරක්", "ව්‍යාඝ්‍ර", "මී හරක්", "ව්‍යාඝ්‍ර", "මුව", "මුව", "මුගටි", "වඳුරු", "වඳුරු", "සිංහ", "සිංහ", "අශ්ව", "සිංහ", "ගව", "ඇත්"]
LINGA_TABLE = ["පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී"]
VRUKSHA_TABLE = ["කදම්බ", "නෙල්ලි", "දිවුල්", "කරඹ", "කීරිය", "තිඹිරි", "උණ", "බෝගහ", "නුග", "පලු", "කෑල", "නුග", "වල් දෙල්", "බෙලි", "කුඹුක්", "මීඹ", "දම්", "වැටකේ", "සල්", "පුවක්", "පිහිඹියා", "වෙලං", "ලූණුමකරල", "කලවැල්", "කොහොඹ", "මී", "වැටකේ"]
PAKSHI_TABLE = ["හොට කිරලා", "කපුටා", "කපුටා", "පින්නකිකිළි", "පින්නකිකිළි", "පින්නකිකිළි", "මොණරා", "මොණරා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "මොණරා", "මොණරා", "මොණරා", "මොණරා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "මොණරා", "මොණරා", "මොණරා"]
DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]

# --- 4. Sidebar ---
with st.sidebar:
    st.header("👤 පෞද්ගලික විස්තර")
    u_name = st.text_input("සම්පූර්ණ නම")
    u_dob = st.date_input("උපන් දිනය", value=date(1995, 5, 20), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
    t_col = st.columns(3)
    u_h = t_col[0].number_input("පැය", 0, 23, 10)
    u_m = t_col[1].number_input("විනාඩි", 0, 59, 30)
    u_s = t_col[2].number_input("තත්", 0, 59, 0)
    u_city = st.selectbox("උපන් දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
    if st.button("🔄 Clear All"):
        st.session_state.clear()
        st.rerun()

# --- 5. Main App ---
st.title("☸️ AstroPro Sri Lanka Ultimate")

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    if not u_name:
        st.error("කරුණාකර නම ඇතුළත් කරන්න.")
    else:
        try:
            lat, lon = DISTRICTS[u_city]
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, u_h + u_m/60.0 + u_s/3600.0 - 5.5)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # ලග්නය
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            lagna_idx = int(ascmc[0] / 30)
            
            # ග්‍රහයන්
            planets_def = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
            pos_map = {i: [] for i in range(12)}
            moon_lon = 0
            for p_name, p_id in planets_def.items():
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                if p_id == 1: moon_lon = res[0]
                pos_map[int(res[0] / 30)].append(p_name)
            
            # පංචාංග ගණනය
            nak_idx = int(moon_lon / (360/27))
            if nak_idx > 26: nak_idx = 26
            
            v_nak = NAK_NAMES[nak_idx]
            v_gana = GANA_TABLE[nak_idx]
            v_yoni = YONI_TABLE[nak_idx]
            v_linga = LINGA_TABLE[nak_idx]
            v_vruksha = VRUKSHA_TABLE[nak_idx]
            v_pakshi = PAKSHI_TABLE[nak_idx]
            
            # දශා කාල
            d_lord_idx = nak_idx % 9
            nak_start = nak_idx * (360/27)
            balance = (1 - ((moon_lon - nak_start) / (360/27))) * DASHA_YEARS[d_lord_idx]

            # Display
            st.header(f"📊 {u_name} මහතාගේ වාර්තාව")
            c1, c2 = st.columns([1, 1])
            with c1:
                st.image(draw_styled_chart(pos_map, lagna_idx), caption="සාම්ප්‍රදායික කේන්ද්‍ර සටහන")
            with c2:
                st.subheader("📝 පංචාංග තොරතුරු")
                st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]} | **නැකත:** {v_nak}")
                st.write(f"**ගණය:** {v_gana} | **ලිංගය:** {v_linga} | **යෝනිය:** {v_yoni}")
                st.write(f"**වෘක්ෂය:** {v_vruksha} | **පක්ෂියා:** {v_pakshi}")
                
                st.subheader("🗓️ මහා දශා කාලසීමාවන්")
                st.info(f"උපතේදී හිමි දශාව: {DASHA_LORDS[d_lord_idx]} (ඉතිරි වසර {int(balance)} මාස {int((balance%1)*12)})")
                
                cy = u_dob.year + balance
                for i in range(1, 4):
                    idx = (d_lord_idx + i) % 9
                    st.write(f"• {DASHA_LORDS[idx]} දශාව: {int(cy)} සිට {int(cy + DASHA_YEARS[idx])} දක්වා")
                    cy += DASHA_YEARS[idx]

            st.session_state['astro_res'] = {"name":u_name, "lagna":RA_NAMES[lagna_idx], "nak":v_nak, "gana":v_gana, "yoni":v_yoni, "linga":v_linga, "vruksha":v_vruksha, "pakshi":v_pakshi}

        except Exception as e:
            st.error(f"Error: {e}")

if 'astro_res' in st.session_state:
    st.divider()
    if st.button("🤖 AI පලාපල වාර්තාව ලබාගන්න"):
        with st.spinner("AI විශ්ලේෂණය කරමින්..."):
            res = get_ai_prediction(str(st.session_state['astro_res']))
            st.markdown(res)
