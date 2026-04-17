import streamlit as st
import swisseph as swe
import google.generativeai as genai
from datetime import datetime, timedelta

# --- මූලික සැකසුම් (Configuration) ---
st.set_page_config(page_title="AstroPro Sri Lanka v5", page_icon="☸️", layout="wide")

# Gemini API සකස් කිරීම (ඔබේ API Key එක මෙතැනට ලබා දෙන්න)
API_KEY = "AQ.Ab8RN6KwUzyZUjMop3GH2VRUV98RWVGUqhFo2ZA4JYhPKfL99A" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- දත්ත පද්ධති (Data) ---
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

# --- Main Logic ---
st.title("☸️ AstroPro Sri Lanka - Full AI Edition")

if st.button("කේන්ද්‍රය සහ AI පලාපල විශ්ලේෂණය කරන්න"):
    try:
        lat, lon = DISTRICTS[city]
        decimal_hour = h + m/60.0 + s/3600.0 - 5.5
        jd = swe.julday(dob.year, dob.month, dob.day, decimal_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # 1. ග්‍රහයන් සහ ලග්නය ගණනය
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        lagna_idx = int(ascmc[0] / 30)
        
        planets = {"රවි": swe.SUN, "සඳු": swe.MOON, "කුජ": swe.MARS, "බුධ": swe.MERCURY, "ගුරු": swe.JUPITER, "සිකුරු": swe.VENUS, "ශනි": swe.SATURN, "රාහු": swe.MEAN_NODE}
        pos_map = {i: [] for i in range(12)}
        pos_map[lagna_idx].append("ලග්නය")
        
        moon_lon = 0
        for name, pid in planets.items():
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            if pid == swe.MOON: moon_lon = res[0]
            pos_map[int(res[0] / 30)].append(name)

        nak_idx = int(moon_lon / (360/27))

        # 2. UI Layout - Chart and Details
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📍 කේන්ද්‍ර සටහන")
            chart = [["" for _ in range(4)] for _ in range(4)]
            mapping = {11:(0,0), 0:(0,1), 1:(0,2), 2:(0,3), 10:(1,0), 3:(1,3), 9:(2,0), 4:(2,3), 8:(3,0), 7:(3,1), 6:(3,2), 5:(3,3)}
            for r_idx, names in pos_map.items():
                r, c = mapping[r_idx]
                chart[r][c] = " / ".join(names)
            st.table(chart)

        with col2:
            st.subheader("📝 මූලික තොරතුරු")
            st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]}")
            st.write(f"**නැකත:** {NAK_NAMES[nak_idx]}")
            st.write(f"**ගණය:** {GANA_MAP[nak_idx]}")
            st.write(f"**යෝනිය:** {YONI_MAP[nak_idx]}")
            st.info(f"චන්ද්‍ර ස්ඵුටය: {moon_lon:.2f}°")

        # 3. AI පලාපල විග්‍රහය (Gemini Integration)
        st.divider()
        st.subheader("🤖 AI පලාපල විග්‍රහය (Gemini AI)")
        
        summary_for_ai = f"ලග්නය: {RA_NAMES[lagna_idx]}, නැකත: {NAK_NAMES[nak_idx]}, ගණය: {GANA_MAP[nak_idx]}, යෝනිය: {YONI_MAP[nak_idx]}."
        
        with st.spinner("Gemini AI දත්ත විශ්ලේෂණය කරමින්..."):
            prompt = f"ඔබ ලාංකීය ජ්‍යොතිෂ්‍ය ප්‍රවීණයෙකි. මෙම දත්ත කියවා ඉතා කෙටියෙන්, සරල සිංහලෙන් පලාපල විග්‍රහයක් කරන්න: {summary_for_ai}. ලග්නය සහ නැකත ගැන විශේෂයෙන් සඳහන් කරන්න."
            response = model.generate_content(prompt)
            st.success("AI විශ්ලේෂණය අවසන්!")
            st.write(response.text)

        # 4. මහා දශා සහ අතුරු දශා
        st.divider()
        st.subheader("🗓️ මහා දශා සහ අතුරු දශා")
        lord_idx = nak_idx % 9
        elapsed = (moon_lon % (360/27)) / (360/27)
        rem_years = DASHA_YEARS[lord_idx] * (1 - elapsed)
        
        curr_date = datetime.combine(dob, datetime.min.time()) + timedelta(hours=h, minutes=m)
        dasha_table = []
        end_date = curr_date + timedelta(days=rem_years * 365.25)
        dasha_table.append({"මහා දශාව": DASHA_LORDS[lord_idx], "ආරම්භය": curr_date.strftime('%Y-%m-%d'), "අවසානය": end_date.strftime('%Y-%m-%d'), "තත්ත්වය": "ශේෂය (Balance)"})
        
        next_start = end_date
        for i in range(1, 4):
            idx = (lord_idx + i) % 9
            end = next_start + timedelta(days=DASHA_YEARS[idx] * 365.25)
            dasha_table.append({"මහා දශාව": DASHA_LORDS[idx], "ආරම්භය": next_start.strftime('%Y-%m-%d'), "අවසානය": end.strftime('%Y-%m-%d'), "තත්ත්වය": "මහා දශා"})
            next_start = end
        st.table(dasha_table)

        st.write(f"**{DASHA_LORDS[lord_idx]} මහා දශාව තුළ අතුරු දශා (මාස වලින්):**")
        bhukti = [{"අතුරු දශා හිමි": DASHA_LORDS[(lord_idx + i) % 9], "කාලය (මාස)": round((DASHA_YEARS[lord_idx] * DASHA_YEARS[(lord_idx + i) % 9]) / 10, 2)} for i in range(9)]
        st.dataframe(bhukti)

    except Exception as e:
        st.error(f"Error: {e}")
