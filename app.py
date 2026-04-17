import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, timedelta
import requests
import json

# --- Configuration ---
st.set_page_config(page_title="AstroPro Sri Lanka v7", page_icon="☸️", layout="wide")

# --- 1. Multi-API Key Support (Load Balancing) ---
API_KEYS = [
    st.secrets.get("GEMINI_API_KEY_1"),
    st.secrets.get("GEMINI_API_KEY_2"),
    st.secrets.get("GEMINI_API_KEY_3")
]

def generate_ai_content(prompt):
    """Try multiple API keys, return first successful response"""
    for i, key in enumerate(API_KEYS):
        if not key:
            continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.warning(f"API Key {i+1} වැඩ කිරීමට අසමත් විය. ඊළඟ key උත්සාහ කරමින්...")
            continue
    return "කණගාටුයි, සියලුම AI සේවාවන් මේ මොහොතේ කාර්යබහුලයි. කරුණාකර පසුව නැවත උත්සාහ කරන්න."

# --- 2. Firebase Database Config ---
FIREBASE_URL = "YOUR_FIREBASE_DATABASE_URL"

def save_to_firebase(user_data):
    try:
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

# යෝනි සහ ලිංග දත්ත
YONI_NAMES = ["අශ්ව", "ගජ", "මේෂ", "සර්ප", "ශ්වාන", "මාර්ජාර", "මූෂික", "ගව", "මහිෂ", "ව්‍යාඝ්‍ර", "මෘග", "වානර", "නකුල", "සිංහ"]
LINGA_NAMES = ["පුරුෂ", "ස්ත්‍රී", "නපුංසක"]

# නැකත් යෝනි mapping (27 නැකත් සඳහා)
NAK_YONI_MAP = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,0,1,2,3,4,5,6,7,8,9,10,11,12]
NAK_LINGA_MAP = [0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2]

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
    
    if st.button("🔄 දත්ත මකා අලුතින් අරඹන්න"):
        st.rerun()

st.title("☸️ AstroPro SL - කේන්ද්‍ර විශ්ලේෂණය")
st.markdown("---")

# Session state එකෙන් prediction store කරමු
if 'prediction' not in st.session_state:
    st.session_state.prediction = None
if 'planet_data' not in st.session_state:
    st.session_state.planet_data = None
if 'basic_data' not in st.session_state:
    st.session_state.basic_data = None

