import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta

# App Settings
st.set_page_config(page_title="AstroPro Sri Lanka v4", page_icon="☸️", layout="wide")

st.title("☸️ AstroPro Sri Lanka - සම්පූර්ණ කේන්ද්‍ර විස්තරය")

# --- දත්ත පද්ධති ---
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
    t_col1, t_col2, t_col3 = st.columns(3)
    h = t_col1.number_input("පැය", 0, 23, 10)
    m = t_col2.number_input("විනාඩි", 0, 59, 30)
    s = t_col3.number_input("තත්", 0, 59, 0)
    city = st.selectbox("උපන් දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

# --- Calculation Engine ---
if st.button("කේන්ද්‍රය සහ සම්පූර්ණ විස්තර බලන්න"):
    try:
        lat, lon = DISTRICTS[city]
        decimal_hour = h + m/60.0 + s/3600.0 - 5.5
        jd = swe.julday(dob.year, dob.month, dob.day, decimal_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # 1. ලග්නය සහ ග්‍රහයින්
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

        # 2. නැකත, ගණය, යෝනිය
        nak_idx = int(moon_lon / (360/27))
        
        # --- UI DISPLAY ---
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            st.subheader("📍 කේන්ද්‍ර සටහන")
            # සාම්ප්‍රදායික කොටු 12 වගුව
            chart = [["" for _ in range(4)] for _ in range(4)]
            mapping = {11:(0,0), 0:(0,1), 1:(0,2), 2:(0,3), 10:(1,0), 3:(1,3), 9:(2,0), 4:(2,3), 8:(3,0), 7:(3,1), 6:(3,2), 5:(3,3)}
            for r_idx, names in pos_map.items():
                r, c = mapping[r_idx]
                chart[r][c] = " / ".join(names)
            st.table(chart)

        with col_b:
            st.subheader("📝 මූලික විස්තර")
            st.write(f"**ලග්නය:** {RA_NAMES[lagna_idx]}")
            st.write(f"**නැකත:** {NAK_NAMES[nak_idx]}")
            st.write(f"**ගණය:** {GANA_MAP[nak_idx]}")
            st.write(f"**යෝනිය:** {YONI_MAP[nak_idx]}")
            st.info(f"චන්ද්‍ර ස්ඵුටය: {moon_lon:.2f}°")

        st.divider()

        # 3. මහා දශා සහ අතුරු දශා
        st.subheader("🗓️ මහා දශා සහ අතුරු දශා කාලසටහන")
        lord_idx = nak_idx % 9
        elapsed = (moon_lon % (360/27)) / (360/27)
        rem_years = DASHA_YEARS[lord_idx] * (1 - elapsed)
        
        curr_date = datetime.combine(dob, datetime.min.time()) + timedelta(hours=h, minutes=m)
        dasha_table = []
        
        # පළමු දශා ශේෂය
        end_date = curr_date + timedelta(days=rem_years * 365.25)
        dasha_table.append({"මහා දශාව": DASHA_LORDS[lord_idx], "ආරම්භය": curr_date.strftime('%Y-%m-%d'), "අවසානය": end_date.strftime('%Y-%m-%d'), "තත්ත්වය": "ශේෂය (Balance)"})
        
        # මීළඟ දශා 3ක්
        next_start = end_date
        for i in range(1, 4):
            idx = (lord_idx + i) % 9
            end = next_start + timedelta(days=DASHA_YEARS[idx] * 365.25)
            dasha_table.append({"මහා දශාව": DASHA_LORDS[idx], "ආරම්භය": next_start.strftime('%Y-%m-%d'), "අවසානය": end.strftime('%Y-%m-%d'), "තත්ත්වය": "මහා දශා"})
            next_start = end
            
        st.table(dasha_table)

        # අතුරු දශා (වත්මන් මහා දශාවට)
        st.write(f"**{DASHA_LORDS[lord_idx]} මහා දශාව තුළ අතුරු දශා බෙදීම:**")
        bhukti = []
        for i in range(9):
            b_idx = (lord_idx + i) % 9
            months = (DASHA_YEARS[lord_idx] * DASHA_YEARS[b_idx]) / 120 * 12
            bhukti.append({"අතුරු දශා හිමි": DASHA_LORDS[b_idx], "කාලය (මාස)": round(months, 2)})
        st.dataframe(bhukti)

    except Exception as e:
        st.error(f"Error: {e}")
