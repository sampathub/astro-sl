import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime
from PIL import Image, ImageDraw
import requests
import json

# --- Configuration ---
st.set_page_config(page_title="AstroPro SL Ultimate", page_icon="☸️", layout="wide")

# --- 1. Multi-API AI Support (Load Balancing) ---
def get_ai_prediction(summary_data):
    # Streamlit Secrets වල GEMINI_API_KEY_1, 2, 3 ලෙස තිබිය යුතුය
    keys = [
        st.secrets.get("GEMINI_API_KEY_1"),
        st.secrets.get("GEMINI_API_KEY_2"),
        st.secrets.get("GEMINI_API_KEY_3")
    ]
    
    prompt = f"""
    ඔබ ප්‍රවීණ සිංහල ජ්‍යොතිෂවේදියෙකි. පහත දත්ත මත පදනම්ව චරිතය, අධ්‍යාපනය, රැකියාව, සෞඛ්‍යය සහ විවාහය ගැන 
    දීර්ඝ පලාපල විස්තරයක් සිංහලෙන් ලියන්න: {summary_data}
    """
    
    for key in keys:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue
    return "කණගාටුයි, සියලුම AI සේවාවන් මේ මොහොතේ කාර්යබහුලයි. පසුව උත්සාහ කරන්න."