# --- ප්‍රධාන බොත්තම: කේන්ද්‍රය ගණනය කිරීම ---
if st.button("🔮 කේන්ද්‍රය ගණනය කරන්න", type="primary"):
    if not user_name:
        st.warning("⚠️ කරුණාකර ඔබගේ නම ඇතුළත් කරන්න.")
    else:
        try:
            lat, lon = DISTRICTS[city]
            decimal_hour = h + m/60.0 + s/3600.0 - 5.5
            jd = swe.julday(dob.year, dob.month, dob.day, decimal_hour)
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            # භාව සහ ලග්නය
            houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
            lagna_idx = int(ascmc[0] / 30)
            lagna_name = RA_NAMES[lagna_idx]
            
            # ග්‍රහයන් ගණනය
            planets_def = {"රවි": swe.SUN, "සඳු": swe.MOON, "කුජ": swe.MARS, "බුධ": swe.MERCURY, 
                          "ගුරු": swe.JUPITER, "සිකුරු": swe.VENUS, "ශනි": swe.SATURN, "රාහු": swe.MEAN_NODE}
            
            pos_map = {i: [] for i in range(12)}
            planet_list = []
            planet_details = {}
            
            moon_lon = 0
            for name, pid in planets_def.items():
                res, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
                lon_deg = res[0]
                if pid == swe.MOON:
                    moon_lon = lon_deg
                r_idx = int(lon_deg / 30)
                r_name = RA_NAMES[r_idx]
                pos_map[r_idx].append(name)
                planet_list.append(f"{name}: {r_name}")
                planet_details[name] = {"රාශිය": r_name, "අංශක": f"{lon_deg:.2f}°"}
            
            # නැකත, යෝනිය, ලිංගය ගණනය
            nak_idx = int(moon_lon / (360/27))
            nak_name = NAK_NAMES[nak_idx]
            yoni_idx = NAK_YONI_MAP[nak_idx] % len(YONI_NAMES)
            yoni_name = YONI_NAMES[yoni_idx]
            linga_idx = NAK_LINGA_MAP[nak_idx] % len(LINGA_NAMES)
            linga_name = LINGA_NAMES[linga_idx]
            
            # දශාවන් ගණනය (Vimshottari Dasha)
            dasha_years = [6, 10, 7, 18, 16, 19, 17, 7, 20]  # Sun to Ketu
            nak_start_deg = nak_idx * (360/27)
            moon_nak_deg = moon_lon - nak_start_deg
            remaining_deg = (360/27) - moon_nak_deg
            remaining_years = (remaining_deg / (360/27)) * dasha_years[nak_idx % 9]
            
            current_dasha_idx = nak_idx % 9
            dasha_names = ["රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ", "කේතු", "සිකුරු"]
            current_dasha = dasha_names[current_dasha_idx]
            
            # Basic data store කරමු
            st.session_state.basic_data = {
                "name": user_name,
                "lagna": lagna_name,
                "nakatha": nak_name,
                "yoniya": yoni_name,
                "lingaya": linga_name,
                "current_dasha": current_dasha,
                "dasha_remaining_years": f"{remaining_years:.2f}",
                "planet_details": planet_details,
                "planet_list": planet_list,
                "pos_map": pos_map
            }
            
            # UI එකේ කේන්ද්‍ර සටහන පෙන්වමු
            st.subheader(f"🌟 {user_name} ගේ ජ්‍යොතිෂ කේන්ද්‍රය")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 කේන්ද්‍ර සටහන")
                # රාශි චක්‍රය simple table එකක්
                chart_html = "<table border='1' style='width:100%; text-align:center;'>"
                for i in range(0, 12, 3):
                    chart_html += "<tr>"
                    for j in range(3):
                        r_idx = (i + j) % 12
                        planets_in_ra = ", ".join(pos_map[r_idx]) if pos_map[r_idx] else "-"
                        chart_html += f"<td><b>{RA_NAMES[r_idx]}</b><br>{planets_in_ra}</td>"
                    chart_html += "</tr>"
                chart_html += "</table>"
                st.markdown(chart_html, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🔮 මූලික තොරතුරු")
                st.metric("⭐ ලග්නය", lagna_name)
                st.metric("🌙 ජන්ම නැකත", nak_name)
                st.metric("🐘 යෝනිය", yoni_name)
                st.metric("⚥ ලිංගය", linga_name)
                st.metric("📅 වත්මන් දශාව", f"{current_dasha} (ඉතිරි වසර: {remaining_years:.2f})")
            
            # ග්‍රහ විස්තර
            with st.expander("🪐 සියලු ග්‍රහයන්ගේ විස්තර"):
                for name, details in planet_details.items():
                    st.write(f"**{name}**: {details['රාශිය']} රාශියේ, {details['අංශක']}")
            
            st.success("✅ කේන්ද්‍රය සාර්ථකව ගණනය කරන ලදී!")
            st.info("👇 පහත බොත්තම ඔබන්න - AI පලාපල විග්‍රහය ලබාගැනීමට")
            
        except Exception as e:
            st.error(f"❌ කේන්ද්‍රය ගණනය කිරීමේ දෝෂයක්: {e}")

# --- දෙවන බොත්තම: AI පලාපල විග්‍රහය (කේන්ද්‍රය ගණනය කළා නම් පමණක්) ---
if st.session_state.basic_data:
    if st.button("🤖 AI පලාපල විග්‍රහය ලබාගන්න", type="secondary"):
        with st.spinner("🌌 ගුරුන්ගේ ආශිර්වාදයෙන් පලාපල විග්‍රහය සකසමින්..."):
            data = st.session_state.basic_data
            
            summary = f"""
            නම: {data['name']}
            ලග්නය: {data['lagna']}
            ජන්ම නැකත: {data['nakatha']}
            යෝනිය: {data['yoniya']}
            ලිංගය: {data['lingaya']}
            වත්මන් දශාව: {data['current_dasha']} (ඉතිරි වසර: {data['dasha_remaining_years']})
            ග්‍රහ පිහිටුම්: {', '.join(data['planet_list'])}
            """
            
            prompt = f"""ඔබ ලාංකීය ජ්‍යොතිෂ්‍ය ප්‍රවීණයෙකි. පහත දත්ත මත පදනම්ව:

{summary}

කරුණාකර පහත කරුණු ඇතුළත් දීර්ඝ පලාපල විග්‍රහයක් සිංහලෙන් කරන්න:

1. චරිත ස්වභාවය සහ පෞරුෂ ලක්ෂණ
2. රැකියාව, වෘත්තිය සහ මුල්‍ය තත්වය
3. සෞඛ්‍ය තත්වය සහ විශේෂ අවධානය යොමු කළ යුතු කරුණු
4. විවාහ ජීවිතය, සහකරුගේ ලක්ෂණ
5. වාසනාවන්ත කාල පරිච්ඡේද (වත්මන් දශාව පදනම් කරගෙන)
6. අනාගත අභියෝග සහ ඒවාට විසඳුම්
7. පූජා, දාන, ග්‍රහ යන්ත්‍ර සහ ප්‍රායෝගික උපදෙස්

පිළිතුර වෘත්තීයමය, පැහැදිලි සහ සිංහල භාෂාවෙන් විය යුතුය."""
            
            st.session_state.prediction = generate_ai_content(prompt)
            
            if "කණගාටුයි" not in st.session_state.prediction:
                # Firebase වෙත සුරකිමු
                data_to_save = {
                    "name": data['name'],
                    "dob": str(dob),
                    "birth_time": f"{h}:{m}:{s}",
                    "city": city,
                    "lagna": data['lagna'],
                    "nakatha": data['nakatha'],
                    "prediction": st.session_state.prediction[:1000],
                    "timestamp": str(datetime.now())
                }
                save_to_firebase(data_to_save)
                st.success("💾 පලාපල විග්‍රහය සාර්ථකව සුරකින ලදී!")
            else:
                st.warning(st.session_state.prediction)

# --- ප්‍රතිඵල පෙන්වීම ---
if st.session_state.prediction and "කණගාටුයි" not in st.session_state.prediction:
    st.divider()
    st.markdown("## 📜 AI පලාපල විග්‍රහය")
    st.markdown(st.session_state.prediction)
    
    # Download button එකක්
    st.download_button(
        label="📥 PDF එකක් ලෙස බාගන්න",
        data=st.session_state.prediction,
        file_name=f"{user_name}_palapala.txt",
        mime="text/plain"
    )
else:
    st.info("💡 මුලින් 'කේන්ද්‍රය ගණනය කරන්න' බොත්තම ඔබන්න, ඉන්පසු AI පලාපල විග්‍රහය ලබාගන්න.")
