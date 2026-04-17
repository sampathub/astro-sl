import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(page_title="AstroPro Sri Lanka v6", page_icon="☸️", layout="wide")

## පැරණි API_KEY පේළිය ඉවත් කර මෙය ඇතුළත් කරන්න
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

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
GANA_MAP = ["දේව", "මනුෂ්‍ය", "රාක්ෂ", "මනුෂ්‍ය", "දේව", "දේව", "දේව", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව", "රාක්ෂ", "රාක්ෂ", "මනුෂ්‍ය", "මනුෂ්‍ය", "දේව"]
YONI_MAP = ["අශ්ව", "එළු", "එළු", "සර්ප", "සර්ප", "බැල්ලි", "බළල්", "බළල්", "මූෂික", "මූෂික", "මී හරක්", "මී හරක්", "මී හරක්", "ව්‍යාඝ්‍ර", "ව්‍යාඝ්‍ර", "මුව", "මුව", "මුගටි", "බැල්ලි", "වඳුරු", "වඳුරු", "සිංහ", "සිංහ", "අශ්ව", "සිංහ", "එළදෙන", "එළදෙන"]
DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("⚙️ දත්ත ඇතුළත් කරන්න")
    dob = st.date_input("උපන් දිනය", value=datetime(1995, 5, 20), min_value=datetime(1900,1,1), max_value=datetime(2100,12,31))
    t_col = st.columns(3)
    h = t_col[0].number_input("පැය", 0, 23, 10)
    m = t_col[1].number_input("විනාඩි", 0, 59, 30)
    s = t_col[2].number_input("තත්", 0, 59, 0)
    city = st.selectbox("උපන් දිස්ත්‍රික්කය", list(DISTRICTS.keys()))
    
    # Clear Data Button
    if st.button("දත්ත මකා අලුතින් අරඹන්න"):
        st.rerun()

st.title("☸️ AstroPro SL - Advanced AI Analysis")

# --- Logic ---
if st.button("කේන්ද්‍රය සහ දීර්ඝ AI පලාපල විග්‍රහය ලබාගන්න"):
    try:
        lat, lon = DISTRICTS[city]
        decimal_hour = h + m/60.0 + s/3600.0 - 5.5
        jd = swe.julday(dob.year, dob.month, dob.day, decimal_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # 1. Calculations
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        lagna_idx = int(ascmc[0] / 30)
        
        planets_def = {"රවි": swe.SUN, "සඳු": swe.MOON, "කුජ": swe.MARS, "බුධ": swe.MERCURY, "ගුරු": swe.JUPITER, "සිකුරු": swe.VENUS, "ශනි": swe.SATURN, "රාහු": swe.MEAN_NODE}
        pos_map = {i: [] for i in range(12)}
        planet_data_text = []
        
        moon_lon = 0
        for name, pid in planets_def.items():
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            deg = res[0]
            if pid == swe.MOON: moon_lon = deg
            r_idx = int(deg / 30)
            pos_map[r_idx].append(name)
            planet_data_text.append(f"{name} සිටින්නේ {RA_NAMES[r_idx]} රාශියේය.")

        nak_idx = int(moon_lon / (360/27))
        
        # 2. Display Charts
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📍 කේන්ද්‍ර සටහන")
            chart = [["" for _ in range(4)] for _ in range(4)]
            mapping = {11:(0,0), 0:(0,1), 1:(0,2), 2:(0,3), 10:(1,0), 3:(1,3), 9:(2,0), 4:(2,3), 8:(3,0), 7:(3,1), 6:(3,2), 5:(3,3)}
            temp_map = pos_map.copy()
            if "ලග්නය" not in temp_map[lagna_idx]: temp_map[lagna_idx].append("ලග්නය")
            for r_idx, names in temp_map.items():
                r, c = mapping[r_idx]
                chart[r][c] = " / ".join(names)
            st.table(chart)

        with col2:
            st.subheader("📝 පංචාංග තොරතුරු")
            st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]}")
            st.write(f"**නැකත:** {NAK_NAMES[nak_idx]}")
            st.write(f"**ගණය:** {GANA_MAP[nak_idx]}")
            st.write(f"**යෝනිය:** {YONI_MAP[nak_idx]}")

        # 3. AI Deep Analysis
        st.divider()
        st.subheader("🤖 Gemini AI දීර්ඝ පලාපල විග්‍රහය")
        
        lord_idx = nak_idx % 9
        summary = (f"උපන් ලග්නය: {RA_NAMES[lagna_idx]}, නැකත: {NAK_NAMES[nak_idx]}, ගණය: {GANA_MAP[nak_idx]}, "
                   f"යෝනිය: {YONI_MAP[nak_idx]}. ග්‍රහ පිහිටීම්: {', '.join(planet_data_text)}. "
                   f"උපතේදී මහා දශාව: {DASHA_LORDS[lord_idx]}.")

        with st.spinner("Gemini AI ඔබගේ ජීවිත කාලයම විශ්ලේෂණය කරමින් පවතියි..."):
            prompt = f"""
            ඔබ ලාංකීය ජ්‍යොතිෂ්‍ය ප්‍රවීණයෙකි. පහත දත්ත මත පදනම්ව ඉතා විස්තරාත්මක සහ දීර්ඝ පලාපල විග්‍රහයක් සිංහලෙන් කරන්න.
            මෙහිදී පහත මාතෘකා යටතේ කරුණු දක්වන්න:
            1. චරිතය සහ පෞරුෂය (Character & Personality)
            2. අධ්‍යාපනය සහ බුද්ධි මට්ටම (Education)
            3. රැකියාව සහ ධනය (Career & Wealth)
            4. සෞඛ්‍යය (Health)
            5. විවාහය සහ පවුල් ජීවිතය (Marriage & Family)
            6. ගෙවුණු කාලය සහ දැනට පවතින කාලය (Past & Present Period)
            7. අනාගතය සහ විශේෂ අවවාද (Future & Advice)
            
            දත්ත: {summary}
            කරුණාකර ඉතා කාරුණික සහ උපදේශාත්මක බසක් භාවිතා කරන්න.
            """
            response = model.generate_content(prompt)
            st.markdown(response.text)

        # 4. Dasha Table
        st.divider()
        st.subheader("🗓️ දශා කාලසටහන")
        elapsed = (moon_lon % (360/27)) / (360/27)
        rem_years = DASHA_YEARS[lord_idx] * (1 - elapsed)
        curr_date = datetime.combine(dob, datetime.min.time()) + timedelta(hours=h, minutes=m)
        
        d_table = []
        end_date = curr_date + timedelta(days=rem_years * 365.25)
        d_table.append({"මහා දශාව": DASHA_LORDS[lord_idx], "අවසානය": end_date.strftime('%Y-%m-%d'), "තත්ත්වය": "ශේෂය"})
        
        next_s = end_date
        for i in range(1, 6): # ඉදිරි දශා 5ක් පෙන්වමු
            idx = (lord_idx + i) % 9
            end = next_s + timedelta(days=DASHA_YEARS[idx] * 365.25)
            d_table.append({"මහා දශාව": DASHA_LORDS[idx], "අවසානය": end.strftime('%Y-%m-%d'), "තත්ත්වය": "ඉදිරියට"})
            next_s = end
        st.table(d_table)

    except Exception as e:
        st.error(f"Error: {e}")
