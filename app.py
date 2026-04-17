import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import requests
import json
import io

# --- Configuration ---
st.set_page_config(page_title="AstroVisual SL v8", page_icon="☸️", layout="wide")

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
    return "AI සේවාව දැනට අක්‍රියයි."

# --- Chart Drawing Function (සාම්ප්‍රදායික කේන්ද්‍රය) ---
def draw_south_indian_chart(pos_map, lagna_idx):
    # රූපය නිර්මාණය (400x400)
    img = Image.new('RGB', (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # කොටු ඇඳීම
    for i in range(5):
        draw.line([(i*100, 0), (i*100, 400)], fill="black", width=2)
        draw.line([(0, i*100), (400, i*100)], fill="black", width=2)
    draw.rectangle([100, 100, 300, 300], fill="white", outline="black", width=2)
    
    # රාශි පිහිටි තැන් (South Indian Style - Clockwise)
    grid_map = {11:(0,0), 0:(100,0), 1:(200,0), 2:(300,0), 10:(0,100), 3:(300,100),
                9:(0,200), 4:(300,200), 8:(0,300), 7:(100,300), 6:(200,300), 5:(300,300)}
    
    for r_idx, (x, y) in grid_map.items():
        names = pos_map.get(r_idx, [])
        text = "\n".join(names)
        if r_idx == lagna_idx:
            draw.text((x+5, y+5), "L", fill="red") # ලග්නය රතු පැහැයෙන්
        draw.text((x+25, y+25), text, fill="black")
        
    return img

# --- Data Tables ---
RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]
GANA_MAP = ["දේව", "මනුෂ්‍ය", "රාක්ෂ"] * 9
YONI_MAP = ["අශ්ව", "එළු", "එළු", "සර්ප", "සර්ප", "බැල්ලි", "බළල්", "බළල්", "මූෂික", "මූෂික", "මී හරක්", "මී හරක්", "මී හරක්", "ව්‍යාඝ්‍ර", "ව්‍යාඝ්‍ර", "මුව", "මුව", "මුගටි", "බැල්ලි", "වඳුරු", "වඳුරු", "සිංහ", "සිංහ", "අශ්ව", "සිංහ", "එළදෙන", "එළදෙන"]
LINGA_MAP = ["පුරුෂ", "ස්ත්‍රී"] * 14 # සරල කළ ලිංග බෙදීම

# --- Inputs ---
with st.sidebar:
    st.header("👤 විස්තර ඇතුළත් කරන්න")
    u_name = st.text_input("නම")
    u_dob = st.date_input("උපන් දිනය", datetime(1995, 5, 20))
    t_col = st.columns(3)
    u_h = t_col[0].number_input("පැය", 0, 23, 12)
    u_m = t_col[1].number_input("විනාඩි", 0, 59, 0)
    u_s = t_col[2].number_input("තත්", 0, 59, 0)
    u_city = st.selectbox("දිස්ත්‍රික්කය", ["කොළඹ", "ගම්පහ", "කළුතර", "මහනුවර", "මාතලේ", "නුවරඑළිය", "ගාල්ල", "මාතර", "හම්බන්තොට", "යාපනය", "මන්නාරම", "වවුනියාව", "මුලතිව්", "මඩකලපුව", "අම්පාර", "ත්‍රිකුණාමලය", "කුරුණෑගල", "පුත්තලම", "අනුරාධපුරය", "පොළොන්නරුව", "බදුල්ල", "මොණරාගල", "රත්නපුරය", "කෑගල්ල"])

# --- Core Logic ---
if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    # 1. Astro Calculations
    jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, u_h + u_m/60.0 - 5.5)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    houses, ascmc = swe.houses_ex(jd, 7.0, 80.0, b'P', swe.FLG_SIDEREAL) # කෑගල්ල ආසන්න අගයන්
    lagna_idx = int(ascmc[0] / 30)
    
    planets = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
    pos_map = {i: [] for i in range(12)}
    moon_lon = 0
    
    for n, p_id in planets.items():
        res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
        if p_id == 1: moon_lon = res[0]
        pos_map[int(res[0] / 30)].append(n)
        
    nak_idx = int(moon_lon / (360/27))
    
    # 2. Results Display
    st.header(f"☸️ {u_name} මහතාගේ/මියගේ කේන්ද්‍රය")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.image(draw_south_indian_chart(pos_map, lagna_idx), caption="සාම්ප්‍රදායික කේන්ද්‍ර සටහන")
    
    with c2:
        st.subheader("📊 පංචාංග විස්තර")
        st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]} | **නැකත:** {NAK_NAMES[nak_idx]}")
        st.write(f"**ගණය:** {GANA_MAP[nak_idx]} | **යෝනිය:** {YONI_MAP[nak_idx]} | **ලිංගය:** {LINGA_MAP[nak_idx]}")
        
        st.subheader("🗓️ මහා දශා කාලය")
        # දශා ගණනය (සරලව)
        d_lord = (nak_idx % 9)
        st.info(f"දැනට ගෙවෙන්නේ {['කේතු','සිකුරු','රවි','සඳු','කුජ','රාහු','ගුරු','ශනි','බුධ'][d_lord]} මහා දශාවයි.")

    # 3. Save to Firebase
    f_url = st.secrets.get("FIREBASE_DATABASE_URL")
    if f_url:
        fb_data = {"name": u_name, "lagna": RA_NAMES[lagna_idx], "nakatha": NAK_NAMES[nak_idx], "time": str(datetime.now())}
        requests.post(f"{f_url}/astro_logs.json", data=json.dumps(fb_data))
        st.toast("දත්ත Firebase වෙත යොමු කළා.")

    # 4. Separate Button for AI Prediction
    if st.button("AI දීර්ඝ පලාපල විස්තරය ලබාගන්න"):
        with st.spinner("AI පලාපල විශ්ලේෂණය කරමින්..."):
            p_summary = f"නම {u_name}, ලග්නය {RA_NAMES[lagna_idx]}, නැකත {NAK_NAMES[nak_idx]}."
            ai_text = get_ai_response(f"මෙම කේන්ද්‍ර විස්තරය අනුව රැකියාව, සෞඛ්‍යය සහ විවාහය ගැන සිංහලෙන් දීර්ඝ පලාපලයක් ලියන්න: {p_summary}")
            st.markdown(f"### 🤖 AI පලාපල විග්‍රහය\n{ai_text}")
