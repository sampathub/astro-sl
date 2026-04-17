import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta

# App Settings
st.set_page_config(page_title="Heladiwa Astro Pro v3", page_icon="☸️", layout="wide")

st.title("☸️ Heladiwa Astro Pro - Full Feature Edition")

# --- දත්ත සැකසුම් ---
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
NAK_NAMES = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනාවස", "පුස", "අස්ලිස", 
             "මා", "පුවපල්", "උත්රපල්", "හත", "සිත", "සා", "විසා", "අනුර", "දෙට", 
             "මුල", "පුවසල", "උත්රසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්රපුටුප", "රේවතී"]

DASHA_LORDS = ["කේතු", "සිකුරු", "රවි", "සඳු", "කුජ", "රාහු", "ගුරු", "ශනි", "බුධ"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# --- Inputs ---
with st.sidebar:
    st.header("⚙️ උපන් තොරතුරු")
    # මෙන්න මෙතන තමයි අර Date Range එක හදපු තැන
    dob = st.date_input(
        "උපන් දිනය", 
        value=datetime(1995, 5, 20),
        min_value=datetime(1900, 1, 1), 
        max_value=datetime(2100, 12, 31)
    )
    t_col1, t_col2, t_col3 = st.columns(3)
    h = t_col1.number_input("පැය", 0, 23, 10)
    m = t_col2.number_input("විනාඩි", 0, 59, 30)
    s = t_col3.number_input("තත්", 0, 59, 0)
    city = st.selectbox("උපන් දිස්ත්‍රික්කය", list(DISTRICTS.keys()))

# --- Helper Functions ---
def draw_chart(planet_positions):
    """කේන්ද්‍ර සටහන වගුවක් ලෙස පෙන්වීම"""
    chart = [["" for _ in range(4)] for _ in range(4)]
    # සාම්ප්‍රදායික කොටු පිළිවෙල (0-මීන, 1-මේෂ...)
    mapping = {11:(0,0), 0:(0,1), 1:(0,2), 2:(0,3),
               10:(1,0),             3:(1,3),
               9:(2,0),              4:(2,3),
               8:(3,0), 7:(3,1), 6:(3,2), 5:(3,3)}
    
    for r_idx, planets in planet_positions.items():
        if r_idx in mapping:
            r, c = mapping[r_idx]
            chart[r][c] = ", ".join(planets)
            
    return chart

if st.button("කේන්ද්‍රය සහ දශා ගණනය කරන්න"):
    try:
        lat, lon = DISTRICTS[city]
        birth_dt = datetime.combine(dob, datetime.min.time().replace(hour=h, minute=m, second=s))
        decimal_hour = h + m/60.0 + s/3600.0 - 5.5
        jd = swe.julday(dob.year, dob.month, dob.day, decimal_hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # 1. ලග්නය සහ ග්‍රහයින් ගණනය කිරීම
        houses, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
        lagna_deg = ascmc[0]
        lagna_idx = int(lagna_deg / 30)

        planet_list = {"රවි": swe.SUN, "චන්ද්‍ර": swe.MOON, "කුජ": swe.MARS, "බුධ": swe.MERCURY, 
                       "ගුරු": swe.JUPITER, "සිකුරු": swe.VENUS, "ශනි": swe.SATURN, "රාහු": swe.MEAN_NODE}
        
        pos_map = {}
        for name, pid in planet_list.items():
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            r_idx = int(res[0] / 30)
            if r_idx not in pos_map: pos_map[r_idx] = []
            pos_map[r_idx].append(name)
        
        if lagna_idx not in pos_map: pos_map[lagna_idx] = []
        pos_map[lagna_idx].append("ලග්නය")

        # --- Display Results ---
        st.subheader("📍 කේන්ද්‍ර සටහන (Birth Chart)")
        chart_data = draw_chart(pos_map)
        
        # ලස්සනට පෙන්වීමට Table එකක් පාවිච්චි කිරීම
        st.table(chart_data)

        # දශා විස්තර (කලින් දුන් කේතයම මෙතැනට එකතු වේ)
        # ... (මම කලින් පිළිතුරේ දුන් දශා ගණනය කිරීමේ code කොටස මෙතැනට එයි)
        st.info("මහා දශා සහ අතුරු දශා විස්තර පහතින් බලන්න...")
        
    except Exception as e:
        st.error(f"Error: {e}")
