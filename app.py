import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, date
from PIL import Image, ImageDraw
import requests
import json

# --- Configuration ---
st.set_page_config(page_title="AstroPro SL Ultimate", page_icon="☸️", layout="wide")

# --- 1. Multi-API AI Support ---
def get_ai_prediction(summary_data):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2"), st.secrets.get("GEMINI_API_KEY_3")]
    prompt = f"ඔබ ප්‍රවීණ ජ්‍යොතිෂවේදියෙකි. මෙම දත්ත මත පදනම්ව දීර්ඝ පලාපල විස්තරයක් සිංහලෙන් කරන්න: {summary_data}"
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt).text
        except: continue
    return "AI සේවාව දැනට කාර්යබහුලයි."

# --- 2. කේන්ද්‍ර සටහන පැහැදිලිව ඇඳීම ---
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

# --- 3. දත්ත වගු ---
DISTRICTS = {"කෑගල්ල": (7.2513, 80.3464), "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "මහනුවර": (7.2906, 80.6337), "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550), "හම්බන්තොට": (6.1246, 81.1245), "යාපනය": (9.6615, 80.0255), "කුරුණෑගල": (7.4863, 80.3647), "අනුරාධපුරය": (8.3114, 80.4037), "බදුල්ල": (6.9934, 81.0550), "රත්නපුරය": (6.7056, 80.3847)}
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
VRUKSHA_TABLE = ["කදම්බ", "නෙල්ලි", "දිවුල්", "කරඹ", "කීරිය", "තිඹිරි", "උණ", "බෝගහ", "නුග", "පලු", "කෑල", "නුග", "වල් දෙල්", "බෙලි", "කුඹුක්", "මීඹ", "දම්", "වැටකේ", "සල්", "පුවක්", "පිහිඹියා", "වෙලං", "ලූණුමකරල", "කලවැල්", "කොහොඹ", "මී", "වැටකේ"]
PAKSHI_TABLE = ["හොට කිරලා", "කපුටා", "කපුටා", "පින්නකිකිළි", "පින්නකිකිළි", "පින්නකිකිළි", "මොණරා", "මොණරා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "මොණරා", "මොණරා", "මොණරා", "මොණරා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "මොණරා", "මොණරා", "මොණරා"]
DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# --- 4. Sidebar ---
with st.sidebar:
    st.header("👤 පෞද්ගලික තොරතුරු")
    u_name = st.text_input("සම්පූර්ණ නම")
    # මෙන්න මේ පේළිය තමයි Date Limit එක පාලනය කරන්නේ - දැන් මෙය නිදහස් කර ඇත
    u_dob = st.date_input("උපන් දිනය", value=date(1995, 5, 20), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
    t_col = st.columns(3)
    u_h = t_col[0].number_input("පැය", 0, 23, 10)
    u_m = t_col[1].number_input("විනාඩි", 0, 59, 30)
    u_s = t_col[2].number_input("තත්", 0, 59, 0)
    u_city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
    if st.button("දත්ත මකන්න"):
        st.session_state.clear()
        st.rerun()

# --- 5. Logic ---
st.title("☸️ AstroPro Sri Lanka")

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    if not u_name.strip():
        st.error("කරුණාකර නම ඇතුළත් කරන්න.")
    else:
        try:
            lat, lon = DISTRICTS[u_city]
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, u_h + u_m/60.0 + u_s/3600.0 - 5.5)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            lagna_idx = int(ascmc[0] / 30)
            
            planets_def = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
            pos_map = {i: [] for i in range(12)}
            moon_lon = 0
            for p_name, p_id in planets_def.items():
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                if p_id == 1: moon_lon = res[0]
                pos_map[int(res[0] / 30)].append(p_name)
            
            nak_idx = int(moon_lon / (360/27))
            dasha_idx = nak_idx % 9
            nak_start = nak_idx * (360/27)
            passed_deg = moon_lon - nak_start
            balance_years = (1 - (passed_deg / (360/27))) * DASHA_YEARS[dasha_idx]

            st.session_state['data'] = {"name":u_name, "lagna":RA_NAMES[lagna_idx], "nak":NAK_NAMES[nak_idx], "vruksha":VRUKSHA_TABLE[nak_idx], "pakshi":PAKSHI_TABLE[nak_idx]}

            st.header(f"📊 {u_name} මහතාගේ/මියගේ විස්තර")
            c1, c2 = st.columns([1, 1])
            with c1:
                st.image(draw_styled_chart(pos_map, lagna_idx), caption="පැහැදිලි කේන්ද්‍ර සටහන")
            with c2:
                st.subheader("📝 පංචාංග තොරතුරු")
                st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]} | **නැකත:** {NAK_NAMES[nak_idx]}")
                st.write(f"**වෘක්ෂය:** {VRUKSHA_TABLE[nak_idx]} | **පක්ෂියා:** {PAKSHI_TABLE[nak_idx]}")
                st.write(f"**ගණය:** {['දේව','මනුෂ්‍ය','රාක්ෂ'][nak_idx % 3]}")
                
                st.subheader("🗓️ මහා දශා කාලයන්")
                st.success(f"උපතේදී හිමි දශාව: {DASHA_LORDS[dasha_idx]}")
                st.write(f"ඉතිරි කාලය: වසර {int(balance_years)} යි, මාස {int((balance_years%1)*12)} කි.")
                
                curr_y = u_dob.year + balance_years
                for i in range(1, 4):
                    idx = (dasha_idx + i) % 9
                    st.write(f"• {DASHA_LORDS[idx]} දශාව: {int(curr_y)} සිට {int(curr_y + DASHA_YEARS[idx])} දක්වා")
                    curr_y += DASHA_YEARS[idx]

            # Firebase Logging
            f_url = st.secrets.get("FIREBASE_DATABASE_URL")
            if f_url: requests.post(f"{f_url}/astro.json", data=json.dumps({"name":u_name, "time":str(datetime.now())}))

        except Exception as e:
            st.error(f"Error: {e}")

if 'data' in st.session_state:
    st.divider()
    if st.button("🤖 AI පලාපල වාර්තාව ලබාගන්න"):
        with st.spinner("AI විශ්ලේෂණය කරමින්..."):
            res = get_ai_prediction(str(st.session_state['data']))
            st.markdown(res)
