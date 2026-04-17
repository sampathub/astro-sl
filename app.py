import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, timedelta
import requests # Firebase සදහා
import json

# --- Configuration ---
st.set_page_config(page_title="AstroPro Sri Lanka v7", page_icon="☸️", layout="wide")

# --- 1. Multi-API Key Support (Load Balancing) ---
# Secrets වල GEMINI_API_KEY_1, GEMINI_API_KEY_2 ලෙස Keys කිහිපයක් දිය හැක
API_KEYS = [
    st.secrets.get("GEMINI_API_KEY_1"),
    st.secrets.get("GEMINI_API_KEY_2"),
    st.secrets.get("GEMINI_API_KEY_3")
]
# වැඩ කරන Key එකක් තෝරාගැනීම
current_key = next((k for k in API_KEYS if k), None)

def generate_ai_content(prompt):
    for key in API_KEYS:
        if not key: continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue # එකක් වැඩ නැත්නම් ඊළඟ එකට යන්න
    return "කණගාටුයි, සියලුම AI සේවාවන් මේ මොහොතේ කාර්යබහුලයි."

# --- 2. Firebase Database Config ---
FIREBASE_URL = "YOUR_FIREBASE_DATABASE_URL" # ඔබේ Firebase URL එක මෙතැනට දමන්න

def save_to_firebase(user_data):
    try:
        # sampathub89_gmail_com ලෙස Folder එකක් සැදීම
        db_path = f"{FIREBASE_URL}/users/sampathub89_gmail_com.json"
        requests.post(db_path, data=json.dumps(user_data))
    except Exception as e:
        print(f"Firebase Error: {e}")

# --- Data Arrays ---
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
# ... (අනෙක් MAP දත්ත කලින් පරිදිම වේ)

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("⚙️ පෞද්ගලික විස්තර")
    user_name = st.text_input("සම්පූර්ණ නම", placeholder="උදා: සම්පත් උදය බණ්ඩාර")
    dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20), min_value=datetime(1900,1,1), max_value=datetime(2100,12,31))
    t_col = st.columns(3)
    h = t_col[0].number_input("පැය", 0, 23, 10)
    m = t_col[1].number_input("විනාඩි", 0, 59, 30)
    s = t_col[2].number_input("තත්", 0, 59, 0)
    city = st.selectbox("උපන් දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
    
    if st.button("දත්ත මකා අලුතින් අරඹන්න"):
        st.rerun()

st.title("☸️ AstroPro SL - Firebase & Multi-API Support")

if st.button("කේන්ද්‍රය සහ දීර්ඝ පලාපල විග්‍රහය ලබාගන්න"):
    if not user_name:
        st.warning("කරුණාකර ඔබගේ නම ඇතුළත් කරන්න.")
    else:
        try:
            lat, lon = DISTRICTS[city]
            decimal_hour = h + m/60.0 + s/3600.0 - 5.5
            jd = swe.julday(dob.year, dob.month, dob.day, decimal_hour)
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            lagna_idx = int(ascmc[0] / 30)
            
            # ග්‍රහයන් ගණනය
            planets_def = {"රවි": swe.SUN, "සඳු": swe.MOON, "කුජ": swe.MARS, "බුධ": swe.MERCURY, "ගුරු": swe.JUPITER, "සිකුරු": swe.VENUS, "ශනි": swe.SATURN, "රාහු": swe.MEAN_NODE}
            pos_map = {i: [] for i in range(12)}
            planet_list = []
            
            moon_lon = 0
            for name, pid in planets_def.items():
                res, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
                if pid == swe.MOON: moon_lon = res[0]
                r_idx = int(res[0] / 30)
                pos_map[r_idx].append(name)
                planet_list.append(f"{name}:{RA_NAMES[r_idx]}")

            nak_idx = int(moon_lon / (360/27))
            
            # UI පෙන්වීම
            st.subheader(f"👤 නම: {user_name}")
            col1, col2 = st.columns(2)
            # ... (කේන්ද්‍ර සටහන සහ පංචාංග පෙන්වන කලින් code කොටස මෙතැනට)

            # AI පලාපල
            st.divider()
            summary = f"නම: {user_name}, ලග්නය: {RA_NAMES[lagna_idx]}, නැකත: {NAK_NAMES[nak_idx]}, ග්‍රහයන්: {', '.join(planet_list)}"
            
            with st.spinner("දීර්ඝ පලාපල විග්‍රහය සකසමින් පවතියි..."):
                prompt = f"ඔබ ලාංකීය ජ්‍යොතිෂ්‍ය ප්‍රවීණයෙකි. {summary} යන දත්ත මත පදනම්ව චරිතය, රැකියාව, සෞඛ්‍යය, විවාහය සහ අනාගතය ගැන දීර්ඝ විස්තරයක් සිංහලෙන් කරන්න."
                prediction = generate_ai_content(prompt)
                st.markdown(prediction)

            # Firebase වෙත දත්ත යැවීම
            data_to_save = {
                "name": user_name,
                "dob": str(dob),
                "birth_time": f"{h}:{m}:{s}",
                "city": city,
                "lagna": RA_NAMES[lagna_idx],
                "prediction": prediction[:500] + "...", # මුල් කොටස පමණක් සේව් කිරීමට
                "timestamp": str(datetime.now())
            }
            save_to_firebase(data_to_save)
            st.success("ඔබේ දත්ත සාර්ථකව පද්ධතියේ ගබඩා කරන ලදී.")

        except Exception as e:
            st.error(f"Error: {e}")
