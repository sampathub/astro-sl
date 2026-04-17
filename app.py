import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageFont
import requests
import json

# --- Configuration ---
st.set_page_config(page_title="AstroPro Sri Lanka v11", page_icon="☸️", layout="wide")

# --- 1. Multi-API AI Support ---
def get_ai_prediction(summary_data):
    keys = [st.secrets.get("GEMINI_API_KEY_1"), st.secrets.get("GEMINI_API_KEY_2"), st.secrets.get("GEMINI_API_KEY_3")]
    prompt = f"ඔබ ප්‍රවීණ ජ්‍යොතිෂවේදියෙකි. මෙම දත්ත මත පදනම්ව දීර්ඝ පලාපල විස්තරයක් සිංහලෙන් කරන්න: {summary_data}"
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            return model.generate_content(prompt).text
        except: continue
    return "AI සේවාව දැනට කාර්යබහුලයි."

# --- 2. කේන්ද්‍ර සටහන වඩාත් පැහැදිලිව ඇඳීම ---
def draw_styled_chart(pos_map, lagna_idx):
    # වඩාත් පැහැදිලි රූපයක් (600x600)
    img = Image.new('RGB', (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # කොටු ඇඳීම
    for i in range(5):
        draw.line([(i*150, 0), (i*150, 600)], fill="black", width=3)
        draw.line([(0, i*150), (600, i*150)], fill="black", width=3)
    
    # මැද කොටුව (Background)
    draw.rectangle([150, 150, 450, 450], fill="#fff9e6", outline="black", width=3)
    
    # රාශි පිහිටීම (Sinhala Labels)
    grid_map = {11:(0,0), 0:(150,0), 1:(300,0), 2:(450,0), 10:(0,150), 3:(450,150),
                9:(0,300), 4:(450,300), 8:(0,450), 7:(150,450), 6:(300,450), 5:(450,450)}
    
    for r_idx, (x, y) in grid_map.items():
        if r_idx == lagna_idx:
            draw.text((x+60, y+10), "L", fill="red") # ලග්නය
        
        planets = pos_map.get(r_idx, [])
        for i, p in enumerate(planets):
            # මෙහි ඉංග්‍රීසි අකුරු භාවිතා කරන්නේ Font ප්‍රශ්න මඟහරවා ගැනීමටයි
            # (S-Sun, M-Moon, Ma-Mars, Me-Merc, J-Jup, V-Ven, Sa-Sat, R-Rahu)
            p_short = {"රවි":"Sun", "සඳු":"Moon", "කුජ":"Mars", "බුධ":"Merc", "ගුරු":"Jup", "සිකුරු":"Ven", "ශනි":"Sat", "රාහු":"Rahu"}
            draw.text((x+20, y+40+(i*25)), p_short.get(p, p), fill="black")
            
    return img

# --- 3. ජ්‍යොතිෂ දත්ත වගු (නිවැරදි කරන ලද) ---
DISTRICTS = {"කෑගල්ල": (7.2513, 80.3464), "කොළඹ": (6.9271, 79.8612), "ගම්පහ": (7.0840, 79.9927), "මහනුවර": (7.2906, 80.6337), "ගාල්ල": (6.0535, 80.2210), "මාතර": (5.9549, 80.5550)} # තවත් දිස්ත්‍රික්ක පෙර පරිදිම එක් කරන්න

NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

# අලුතින් එක් කළ දත්ත (Vruksha & Pakshi)
VRUKSHA_TABLE = ["කදම්බ", "නෙල්ලි", "දිවුල්", "කරඹ", "කීරිය", "තිඹිරි", "උණ", "බෝගහ", "නුග", "පලු", "කෑල", "නුග", "වල් දෙල්", "බෙලි", "කුඹුක්", "මීඹ", "දම්", "වැටකේ", "සල්", "පුවක්", "පිහිඹියා", "වෙලං", "ලූණුමකරල", "කලවැල්", "කොහොඹ", "මී", "වැටකේ"]
PAKSHI_TABLE = ["හොට කිරලා", "කපුටා", "කපුටා", "පින්නකිකිළි", "පින්නකිකිළි", "පින්නකිකිළි", "මොණරා", "මොණරා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "කුකුළා", "මොණරා", "මොණරා", "මොණරා", "මොණරා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "සිංහයා", "මොණරා", "මොණරා", "මොණරා"]

GANA_TABLE = ["දේව", "මනුෂ්‍ය", "රාක්ෂ"] * 9
DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# --- 4. Sidebar ---
with st.sidebar:
    st.header("👤 තොරතුරු")
    u_name = st.text_input("නම")
    u_dob = st.date_input("උපන් දිනය", value=date(1995, 5, 20))
    t_col = st.columns(2)
    u_h = t_col[0].number_input("පැය", 0, 23, 10)
    u_m = t_col[1].number_input("විනාඩි", 0, 59, 30)
    u_city = st.selectbox("දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
    if st.button("මකන්න"):
        st.session_state.clear()
        st.rerun()

# --- 5. Main Logic ---
st.title("☸️ AstroPro Sri Lanka - වෘක්ෂ/පක්ෂි/දශා සහිතව")

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    if not u_name:
        st.warning("නම ඇතුළත් කරන්න.")
    else:
        try:
            lat, lon = DISTRICTS[u_city]
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, u_h + u_m/60.0 - 5.5)
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
            
            # --- Calculations ---
            nak_idx = int(moon_lon / (360/27))
            v_gana = GANA_TABLE[nak_idx % 3]
            v_vruksha = VRUKSHA_TABLE[nak_idx]
            v_pakshi = PAKSHI_TABLE[nak_idx]
            
            # දශා කාලය ගණනය (Balance Dasha)
            dasha_idx = nak_idx % 9
            nak_start = nak_idx * (360/27)
            passed_deg = moon_lon - nak_start
            balance_factor = 1 - (passed_deg / (360/27))
            balance_years = balance_factor * DASHA_YEARS[dasha_idx]

            # Display
            st.subheader(f"📊 {u_name} මහතාගේ පංචාංග විස්තර")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(draw_styled_chart(pos_map, lagna_idx), caption="පැහැදිලි කේන්ද්‍ර සටහන")
            
            with col2:
                st.markdown(f"**ලග්නය:** {RA_NAMES[lagna_idx]}  \n**නැකත:** {NAK_NAMES[nak_idx]}")
                st.markdown(f"**වෘක්ෂය:** {v_vruksha}  \n**පක්ෂියා:** {v_pakshi}")
                st.markdown(f"**ගණය:** {v_gana}")
                
                st.subheader("🗓️ මහා දශා තොරතුරු")
                st.info(f"උපතේදී හිමි දශාව: {DASHA_LORDS[dasha_idx]}")
                st.write(f"ඉතිරි කාලය: වසර {int(balance_years)} යි, මාස {int((balance_years%1)*12)} කි.")
                
                # දශා ලැයිස්තුව
                st.write("**මීළඟ දශා කාලසීමාවන්:**")
                current_yr = u_dob.year + balance_years
                for i in range(1, 5):
                    next_d_idx = (dasha_idx + i) % 9
                    duration = DASHA_YEARS[next_d_idx]
                    st.write(f"- {DASHA_LORDS[next_d_idx]} දශාව: {int(current_yr)} සිට {int(current_yr + duration)} දක්වා")
                    current_yr += duration

            st.session_state['summary'] = f"නම: {u_name}, ලග්නය: {RA_NAMES[lagna_idx]}, නැකත: {NAK_NAMES[nak_idx]}, වෘක්ෂය: {v_vruksha}, පක්ෂියා: {v_pakshi}."

        except Exception as e:
            st.error(f"Error: {e}")

# AI Button
if 'summary' in st.session_state:
    st.divider()
    if st.button("🤖 AI දීර්ඝ පලාපල වාර්තාව ලබාගන්න"):
        with st.spinner("Gemini AI වාර්තාව සකසමින්..."):
            res = get_ai_prediction(st.session_state['summary'])
            st.markdown(res)