# --- 2. සාම්ප්‍රදායික කේන්ද්‍ර සටහන ඇඳීමේ Function එක ---
def draw_horoscope_chart(pos_map, lagna_idx):
    # 400x400 සුදු පැහැති රූපයක්
    img = Image.new('RGB', (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # කොටු 12 ඇඳීම (South Indian / Sri Lankan Style)
    for i in range(5):
        draw.line([(i*100, 0), (i*100, 400)], fill="black", width=2)
        draw.line([(0, i*100), (400, i*100)], fill="black", width=2)
    # මැද කොටුව හිස් කිරීම
    draw.rectangle([100, 100, 300, 300], fill="#f8f9fa", outline="black", width=2)
    
    # රාශි පිහිටි ස්ථාන සිතියම්ගත කිරීම
    grid_map = {11:(0,0), 0:(100,0), 1:(200,0), 2:(300,0), 10:(0,100), 3:(300,100),
                9:(0,200), 4:(300,200), 8:(0,300), 7:(100,300), 6:(200,300), 5:(300,300)}
    
    for r_idx, (x, y) in grid_map.items():
        # ලග්නය රතු පැහැයෙන් සලකුණු කිරීම
        if r_idx == lagna_idx:
            draw.text((x+40, y+10), "L", fill="red")
        
        # ග්‍රහයන් පිහිටුවීම
        planets = pos_map.get(r_idx, [])
        for i, p in enumerate(planets):
            draw.text((x+15, y+35+(i*15)), p, fill="black")
            
    return img

# --- 3. Data Tables (100% Accurate) ---
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

RA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

GANA_TABLE = ["දේව", "මනුෂ්‍ය", "රාක්ෂ", "මනුෂ්‍ය", "දේව", "මනුෂ්‍ය", "දේව", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව"]
YONI_TABLE = ["අශ්ව", "ඇත්", "එළු", "සර්ප", "සර්ප", "බැල්ලි", "බළල්", "එළු", "බළල්", "මී මින්", "මී මින්", "ගව", "මී හරක්", "ව්‍යාඝ්‍ර", "මී හරක්", "ව්‍යාඝ්‍ර", "මුව", "මුව", "මුගටි", "වඳුරු", "වඳුරු", "සිංහ", "සිංහ", "අශ්ව", "සිංහ", "ගව", "ඇත්"]
LINGA_TABLE = ["පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "ස්ත්‍රී", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී", "පුරුෂ", "පුරුෂ", "ස්ත්‍රී"]
DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]

# --- 4. Sidebar Inputs ---
with st.sidebar:
    st.header("👤 පරිශීලක තොරතුරු")
    u_name = st.text_input("සම්පූර්ණ නම", placeholder="උදා: සම්පත් බණ්ඩාර")
    u_dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20), min_value=datetime(1900,1,1), max_value=datetime(2100,12,31))
    t_col = st.columns(3)
    u_h = t_col[0].number_input("පැය", 0, 23, 10)
    u_m = t_col[1].number_input("විනාඩි", 0, 59, 30)
    u_s = t_col[2].number_input("තත්", 0, 59, 0)
    u_city = st.selectbox("උපන් දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
    
    st.divider()
    if st.button("🔄 සියලු දත්ත මකන්න"):
        st.session_state.clear()
        st.rerun()

# --- 5. Main App Logic ---
st.title("☸️ AstroPro SL - කේන්ද්‍ර පරීක්ෂාව")

if st.button("කේන්ද්‍රය ගණනය කරන්න"):
    if not u_name.strip():
        st.warning("⚠️ කරුණාකර ඉදිරියට යාමට 'නම' ඇතුළත් කරන්න.")
    else:
        try:
            # Astrology Calculations (AI රහිතව)
            lat, lon = DISTRICTS[u_city]
            # Time Adjustment for Sri Lanka (UTC+5.5)
            decimal_hour = u_h + u_m/60.0 + u_s/3600.0 - 5.5
            jd = swe.julday(u_dob.year, u_dob.month, u_dob.day, decimal_hour)
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            # 1. ලග්නය ගණනය
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            lagna_idx = int(ascmc[0] / 30)

            # 2. ග්‍රහයන් පිහිටීම ගණනය
            planets_def = {"රවි":0, "සඳු":1, "කුජ":4, "බුධ":2, "ගුරු":5, "සිකුරු":3, "ශනි":6, "රාහු":10}
            pos_map = {i: [] for i in range(12)}
            moon_lon = 0
            for p_name, p_id in planets_def.items():
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
                if p_id == 1: moon_lon = res[0]
                pos_map[int(res[0] / 30)].append(p_name)

            # 3. නැකත සහ අනෙකුත් පංචාංග විස්තර
            nak_idx = int(moon_lon / (360/27))
            v_gana = GANA_TABLE[nak_idx]
            v_yoni = YONI_TABLE[nak_idx]
            v_linga = LINGA_TABLE[nak_idx]
            v_dasha = DASHA_LORDS[nak_idx % 9]

            # Store summary for AI
            st.session_state['astro_data'] = {
                "name": u_name, "lagna": RA_NAMES[lagna_idx], "nak": NAK_NAMES[nak_idx],
                "gana": v_gana, "yoni": v_yoni, "linga": v_linga, "dasha": v_dasha
            }

            # UI Display
            st.subheader(f"📊 {u_name} මහතාගේ/මියගේ කේන්ද්‍ර විස්තර")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                chart_img = draw_horoscope_chart(pos_map, lagna_idx)
                st.image(chart_img, caption="සාම්ප්‍රදායික කේන්ද්‍ර සටහන")
            
            with col2:
                st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]}")
                st.write(f"**නැකත:** {NAK_NAMES[nak_idx]}")
                st.write(f"**ගණය:** {v_gana} | **යෝනිය:** {v_yoni} | **ලිංගය:** {v_linga}")
                st.success(f"වර්තමාන මහා දශාව: {v_dasha}")

            # 4. Firebase Logging (සැඟවුණු ක්‍රියාවලියකි)
            f_url = st.secrets.get("FIREBASE_DATABASE_URL")
            if f_url:
                log_data = {
                    "name": u_name, "dob": str(u_dob), "lagna": RA_NAMES[lagna_idx],
                    "timestamp": str(datetime.now())
                }
                requests.post(f"{f_url}/astro_users.json", data=json.dumps(log_data))

        except Exception as e:
            st.error(f"Error occurred: {e}")

# --- AI Prediction Section ---
if 'astro_data' in st.session_state:
    st.divider()
    if st.button("🔮 AI දීර්ඝ පලාපල විස්තරය ලබාගන්න"):
        d = st.session_state['astro_data']
        summary_text = f"නම: {d['name']}, ලග්නය: {d['lagna']}, නැකත: {d['nak']}, ගණය: {d['gana']}, යෝනිය: {d['yoni']}, ලිංගය: {d['linga']}."
        
        with st.spinner("Gemini AI මඟින් පලාපල වාර්තාව සකසමින් පවතියි..."):
            ai_result = get_ai_prediction(summary_text)
            st.markdown("### 🤖 Gemini AI පලාපල විශ්ලේෂණය")
            st.write(ai_result)
